# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from badwolf.utils import sanitize_sensitive_data


def test_sanitize_basic_auth_urls():
    text = 'abc http://user:pwd@example.com def'
    sanitized = sanitize_sensitive_data(text)
    assert 'user' not in sanitized
    assert 'pwd' not in sanitized
    assert 'http://example.com' in sanitized

    text = '''abc
    http://user:pwd@example.com

    def
    '''
    sanitized = sanitize_sensitive_data(text)
    assert 'user' not in sanitized
    assert 'pwd' not in sanitized
    assert 'http://example.com' in sanitized
