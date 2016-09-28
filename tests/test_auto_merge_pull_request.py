# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json
try:
    import unittest.mock as mock
except ImportError:
    import mock

from flask import url_for

import badwolf.bitbucket as bitbucket


def test_auto_merge_not_enabled(app, test_client):
    app.config['AUTO_MERGE_ENABLED'] = False
    payload = '{}'
    with mock.patch.object(bitbucket.PullRequest, 'get') as pr_get:
        test_client.post(
            url_for('webhook.webhook_push'),
            data=payload,
            headers={
                'X-Event-Key': 'pullrequest:approved',
            }
        )
        pr_get.assert_not_called()
    app.config['AUTO_MERGE_ENABLED'] = True


def test_auto_merge_skip_title(test_client):
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
        },
        'pullrequest': {
            'id': 1,
            'title': 'PR 1 [merge skip]',
            'description': 'PR 1',
        },
    })
    with mock.patch.object(bitbucket.PullRequest, 'get') as pr_get:
        test_client.post(
            url_for('webhook.webhook_push'),
            data=payload,
            headers={
                'X-Event-Key': 'pullrequest:approved',
            }
        )
        pr_get.assert_not_called()


def test_auto_merge_skip_description(test_client):
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
        },
        'pullrequest': {
            'id': 1,
            'title': 'PR 1',
            'description': 'This is PR1. merge skip',
        },
    })
    with mock.patch.object(bitbucket.PullRequest, 'get') as pr_get:
        test_client.post(
            url_for('webhook.webhook_push'),
            data=payload,
            headers={
                'X-Event-Key': 'pullrequest:approved',
            }
        )
        pr_get.assert_not_called()


def test_auto_merge_skip_pr_not_in_open_state(test_client):
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
        },
        'pullrequest': {
            'id': 1,
            'title': 'PR 1',
            'description': 'This is PR1',
        },
    })
    with mock.patch.object(bitbucket.PullRequest, 'get') as pr_get:
        pr_get.return_value = {
            'state': 'CLOSED',
        }
        test_client.post(
            url_for('webhook.webhook_push'),
            data=payload,
            headers={
                'X-Event-Key': 'pullrequest:approved',
            }
        )
        with mock.patch.object(bitbucket.BuildStatus, 'get') as status_get:
            status_get.assert_not_called()
