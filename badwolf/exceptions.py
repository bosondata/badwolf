# -*- coding: utf-8 -*-


class BadwolfException(Exception):
    '''Base exception for badwolf'''


class SpecificationNotFound(BadwolfException):
    pass


class BuildDisabled(BadwolfException):
    pass


class InvalidSpecification(BadwolfException):
    pass
