# -*- coding: utf-8 -*-
from __future__ import unicode_literals
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
