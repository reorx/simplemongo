#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pymongo.cursor import Cursor


class SimplemongoCursor(Cursor):
    def __init__(self, *args, **kwargs):
        self.__wrapper = kwargs.pop('wrapper')

        super(SimplemongoCursor, self).__init__(*args, **kwargs)

    def next(self):
        # Directly call pymongo Cursor's `next` method
        raw = super(SimplemongoCursor, self).next()

        if raw is None:
            return None

        return self.__wrapper(raw, from_db=True)

    def __getitem__(self, index):
        rv = super(SimplemongoCursor, self).__getitem__(index)

        if isinstance(rv, dict):
            return self.__wrapper(rv, from_db=True)
        else:
            # rv is SimplemongoCursor instance
            return rv
