# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import re


_PARAGRAPH_RE = re.compile(r'(?:\r\n|\r|\n){2,}')


def create_app(config=None):
    from .app import create_app as _create_app

    app = _create_app(config)

    register_extensions(app)
    register_filters(app)
    register_blueprints(app)
    register_error_handlers(app)
    return app


def register_blueprints(app):
    import badwolf.webhook.views

    app.register_blueprint(badwolf.webhook.views.blueprint)


def register_error_handlers(app):
    pass


def register_extensions(app):
    from .extensions import sentry, mail

    sentry.init_app(app)
    mail.init_app(app)


def register_filters(app):
    from jinja2 import evalcontextfilter, Markup, escape

    @app.template_filter()
    @evalcontextfilter
    def nl2br(eval_ctx, value):
        result = '\n\n'.join('<p>%s</p>' % p.replace('\n', Markup('<br/>\n'))
                             for p in _PARAGRAPH_RE.split(escape(value)))
        if eval_ctx.autoescape:
            result = Markup(result)
        return result

    @app.template_filter()
    @evalcontextfilter
    def blankspace2nbsp(eval_ctx, value):
        result = value.replace(' ', Markup('&nbsp;'))
        result = result.replace('\t', Markup('&nbsp;&nbsp;&nbsp;&nbsp;'))
        if eval_ctx.autoescape:
            result = Markup(result)
        return result
