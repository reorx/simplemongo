#!/usr/bin/env python
# -*- coding: utf-8 -*-


class SimplemongoException(Exception):
    pass


class ObjectNotFound(SimplemongoException):
    pass


class MultipleObjectsReturned(SimplemongoException):
    pass
