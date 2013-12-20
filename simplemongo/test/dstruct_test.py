#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import unittest
from nose.tools import assert_raises
import datetime
import copy

from simplemongo.dstruct import (
    check_struct, build_dict, validate_dict,
    retrieve_dict, map_dict, hash_dict,
    StructuredDict, ObjectId,
)
from simplemongo.errors import StructError


STRUCT_SAMPLE = {
    'id': ObjectId,
    'name': str,
    'nature': {
        'luck': int,
    },
    'people': [str],
    'disks': [
        {
            'is_primary': bool,
            'last_modified': datetime.datetime,
            'volums': [
                {
                    'name': str,
                    'size': int,
                    'block': [int]
                }
            ]
        }
    ],
    'extra': float
}


DICT_SAMPLE = {
    'id': ObjectId(),
    'name': 'reorx',
    'nature': {
        'luck': 1,
    },
    'people': ['ayanami', 'asuka'],
    'disks': [
        {
            'is_primary': True,
            'last_modified': datetime.datetime.now(),
            'volums': [
                {
                    'name': 'EVA-01',
                    'size': 1048,
                    'block': [1, 2, 3]
                }
            ]
        }
    ],
    'extra': float(1.234)
}


class TestFunctions(object):
    def s(self, **kwargs):
        d = copy.deepcopy(STRUCT_SAMPLE)
        d.update(kwargs)
        return d

    def d(self, **kwargs):
        d = copy.deepcopy(DICT_SAMPLE)
        d.update(kwargs)
        return d

    def test_check_struct(self):
        check_struct(self.s())

        with assert_raises(StructError):
            check_struct(self.s(name='hello'))

        with assert_raises(StructError):
            check_struct(self.s(people=['me']))

        with assert_raises(StructError):
            d = self.s()
            d['nature']['luck'] = 9
            check_struct(d)

        with assert_raises(StructError):
            d = self.s()
            d['disks'][0]['volums'][0]['block'][0] = 1024
            check_struct(d)

        with assert_raises(StructError):
            d = self.s()
            d['disks'][0]['volums'][0]['name'] = 'C'
            check_struct(d)

    def test_validate_dict(self):
        # 0. original
        d = self.d()
        validate_dict(d, self.s())
        d['name'] = 123
        with assert_raises(TypeError):
            validate_dict(d, self.s())

    def test_validate_dict_nr_ns(self):
        # 1 not required and not strict
        #   - not exist
        #   - exist and value is instance of type
        #   - exist and value is None

        d = self.d(disks=None)
        del d['name']
        validate_dict(d, self.s())

    def test_validate_dict_r_ns(self):
        # 2 required and not strict
        #   - exist and value is instance of type
        #   - exist and value is None

        d = self.d()
        del d['name']
        with assert_raises(KeyError):
            validate_dict(d, self.s(), required_fields=['name'])

        d = self.d(nature=None)
        validate_dict(d, self.s(), required_fields=['nature'])
        with assert_raises(TypeError):
            validate_dict(d, self.s(), required_fields=['nature.luck'])
        d['nature'] = {}
        with assert_raises(KeyError):
            validate_dict(d, self.s(), required_fields=['nature.luck'])

    def test_validate_dict_nr_s(self):
        # 3. not required and strict
        #    - not exist
        #    - exist and value is instance of type
        d = self.d()
        del d['name']
        validate_dict(d, self.s(), strict_fields=['name'])

        d = self.d(name=None)
        with assert_raises(TypeError):
            validate_dict(d, self.s(), strict_fields=['name'])

    def test_validate_dict_r_s(self):
        # 4. required and strict
        #    - exist and value is instance of type
        d = self.d()
        del d['name']
        with assert_raises(KeyError):
            validate_dict(d, self.s(), required_fields=['name'], strict_fields=['name'])

        d = self.d()
        validate_dict(d, self.s(), required_fields=['nature.luck'], strict_fields=['nature.luck'])

        d['nature']['luck'] = None
        with assert_raises(TypeError):
            validate_dict(d, self.s(), required_fields=['nature.luck'], strict_fields=['nature.luck'])

        del d['nature']['luck']
        with assert_raises(KeyError):
            validate_dict(d, self.s(), required_fields=['nature.luck'], strict_fields=['nature.luck'])


    def test_validate_dict_nis(self):
        # 5. not in struct
        d = self.d(foo='bar')
        validate_dict(d, self.s())

    # require validate_dict
    def test_build_dict(self):
        d1 = build_dict(self.s(), ('nature.luck', 1))
        print d1
        validate_dict(d1, self.s())

        d2 = build_dict(self.s(), ('nature.luck', 2))
        print d2
        assert d1['nature']['luck'] != d2['nature']['luck']

    def test_retrieve_dict(self):
        d = self.d()
        assert d['name'] == retrieve_dict(d, 'name')
        assert d['people'][1] == retrieve_dict(d, 'people.[1]')
        assert d['nature']['luck'] == retrieve_dict(d, 'nature.luck')
        assert d['disks'][0]['volums'][0]['size'] == retrieve_dict(d, 'disks.[0].volums.[0].size')

    # require test_retrieve_dict
    def test_map_dict(self):
        d = self.d()
        mapping = map_dict(d)
        for k, v in mapping.iteritems():
            assert retrieve_dict(d, k) == v

    def test_hash_dict(self):
        d1 = self.d()
        d2 = self.d()
        assert d1 is not d2
        assert hash_dict(d1) == hash_dict(d2)

        # change d2
        d2['id'] = ObjectId()
        assert hash_dict(d1) != hash_dict(d2)

        # acturally a test for validate_dict,
        # to test whether dict is changed or not after validate process
        d3 = self.d()
        hash_before = hash_dict(d3)
        validate_dict(d3, self.s())
        assert hash_dict(d3) == hash_before


class TestStructedDict(object):
    def setUp(self):
        class UserDict(StructuredDict):
            struct = {
                'id': ObjectId,
                'name': str,
                'bio': str,
                'attributes': {
                    'strength': int,
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
                'id', 'name',
                'attributes.strength', 'attributes.armor',
                'skills', 'skills.name', 'skills.damage'
            ]

            strict_fields = ['id', 'slots', 'skills.damage', 'skills.level']

        self.UserDict = UserDict

    def sample(self, **kwargs):
        d = self.UserDict({
            'id': ObjectId(),
            'name': 'reorx',
            'bio': 'blade of chaos',
            'attributes': {
                'strength': 10,
                'armor': 20,
                'fortune': 8,
            },
            'slots': ['red_potion', 'red_potion', 'blue_potion'],
            'skills': [
                {
                    'name': 'heavy punch',
                    'level': 5,
                    'damage': 90.0,
                    'is_primary': False,
                },
                {
                    'name': 'upper cut',
                    'level': 3,
                    'damage': 180.0,
                    'is_primary': True,
                    'parents': [
                        {
                            'name': 'heavy punch',
                            'distance': 1,
                        }
                    ]
                }
            ],
        })

        d.update(kwargs)
        return d

    def test_validate(self):
        ud = self.sample()
        ud.validate()

        ud['skills'][1]['parents'][0]['distance'] = 'wtf'
        with assert_raises(TypeError):
            ud.validate()
        ud['skills'][1]['parents'][0]['distance'] = 1

    def test_validate_nr_ns(self):
        ud = self.sample()

        # 1. nr ns
        print '# 1. nr ns'
        del ud['bio']
        del ud['slots']
        ud.validate()

    def test_validate_r_ns(self):
        ud = self.sample()

        # 2. r ns
        print '# 2. r ns'
        del ud['attributes']['strength']
        with assert_raises(KeyError):
            ud.validate()
        ud['attributes']['strength'] = 11

        ud['skills'][0]['name'] = None
        ud.validate()
        del ud['skills'][0]['name']
        with assert_raises(KeyError):
            ud.validate()
        ud['skills'][0]['name'] = 'punch'

        ud['skills'] = None
        ud.validate()

    def test_validate_nr_s(self):
        ud = self.sample()

        # 3. nr s
        print '# 3. nr s'
        ud['slots'] = None
        with assert_raises(TypeError):
            ud.validate()
        del ud['slots']
        ud.validate()
        ud['slots'] = []

        ud['skills'][0]['level'] = None
        with assert_raises(TypeError):
            ud.validate()
        del ud['skills'][0]['level']
        ud.validate()
        ud['skills'][0]['level'] = 5


    def test_validate_r_s(self):
        ud = self.sample()

        # 4. r s
        print '# 4. r s'
        ud['id'] = None
        with assert_raises(TypeError):
            ud.validate()
        del ud['id']
        with assert_raises(KeyError):
            ud.validate()
        ud['id'] = ObjectId()

        ud['skills'][0]['damage'] = None
        with assert_raises(TypeError):
            ud.validate()
        del ud['skills'][0]['damage']
        with assert_raises(KeyError):
            ud.validate()
        ud['skills'][0]['damage'] = 90.0

    # internally requires test_validate
    def test_build_instance(self):
        # meet required_fields and strict_fields
        # required_fields = [
        #     'id', 'name',
        #     'attributes.strength', 'attributes.armor',
        #     'skills', 'skills.name', 'skills.damage'
        # ]
        # strict_fields = ['id', 'slots', 'skills.damage', 'skills.level']

        kwargs = dict(
            id=ObjectId(),
            name='reorx',
            attributes={
                'strength': 10,
                'armor': 10
            },
            skills=[{'name': 'test', 'damage': 1.1}],
            slots=[]
        )

        ins = self.UserDict.build_instance(**kwargs)
        d = build_dict(self.UserDict.struct, **kwargs)

        assert d['name'] == 'reorx'
        assert d['skills'][0]['name'] == 'test'

        del ins['id']
        del d['id']
        assert hash_dict(ins) == hash_dict(d)

        with assert_raises(TypeError):
            ins = self.UserDict.build_instance(name=1)

    # requires test_build_instance
    def test_retrieval_operations(self):
        ins = self.UserDict.build_instance(
            id=ObjectId(),
            name='reorx',
            attributes={
                'strength': 10,
                'armor': 10
            },
            skills=[{'name': 'test', 'damage': 1.1}],
            slots=[]
        )

        assert ins['name'] == ins.retrieval_get('name')
        assert ins['attributes']['strength'] == ins.retrieval_get('attributes.strength')
        assert ins['skills'][0]['damage'] == ins.retrieval_get('skills.[0].damage')

    # # requires UtilitiesTest.test_build_dict
    def test_gen(self):
        assert isinstance(self.UserDict.gen.id(), ObjectId)

        d = self.UserDict.gen.attributes()
        print d
        assert len(d.keys()) == 3 and 'strength' in d

        d = self.UserDict.gen.skills.parents(name='foo')
        assert hash_dict(d) == hash_dict(
            build_dict(self.UserDict.struct['skills'][0]['parents'][0], name='foo'))
