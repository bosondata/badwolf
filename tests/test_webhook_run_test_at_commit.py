# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock

from flask import url_for


def test_no_repo_bad_request(test_client):
    res = test_client.post(
        url_for('webhook.run_test_at_commit'),
        data={
            'commit': '4efef562fdf37ddb1a64b7751e81a03d489a6979',
        }
    )
    assert res.status_code == 400


def test_no_commit_bad_request(test_client):
    res = test_client.post(
        url_for('webhook.run_test_at_commit'),
        data={
            'repo': 'deepanalyzer/badwolf',
        }
    )
    assert res.status_code == 400


def test_valid_run_success(test_client):
    import badwolf.tasks

    with mock.patch.object(badwolf.tasks.run_test, 'delay', return_value=True):
        res = test_client.post(
            url_for('webhook.run_test_at_commit'),
            data={
                'repo': 'deepanalyzer/badwolf',
                'commit': '4efef562fdf37ddb1a64b7751e81a03d489a6979',
            }
        )
    assert res.status_code == 200
