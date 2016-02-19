# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from multiprocessing import Lock

import git
import mock
import pytest

from badwolf.runner import TestContext, TestRunner


@pytest.fixture(scope='function')
def push_context():
    return TestContext(
        'deepanalyzer/badwolf',
        'git@bitbucket.org:deepanalyzer/badwolf.git',
        {},
        'commit',
        'Update',
        {
            'branch': {'name': 'master'},
            'commit': {'hash': '2cedc1af762'},
        }
    )


@pytest.fixture(scope='function')
def push_runner(push_context):
    return TestRunner(push_context, Lock())


def test_clone_repo_failed(app, push_runner):
    with mock.patch.object(push_runner, 'update_build_status') as status, \
            mock.patch.object(push_runner, 'clone_repository') as clone_repo, \
            mock.patch.object(push_runner, 'validate_settings') as validate_settings:
        status.return_value = None
        clone_repo.side_effect = git.GitCommandError('git clone', 1)
        push_runner.run()

        validate_settings.assert_not_called()
