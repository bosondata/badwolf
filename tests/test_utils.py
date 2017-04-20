# -*- coding: utf-8 -*-
from badwolf.utils import sanitize_sensitive_data


def test_sanitize_basic_auth_urls():
    text = 'abc http://user:pwd@example.com def'
    sanitized = sanitize_sensitive_data(text)
    assert 'user' not in sanitized
    assert 'pwd' not in sanitized
    assert 'http://***:***@example.com' in sanitized

    text = '''abc
    http://user:pwd@example.com

    def
    '''
    sanitized = sanitize_sensitive_data(text)
    assert 'user' not in sanitized
    assert 'pwd' not in sanitized
    assert 'http://***:***@example.com' in sanitized

    text = '''abc
    http://example.com

    -e git+https://user:pwd@example.com/

    def
    '''
    sanitized = sanitize_sensitive_data(text)
    assert 'user' not in sanitized
    assert 'pwd' not in sanitized
    assert 'http://example.com' in sanitized
    assert 'git+https://***:***@example.com' in sanitized

    lots_of_urls = ['-e git+https://user:pwd@example.com  abcd'] * 1000
    lots_of_urls.extend(['abc http://example.com def'] * 1000)
    text = '\n'.join(lots_of_urls)
    sanitized = sanitize_sensitive_data(text)
    assert 'user' not in sanitized
    assert 'pwd' not in sanitized
    assert 'http://example.com' in sanitized
    assert 'git+https://***:***@example.com' in sanitized


def test_sanitize_basic_auth_urls_same_line():
    text = '''abc
    http://example.com -e git+https://user:pwd@example.com/

    def
    '''
    sanitized = sanitize_sensitive_data(text)
    assert 'user' not in sanitized
    assert 'pwd' not in sanitized
    assert 'http://example.com' in sanitized
    assert 'git+https://***:***@example.com' in sanitized
