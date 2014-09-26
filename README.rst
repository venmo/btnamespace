btnamespace
===========

.. image:: https://travis-ci.org/venmo/btnamespace.svg?branch=master
    :target: https://travis-ci.org/venmo/btnamespace

A Braintree namespace isolates state on the Braintree gateway:

.. code-block:: python

    import braintree
    import btnamespace

    with btnamespace.Namespace():
        customer = braintree.Customer.create({"id": "123"})
        assert customer.id == "123"
        braintree.Customer.find("123")  # success

    braintree.Customer.find("123")  # NotFound exception

This is primarily useful during integration tests:

.. code-block:: python

    def setUp(self):
        self.namespace = btnamespace.Namespace()
        self.namespace.__enter__()

    def test_some_sandbox_integration(self):
        #...

    def tearDown(self):
        self.namespace.__exit__()


Compared to calling eg ``braintree.Customer.delete`` during ``tearDown``, this has a number of advantages:

-  it's faster, since no teardown is needed
-  it's simpler, since it doesn't require any bookkeeping
-  it's robust, since tests can be written without any state assumptions

You can install it with ``$ pip install btnamespace``.


What's supported
----------------

- Customer create, update, find, delete
- CreditCard create, update, find, delete
- Transaction create, find

All operations involving subresources - eg creating a CreditCard and Customer in one call - work as expected.

Adding support for other operations is easy; we just haven't needed them yet.
Contributions welcome!


How it Works
------------

Under the hood, a Namespace globally patches the braintree client library.

During create operations, any provided ids are removed.
This forces the gateway to respond with unique ids, which are later mapped back to the originally-provided ids.
Here's an example:

- on a call to ``braintree.Customer.create({'id': '123', ...})``, ``'123'`` is stored as a Customer id and the call becomes ``braintree.Customer.create({...})``.
- then, the server returns a unique id ``'abcde'`` for the Customer. ``'123'`` is mapped to ``'abcde'``, and the resulting Customer object's id is set to ``'123'``.
- later, a call to ``braintree.Customer.find('123')`` becomes ``braintree.Customer.find('abcde')``.


Contributing
------------

Inside your vitualenv:

.. code-block:: bash

    $ cd btnamespace
    $ pip install -e .
    $ pip install -r requirements.txt


To run the tests, first add your sandbox credentials:

.. code-block:: bash

    $ export BT_MERCHANT_ID=merchant-id
    $ export BT_PUBLIC_KEY=public-id
    $ export BT_PRIVATE_KEY=private-key


Then run ``$ python tests/test_integration.py``.
