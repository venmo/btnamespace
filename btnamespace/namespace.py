import collections

import braintree
from mock import patch

from .patch import SchemaPatcher
from .schemas import schemas
from .shared import UnsupportedSearchNode


class Namespace(object):
    """A Namespace is a context manager which guarantees that state on Braintree
    will not be shared."""

    def __init__(self, custom_schemas=None, options=None):
        """
        :param customer_schemas: (optional) a list of CallSchemas to guide patching.
          If they're not provided, those defined in actions.schemas will be used.
        :param options (optional) a dictionary of configuration passed through to
          actions. Built in options:
              * 'strict_missing': raise a braintree.exceptions.NotFoundError when
                non-namespaced resources are requested. By default this will be
                warned and logged, but the request allowed to be made.

          All options are False by default.
        """

        if custom_schemas is None:
            custom_schemas = schemas

        if options is None:
            options = {}

        self.schemas = custom_schemas
        self.options = options
        self.schema_patcher = SchemaPatcher(self.options)
        self._patchers = self.schema_patcher.create_patchers(self.schemas)

        search_patch_nodes = {
            braintree.CustomerSearch: [
                'id', 'payment_method_token', 'payment_method_token_with_duplicates'],

            braintree.TransactionSearch: [
                'id', 'payment_method_token', 'customer_id'],
        }

        for search_cls, node_names in search_patch_nodes.items():
            for node_name in node_names:
                self._patchers.append(
                    patch.object(search_cls, node_name, UnsupportedSearchNode())
                )

    def __enter__(self):
        """Globally patch the braintree library to create a new namespace.

        Only one namespace may be active at any time.
        Results from entering more than once are undefined.
        """
        for patcher in self._patchers:
            patcher.start()

    def __exit__(self, *exc):
        for patcher in self._patchers:
            patcher.stop()
