# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import uuid
import tempfile
import platform

from badwolf.utils import to_text


if platform.system() == 'Darwin':
    # On macOS, tempfile.gettempdir function doesn't return '/tmp'
    # But Docker for Mac can not mount the path returned by tempfile.gettempdir
    # by default, so let's hardcode it to '/tmp'
    TMP_PATH = '/tmp'  # nosec
else:
    TMP_PATH = tempfile.gettempdir()


class Context(object):
    """Badwolf build/lint context"""
    def __init__(self, repository, actor, type, message, source,
                 target=None, rebuild=False, pr_id=None, cleanup_lint=False,
                 nocache=False, clone_depth=50):
        self.task_id = to_text(uuid.uuid4())
        self.repository = repository
        self.repo_name = repository.split('/')[-1]
        self.actor = actor
        self.type = type
        self.message = message
        self.source = source
        self.target = target
        self.rebuild = rebuild
        self.pr_id = pr_id
        self.cleanup_lint = cleanup_lint
        # Don't use cache when build Docker image
        self.nocache = nocache
        self.clone_depth = clone_depth

        if 'repository' not in self.source:
            self.source['repository'] = {'full_name': repository}

        self.clone_path = os.path.join(
            TMP_PATH,
            'badwolf',
            self.task_id,
            self.repo_name,
        )
