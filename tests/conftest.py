# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import sys
import pytest

CURR_DIR = os.path.abspath(os.path.dirname(__file__))
PROJ_DIR = os.path.dirname(CURR_DIR)
if PROJ_DIR not in sys.path:
    sys.path.insert(0, PROJ_DIR)


@pytest.fixture(scope='module')
def app(request):
    from badwolf.wsgi import app

    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = 'localhost'
    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope='module')
def test_client(app):
    return app.test_client()
