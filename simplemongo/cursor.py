#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pymongo.cursor import Cursor


class SimplemongoCursor(Cursor):
    def __init__(self, *args, **kwargs):
        self.__wrapper = kwargs.pop('wrapper', None)

        super(SimplemongoCursor, self).__init__(*args, **kwargs)

    def next(self):
        ## Original `next` method:
        # if self._Cursor__empty:
        #     raise StopIteration
        # db = self._Cursor__collection.database
        # if len(self._Cursor__data) or self._refresh():
        #     if self._Cursor__manipulate:
        #         raw = db._fix_outgoing(self._Cursor__data.popleft(),
        #                                 self._Cursor__collection)
        #     else:
        #         raw = self._Cursor__data.popleft()

        # Directly call pymongo Cursor's `next` method
        raw = super(SimplemongoCursor, self).next()

        if self.__wrapper:
            return self.__wrapper(raw, from_db=True)
        else:
            return raw

    def __getitem__(self, index):
        rv = super(SimplemongoCursor, self).__getitem__(index)

        # `rv` could be `self` or document dict
        if self.__wrapper and isinstance(rv, dict):
            return self.__wrapper(rv, from_db=True)
        else:
            return rv
