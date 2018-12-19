# -*- coding: utf-8 -*-
import json
import unittest.mock as mock
from concurrent.futures import Future

from flask import url_for

from badwolf.utils import to_text


def test_invalid_http_header_bad_request(test_client):
    payload = '{}'
    res = test_client.post(url_for('webhook.webhook_push'), data=payload)
    assert res.status_code == 400


def test_valid_http_header(test_client):
    payload = '{}'
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'repo:push',
        }
    )
    assert res.status_code == 200


def test_unhandled_event(test_client):
    payload = json.dumps({
        'push': {
            'changes': [
            ]
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'repo:created',
        }
    )
    assert res.status_code == 200
    assert to_text(res.data) == ''


def test_repo_push_no_new_changes(test_client):
    payload = json.dumps({
        'push': {
            'changes': [
            ]
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'repo:push',
        }
    )
    assert res.status_code == 200
    assert to_text(res.data) == ''


def test_repo_push_unsupported_push_type(test_client):
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'push': {
            'changes': [
                {
                    'new': {
                        'type': 'wrong_push_type',
                    }
                }
            ]
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'repo:push',
        }
    )
    assert res.status_code == 200
    assert to_text(res.data) == ''


def test_repo_push_unsupported_scm(test_client):
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'hg',
        },
        'push': {
            'changes': [
                {
                    'new': {
                        'type': 'branch',
                    }
                }
            ]
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'repo:push',
        }
    )
    assert res.status_code == 200
    assert to_text(res.data) == ''


def test_repo_push_no_commits(test_client):
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'push': {
            'changes': [
                {
                    'new': {
                        'type': 'branch',
                    },
                    'commits': [],
                }
            ]
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'repo:push',
        }
    )
    assert res.status_code == 200
    assert to_text(res.data) == ''


def test_repo_push_ci_skip_found(test_client):
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'push': {
            'changes': [
                {
                    'new': {
                        'type': 'branch',
                    },
                    'commits': [
                        {
                            'hash': '2cedc1af762',
                            'message': 'Test [ci skip]',
                        }
                    ],
                }
            ]
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'repo:push',
        }
    )
    assert res.status_code == 200
    assert to_text(res.data) == ''


@mock.patch('badwolf.webhook.views._cancel_outdated_pipelines')
@mock.patch('badwolf.webhook.views.start_pipeline')
def test_repo_push_trigger_start_pipeline(mock_start_pipeline, mock_cancel_pipelines, test_client):
    mock_start_pipeline.delay.return_value = Future()
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'actor': {},
        'push': {
            'changes': [
                {
                    'new': {
                        'type': 'branch',
                        'name': 'master',
                    },
                    'commits': [
                        {
                            'hash': '2cedc1af762',
                            'message': 'Test [ci rebuild]',
                        }
                    ],
                }
            ]
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'repo:push',
        }
    )
    assert res.status_code == 200
    assert mock_start_pipeline.delay.called


@mock.patch('badwolf.webhook.views._cancel_outdated_pipelines')
@mock.patch('badwolf.webhook.views.start_pipeline')
def test_repo_push_tag_trigger_start_pipeline(mock_start_pipeline, mock_cancel_pipelines, test_client):
    mock_start_pipeline.delay.return_value = Future()
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
            'scm': 'git',
        },
        'actor': {},
        'push': {
            'changes': [
                {
                    'new': {
                        'type': 'tag',
                        'name': 'v0.1.0',
                        'target': {
                            'hash': '2cedc1af762',
                            'message': 'Test',
                        }
                    }
                }
            ]
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'User-Agent': 'Bitbucket-Webhooks/2.0',
            'X-Event-Key': 'repo:push',
        }
    )
    assert res.status_code == 200
    assert mock_start_pipeline.delay.called
