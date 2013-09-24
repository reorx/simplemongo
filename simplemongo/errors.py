#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ConnectionError(TorextException):
    """
    error occurs in connection
    """
    pass


class ObjectNotFound(TorextException):
    pass


class MultipleObjectsReturned(TorextException):
    pass
