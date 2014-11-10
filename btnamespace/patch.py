import copy
import functools
import logging

from mock import patch

from .compat import getcallargs
from .schemas import ResourceId

logger = logging.getLogger(__name__)


class PatchedMethod(object):
    """Instances of this callable replace braintree methods."""

    def __init__(self, method, state, call_schema, options):
        """
        :param method: a staticmethod or instance method
        :param state: the state dictionary to provide to actions
        :param call_schema
        :param options: dictionary with arbitrary contents passed through to actions
        """

        self.method = method
        self.state = state
        self.call_schema = call_schema
        self.options = options

    def __call__(self, *args, **kwargs):
        named_args = getcallargs(self.method, *args, **kwargs)

        # Avoid mutating caller objects.
        # We can't just do deepcopy(named_args), because then we'll make copies of
        # self and gateway.
        named_args_copy = copy.copy(named_args)
        for key in self.call_schema.params:
            named_args_copy[key] = copy.deepcopy(named_args_copy[key])

        if self.call_schema.start_hook is not None:
            self.call_schema.start_hook(self.state, named_args_copy, self.options)

        self._apply_param_actions(named_args_copy, self.call_schema.params)

        if (('self' in named_args_copy
             and args[0] is named_args_copy['self'])):
            # Receivers need to be passed positionally, apparently.
            receiver = named_args_copy.pop('self')
            return self.method(receiver, **named_args_copy)

        return self.method(**named_args_copy)

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
                                   resource_id, self.state, self.options)
            else:
                logger.error("Invalid value in schema params: %r. schema_params: %r and params: %r",
                             val, schema_params, params)

    def __get__(self, obj, objtype):
        if obj is None:
            # This is a staticmethod; don't provide the receiver.
            return self.__call__

        # This is an instance method; freeze the receiver onto the call.
        return functools.partial(self.__call__, obj)


class SchemaPatcher(object):
    def __init__(self, options):
        self._action_state = {}
        self.options = options

    def create_patchers(self, call_schemas):
        patchers = []

        for call_schema in call_schemas:
            bt_class = call_schema.bt_class
            original_method = getattr(bt_class, call_schema.method_name)

            replacement = PatchedMethod(original_method, self._action_state,
                                        call_schema, self.options)
            patchers.append(patch.object(bt_class, call_schema.method_name, replacement))

        return patchers
