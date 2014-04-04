import copy
import inspect
import logging

from decorator import decorator

from .schemas import ResourceId
from .shared import get_caller_args

logger = logging.getLogger(__name__)


class SchemaPatcher(object):
    def __init__(self):
        self._action_state = {}

    def apply_patches(self, call_schemas):
        for call_schema in call_schemas:
            self._apply_patch(call_schema)

    def _apply_patch(self, call_schema):
        # We can't do this inside the loop since we need to ensure the
        # correct schema is closed over.
        # The normal trick (copying at compile-time with a default argument)
        # won't work, since we require f as the first arg and
        # generic args after that.

        # This third-party module will doctor up our patched method's arg signature
        # to match the one we're wrapping.
        # Without it, we wouldn't be able to use get_caller_args().
        @decorator
        def wrapper(original_function, *args, **kwargs):
            # This is a dictionary of named arguments.
            # It doesn't matter how they were passed (which kwargs would take into account).
            named_args, _ = get_caller_args()

            # Avoid mutating caller objects.
            # We can't just do deepcopy(named_args), because then we'll make copies of
            # self and gateway.
            named_args_copy = copy.copy(named_args)
            for key in call_schema.params:
                named_args_copy[key] = copy.deepcopy(named_args_copy[key])

            if call_schema.start_hook is not None:
                call_schema.start_hook(self._action_state, named_args_copy)

            self._apply_param_actions(named_args_copy, call_schema.params)

            return original_function(**named_args_copy)

        bt_class = call_schema.bt_class
        original_method = getattr(bt_class, call_schema.method_name)

        # See http://stackoverflow.com/a/9527450 for more details on this block.
        #TODO is there a more generic way of doing this?
        # Currently, classmethods and properties aren't handled.
        if not inspect.ismethod(original_method):
            # This is a staticmethod, so ensure the descriptor gets created.
            wrapped = staticmethod(wrapper(original_method))
        else:
            # This is an unbound method.
            # Method objects aren't callable: we want the function object.
            wrapped = wrapper(original_method.__func__)

        setattr(bt_class, call_schema.method_name, wrapped)

    def _apply_param_actions(self, params, schema_params):
        """Traverse a schema and perform the updates it describes to params."""

        for key, val in schema_params.items():
            if key not in params:
                continue

            if isinstance(val, dict):
                self._apply_param_actions(params[key], schema_params[key])
            elif isinstance(val, ResourceId):
                resource_id = val

                # Callers can provide ints as ids.
                # We normalize them to strings so that actions don't get confused.
                params[key] = str(params[key])

                resource_id.action(params, schema_params, key,
                                   resource_id, self._action_state)
            else:
                logger.error("Invalid value in schema params: %r. schema_params: %r and params: %r",
                             val, schema_params, params)
