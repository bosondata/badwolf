# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import logging.config

from flask import Flask
from celery import Celery


def create_app(config=None):
    app = Flask(__name__)

    # Load default configuration
    app.config.from_object('badwolf.default_settings')

    # Load environment configuration
    if 'BADWOLF_CONF' in os.environ:
        app.config.from_envvar('BADWOLF_CONF')

    # Load app sepcified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        else:
            app.config.from_pyfile(config)

    # Setup logging
    logging.config.dictConfig(app.config['LOGGING'])
    return app


def create_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super(ContextTask, self).__call__(*args, **kwargs)

    celery.Task = ContextTask
    return celery
