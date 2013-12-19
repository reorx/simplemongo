#!/usr/bin/env python
# -*- coding: utf-8 -*-

# simple orm wrapper of MongoDB using pymongo

import copy
import logging
from bson.objectid import ObjectId
from pymongo.collection import Collection
from . import errors
from .dstruct import StructuredDict, StructuredDictMetaclass, check_struct
from .cursor import SimplemongoCursor, Cursor


# TODO replace logging to certain logger


def oid(id):
    if isinstance(id, ObjectId):
        return id
    elif isinstance(id, (str, unicode)):
        if isinstance(id, unicode):
            id = id.encode('utf8')
        return ObjectId(id)
    else:
        raise ValueError('get type %s, should str\unicode or ObjectId' % type(id))


class DocumentMetaclass(StructuredDictMetaclass):
    """
    use for judging if Document's subclasses have assign attribute 'col' properly
    """
    def __new__(cls, name, bases, attrs):

        # Repeat code in dstruct.StructuredDictMetaclass.__new__
        if 'struct' in attrs:
            check_struct(attrs['struct'])

        # judge if the target class is Document
        if not (len(bases) == 1 and bases[0] is StructuredDict):
            if not ('col' in attrs and isinstance(attrs['col'], Collection)):
                raise errors.StructError(
                    'col of a Document is not set properly, received: %s %s' %
                    (attrs['col'], type(attrs['col'])))

            struct = attrs.get('struct')
            if struct:
                check_struct(struct)

        return type.__new__(cls, name, bases, attrs)


class Document(StructuredDict):
    """A wrapper of MongoDB Document, can also be used to init new document.

    Acturally, a Document is a representation of one certaion collectino which store
    data in structure of the Document, they two are of one-to-one relation

    By default all the fields in struct are not required to **exist**
    if exist, None value is allowed
    there are two lists to mark field option
    1. required_fields
       a field in required fields must exist in doc, despite it value type
    2. strict_fields
       a field in strict_fields must be exactly the type defined in struct,
       that means, could not be None (the only exception is defined type is None)
    So there are 4 situations for a field:
    1. not required and not strict
       it can be:
       - not exist
       - exist and value is instance of type
       - exist and value is None
    2. required and not strict
       it can be:
       - exist and value is instance of type
       - exist and value is None
    3. not required and strict
       it can be:
       - not exist
       - exist and value is instance of type
    4. required and strict
       it can only be:
       - exist and value is instance of type
    Additionally, a field that is not defined in struct will not be handled,
    no matter what value it is. a list to restrict fields that can't be exist
    is not considered to be implemented currently.

    Usage:
    1. create new document
    >>> class ADoc(Document):
    ...     col = mongodb['dbtest']['coltest']
    ...

    2. init from existing document

    """
    __metaclass__ = DocumentMetaclass

    __safe_operation__ = True

    __write_concern__ = {
        'w': 1,
        'j': False
    }

    __validate__ = True

    def __init__(self, raw=None, from_db=False):
        """ wrapper of raw data from cursor

        NOTE *initialize without validation*
        """
        if raw is None:
            super(Document, self).__init__()
        else:
            super(Document, self).__init__(raw)

        self._in_db = from_db

    def __str__(self):
        return '<Document: %s >' % dict(self)

    def deepcopy(self):
        return copy.deepcopy(self)

    @property
    def identifier(self):
        return {'_id': self['_id']}

    def _get_write_options(self, **kwgs):
        options = self.__class__.__write_concern__.copy()
        options.update(kwgs)
        return options

    def save(self):
        if self.__class__.__validate__:
            logging.debug('__validate__ is on')
            self.validate()
        rv = self.col.save(self, **self._get_write_options(manipulate=True))
        logging.debug('ObjectId(%s) saved' % rv)
        self._in_db = True
        return rv

    def remove(self):
        assert self._in_db, 'Could not remove document which is not in database'
        self._history = self.copy()
        _id = self['_id']
        self.col.remove(_id, **self._get_write_options())
        logging.debug('%s removed' % _id)
        self.clear()
        self._in_db = False

    def update_doc(self, spec, **kwargs):
        rv = self.col.update(
            self.identifier, spec, **self._get_write_options(**kwargs))
        return rv

    def pull(self):
        """Update document from database
        """
        cursor = Cursor(self.col, self.identifier)
        try:
            doc = cursor.next()
        except StopIteration:
            raise errors.SimplemongoException('Document was deleted before `pull` was called')
        self.clear()
        self.update(doc)

    @classmethod
    def new(cls, **kwargs):
        """
        initialize by structure of self.struct
        """
        instance = cls.build_instance(**kwargs)
        instance['_id'] = ObjectId()
        logging.debug('_id generated %s' % instance['_id'])
        return instance

    @classmethod
    def find(cls, *args, **kwargs):
        # Copy from ``find`` in pymongo==2.6, this method should be mostly the same as it
        if not 'slave_okay' in kwargs:
            kwargs['slave_okay'] = cls.col.slave_okay
        if not 'read_preference' in kwargs:
            kwargs['read_preference'] = cls.col.read_preference
        if not 'tag_sets' in kwargs:
            kwargs['tag_sets'] = cls.col.tag_sets
        if not 'secondary_acceptable_latency_ms' in kwargs:
            kwargs['secondary_acceptable_latency_ms'] = (
                cls.col.secondary_acceptable_latency_ms)

        kwargs['wrapper'] = cls
        cursor = SimplemongoCursor(cls.col, *args, **kwargs)
        return cursor

    @classmethod
    def one(cls, spec_or_id, allow_multiple=False, *args, **kwargs):
        if spec_or_id is not None and not isinstance(spec_or_id, dict):
            spec_or_id = {"_id": spec_or_id}

        cursor = cls.find(spec_or_id, *args, **kwargs)
        if not allow_multiple:
            count = cursor.count()
            if count > 1:
                raise errors.MultipleObjectsReturned(
                    'Got multiple(%s) results in query %s' % (count, spec_or_id))
        for doc in cursor:
            return doc
        return None
