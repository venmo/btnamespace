import collections

import braintree

from .patch import SchemaPatcher
from .schemas import schemas
from .shared import UnsupportedSearchNode


class Namespace(object):
    """A Namespace is a context manager which guarantees that state on Braintree
    will not be shared."""

    def __init__(self, custom_schemas=None):
        """
        :param customer_schemas: (optional) a list of CallSchemas to guide patching.
          If they're not provided, those defined in actions.schemas will be used.
        """

        if custom_schemas is None:
            custom_schemas = schemas

        self.schemas = custom_schemas
        self.schema_patcher = SchemaPatcher()
        self.original_methods = collections.defaultdict(dict)
        self.original_advanced_searches = collections.defaultdict(dict)

    def __enter__(self):
        """Globally patch the braintree library to create a new namespace.

        Only one namespace may be active at any time.
        Results from entering more than once are undefined.
        """
        # TODO enter/exit should either be idempotent or nest properly; they're neither right now.

        self._save_original_methods()
        self._patch_all_methods()

        self._save_original_advanced_searches()
        self._patch_advanced_searches()

    def __exit__(self, *exc):
        self._restore_original_methods()
        self._restore_advanced_searches()

    def _save_original_methods(self):
        for schema in self.schemas:
            bt_class, method_name = schema.bt_class, schema.method_name
            self.original_methods[bt_class][method_name] = getattr(bt_class, method_name)

    def _save_original_advanced_searches(self):
        self.original_advanced_searches = {
            braintree.CustomerSearch: {
                'id': braintree.CustomerSearch.id,
                'payment_method_token': braintree.CustomerSearch.payment_method_token,
                'payment_method_token_with_duplicates':
                braintree.CustomerSearch.payment_method_token_with_duplicates,
            },
            braintree.TransactionSearch: {
                'id': braintree.TransactionSearch.id,
                'payment_method_token': braintree.TransactionSearch.payment_method_token,
                'customer_id': braintree.TransactionSearch.customer_id
            }
        }

    def _patch_all_methods(self):
        self.schema_patcher.apply_patches(schemas)

    def _patch_advanced_searches(self):
        for search_class, attribute_to_node in self.original_advanced_searches.iteritems():
            for attribute in attribute_to_node:
                setattr(search_class, attribute, UnsupportedSearchNode())

    def _restore_original_methods(self):
        for cls, action_name_to_method in self.original_methods.items():
            for action_name, orig_method in action_name_to_method.items():
                setattr(cls, action_name, staticmethod(orig_method))

    def _restore_advanced_searches(self):
        for search_class, attribute_to_node in self.original_advanced_searches.iteritems():
            for attribute, node in attribute_to_node.iteritems():
                setattr(search_class, attribute, node)
