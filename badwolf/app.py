# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os

from flask import Flask


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
    return app
