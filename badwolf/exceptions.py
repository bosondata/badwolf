# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals


class BadwolfException(Exception):
    '''Base exception for badwolf'''


class SpecificationNotFound(BadwolfException):
    pass


class BuildDisabled(BadwolfException):
    pass


class InvalidSpecification(BadwolfException):
    pass
