import copy
import os
import uuid

import braintree
from unittest2 import TestCase, main

from btnamespace import Namespace, NamespaceError

braintree.Configuration.configure(
    braintree.Environment.Sandbox,
    os.environ['BT_MERCHANT_ID'],
    os.environ['BT_PUBLIC_KEY'],
    os.environ['BT_PRIVATE_KEY'],
)


def _ensure_user_exists(user_params):
    try:
        braintree.Customer.find(user_params['id'])
    except braintree.exceptions.NotFoundError:
        braintree.Customer.create(user_params)

    braintree.Customer.find(user_params['id'])


class ActionOutsideNamespaceTest(TestCase):
    def test_customer_operations_outside_of_namespace(self):
        with self.assertRaises(braintree.exceptions.NotFoundError):
            braintree.Customer.find('nonexistent')

        _ensure_user_exists({
            'id': 'nonnamespaced',
        })

        with Namespace():
            pass

        try:
            braintree.Customer.find('nonnamespaced')
        except braintree.exceptions.NotFoundError:
            self.fail()


class NamespaceTest(TestCase):
    def setUp(self):
        self.namespace = Namespace()
        self.namespace.__enter__()
        self.addCleanup(self.namespace.__exit__)


class OptionsTest(NamespaceTest):
    def test_omit_options_gets_empty(self):
        namespace = Namespace()
        self.assertEqual(namespace.options, {})


class StrictMissingOptionTest(NamespaceTest):
    def setUp(self):
        _ensure_user_exists({
            "id": "existing",
            "first_name": "Existing",
            "last_name": "User",
        })

        # Cleanups are run LIFO, so this runs outside of the namespace.
        self.addCleanup(braintree.Customer.delete, 'existing')
        super(StrictMissingOptionTest, self).setUp()

    def test_existing_nonnamespace_user_found_with_default_options(self):
        braintree.Customer.find('existing')  # should not raise NotFoundError

    def test_strict_missing_will_404_existing_nonnamespace_user(self):
        self.namespace.options['strict_missing'] = True

        with self.assertRaises(braintree.exceptions.NotFoundError):
            braintree.Customer.find('existing')

    def test_strict_missing_exception_overrides_notfounderror(self):
        self.namespace.options['strict_missing'] = True
        self.namespace.options['strict_missing_exception'] = ValueError

        with self.assertRaises(ValueError):
            braintree.Customer.find('existing')


class PatchDeleteTest(NamespaceTest):
    def test_delete_customer(self):
        result = braintree.Customer.create({
            "id": "customer_id",
            "first_name": "Jen",
            "last_name": "Smith",
            "company": "Braintree",
            "email": "jen@example.com",
            "phone": "312.555.1234",
            "fax": "614.555.5678",
            "website": "www.example.com"
        })
        self.assertTrue(result.is_success, result)

        result = braintree.Customer.delete('customer_id')
        self.assertTrue(result.is_success, result)

    def test_delete_credit_card(self):
        result = braintree.Customer.create({
            "id": "customer_id",
            "first_name": "Jen",
            "last_name": "Smith",
            "company": "Braintree",
            "email": "jen@example.com",
            "phone": "312.555.1234",
            "fax": "614.555.5678",
            "website": "www.example.com",
            "credit_card": {
                "token": "credit_card_token",
                "number": "4111111111111111",
                "expiration_date": "05/2015",
                "cvv": "123"
            }
        })
        self.assertTrue(result.is_success, result)

        result = braintree.CreditCard.delete('credit_card_token')
        self.assertTrue(result.is_success, result)


class PatchFindTest(NamespaceTest):
    def test_find_customer(self):
        result = braintree.Customer.create({
            "id": "customer_id",
            "first_name": "Jen",
            "last_name": "Smith",
            "company": "Braintree",
            "email": "jen@example.com",
            "phone": "312.555.1234",
            "fax": "614.555.5678",
            "website": "www.example.com",
            "credit_card": {
                "token": "credit_card_token",
                "number": "4111111111111111",
                "expiration_date": "05/2015",
                "cvv": "123"
            }
        })
        self.assertTrue(result.is_success, result)

        customer = braintree.Customer.find('customer_id')
        self.assertEqual(customer.id, 'customer_id')
        self.assertEqual(customer.credit_cards[0].token, 'credit_card_token')

    def test_find_card(self):
        result = braintree.Customer.create({
            "id": "customer_id",
            "first_name": "Jen",
            "last_name": "Smith",
            "company": "Braintree",
            "email": "jen@example.com",
            "phone": "312.555.1234",
            "fax": "614.555.5678",
            "website": "www.example.com",
            "credit_card": {
                "token": "credit_card_token",
                "number": "4111111111111111",
                "expiration_date": "05/2015",
                "cvv": "123"
            }
        })
        self.assertTrue(result.is_success, result)

        card = braintree.CreditCard.find('credit_card_token')
        self.assertEqual(card.token, 'credit_card_token')

    def test_find_transaction(self):
        result = braintree.Transaction.sale({
            "id": "txn_id",
            "amount": "10.00",
            "order_id": str(uuid.uuid4()),  # sidestep duplicate transaction validation
            "credit_card": {
                "token": "credit_card_token",
                "number": "4111111111111111",
                "expiration_date": "05/2015",
                "cvv": "123"
            },
            "customer": {
                "id": "customer_id",
                "first_name": "Drew",
                "last_name": "Smith",
                "company": "Braintree",
                "phone": "312-555-1234",
                "fax": "312-555-1235",
                "website": "http://www.example.com",
                "email": "drew@example.com"
            },
        })
        self.assertTrue(result.is_success, result)

        transaction = braintree.Transaction.find('txn_id')

        self.assertEqual(transaction.id, 'txn_id')
        self.assertEqual(transaction.customer_details.id, 'customer_id')
        self.assertEqual(transaction.credit_card_details.token, 'credit_card_token')


class PatchUpdateTest(NamespaceTest):
    def test_update_customer(self):
        result = braintree.Customer.create({
            "id": "customer_id",
            "first_name": "Jen",
            "last_name": "Smith",
            "company": "Braintree",
            "email": "jen@example.com",
            "phone": "312.555.1234",
            "fax": "614.555.5678",
            "website": "www.example.com",
            "credit_card": {
                "token": "credit_card_token",
                "number": "4111111111111111",
                "expiration_date": "05/2015",
                "cvv": "123"
            }
        })
        self.assertTrue(result.is_success, result)
        result = braintree.Customer.update('customer_id', {"first_name": "Jenny"})
        self.assertTrue(result.is_success, result)

        self.assertEqual(result.customer.id, 'customer_id')
        self.assertEqual(result.customer.credit_cards[0].token, 'credit_card_token')

    def test_update_customer_and_existing_card(self):
        result = braintree.Customer.create({
            "id": "customer_id",
            "first_name": "Jen",
            "last_name": "Smith",
            "company": "Braintree",
            "email": "jen@example.com",
            "phone": "312.555.1234",
            "fax": "614.555.5678",
            "website": "www.example.com",
            "credit_card": {
                "token": "credit_card_token",
                "number": "4111111111111111",
                "expiration_date": "05/2015",
                "cvv": "123"
            }
        })
        self.assertTrue(result.is_success, result)

        result = braintree.Customer.update('customer_id', {
            'first_name': 'Jenny',
            'credit_card': {
                'cvv': '123',
                'expiration_date': '08/2016',
                'options': {
                    'update_existing_token': 'credit_card_token',
                }
            }
        })
        self.assertTrue(result.is_success, result)

        self.assertEqual(result.customer.first_name, 'Jenny')
        self.assertEqual(result.customer.credit_cards[0].expiration_date, '08/2016')

    def test_update_credit_card(self):
        result = braintree.Customer.create({
            "id": "customer_id",
            "first_name": "Jen",
            "last_name": "Smith",
            "company": "Braintree",
            "email": "jen@example.com",
            "phone": "312.555.1234",
            "fax": "614.555.5678",
            "website": "www.example.com",
            "credit_card": {
                "token": "credit_card_token",
                "number": "4111111111111111",
                "expiration_date": "05/2015",
                "cvv": "123"
            }
        })
        self.assertTrue(result.is_success, result)

        result = braintree.CreditCard.update('credit_card_token', {
            'number': '4005519200000004',
            'cvv': '123'
        })
        self.assertEqual(result.credit_card.token, 'credit_card_token')


class PatchCreateTest(NamespaceTest):
    def setUp(self):
        super(PatchCreateTest, self).setUp()

        self.customer_params_no_id = {
            "first_name": "Jen",
            "last_name": "Smith",
            "company": "Braintree",
            "email": "jen@example.com",
            "phone": "312.555.1234",
            "fax": "614.555.5678",
            "website": "www.example.com",
        }

        self.card_params_no_token = {
            "number": "4111111111111111",
            "expiration_date": "05/2015",
            "cardholder_name": "The Cardholder",
            "cvv": "123",
        }

    def id_maps(self):
        # This isn't super clean: we're using internal knowledge of action state.
        return self.namespace.schema_patcher._action_state['id_maps']

    def get_real_id(self, bt_class, fake_id):
        return self.id_maps()[bt_class].fake_ids[fake_id]

    def get_fake_id(self, bt_class, real_id):
        return self.id_maps()[bt_class].real_ids[real_id]

    def assert_self_mapping(self, bt_class, fake_id):
        """Assert that this id is mapped symetrically to itself."""
        self.assertEqual(fake_id, self.get_fake_id(bt_class, fake_id))
        self.assertEqual(fake_id, self.get_real_id(bt_class, fake_id))

    def assert_nonself_mapping(self, bt_class, fake_id):
        """Assert that this id is mapped to something other than itself
        (ie, a random braintree-provided id)."""
        real_id = self.get_real_id(bt_class, fake_id)
        self.assertNotEqual(fake_id, real_id)


class PatchCustomerCreate(PatchCreateTest):
    def test_create_patch_no_id(self):
        result = braintree.Customer.create(self.customer_params_no_id)
        self.assertTrue(result.is_success, result)
        real_id = result.customer.id

        self.assert_self_mapping(braintree.Customer, real_id)

    def test_create_patch_with_id(self):
        customer_params = copy.copy(self.customer_params_no_id)
        customer_params['id'] = 'original_id'

        result = braintree.Customer.create(customer_params)
        self.assertTrue(result.is_success, result)
        self.assertEqual(result.customer.id, "original_id")

        self.assert_nonself_mapping(braintree.Customer, 'original_id')

    def test_create_patch_with_card_no_token(self):
        customer_params = copy.copy(self.customer_params_no_id)
        customer_params['id'] = 'original_id'
        customer_params['credit_card'] = self.card_params_no_token

        result = braintree.Customer.create(customer_params)
        self.assertTrue(result.is_success, result)
        self.assertEqual(result.customer.id, "original_id")
        self.assertEqual(len(result.customer.credit_cards), 1)
        server_tok = result.customer.credit_cards[0].token

        self.assert_nonself_mapping(braintree.Customer, 'original_id')
        self.assert_self_mapping(braintree.CreditCard, server_tok)

    def test_create_patch_with_card_and_token(self):
        customer_params = copy.copy(self.customer_params_no_id)
        customer_params['id'] = 'original_id'

        customer_params['credit_card'] = self.card_params_no_token
        customer_params['credit_card']['token'] = 'original_tok'

        result = braintree.Customer.create(customer_params)
        self.assertTrue(result.is_success, result)
        self.assertEqual(result.customer.id, "original_id")
        self.assertEqual(len(result.customer.credit_cards), 1)
        self.assertEqual(result.customer.credit_cards[0].token, "original_tok")

        self.assert_nonself_mapping(braintree.Customer, 'original_id')
        self.assert_nonself_mapping(braintree.CreditCard, 'original_tok')

    def test_double_create_causes_error(self):
        """Creating a customer twice should return an error from the gateway."""

        customer_params = copy.copy(self.customer_params_no_id)
        customer_params['id'] = 'original_id'

        result = braintree.Customer.create(customer_params)
        self.assertTrue(result.is_success, result)

        result = braintree.Customer.create(customer_params)
        self.assertFalse(result.is_success, result)

    def test_different_class_stale_state_is_ignored(self):
        # Make a failed request that provides a card token.
        customer_params = copy.copy(self.customer_params_no_id)
        customer_params['credit_card'] = copy.copy(self.card_params_no_token)
        customer_params['credit_card']['token'] = 'tok_from_failure'
        customer_params['credit_card']['cvv'] = 'invalid cvv'

        result = braintree.Customer.create(customer_params)
        self.assertFalse(result.is_success, result)

        # Make a good request without a card token.
        result = braintree.Customer.create(self.customer_params_no_id)
        self.assertTrue(result.is_success, result)
        customer_id = result.customer.id
        card_params = self.card_params_no_token
        card_params['customer_id'] = customer_id
        result = braintree.CreditCard.create(self.card_params_no_token)
        self.assertTrue(result.is_success, result)

        # The token from the failed request shouldn't be returned.
        self.assertNotEqual(result.credit_card.token, 'tok_from_failure')


class PatchTransactionCreate(PatchCreateTest):
    def setUp(self):
        super(PatchTransactionCreate, self).setUp()
        self.txn_params_no_id = {
            'amount': '10.00',
            'order_id': str(uuid.uuid4())  # sidestep duplicate transaction validation
        }

    def test_create_patch_with_customer_card_and_token(self):
        params = self.txn_params_no_id
        params['id'] = 'orig_txn_id'
        params['amount'] = '10.00'
        params['credit_card'] = self.card_params_no_token
        params['credit_card']['token'] = 'orig_cc_tok'
        params['customer'] = self.customer_params_no_id
        params['customer']['id'] = 'orig_cust_id'

        result = braintree.Transaction.sale(params)

        self.assertTrue(result.is_success, result)
        self.assertEqual(result.transaction.id, "orig_txn_id")
        self.assertEqual(result.transaction.customer_details.id, "orig_cust_id")
        self.assertEqual(result.transaction.credit_card_details.token, "orig_cc_tok")

        self.assert_nonself_mapping(braintree.Customer, 'orig_cust_id')
        self.assert_nonself_mapping(braintree.CreditCard, 'orig_cc_tok')
        self.assert_nonself_mapping(braintree.Transaction, 'orig_txn_id')

    def test_create_with_existing_card(self):
        customer_params = copy.copy(self.customer_params_no_id)
        customer_params['id'] = 'orig_cust_id'

        result = braintree.Customer.create(customer_params)
        self.assertTrue(result.is_success, result)
        customer_id = result.customer.id

        card_params = self.card_params_no_token
        card_params['token'] = 'orig_cc_tok'
        card_params['customer_id'] = customer_id
        result = braintree.CreditCard.create(card_params)
        self.assertTrue(result.is_success, result)
        card_tok = result.credit_card.token

        txn_params = self.txn_params_no_id
        txn_params['payment_method_token'] = card_tok
        txn_params['id'] = 'orig_txn_id'
        txn_params['customer_id'] = customer_id

        result = braintree.Transaction.sale(txn_params)
        self.assertTrue(result.is_success)
        self.assertEqual(result.transaction.id, "orig_txn_id")
        self.assertEqual(result.transaction.customer_details.id, "orig_cust_id")
        self.assertEqual(result.transaction.credit_card_details.token, "orig_cc_tok")

        self.assert_nonself_mapping(braintree.Customer, 'orig_cust_id')
        self.assert_nonself_mapping(braintree.CreditCard, 'orig_cc_tok')
        self.assert_nonself_mapping(braintree.Transaction, 'orig_txn_id')


class PatchCreditCardCreate(PatchCreateTest):
    def setUp(self):
        super(PatchCreditCardCreate, self).setUp()

        # cards can only be added to existing customers
        result = braintree.Customer.create(self.customer_params_no_id)
        self.assertTrue(result.is_success, result)
        self.customer_id = result.customer.id

    def test_create_with_token(self):
        params = copy.copy(self.card_params_no_token)
        params['customer_id'] = self.customer_id
        params['token'] = 'orig_tok'

        result = braintree.CreditCard.create(params)

        self.assertTrue(result.is_success, result)
        self.assertEqual(result.credit_card.token, "orig_tok")
        self.assert_nonself_mapping(braintree.CreditCard, 'orig_tok')

    def test_create_no_token(self):
        params = copy.copy(self.card_params_no_token)
        params['customer_id'] = self.customer_id

        result = braintree.CreditCard.create(params)

        self.assertTrue(result.is_success, result)
        server_tok = result.credit_card.token
        self.assert_self_mapping(braintree.CreditCard, server_tok)

    def test_same_class_stale_state_is_ignored(self):
        """Ensure creation ids from failed requests don't stick around."""

        params = copy.copy(self.card_params_no_token)

        params['token'] = 'first_id'
        result = braintree.CreditCard.create(params)
        self.assertFalse(result.is_success, result)

        params['token'] = 'second_id'
        params['customer_id'] = self.customer_id
        result = braintree.CreditCard.create(params)
        self.assertTrue(result.is_success, result)

        self.assertTrue('first_id' not in self.id_maps()[braintree.CreditCard].fake_ids)
        self.assertTrue('second_id' in self.id_maps()[braintree.CreditCard].fake_ids)


class PatchAdvancedSearch(NamespaceTest):
    def test_customer_advanced_search_on_id(self):
        with self.assertRaises(NamespaceError):
            braintree.Customer.search(
                braintree.CustomerSearch.id == 'my_id'
            )

    def test_customer_advanced_search_on_payment_method_token(self):
        with self.assertRaises(NamespaceError):
            braintree.Customer.search(
                braintree.CustomerSearch.payment_method_token == 'my_tok'
            )

    def test_customer_advanced_search_on_payment_method_token_with_duplicates(self):
        with self.assertRaises(NamespaceError):
            braintree.Customer.search(
                braintree.CustomerSearch.payment_method_token_with_duplicates == 'my_tok'
            )

    def test_transaction_advanced_search_on_id(self):
        with self.assertRaises(NamespaceError):
            braintree.Transaction.search(
                braintree.TransactionSearch.id == 'my_id'
            )

    def test_transaction_advanced_search_on_payment_method_token(self):
        with self.assertRaises(NamespaceError):
            braintree.Transaction.search(
                braintree.TransactionSearch.payment_method_token == 'my_tok'
            )

    def test_transaction_advanced_search_on_customer_id(self):
        with self.assertRaises(NamespaceError):
            braintree.Transaction.search(
                braintree.TransactionSearch.customer_id == 'my_id'
            )


class PatchClientTokenGenerate(NamespaceTest):
    def test_client_token_generate_with_customer_id(self):
        result = braintree.Customer.create({
            "id": "customer_id",
            "first_name": "Jen",
            "last_name": "Smith",
            "company": "Braintree",
            "email": "jen@example.com",
            "phone": "312.555.1234",
            "fax": "614.555.5678",
            "website": "www.example.com"
        })
        self.assertTrue(result.is_success, result)
        client_token = braintree.ClientToken.generate({'customer_id': 'customer_id'})
        self.assertIsNotNone(client_token)


class PatchAllTest(TestCase):
    @staticmethod
    def _get_current_methods():
        return [
            braintree.Customer.__init__,
            braintree.Customer.find,
            braintree.Customer.create,
            braintree.Customer.delete,
            braintree.Customer.update,
            braintree.CreditCard.__init__,
            braintree.CreditCard.find,
            braintree.CreditCard.create,
            braintree.CreditCard.delete,
            braintree.CreditCard.update,
            braintree.Transaction.__init__,
            braintree.Transaction.find,
            braintree.Transaction.create,
        ]

    @staticmethod
    def _get_current_search_nodes():
        return [
            braintree.CustomerSearch.id,
            braintree.CustomerSearch.payment_method_token,
            braintree.CustomerSearch.payment_method_token_with_duplicates,
            braintree.TransactionSearch.id,
            braintree.TransactionSearch.payment_method_token,
            braintree.TransactionSearch.customer_id,
        ]

    def test_schema_methods_get_patched(self):
        original_methods = self._get_current_methods()

        with Namespace():
            patched_methods = self._get_current_methods()

        unpatched_methods = self._get_current_methods()

        for original_method, patched_method, unpatched_method in \
                zip(original_methods, patched_methods, unpatched_methods):
            self.assertEqual(original_method, unpatched_method)
            self.assertNotEqual(original_method, patched_method)

    def test_advanced_search_gets_patched(self):
        original_nodes = self._get_current_search_nodes()

        with Namespace():
            patched_nodes = self._get_current_search_nodes()

        unpatched_nodes = self._get_current_search_nodes()

        # NamespaceError is raised on __getattribute__ for patched nodes.
        for orig_node, unpatched_node in zip(original_nodes, unpatched_nodes):
            self.assertIs(orig_node, unpatched_node)
            self.assertIsNone(getattr(orig_node, 'foo', None))  # should not raise NamespaceError

        for node in patched_nodes:
            with self.assertRaises(NamespaceError):
                node.foo

if __name__ == '__main__':
    main()
