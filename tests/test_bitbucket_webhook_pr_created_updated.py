# -*- coding: utf-8 -*-
import json
import unittest.mock as mock
from concurrent.futures import Future

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
            'User-Agent': 'Bitbucket-Webhooks/2.0',
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
        },
        'source': {
            'repository': {'full_name': 'deepanalyzer/badwolf'},
            'branch': {'name': 'develop'},
            'commit': {'hash': 'abc'}
        },
        'target': {
            'repository': {'full_name': 'deepanalyzer/badwolf'},
            'branch': {'name': 'master'},
            'commit': {'hash': 'abc'}
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
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
        },
        'source': {
            'repository': {'full_name': 'deepanalyzer/badwolf'},
            'branch': {'name': 'develop'},
            'commit': {'hash': 'abc'}
        },
        'target': {
            'repository': {'full_name': 'deepanalyzer/badwolf'},
            'branch': {'name': 'master'},
            'commit': {'hash': 'abc'}
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'pullrequest:updated',
        }
    )
    assert res.status_code == 200
    assert to_text(res.data) == ''


@mock.patch('badwolf.webhook.views._cancel_outdated_pipelines')
@mock.patch('badwolf.webhook.views.start_pipeline')
def test_pr_created_trigger_start_pipeline(mock_start_pipeline, mock_cancel_pipelines, test_client):
    mock_start_pipeline.delay.return_value = Future()
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
            'source': {
                'repository': {'full_name': 'deepanalyzer/badwolf'},
                'branch': {'name': 'develop'},
                'commit': {'hash': 'abc'}
            },
            'destination': {
                'repository': {'full_name': 'deepanalyzer/badwolf'},
                'branch': {'name': 'master'},
                'commit': {'hash': 'abc'}
            }
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'pullrequest:updated',
        }
    )
    assert res.status_code == 200
    assert mock_start_pipeline.delay.called
