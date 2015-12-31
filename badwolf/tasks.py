# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task


@shared_task
def run_test(repo, commit_hash):
    pass
