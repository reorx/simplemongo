Simplemongo
===========

.. image:: https://travis-ci.org/reorx/simplemongo.png
  :target: https://travis-ci.org/reorx/simplemongo

.. image:: https://coveralls.io/repos/reorx/simplemongo/badge.png?branch=master
  :target: https://coveralls.io/r/reorx/simplemongo?branch=master


Inspired by `Mongokit <https://github.com/namlook/mongokit>`_, Simplemongo shares
the same concept on designing the object oriented interface:
using a predefined dict to restrict structure and value type of the document.
( *mongoengine represents another genre, which use a rdbms way like django orm and that
make simple things complicated* ) But the validation mechanism of Simplemongo are formulated
to be more reasonable and explicit. Following the philosophy of how MongoDB was made to be,
it provides the most scalability under the premise of simplicity, let you
think that you are still using pymongo and MongoDB, not some restrained orm with
many rules you must follow.

The document is currently on development, feel free to check the code or test cases if you want to learn more.


Tutorial
--------

.. code:: python

    import pymongo
    from simplemongo import Document

    # Simplemongo won't create the connection or choose the database for you,
    # you must explicitly get you database object yourself
    db = pymongo.MongoClient()['mydatabase']


    class User(Document):
        # Define the collection of User document class ('col' abbr 'collection')
        col = db['user']

        # Enable validation on writing the document
        __validate__ = True

        # Define the struct of the document
        struct = {
            'name': str,
            'age': int,
            'attributes': {
                'vitality': float,
                'armor': int,
                'fortune': int,
            },
        }

    user = User({
        'name': 'reorx',
        'age': 21,
        'attributes': {
            'vitality': 100.0,
            'armor': 20,
            'fortune': 15
        }
    })

    # The document will be validated according to ``struct`` before writing to database
    # An `_id` field will be added if not exist
    user.save()
    print user['_id']

    # `user.identifier` returns {'_id': user['_id']} as the identifier of the document
    # The arguments of Document's `find` method is just the same with `pymongo.Collection.find`
    cursor = User.find(user.identifier)

    # `cursor` support all the ways `pymongo.Cursor` instance can be operated,
    # instead of dict, it returns the instance of `User` class
    print cursor.next()

    # `one` process a find query and return the only result of the query,
    # if no result, it returns `None`, if get multiple results, it raise a `MultipleObjectsReturned` exception
    fetched_user = User.one(user.identifier)
    print fetched_user['_id'] == user['_id']

    # The document data of user object can and only be changed by d[key] operation,
    # dot notation (user.name) is not supported, dict should act as dict does
    user['name'] = 'Reorx'

    # `update` is just the dict update, it won't hit the database
    user.update(age=22)

    # `update_self` calls the `update` method of collection object,
    # equals to: user.col.update(user.identifier, {'$set': {'attributes.armor': 30}})
    user.update_self({'$set': {'attributes.armor': 30}})

    # `update_changes` compares raw data with the changes we have made,
    # then do a `update` operation on the original collection object,
    # this line equals to:
    # >>> user.col.update(user.identifier, {'$set': {'name': 'Reorx'}, '$inc': {'age': 1}})
    user.update_changes()

    # `remove` will remove a saved or fetched document from database,
    # if the document is not written in database, an AssertErrro will be raised
    user.remove()

A detailed example
------------------

.. code:: python

    class UserDict(StructuredDict):
        struct = {
            'name': str,
            'age': int,
            'attributes': {
                'vitality': float,
                'armor': int,
                'fortune': int,
            },
            'slots': [str],
            'skills': [
                {
                    'name': str,
                    'level': int,
                    'damage': float,
                    'is_primary': bool,
                    'parents': [
                        {
                            'name': str,
                            'distance': int,
                        }
                    ]
                }
            ],
        }

        required_fields = [
            'name', 'attributes.vitality', 'attributes.armor',
            'skills', 'skills.name', 'skills.damage'
        ]

        strict_fields = ['slots', 'skills.damage', 'skills.level']


Mechanism
---------

The validation mechanism is based on three class attributes: ``struct``, ``required_fields`` and ``strict_fields``

- ``struct`` is considered the field-type checker,
  it only checks the type of fields in the document, ignore whether
  the structure of the document is matched.

- A field defined in ``struct`` will only be checked when it exists
  in the document, if not exists, ``struct`` check won't be triggered.

- A field defined in ``struct`` is allowed to be of ``None`` value.

- A field not defined in ``struct`` will not be checked or handled,
  whatever value it is.

For fields defined in ``struct`` there are two extra
attributes to configure validation conditions:

1. ``required_fields``

   A field in ``required_fields`` is required to exist in the document, if not,
   a ``KeyError`` exception will be raised on validation.

2. ``strict_fields``

   Whe a field in ``strict_fields`` exist in the docuement, its value
   must be strictly of the type defined in struct, that means,
   it could not be None unless the type is defined to be ``None``

So there are 4 situations for a field (defined in ``struct`` firstly):

1. **not required and not strict** (marked ``nr_ns`` in test code)

   it can be:

   - not exist

   - exist and value is instance of type

   - exist and value is None

2. **required and not strict** (marked ``r_ns`` in test code)

   it can be:

   - exist and value is instance of type

   - exist and value is None

3. **not required and strict** (marked ``nr_s`` in test code)

   it can be:

   - not exist

   - exist and value is instance of type

4. **required and strict** (marked ``r_s`` in test code)

   it can only be:

   - exist and value is instance of type
