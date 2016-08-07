# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sys

import raven

from badwolf.utils import yesish

# is debugging
DEBUG = yesish(os.environ.get('BADWOLF_DEBUG', False))

JSON_AS_ASCII = yesish(os.environ.get('JSON_AS_ASCII', False))

# secret key
SECRET_KEY = os.environ.get('SECRET_KEY', '')

# Sentry
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')

# Docker
DOCKER_HOST = os.environ.get('DOCKER_HOST', 'unix://var/run/docker.sock')
DOCKER_API_TIMEOUT = int(os.environ.get('DOCKER_API_TIMEOUT', 600))
DOCKER_RUN_TIMEOUT = int(os.environ.get('DOCKER_RUN_TIMEOUT', 1200))

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'handlers': {
        'console': {
            'level': 'INFO',
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
            'format': '%(asctime)s %(levelname)-2s %(name)s.%(funcName)s:%(lineno)-5d %(message)s',  # NOQA
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

# Sentry Release
try:
    SENTRY_RELEASE = raven.fetch_package_version('badwolf')
except Exception:  # pragma: no cover
    pass
