# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import pytest


@pytest.fixture(scope='module')
def app(request):
    from badwolf.wsgi import app

    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app
