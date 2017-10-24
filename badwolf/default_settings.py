# -*- coding: utf-8 -*-
import os
import sys
import base64
import tempfile
import platform

import raven
import deansi

from badwolf.utils import yesish

# is debugging
DEBUG = yesish(os.getenv('BADWOLF_DEBUG', False))

JSON_AS_ASCII = yesish(os.getenv('JSON_AS_ASCII', False))
SERVER_NAME = os.getenv('SERVER_NAME', 'localhost:8000')

# secret key
SECRET_KEY = os.getenv('SECRET_KEY', '')

# secure token key
SECURE_TOKEN_KEY = os.getenv('SECURE_TOKEN_KEY', base64.urlsafe_b64encode(os.urandom(32)))

# Sentry
SENTRY_DSN = os.getenv('SENTRY_DSN', '')

# Docker
DOCKER_HOST = os.getenv('DOCKER_HOST', 'unix:///var/run/docker.sock')
DOCKER_API_TIMEOUT = int(os.getenv('DOCKER_API_TIMEOUT', 600))
DOCKER_RUN_TIMEOUT = int(os.getenv('DOCKER_RUN_TIMEOUT', 1200))

# Mail
MAIL_SERVER = os.getenv('MAIL_SERVER', '')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = yesish(os.getenv('MAIL_USE_TLS', True))
MAIL_USE_SSL = yesish(os.getenv('MAIL_USE_SSL', False))
MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
MAIL_MAX_EMAILS = None
MAIL_DEFAULT_SENDER = (
    os.getenv('MAIL_SENDER_NAME', 'badwolf'),
    os.getenv('MAIL_SENDER_ADDRESS', '')
)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'handlers': ['console'],
        'level': 'INFO' if not DEBUG else 'DEBUG',
    },
    'handlers': {
        'console': {
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': sys.stderr,
        }
    },
    'loggers': {
        'urllib3': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)-2s %(name)s.%(funcName)s:%(lineno)-5d %(message)s',
        },
    },
}

BADWOLF_PROJECT_CONF = '.badwolf.yml'
AUTO_MERGE_ENABLED = yesish(os.getenv('AUTO_MERGE_ENABLED', True))
AUTO_MERGE_APPROVAL_COUNT = int(os.getenv('AUTO_MERGE_APPROVAL_COUNT', 3))

BITBUCKET_OAUTH_KEY = os.getenv('BITBUCKET_OAUTH_KEY', '')
BITBUCKET_OAUTH_SECRET = os.getenv('BITBUCKET_OAUTH_SECRET', '')

BITBUCKET_USERNAME = os.getenv('BITBUCKET_USERNAME', '')
BITBUCKET_PASSWORD = os.getenv('BITBUCKET_PASSWORD', '')

BADWOLF_DATA_DIR = os.getenv('BADWOLF_DATA_DIR', '/var/lib/badwolf')
if DEBUG:
    if platform.system() == 'Darwin':
        # On macOS, tempfile.gettempdir function doesn't return '/tmp'
        # But Docker for Mac can not mount the path returned by tempfile.gettempdir
        # by default, so let's hardcode it to '/tmp'
        BADWOLF_DATA_DIR = '/tmp/badwolf'  # nosec
    else:
        BADWOLF_DATA_DIR = os.path.join(tempfile.gettempdir(), 'badwolf')
BADWOLF_LOG_DIR = os.getenv('BADWOLF_LOG_DIR', os.path.join(BADWOLF_DATA_DIR, 'log'))
BADWOLF_REPO_DIR = os.getenv('BADWOLF_REPO_DIR', os.path.join(BADWOLF_DATA_DIR, 'repos'))
BADWOLF_ARTIFACTS_DIR = os.getenv('BADWOLF_REPO_DIR', os.path.join(BADWOLF_DATA_DIR, 'artifacts'))

# Vault
VAULT_URL = os.getenv('VAULT_URL', os.getenv('VAULT_ADDR'))
VAULT_TOKEN = os.getenv('VAULT_TOKEN')

# Sentry Release
try:
    SENTRY_RELEASE = raven.fetch_package_version('badwolf')
except Exception:  # pragma: no cover
    pass


# deansi color override
deansi.variations[0] = ('black', '#333', 'gray')
