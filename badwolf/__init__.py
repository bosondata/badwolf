# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals


def create_app(config=None):
    from .app import create_app as _create_app

    app = _create_app(config)

    register_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    setup_celery(app)
    return app


def register_blueprints(app):
    import badwolf.webhook.views

    app.register_blueprint(badwolf.webhook.views.blueprint)


def register_error_handlers(app):
    pass


def setup_celery(app):
    from .app import create_celery

    celery = create_celery(app)
    celery.autodiscover_tasks([
        'badwolf',
    ])
    app.celery = celery


def register_extensions(app):
    from .extensions import sentry

    sentry.init_app(app)
