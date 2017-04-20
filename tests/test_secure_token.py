# -*- coding: utf-8 -*-

from badwolf.security import SecureToken


def test_secure_token(app):
    plaintext = 'super secret'
    token = SecureToken.encrypt(plaintext)
    decrypted = SecureToken.decrypt(token)
    assert plaintext == decrypted
