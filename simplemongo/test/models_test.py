#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from nose.tools import assert_raises
from pymongo import Connection
from simplemongo.models import Document, ObjectId
from simplemongo.errors import ObjectNotFound, MultipleObjectsReturned, StructError


_FAKE_DATA = {
    'id': ObjectId(),
    'name': 'reorx',
    'age': 20,
    'is_choosen': True,
    'skills': [
        {
            'name': 'Break',
            'power': 9.0
        }
    ],
    'magic': {
        'spell': 12.3,
        'camp': 'Chaos'
    }
}

fake_data = lambda: _FAKE_DATA.copy()


try:
    db = Connection('mongodb://localhost')['_simplemongo_test']
except:
    # Not in a mongodb environment
    db = None


class ModelTest(unittest.TestCase):

    def setUp(self):

        class User(Document):
            col = db['user']
            struct = {
                'id': ObjectId,
                'name': str,
                'age': int,
                'is_choosen': bool,
                'skills': [
                    {
                        'name': str,
                        'power': float
                    }
                ],
                'magic': {
                    'spell': float,
                    'camp': str
                }
            }

            defaults = {
                'name': 'hello',
                'magic.spell': 10.1,
            }

            required_fields = ['name', 'age', 'magic.camp']

            strict_fields = ['id', 'age', 'magic.spell']

        self.User = User
        self.db = db

    def tearDown(self):
        self.db.drop_collection(self.User.col)
        self.User = None

    def get_fake(self):
        d = fake_data()
        self.User(d).validate()
        return d

    def test_define_error(self):
        with assert_raises(StructError):
            class User(Document):
                struct = {
                    'id': ObjectId,
                    'name': str,
                    'age': int,
                    'is_choosen': bool,
                    'skills': [
                        {
                            'name': 'wtf',
                            'power': float
                        }
                    ],
                    'magic': {
                        'spell': float,
                        'camp': str
                    }
                }

    def get_new(self):
        u = self.User.new(
            id=ObjectId(),
            name='reorx',
            age=20,
            is_choosen=True,
            skills=[
                self.User.gen.skills(name='Kill')
            ],
            magic=self.User.gen.magic(camp='Chaos', spell=354.21),
            # an extra key
            extra=None
        )
        return u

    def test_new_and_gen(self):
        with assert_raises(TypeError):
            self.User.new(magic=self.User.gen.magic(camp=1))

        u = self.get_new()

        print set(u.keys()), set(self.User.struct.keys())
        assert (set(u.keys()) ^ set(self.User.struct.keys())) == set(['extra', '_id'])

        assert u['name'] == 'reorx'
        assert u['age'] == 20
        assert u['is_choosen'] is True
        assert u['skills'][0]['name'] == 'Kill'
        assert u['magic']['camp'] == 'Chaos'

    def test_save(self):
        u = self.get_new()

        rv = u.save()
        assert isinstance(rv, ObjectId) and rv == u['_id']

    def test_remove(self):
        pass

    def test_find(self):
        d = self.get_fake()

        self.User.col.insert(d)
        cur = self.User.find({'name': 'reorx'})
        assert cur.count() == 1

        u = cur.next()
        assert isinstance(u, Document)
        assert dict(u) == d

    def test_find_many(self):
        user_names = ['shinji', 'asuka', 'ayanami']
        for name in user_names:
            d = self.get_fake()
            d['name'] = name
            d['age'] = 14
            print d
            self.User.col.insert(d)
        cur = self.User.find({'age': 14})
        print [i for i in cur]
        assert cur.count() == 3
        for u in cur:
            assert isinstance(u, Document)
            assert u['name'] in user_names

    def test_one(self):
        d = self.get_fake()

        self.User.col.insert(d)
        query = {'name': 'reorx'}
        assert self.User.one(query)
        assert not self.User.one({'foo': 'bar'})

        self.User.col.insert(self.get_fake())
        with assert_raises(MultipleObjectsReturned):
            self.User.one(query)

        with assert_raises(ObjectNotFound):
            self.User.one_or_raise({'age': 1})

    def test_identifier(self):
        u = self.get_new()
        assert u.identifier == {'_id': u['_id']}

    def test_deepcopy(self):
        d = self.get_fake()

        _id_str = self.User.col.insert(d)
        u = self.User.one({'_id': ObjectId(_id_str)})

        d = u.deepcopy()
        d['magic']['camp'] = 'Order'
        assert d['magic']['camp'] != u['magic']['camp']

        d['skills'].append(1)
        assert len(d['skills']) != len(u['skills'])

    def test_changes(self):
        u = self.get_new()
        print u
        u['name'] = 'reorx reborn'
        u['age'] = 21
        u['skills'].append(1)
        u['magic']['spell'] = 111
        del u['is_choosen']

        c = {
            '$set': {
                'name': 'reorx reborn',
                'skills': [{'name': 'Kill', 'power': None}, 1],
                'magic': {
                    'camp': 'Chaos',
                    'spell': 111
                }
            },
            '$inc': {
                'age': 1
            },
            '$unset': ['is_choosen']
        }
        _c = u.changes
        # print _c
        for k in c:
            print c[k], _c[k]
            assert c[k] == _c[k]

    def test_update_changes(self):
        u = self.get_new()
        u.save()

        u['name'] = 'reorx reborn'
        u['age'] = 21
        u['magic']['spell'] = 111.11

        u.update_changes()

        d = self.User.col.find_one(u.identifier)
        print d
        assert d['name'] == 'reorx reborn'
        assert d['age'] == 21
        assert d['magic']['spell'] == 111.11


if not db:
    # Skip test if not in mongodb environment
    ModelTest.__name__ = '_ModelNotest'
