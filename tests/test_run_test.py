# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from badwolf.tasks import run_test


repo_name = 'deepanalyzer/badwolf'
clone_url = 'git@bitbucket.org:{}.git'.format(repo_name)
commit = '46322a270817559a3603e67b5e3c3f563d388154'


def test_run_test_no_new_changes(app):
    payload = {
        'push': {
            'changes': [
                {
                    'new': None
                }
            ]
        }
    }
    ret = run_test(repo_name, clone_url, commit, payload)
    assert ret is None
