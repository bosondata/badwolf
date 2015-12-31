# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from badwolf.app import create_celery
from badwolf.wsgi import app


celery = create_celery(app)


@celery.task
def run_test(repo, commit_hash):
    pass
