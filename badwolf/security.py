# -*- coding: utf-8 -*-

from flask import current_app, Blueprint, request
from cryptography.fernet import Fernet

from badwolf.utils import to_binary, to_text


blueprint = Blueprint('securetoken', __name__)


class SecureToken(object):

    @staticmethod
    def encrypt(text):
        fernet = Fernet(to_binary(current_app.config['SECURE_TOKEN_KEY']))
        return fernet.encrypt(to_binary(text))

    @staticmethod
    def decrypt(encrypted):
        fernet = Fernet(to_binary(current_app.config['SECURE_TOKEN_KEY']))
        text = fernet.decrypt(to_binary(encrypted))
        return to_text(text)


def parse_secretfile(fd):
    env = []
    for line in fd:
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            continue
        elif line.startswith('>'):
            # Write to file not supported for now
            continue
        else:
            env.append(line)
    return env


@blueprint.route('/', methods=['POST'])
def generate_secure_token():
    payload = request.get_data()
    token = SecureToken.encrypt(payload)
    return token + b'\n'
