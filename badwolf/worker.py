# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from badwolf import create_app


flask_app = create_app()
app = flask_app.celery
