# -*- coding: utf-8 -*-
import pytest


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
