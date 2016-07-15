import collections
import logging

from bidict import namedbidict
import braintree

from .compat import getcallargs

logger = logging.getLogger(__name__)

IDMap = namedbidict('IDMap', 'fake_id', 'real_id')


def ensure_state_is_init(f):
    def wrapper(*args, **kwargs):
        # There's not currently a place to provide global init for the state dict,
        # each action needs to ensure subitems are initialized.

        named_args = getcallargs(f, *args, **kwargs)
        state = named_args['state']

        if 'id_maps' not in state:
            state['id_maps'] = collections.defaultdict(IDMap)
        if 'last_fake_ids' not in state:
            state['last_fake_ids'] = {}

        return f(*args, **kwargs)
    return wrapper


def clear_old_creation_ids(state, call_params, options):
    # Used as a start_hook in appcode entry points (ie, not __init__)
    # to ensure that old state doesn't stick around.
    state['last_fake_ids'] = {}


@ensure_state_is_init
def convert_to_real_id(params, schema_params, key, resource_id, state, options):
    fake_id = params[key]
    id_maps = state['id_maps']

    # When replacing, we always default to the value itself.
    # This means that when we don't have the necessary bookkeeping
    # to replace it, everything still proceeds normally.
    real_id = fake_id
    try:
        real_id = id_maps[resource_id.bt_class].fake_id_for[fake_id]
    except KeyError:
        # This can happen in two cases:
        #   * The caller made a mistake and didn't create the resource yet.
        #   * The caller created the resource, but not through our (patched) braintree library.
        if (('strict_missing_exception' in options or
             options.get('strict_missing', False))):
            exception = options.get('strict_missing_exception', braintree.exceptions.NotFoundError)
            raise exception
        else:
            logger.warning("The braintree id %r has not been previously stored."
                           " Either the resource was never created,"
                           " or it was not created through this client and namespace.", fake_id)

    params[key] = real_id
    logger.debug("%r --[real_id]--> %r", fake_id, params[key])


@ensure_state_is_init
def delete_and_store(params, schema_params, key, resource_id, state, options):
    provided_id = params[key]
    bt_class = resource_id.bt_class
    id_maps = state['id_maps']

    if provided_id in id_maps[bt_class].fake_id_for:
        # Properly handle duplicate creates of the same id.
        # We should pass these through, since the gateway will return an error.
        params[key] = id_maps[bt_class].fake_id_for[provided_id]
        logger.debug("would have deleted, but %r has been used in a prior creation", provided_id)
    else:
        # We need to know which id the client expects the response to be mapped to.
        # This only works because multiple creations are impossible.
        state['last_fake_ids'][bt_class] = provided_id
        del params[key]
        logger.debug("deleting %r in create call", provided_id)


@ensure_state_is_init
def convert_to_fake_id(params, schema_params, key, resource_id, state, options):
    real_id = params[key]
    id_maps = state['id_maps']
    bt_class = resource_id.bt_class
    last_fake_ids = state['last_fake_ids']

    if real_id not in id_maps[bt_class].real_id_for:
        # We need to update our mapping.
        # This condition also prevents us from updating existing mappings,
        # which we'd want to change to support id updates.

        if bt_class in last_fake_ids:
            # An id was provided during creation; include it in our mapping.
            fake_id = last_fake_ids.pop(bt_class)
        else:
            # There are actually two cases here, but we don't currently distinguish
            # between them:
            #    1) No id provided during creation: self-map this key.
            #    2) We don't have bookkeeping for this id at all: this is an error,
            #       but the chance of it happening and *also* disrupting normal
            #       operation is incredibly slim.
            fake_id = real_id

        id_maps[bt_class].fake_id_for[fake_id] = real_id
        logger.debug('mapping updated: fake_id %r == %r', fake_id, real_id)

    params[key] = id_maps[bt_class].real_id_for[real_id]
    logger.debug("%r <--[fake_id]-- %r", params[key], real_id)
