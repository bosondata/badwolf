# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
try:
    import re2 as re
except ImportError:
    import re

import six

BASIC_AUTH_URL_RE = re.compile(
    r'(?P<protocol>\S+?//)(?P<username>[^:\s]+?):(?P<password>[^@\s]+?)@(?P<address>\S+?)',
    re.I | re.U
)


class ObjectDict(dict):
    """Makes a dictionary behave like an object, with attribute-style access.
    """
    def __getattr__(self, key):
        if key in self:
            return self[key]
        return None

    def __setattr__(self, key, value):
        self[key] = value


def to_text(value, encoding='utf-8', errors='ignore'):
    """Convert value to unicode, default encoding is utf-8

    :param value: Value to be converted
    :param encoding: Desired encoding
    """
    if not value:
        return ''
    if isinstance(value, six.text_type):
        return value
    if isinstance(value, six.binary_type):
        return value.decode(encoding, errors)
    return six.text_type(value)


def to_binary(value, encoding='utf-8'):
    """Convert value to binary string, default encoding is utf-8

    :param value: Value to be converted
    :param encoding: Desired encoding
    """
    if not value:
        return b''
    if isinstance(value, six.binary_type):
        return value
    if isinstance(value, six.text_type):
        return value.encode(encoding)
    return six.binary_type(value)


def yesish(value):
    """Typecast booleanish environment variables to :py:class:`bool`.

    :param string value: An environment variable value.
    :returns: :py:class:`True` if ``value`` is ``1``, ``true``, or ``yes``
        (case-insensitive); :py:class:`False` otherwise.
    """
    if isinstance(value, bool):
        return value
    return value.lower() in ('1', 'true', 'yes')


def sanitize_sensitive_data(s):
    return _sanitize_urls(s)


def _sanitize_urls(s):
    def remove_basic_auth(match):
        return '{}***:***@{}'.format(
            match.group('protocol'),
            match.group('address'),
        )
    ret = []
    for line in s.split('\n'):
        ret.append(BASIC_AUTH_URL_RE.sub(remove_basic_auth, line))
    return '\n'.join(ret)
