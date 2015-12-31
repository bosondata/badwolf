# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys

from kombu import Exchange, Queue

# is debugging
DEBUG = False

JSON_AS_ASCII = False

# secret key
SECRET_KEY = ''

# Sentry
SENTRY_DSN = ''

# Celery
CELERY_BROKER_URL = 'amqp://guest@localhost//'
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
CELERY_QUEUES = (
    Queue('badwolf', Exchange('badwolf'), routing_key=''),
)
CELERY_DEFAULT_QUEUE = 'badwolf'

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
