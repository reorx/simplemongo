#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymongo
from simplemongo import Document

# Simplemongo won't create the connection or choose the database for you,
# you must explicitly get you database object yourself
db = pymongo.Connection()['mydatabase']


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
