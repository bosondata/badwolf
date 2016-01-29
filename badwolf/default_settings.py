# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sys

# is debugging
DEBUG = False

JSON_AS_ASCII = False

# secret key
SECRET_KEY = ''

# Sentry
SENTRY_DSN = ''

# Docker
DOCKER_HOST = os.environ.get('DOCKER_HOST', 'unix://var/run/docker.sock')
DOCKER_API_TIMEOUT = 600

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
            'format': '%(asctime)s %(levelname)-2s %(pathname)s:%(lineno)-5d %(message)s',  # NOQA
        },
    },
}

BADWOLF_PROJECT_CONF = '.badwolf.yml'
AUTO_MERGE_ENABLED = True
AUTO_MERGE_APPROVAL_COUNT = 3

BITBUCKET_OAUTH_KEY = ''
BITBUCKET_OAUTH_SECRET = ''

BITBUCKET_USERNAME = ''
BITBUCKET_PASSWORD = ''
