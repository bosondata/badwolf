# -*- coding: utf-8 -*-
import os
import logging.config

from flask import Flask


def create_app(config=None):
    app = Flask(__name__)

    # Load default configuration
    app.config.from_object('badwolf.default_settings')

    # Load configuration from ~/.badwolf.conf.py
    user_conf = os.path.expanduser('~/.badwolf.conf.py')
    if os.path.isfile(user_conf):
        app.config.from_pyfile(user_conf)

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
