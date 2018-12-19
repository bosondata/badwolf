# -*- coding: utf-8 -*-
import json
import unittest.mock as mock

from flask import url_for

import badwolf.bitbucket as bitbucket


def test_auto_merge_not_enabled(app, test_client):
    app.config['AUTO_MERGE_ENABLED'] = False
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
        test_client.post(
            url_for('webhook.webhook_push'),
            data=payload,
            headers={
                'User-Agent': 'Bitbucket-Webhooks/2.0',
                'X-Event-Key': 'pullrequest:approved',
            }
        )
        pr_get.assert_not_called()
    app.config['AUTO_MERGE_ENABLED'] = True


def test_auto_merge_failure_pr_get_error(app, test_client):
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
        pr_get.side_effect = bitbucket.BitbucketAPIError(404, 'not found', 'PR not found')
        test_client.post(
            url_for('webhook.webhook_push'),
            data=payload,
            headers={
                'User-Agent': 'Bitbucket-Webhooks/2.0',
                'X-Event-Key': 'pullrequest:approved',
            }
        )
        with mock.patch.object(bitbucket.BuildStatus, 'get') as status_get:
            status_get.assert_not_called()


def test_auto_merge_skip_merge_skip_in_title(test_client):
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
                'User-Agent': 'Bitbucket-Webhooks/2.0',
                'X-Event-Key': 'pullrequest:approved',
            }
        )
        pr_get.assert_not_called()


def test_auto_merge_skip_merge_skip_in_description(test_client):
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
                'User-Agent': 'Bitbucket-Webhooks/2.0',
                'X-Event-Key': 'pullrequest:approved',
            }
        )
        pr_get.assert_not_called()


def test_auto_merge_skip_wip_in_title(test_client):
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
        },
        'pullrequest': {
            'id': 1,
            'title': '[wip] PR 1',
            'description': 'PR 1',
        },
    })
    with mock.patch.object(bitbucket.PullRequest, 'get') as pr_get:
        test_client.post(
            url_for('webhook.webhook_push'),
            data=payload,
            headers={
                'User-Agent': 'Bitbucket-Webhooks/2.0',
                'X-Event-Key': 'pullrequest:approved',
            }
        )
        pr_get.assert_not_called()


def test_auto_merge_skip_wip_in_description(test_client):
    payload = json.dumps({
        'repository': {
            'full_name': 'deepanalyzer/badwolf',
        },
        'pullrequest': {
            'id': 1,
            'title': 'PR 1',
            'description': 'This is PR1. WIP',
        },
    })
    with mock.patch.object(bitbucket.PullRequest, 'get') as pr_get:
        test_client.post(
            url_for('webhook.webhook_push'),
            data=payload,
            headers={
                'User-Agent': 'Bitbucket-Webhooks/2.0',
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
                'User-Agent': 'Bitbucket-Webhooks/2.0',
                'X-Event-Key': 'pullrequest:approved',
            }
        )
        with mock.patch.object(bitbucket.BuildStatus, 'get') as status_get:
            status_get.assert_not_called()


def test_auto_merge_skip_not_enough_approval(test_client):
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
            'state': 'OPEN',
            'participants': [
                {'approved': False},
                {'approved': True},
                {'approved': False},
            ]
        }
        test_client.post(
            url_for('webhook.webhook_push'),
            data=payload,
            headers={
                'User-Agent': 'Bitbucket-Webhooks/2.0',
                'X-Event-Key': 'pullrequest:approved',
            }
        )
        with mock.patch.object(bitbucket.BuildStatus, 'get') as status_get:
            status_get.assert_not_called()


def test_auto_merge_success(test_client):
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
    with mock.patch.object(bitbucket.PullRequest, 'get') as pr_get, \
            mock.patch.object(bitbucket.PullRequest, 'merge') as pr_merge, \
            mock.patch.object(bitbucket.BuildStatus, 'get') as status_get:
        pr_get.return_value = {
            'state': 'OPEN',
            'participants': [
                {'approved': True},
                {'approved': True},
                {'approved': True},
            ],
            'source': {
                'repository': {'full_name': 'deepanalyzer/badwolf'},
                'commit': {'hash': '0000000'},
            },
        }
        status_get.return_value = {
            'state': 'SUCCESSFUL',
        }
        pr_merge.return_value = None
        test_client.post(
            url_for('webhook.webhook_push'),
            data=payload,
            headers={
                'User-Agent': 'Bitbucket-Webhooks/2.0',
                'X-Event-Key': 'pullrequest:approved',
            }
        )
        assert status_get.called
        assert pr_merge.called


def test_auto_merge_call_error(test_client):
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
    with mock.patch.object(bitbucket.PullRequest, 'get') as pr_get, \
            mock.patch.object(bitbucket.PullRequest, 'merge') as pr_merge, \
            mock.patch.object(bitbucket.BuildStatus, 'get') as status_get:
        pr_get.return_value = {
            'state': 'OPEN',
            'participants': [
                {'approved': True},
                {'approved': True},
                {'approved': True},
            ],
            'source': {
                'repository': {'full_name': 'deepanalyzer/badwolf'},
                'commit': {'hash': '0000000'},
            },
        }
        status_get.return_value = {
            'state': 'SUCCESSFUL',
        }
        pr_merge.side_effect = bitbucket.BitbucketAPIError(401, 'access denied', 'access denied')
        test_client.post(
            url_for('webhook.webhook_push'),
            data=payload,
            headers={
                'User-Agent': 'Bitbucket-Webhooks/2.0',
                'X-Event-Key': 'pullrequest:approved',
            }
        )
        assert status_get.called
        assert pr_merge.called
