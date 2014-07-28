import braintree

from .actions import (
    clear_old_creation_ids,
    convert_to_real_id,
    delete_and_store,
    convert_to_fake_id
)
from .shared import ResourceId, CallSchema


def creation_id(bt_class):
    return ResourceId(bt_class, action=delete_and_store)


def fake_id(bt_class):
    return ResourceId(bt_class, action=convert_to_real_id)


def real_id(bt_class):
    return ResourceId(bt_class, action=convert_to_fake_id)


def schema(**kwargs):
    if 'start_hook' not in kwargs:
        kwargs['start_hook'] = None

    return CallSchema(**kwargs)


schemas = [
    schema(
        bt_class=braintree.Customer,
        method_name='__init__',
        params={
            'attributes': {
                # Semantically, this is read as:
                #  "this param will be a real id of a Customer".
                'id': real_id(braintree.Customer),
            }
        }
    ),
    schema(
        bt_class=braintree.Customer,
        method_name='create',
        start_hook=clear_old_creation_ids,
        params={
            'params': {
                'id': creation_id(braintree.Customer),
                'credit_card': {
                    'token': creation_id(braintree.CreditCard),
                }
            }
        },
    ),
    schema(
        bt_class=braintree.Customer,
        method_name='update',
        start_hook=clear_old_creation_ids,
        params={
            'customer_id': fake_id(braintree.Customer),
            'params': {
                'credit_card': {
                    'options': {
                        'update_existing_token': fake_id(braintree.CreditCard),
                    }
                }
            }
        }
    ),
    schema(
        bt_class=braintree.Customer,
        method_name='find',
        start_hook=clear_old_creation_ids,
        params={
            'customer_id': fake_id(braintree.Customer),
        }
    ),
    schema(
        bt_class=braintree.Customer,
        method_name='delete',
        start_hook=clear_old_creation_ids,
        params={
            'customer_id': fake_id(braintree.Customer),
        }
    ),

    # cards
    schema(
        bt_class=braintree.CreditCard,
        method_name='__init__',
        params={
            'attributes': {
                'token': real_id(braintree.CreditCard),
                'customer_id': real_id(braintree.Customer),
            }
        }
    ),
    schema(
        bt_class=braintree.CreditCard,
        method_name='create',
        start_hook=clear_old_creation_ids,
        params={
            'params': {
                'token': creation_id(braintree.CreditCard),
                'customer_id': fake_id(braintree.Customer),
            }
        },
    ),
    schema(
        bt_class=braintree.CreditCard,
        method_name='update',
        start_hook=clear_old_creation_ids,
        params={
            'credit_card_token': fake_id(braintree.CreditCard),
        }
    ),
    schema(
        bt_class=braintree.CreditCard,
        method_name='find',
        start_hook=clear_old_creation_ids,
        params={
            'credit_card_token': fake_id(braintree.CreditCard),
        }
    ),
    schema(
        bt_class=braintree.CreditCard,
        method_name='delete',
        start_hook=clear_old_creation_ids,
        params={
            'credit_card_token': fake_id(braintree.CreditCard),
        }
    ),

    # transactions
    schema(
        bt_class=braintree.Transaction,
        method_name='__init__',
        params={
            'attributes': {
                'id': real_id(braintree.Transaction),
            }
        }
    ),
    schema(
        bt_class=braintree.Transaction,
        method_name='create',
        start_hook=clear_old_creation_ids,
        params={
            'params': {
                'id': creation_id(braintree.Transaction),
                'customer_id': fake_id(braintree.Customer),
                'payment_method_token': fake_id(braintree.CreditCard),
                'credit_card': {
                    'token': creation_id(braintree.CreditCard),
                },
                'customer': {
                    'id': creation_id(braintree.Customer),
                },
            }
        },
    ),
    schema(
        bt_class=braintree.Transaction,
        method_name='find',
        start_hook=clear_old_creation_ids,
        params={
            'transaction_id': fake_id(braintree.Transaction),
        }
    ),
    # Transactions can not be deleted nor updated.

    # client tokens
    schema(
        bt_class=braintree.ClientToken,
        method_name='generate',
        params={
            'params': {
                'customer_id': fake_id(braintree.Customer)
            }
        }
    ),
]
