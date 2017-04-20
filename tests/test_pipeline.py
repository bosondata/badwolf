# -*- coding: utf-8 -*-
import unittest.mock as mock

import git
import pytest

from badwolf.context import Context
from badwolf.bitbucket import PullRequest, Changesets
from badwolf.pipeline import Pipeline


@pytest.fixture(scope='function')
def push_context():
    return Context(
        'deepanalyzer/badwolf',
        {},
        'commit',
        'Update',
        {
            'repository': {'full_name': 'deepanalyzer/badwolf'},
            'branch': {'name': 'master'},
            'commit': {'hash': '2cedc1af762'},
        }
    )


@pytest.fixture(scope='function')
def pipeline(push_context):
    return Pipeline(push_context)


def test_clone_repo_failed(app, pipeline):
    with mock.patch.object(pipeline, 'clone') as mock_clone, \
            mock.patch.object(pipeline, '_report_git_error') as report_git_error, \
            mock.patch.object(pipeline, 'parse_spec') as mock_spec, \
            mock.patch.object(PullRequest, 'comment') as pr_comment, \
            mock.patch.object(Changesets, 'comment') as cs_comment:
        mock_clone.side_effect = git.GitCommandError('git clone', 1)
        report_git_error.return_value = None
        pr_comment.return_value = None
        cs_comment.return_value = None
        pipeline.start()
        assert report_git_error.called
        mock_spec.assert_not_called()
