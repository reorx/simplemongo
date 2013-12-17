#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = [
    'Document', 'Struct', 'ObjectId', 'oid',
]

from bson.objectid import ObjectId
from .dstruct import Struct
from .models import Document, oid
