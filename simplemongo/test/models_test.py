#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from nose.tools import assert_raises
from pymongo import Connection
from simplemongo.models import Document, Struct, ObjectId, StructDefineError
from simplemongo.errors import ObjectNotFound, MultipleObjectsReturned


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


class ModelTest(unittest.TestCase):

    def setUp(self):
        db = Connection('mongodb://localhost')['_simplemongo_test']

        class User(Document):
            col = db['user']
            struct = Struct({
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
            })

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
        with assert_raises(StructDefineError):
            class User(Document):
                struct = Struct({
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
                })

    def test_new_and_gen(self):
        with assert_raises(TypeError):
            self.User.new(magic=self.User.gen.magic(camp=1))

        u = self.User.new(
            name='reorx',
            age=20,
            is_choosen=True,
            skills=[
                self.User.gen.skills(name='Kill')
            ],
            magic=self.User.gen.magic(camp='Chaos'),
            # an extra key
            extra=None
        )

        print set(u.keys()), set(self.User.struct.keys())
        assert (set(u.keys()) ^ set(self.User.struct.keys())) == set(['extra', '_id'])

        assert u['name'] == 'reorx'
        assert u['age'] == 20
        assert u['is_choosen'] is True
        assert u['skills'][0]['name'] == 'Kill'
        assert u['magic']['camp'] == 'Chaos'

    def test_save(self):
        u = self.User.new(
            name='reorx',
            age=20,
            is_choosen=True,
            skills=[
                self.User.gen.skills(name='Kill')
            ],
            magic=self.User.gen.magic(camp='Chaos')
        )

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

    def test_exist(self):
        d = self.get_fake()

        self.User.col.insert(d)

        assert self.User.exist({'name': 'reorx'})

        assert not self.User.exist({'name': 'zorro'})

    def test_one(self):
        d = self.get_fake()

        self.User.col.insert(d)
        query = {'name': 'reorx'}
        self.User.one(query)

        self.User.col.insert(self.get_fake())
        with assert_raises(MultipleObjectsReturned):
            self.User.one(query)

        with assert_raises(ObjectNotFound):
            self.User.one({'age': 1})

    def test_by__id(self):
        d = self.get_fake()

        _id = self.User.col.insert(d)
        u = self.User.by__id(_id)
        assert u['_id'] == _id

    def test_by__id_str(self):
        d = self.get_fake()

        _id = self.User.col.insert(d)
        u = self.User.by__id_str(str(_id))
        assert u['_id'] == _id

    def test_identifier(self):
        u = self.User.new()
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
