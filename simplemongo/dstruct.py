#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import datetime
from hashlib import md5
from bson.objectid import ObjectId
from .errors import StructError


logger = logging.getLogger('simplemongo')
# logger.setLevel(logging.DEBUG)


# TODO change dict building mechanism:
#      1. no str & unicode difference, only str
#      2. all allow None, except: list, dict, ObjectId

_None = lambda: None

TYPE_DEFAULT_VALUE = {
    int: int,
    float: float,
    str: _None,
    unicode: _None,
    # bool() == False
    bool: bool,
    list: list,
    dict: dict,
    ObjectId: ObjectId,
    datetime.datetime: lambda: datetime.datetime.now()
}


ALLOW_TYPES = [
    bool,
    int, float,
    str, unicode,
    list,
    dict,
    ObjectId,
    datetime.datetime,
]


def check_struct(struct):
    """
    ensure every key in struct is of str type
    """
    for k, v in struct.iteritems():
        # check key to be str
        if not isinstance(k, str):
            raise StructError('key "%s" is not a str' % k)

        # NOTE isinstance(dict, dict) is False
        if isinstance(v, dict):
            check_struct(v)

        elif isinstance(v, list):
            if len(v) > 1:
                raise StructError('value "%s" can at most contains one item' % v)
            elif len(v) == 1:
                v_item = v[0]
                if isinstance(v_item, dict):
                    check_struct(v_item)
                else:
                    if not v_item in ALLOW_TYPES:
                        raise StructError('value "%s" in list '
                                                'is neither one of ALLOW_TYPES '
                                                'nor instance of dict' % v_item)

        # check value to be type in `ALLOW_TYPES` if not instance of dict or list
        else:
            if not v in ALLOW_TYPES:
                raise StructError('value "%s" is not one of ALLOW_TYPES' % v)


def _remove_list_mark(key):
    if '[' in key:
        index = key.find('[')
        key = key[0:index - 1] + key[index + 3:]
        return _remove_list_mark(key)
    return key


def validate_dict(doc, struct, required_fields=None, strict_fields=None):
    """
    Validate a dict from the defined structure.

    Thoughts:
        In the inner function `recurse_check`, treat `st` as basement,
        iter every key and value to see if key-value exists and fits in `o`,

        during the iteration, when list is encountered, check if the value of
        the same key in `o` is list, then iter the list value from `o` ( not `st`),
        and pass the first item of `st`s list value as `st` argument to the
        newly running `recurse_check`.

    This function can strictly check that if every key in `struct`
    is the same as in `doc`, that is, `struct` -> `doc`, so this example will not pass:
    >>> doc = {
    ...     'a': '',
    ...     'b': [
    ...         {
    ...             'c': 0
    ...         }
    ...     ]
    ... }
    >>> struct = {
    ...     'a': str,
    ...     'b': [
    ...         {
    ...             'c': int
    ...             'd': str
    ...         }
    ...     ]
    ... }
    >>> validate_dict(doc, struct)

    Traceback (most recent call last):
        raise TypeError('%s: key %s not in %s' % (ck, k, o))
    TypeError: $.b.[0]: key d not in {'c': 0}

    Because we don't see if every key in `doc` is in `struct` reversely,
    this example will just pass:
    >>> doc = {
    ...     'a': '',
    ...     'b': [
    ...         {
    ...             'c': 0
    ...             'd': '',
    ...             'e': 'i am e'
    ...         }
    ...     ],
    ...     'f': 'i am f'
    ... }
    >>> struct = {
    ...     'a': str,
    ...     'b': [
    ...         {
    ...             'c': int
    ...             'd': str
    ...         }
    ...     ]
    ... }
    >>> validate_dict(doc, struct)
    """
    logger.debug('------call validate_dict()')

    # assert isinstance(doc, dict), 'doc must be dict'
    assert isinstance(struct, dict), 'struct must be dict'
    check_struct(struct)

    # required_parents_set = set()
    # for i in required_fields:
    #     if '.' in i:
    #         required_parents_set |= set(i.split('.')[1:])
    # print 'parents set', required_parents_set
    if required_fields is None:
        required_fields = []
    if strict_fields is None:
        strict_fields = []

    # required_sets = set(required_fields)

    logger.debug('required_fields: %s', required_fields)
    logger.debug('strict_fields: %s', strict_fields)

    def parent_of(k):
        for i in required_fields:
            kdot = k + '.'
            if i.startswith(kdot):
                return i
        return False

    def is_strict(k):
        if _remove_list_mark(k) in strict_fields:
            return True
        return False

    def recurse_check(st, o, ck, local_required=None):
        # `st` means struct, it could be a type
        # `nst` means next loop struct
        # `o`  means object to be validate
        # `ck` means current key
        # `nk` means next key
        # `bv` means bottom value

        if local_required is None:
            local_required = []
        local_required_current = []
        # local_required_next = []
        for i in local_required:
            sp = i.split('.')
            local_required_current.append(sp[0])
            # if len(sp) > 1:
            #     local_required_next.append('.'.join(sp[1:]))

        def get_next_required(k):
            nr = []
            for i in local_required:
                if i.startswith(k + '.'):
                    nr.append(i[len(k) + 1:])
            return nr

        if st in ALLOW_TYPES:
            typ = st
        else:
            # list or dict
            typ = type(st)
        logger.debug(
            '@ %s\ndefined: %s\nobj   : %s %s\nrequired: %s',
            ck, typ, type(o), o, local_required_current)

        if o is None:
            if local_required_current and typ is dict:
            # field = parent_of(ck)
            # if field:
            #     logger.debug('parent of %s' % field)
                raise TypeError(
                    "On key '%s' None, should not be None since %s are required in it" %
                    (ck, local_required_current))

            if is_strict(ck):
                raise TypeError("On key '%s' %s, %s, should be type %s" % (ck, o, type(o), typ))

            return

        elif not isinstance(o, typ):
            # TODO support multi-type validation (use tuple to define)
            raise TypeError("On key '%s' %s, %s, should be type %s" % (ck, o, type(o), typ))

        logger.debug('---')

        # recurse down step
        if isinstance(st, dict):
            for k, nst in st.iteritems():
                if k in local_required_current and not k in o:
                    raise KeyError("Under key '%s', subkey '%s', value %s, not exist" % (ck or '$', k, o))

                # local_required_next = get_next_required(k)
                # if local_required_next:
                #     if not k in o:
                #         raise TypeError(
                #             "On key '%s' None, should not be None since %s is required in it" %
                #             (ck, local_required_next))

                if k in o:
                    if ck is None:
                        nk = k
                    else:
                        nk = ck + '.' + k

                    # if nk in required_sets:
                    #     required_sets.remove(nk)


                    recurse_check(nst, o[k], nk, get_next_required(k))

        elif isinstance(st, list) and len(st) == 1:
            # NOTE currently, redundancy validations, which may occured on list,
            # could not be reduced, because of the unperfect mechanism ..
            # nk = ck + '.*'
            nst = st[0]
            for loop, i in enumerate(o):
                nk = '%s.[%s]' % (ck, loop)
                recurse_check(nst, i, nk, local_required)

    recurse_check(struct, doc, None, required_fields)

    # if required_sets:
    #     raise KeyError('required fields: %s not exist', required_sets)
    logger.debug('------validation all passed !')


def build_dict(struct, *args, **kwargs):
    """
    args: (key, value)
    kwargs: key=value

    DICT !!
    WILL NEVER HANDLE ANY THING IN LIST !!

    build a dict from struct,
    struct & the result can only be dict

    NOTE
     * inner list will be ignored (build to [])
     * KeyError will be raised if not all dot_keys in default are properly set
    """
    assert isinstance(struct, dict), 'struct must be dict'

    defaults = kwargs
    if args:
        defaults.update(dict(args))

    def recurse_struct(st, pk):
        cd = {}

        for k, v in st.iteritems():
            if pk is None:
                ck = k
            else:
                ck = pk + '.' + k

            # if dot_key is found in default, stop recurse and set value immediatelly
            # this may make the dict structure broken (not valid with struct),
            # so a validate() will do at following
            if ck in defaults:
                kv = defaults.pop(ck)
            else:
                if isinstance(v, dict):
                    kv = recurse_struct(v, ck)
                else:
                    if isinstance(v, list):
                        v = list
                    assert isinstance(v, type), '%s %s must be <type type>' % (ck, v)

                    # The default value is None if not specified in `defaults`
                    # kv = TYPE_DEFAULT_VALUE.get(v, lambda: None)()
                    kv = None

            cd[k] = kv
            logger.debug('build: $.%s -> %s' % (ck, kv))

        return cd

    built = recurse_struct(struct, None)

    #if len(defaults.keys()) > 0:
        #raise KeyError('Assignment of default value `%s` failed' % defaults)
    built.update(defaults)

    return built


def _key_rule(k):
    if k.startswith('[') and k.endswith(']'):
        k = int(k[1:-1])
    return k


def retrieve_dict(doc, dot_key):
    """
    Could index value out by dot_key like this:
        foo.bar.[0].player

    """
    def recurse_dict(d, klist):
        try:
            k = klist.pop(0)
        except IndexError:
            return d

        d = d[_key_rule(k)]
        return recurse_dict(d, klist)

    spKeys = dot_key.split('.')

    return recurse_dict(doc, spKeys)


def map_dict(o):
    def recurse_doc(mapping, d, pk):
        if isinstance(d, dict):
            for k, v in d.iteritems():
                if pk is None:
                    ck = k
                else:
                    ck = pk + '.' + k
                recurse_doc(mapping, v, ck)
        elif isinstance(d, list):
            for loop, i in enumerate(d):
                ck = pk + '.' + '[%s]' % loop
                recurse_doc(mapping, i, ck)
        else:
            mapping[pk] = d
        return mapping

    return recurse_doc({}, o, None)


def hash_dict(o):
    """
    As dict is not hashable, this function is to generate a hash string
    from a dict unnormally, use every key & value of the dict,
    join then up and compute its md5 value.
    """
    seprator = '\n'
    mapping = map_dict(o)
    keys = mapping.keys()

    # get rid the random effect of dict keys, to ensure same dict will result to same value.
    keys.sort()

    string = seprator.join(['%s:%s' % (k, mapping[k]) for k in keys])
    return md5(string).hexdigest()


def diff_dicts(new, origin):
    """Only compare the first layer, return a the dict that represent
    add, remove, modify changes from new to origin

    NOTE: If one of the two dicts comes from another, eg. from .copy(),
    # make sure new and origin are totally different from each other,
    that means, the result may not be as you think. So use deepcopy in case.
    """
    diff = {
        '+': {},
        '-': [],
        '~': {}
    }
    for k, v in new.iteritems():
        if not k in origin:
            diff['+'][k] = v
            continue
        if v != origin[k]:
            diff['~'][k] = v

    for k in origin:
        if not k in new:
            diff['-'].append(k)

    return diff


class GenCaller(object):
    def __get__(self, ins, owner):
        return Gen(owner)


class Gen(object):
    def __init__(self, struct_class):
        self.__struct_class = struct_class
        self.__dot_key = None

    def __get_struct(self):
        """
        if the struct indexed is a list, return its first item

        the result can be anything in TYPE_DEFAULT_VALUE except 'list'

        note that '__' is used for naming attributes to avoid conflicts
        """
        def recurse_struct(st, klist):
            if isinstance(st, list):
                st = st[0]
            try:
                k = klist.pop(0)
            except IndexError:
                return st
            st = st[k]
            return recurse_struct(st, klist)

        keys = self.__dot_key.split('.')
        return recurse_struct(self.__struct_class.struct, keys)

    def __call__(self, *args, **kwargs):
        struct = self.__get_struct()
        #logging.debug('%s index struct: %s' % (self.__dot_key, struct))
        if isinstance(struct, dict):
            return build_dict(struct, *args, **kwargs)
        else:
            return TYPE_DEFAULT_VALUE.get(struct, lambda: None)()

    def __getattr__(self, key):
        if self.__dot_key is None:
            self.__dot_key = key
        else:
            self.__dot_key += '.' + key
        return self

    def __str__(self):
        return '<Gen struct:%s>' % self.__get_struct()


class Struct(object):
    """
    Struct is designed for validate dict that will be stored into mongodb,
    so it will follow mongodb documents' standard on namespace, type, and value.

    Notations:
        * key must be str type
        * only allow these types (explained in python thought):
            1. type(None)
            2. bool
            3. int/float
            4. str/unicode
            5. list
            6. dict
            7. ObjectId
    """


    def __init__(self, struct):
        assert isinstance(struct, dict), 'struct must be dict type'

        check_struct(struct)
        self._struct = struct

    def __get__(self, ins, owner):
        return self._struct


class StructuredDictMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if 'struct' in attrs:
            check_struct(attrs['struct'])
        return type.__new__(cls, name, bases, attrs)


class StructuredDict(dict):
    """
    Philosophy:
        1. instance has the same keys, no less, no more, with defined struct.
        2. when initializing instance, if no default value input, key-value will be auto created.
        3. when auto creating and validating, if the key isn't in `force_type`, None will be allowed.
        4. no unique judgements
        5. keys not in struct could not be read or set.
        6. validator is not included in concept, it should be outside of structure.

    TODO.
        * auto_fix for raw doc in mongodb to fit struct (always use in developing at which time struct changes frequently)

    NOTE.
        * '' and None. When a key has no input default value, it will be asigned as None
          unless it's in strict_indexes
        * keys in struct must be str

    Usage::

        # define a new struct:
        >>> class SomeStruct(StructuredDict):
        ...     struct = {
        ...         'id': ObjectId,
        ...         'name': {
        ...             'first': str,
        ...             'last': str
        ...         },
        ...         'contributers': [
        ...             {
        ...                 'name': str,
        ...                 'rate': float,
        ...                 'hangon': bool,
        ..              }
        ...         ],
        ...         'flag': str,
        ...     }
        ...
        ...     defaults = [
        ...         ('name.last', 'Clanned')
        ...         ('flag', 'A')
        ...     ]
        ...
        ...     required_fields = ['id', 'contributers']
        ...
        ...     strict_fields = ['id', 'name']
        ...

        # build a pure instance:
        >>> doc = SomeStruct.build_instance()

        # or with some default values
        >>> doc = SomeStruct.build_instance(default={
        ...     'name': 'Just Bili.H',
        ... })

        then you can do some thing with it
    """
    __metaclass__ = StructuredDictMetaclass

    gen = GenCaller()

    required_fields = None

    strict_fields = None

    @classmethod
    def build_instance(cls, *args, **kwgs):
        """
        use build_dict() to create a dict object,
        return an instance of cls from that dict object.
        """
        assert hasattr(cls, 'struct'), '`build_instance` method requires definition of `struct`'
        ins = cls(build_dict(cls.struct, *args, **kwgs))
        ins.validate()
        return ins

    def validate(self):
        cls = self.__class__
        assert hasattr(cls, 'struct'), '`validate` method requires definition of `struct`'
        validate_dict(self, cls.struct,
                      required_fields=cls.required_fields,
                      strict_fields=cls.strict_fields)

    def retrieval_get(self, dot_key):
        """
        raise IndexError or KeyError if can not get

        Example:
            'menu.file.name'
            'menu.ps.[0].title'
        """
        return retrieve_dict(dict(self), dot_key)

    def retrieval_set(self, dot_key, value):
        keys = dot_key.split('.')
        last_key = keys.pop(-1)
        last = self.retrieval_get('.'.join(keys))
        last[_key_rule(last_key)] = value

    def retrieval_del(self, dot_key):
        keys = dot_key.split('.')
        last_key = keys.pop(-1)
        last = self.retrieval_get('.'.join(keys))
        del last[_key_rule(last_key)]

    def _pprint(self):
        from torext.utils import pprint
        pprint(dict(self))

    def __str__(self):
        s = '<%s of StructuredDict: %s>' %\
            (self.__class__.__name__,
             ','.join(['%s=%s' % (k, v) for k, v in self.iteritems()]))
        return s
