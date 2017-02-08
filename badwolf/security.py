# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import base64

from flask import current_app, Blueprint, request
from cryptography.fernet import Fernet

from badwolf.utils import to_binary, to_text


blueprint = Blueprint('securetoken', __name__)


class SecureToken(object):

    @staticmethod
    def encrypt(text):
        key = base64.urlsafe_b64encode(to_binary(current_app.config['SECURE_TOKEN_KEY']))
        fernet = Fernet(key)
        return fernet.encrypt(to_binary(text))

    @staticmethod
    def decrypt(encrypted):
        key = base64.urlsafe_b64encode(to_binary(current_app.config['SECURE_TOKEN_KEY']))
        fernet = Fernet(key)
        text = fernet.decrypt(to_binary(encrypted))
        return to_text(text)


@blueprint.route('/', methods=['POST'])
def generate_secure_token():
    payload = request.get_data()
    token = SecureToken.encrypt(payload)
    return token + b'\n'
