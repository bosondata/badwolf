# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import tempfile
try:
    import unittest.mock as mock
except ImportError:
    import mock

import git
import pytest

from badwolf.runner import BuildContext, BuildRunner
from badwolf.bitbucket import PullRequest, Changesets


@pytest.fixture(scope='function')
def push_context():
    return BuildContext(
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
def push_runner(push_context):
    runner = BuildRunner(push_context, docker_version=None)
    runner.clone_path = os.path.join(
        tempfile.gettempdir(),
        'badwolf',
        runner.task_id,
        runner.repo_name
    )
    return runner


def test_clone_repo_failed(app, push_runner):
    with mock.patch.object(push_runner, 'update_build_status') as status, \
            mock.patch.object(push_runner, 'clone_repository') as clone_repo, \
            mock.patch.object(push_runner, 'validate_settings') as validate_settings, \
            mock.patch.object(PullRequest, 'comment') as pr_comment, \
            mock.patch.object(Changesets, 'comment') as cs_comment:
        status.return_value = None
        clone_repo.side_effect = git.GitCommandError('git clone', 1)
        pr_comment.return_value = None
        cs_comment.return_value = None

        push_runner.run()

        validate_settings.assert_not_called()
