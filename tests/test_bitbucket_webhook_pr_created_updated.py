# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json
try:
    import unittest.mock as mock
except ImportError:
    import mock

from flask import url_for

from badwolf.utils import to_text


def test_pr_created_unsupported_scm(test_client):
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'hg',
        },
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'X-Event-Key': 'pullrequest:created',
        }
    )
    assert res.status_code == 200
    assert to_text(res.data) == ''


def test_pr_updated_ci_skip_found(test_client):
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'pullrequest': {
            'title': 'Test PR',
            'description': 'ci skip',
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'X-Event-Key': 'pullrequest:updated',
        }
    )
    assert res.status_code == 200
    assert to_text(res.data) == ''


def test_pr_updated_state_not_open(test_client):
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'pullrequest': {
            'title': 'Test PR',
            'description': '',
            'state': 'MERGED',
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'X-Event-Key': 'pullrequest:updated',
        }
    )
    assert res.status_code == 200
    assert to_text(res.data) == ''


@mock.patch('badwolf.webhook.views.start_pipeline')
def test_pr_created_trigger_start_pipeline(mock_start_pipeline, test_client):
    mock_start_pipeline.delay.return_value = None
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'actor': {},
        'pullrequest': {
            'id': 1,
            'title': 'Test PR',
            'description': 'ci rebuild',
            'state': 'OPEN',
            'source': {},
            'destination': {}
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'X-Event-Key': 'pullrequest:updated',
        }
    )
    assert res.status_code == 200
    assert mock_start_pipeline.delay.called
