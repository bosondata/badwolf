# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json

from flask import url_for


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
            'X-Event-Key': 'repo:push',
        }
    )
    assert res.status_code == 200


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
            'X-Event-Key': 'repo:push',
        }
    )
    assert res.status_code == 200
    assert res.data == ''


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
                        'type': 'tag',
                    }
                }
            ]
        }
    })
    res = test_client.post(
        url_for('webhook.webhook_push'),
        data=payload,
        headers={
            'X-Event-Key': 'repo:push',
        }
    )
    assert res.status_code == 200
    assert res.data == ''
