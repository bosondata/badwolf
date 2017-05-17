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
DEBUG = yesish(os.environ.get('BADWOLF_DEBUG', False))

JSON_AS_ASCII = yesish(os.environ.get('JSON_AS_ASCII', False))
SERVER_NAME = os.environ.get('SERVER_NAME', 'localhost:8000')

# secret key
SECRET_KEY = os.environ.get('SECRET_KEY', '')

# secure token key
SECURE_TOKEN_KEY = os.environ.get('SECURE_TOKEN_KEY', base64.urlsafe_b64encode(os.urandom(32)))

# Sentry
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')

# Docker
DOCKER_HOST = os.environ.get('DOCKER_HOST', 'unix:///var/run/docker.sock')
DOCKER_API_TIMEOUT = int(os.environ.get('DOCKER_API_TIMEOUT', 600))
DOCKER_RUN_TIMEOUT = int(os.environ.get('DOCKER_RUN_TIMEOUT', 1200))

# Mail
MAIL_SERVER = os.environ.get('MAIL_SERVER', '')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = yesish(os.environ.get('MAIL_USE_TLS', True))
MAIL_USE_SSL = yesish(os.environ.get('MAIL_USE_SSL', False))
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
MAIL_MAX_EMAILS = None
MAIL_DEFAULT_SENDER = (
    os.environ.get('MAIL_SENDER_NAME', 'badwolf'),
    os.environ.get('MAIL_SENDER_ADDRESS', '')
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
AUTO_MERGE_ENABLED = yesish(os.environ.get('AUTO_MERGE_ENABLED', True))
AUTO_MERGE_APPROVAL_COUNT = int(os.environ.get('AUTO_MERGE_APPROVAL_COUNT', 3))

BITBUCKET_OAUTH_KEY = os.environ.get('BITBUCKET_OAUTH_KEY', '')
BITBUCKET_OAUTH_SECRET = os.environ.get('BITBUCKET_OAUTH_SECRET', '')

BITBUCKET_USERNAME = os.environ.get('BITBUCKET_USERNAME', '')
BITBUCKET_PASSWORD = os.environ.get('BITBUCKET_PASSWORD', '')

BADWOLF_DATA_DIR = os.environ.get('BADWOLF_DATA_DIR', '/var/lib/badwolf')
BADWOLF_LOG_DIR = os.environ.get('BADWOLF_LOG_DIR', os.path.join(BADWOLF_DATA_DIR, 'log'))
BADWOLF_REPO_DIR = os.environ.get('BADWOLF_REPO_DIR', os.path.join(BADWOLF_DATA_DIR, 'repos'))
if DEBUG:
    if platform.system() == 'Darwin':
        # On macOS, tempfile.gettempdir function doesn't return '/tmp'
        # But Docker for Mac can not mount the path returned by tempfile.gettempdir
        # by default, so let's hardcode it to '/tmp'
        BADWOLF_REPO_DIR = '/tmp/badwolf'  # nosec
    else:
        BADWOLF_REPO_DIR = os.path.join(tempfile.gettempdir(), 'badwolf')

# Sentry Release
try:
    SENTRY_RELEASE = raven.fetch_package_version('badwolf')
except Exception:  # pragma: no cover
    pass


# deansi color override
deansi.variations[0] = ('black', '#333', 'gray')
