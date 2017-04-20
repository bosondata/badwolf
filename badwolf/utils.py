# -*- coding: utf-8 -*-
import os
import logging
import subprocess
try:
    import re2 as re
except ImportError:
    import re

logger = logging.getLogger(__name__)
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
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode(encoding, errors)
    return str(value)


def to_binary(value, encoding='utf-8'):
    """Convert value to binary string, default encoding is utf-8

    :param value: Value to be converted
    :param encoding: Desired encoding
    """
    if not value:
        return b''
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode(encoding)
    return bytes(value)


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


def run_command(command, split=False, include_errors=False, cwd=None, shell=False):
    """Run command in subprocess and return exit code and output"""
    env = os.environ.copy()
    if include_errors:
        error_pipe = subprocess.STDOUT
    else:
        error_pipe = subprocess.PIPE

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=error_pipe,
        shell=shell,
        universal_newlines=True,
        cwd=cwd,
        env=env
    )
    if split:
        output = process.stdout.readlines()
    else:
        output = process.stdout.read()

    return_code = process.wait()
    logger.debug('subprocess %s returned %d, output: %s', command, return_code, output)
    return return_code, output
