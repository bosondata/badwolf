# -*- coding: utf-8 -*-
import json
import unittest.mock as mock
from concurrent.futures import Future

from flask import url_for


@mock.patch('badwolf.webhook.views.start_pipeline')
def test_repo_commit_comment_created_ci_retry(mock_start_pipeline, test_client):
    mock_start_pipeline.delay.return_value = Future()
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'comment': {
            'content': {
                'raw': 'test ci retry ',
            }
        },
        'commit': {
            'hash': '00000000',
            'message': 'Test commit',
        },
        'actor': {},
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'repo:commit_comment_created',
        }
    )
    assert res.status_code == 200
    assert mock_start_pipeline.delay.called


@mock.patch('badwolf.webhook.views.start_pipeline')
def test_repo_commit_comment_created_ci_rebuild(mock_start_pipeline, test_client):
    mock_start_pipeline.delay.return_value = Future()
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'comment': {
            'content': {
                'raw': 'test ci rebuild no cache',
            }
        },
        'commit': {
            'hash': '00000000',
            'message': 'Test commit',
        },
        'actor': {},
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'repo:commit_comment_created',
        }
    )
    assert res.status_code == 200
    assert mock_start_pipeline.delay.called


@mock.patch('badwolf.webhook.views.start_pipeline')
def test_repo_commit_comment_created_do_nothing(mock_start_pipeline, test_client):
    mock_start_pipeline.delay.return_value = Future()
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'comment': {
            'content': {
                'raw': 'hello world',
            }
        },
        'commit': {
            'hash': '00000000',
            'message': 'Test commit',
        },
        'actor': {},
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'repo:commit_comment_created',
        }
    )
    assert res.status_code == 200
    mock_start_pipeline.delay.assert_not_called()


@mock.patch('badwolf.webhook.views._cancel_outdated_pipelines')
@mock.patch('badwolf.webhook.views.start_pipeline')
def test_pr_commit_comment_created_do_nothing(mock_start_pipeline, mock_cancel_pipelines, test_client):
    mock_start_pipeline.delay.return_value = Future()
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'comment': {
            'content': {
                'raw': 'hello world',
            }
        },
        'pullrequest': {
            'id': 1,
            'title': 'Test PR',
            'state': 'OPEN',
            'source': {},
            'destination': {},
        },
        'actor': {},
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'pullrequest:comment_created',
        }
    )
    assert res.status_code == 200
    mock_start_pipeline.delay.assert_not_called()


@mock.patch('badwolf.webhook.views._cancel_outdated_pipelines')
@mock.patch('badwolf.webhook.views.start_pipeline')
def test_pr_commit_comment_created_ci_retry(mock_start_pipeline, mock_cancel_pipelines, test_client):
    mock_start_pipeline.delay.return_value = Future()
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'comment': {
            'content': {
                'raw': 'ci retry please',
            }
        },
        'pullrequest': {
            'id': 1,
            'title': 'Test PR',
            'description': '',
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
        },
        'actor': {},
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'pullrequest:comment_created',
        }
    )
    assert res.status_code == 200
    assert mock_start_pipeline.delay.called


@mock.patch('badwolf.webhook.views._cancel_outdated_pipelines')
@mock.patch('badwolf.webhook.views.start_pipeline')
def test_pr_commit_comment_created_ci_rebuild(mock_start_pipeline, mock_cancel_pipelines, test_client):
    mock_start_pipeline.delay.return_value = Future()
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'comment': {
            'content': {
                'raw': 'ci retry please, with no cache',
            }
        },
        'pullrequest': {
            'id': 1,
            'title': 'Test PR',
            'description': '',
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
        },
        'actor': {}
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'pullrequest:comment_created',
        }
    )
    assert res.status_code == 200
    assert mock_start_pipeline.delay.called


@mock.patch('badwolf.webhook.views._cancel_outdated_pipelines')
@mock.patch('badwolf.webhook.views.start_pipeline')
def test_pr_commit_comment_created_ci_retry_state_not_open(mock_start_pipeline, mock_cancel_pipelines, test_client):
    mock_start_pipeline.delay.return_value = Future()
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'comment': {
            'content': {
                'raw': 'ci retry',
            }
        },
        'pullrequest': {
            'id': 1,
            'title': 'Test PR',
            'description': '',
            'state': 'MERGED',
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
        },
        'actor': {}
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'pullrequest:comment_created',
        }
    )
    assert res.status_code == 200
    mock_start_pipeline.delay.assert_not_called()
