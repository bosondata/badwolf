# -*- coding: utf-8 -*-
import os
import uuid

from flask import current_app

from badwolf.utils import to_text


class Context(object):
    """Badwolf build/lint context"""
    def __init__(self, repository, actor, type, message, source, target=None,
                 rebuild=False, pr_id=None, nocache=False, clone_depth=50):
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
        # Don't use cache when build Docker image
        self.nocache = nocache
        self.clone_depth = clone_depth

        if 'repository' not in self.source:
            self.source['repository'] = {'full_name': repository}

        self.clone_path = os.path.join(
            current_app.config['BADWOLF_REPO_DIR'],
            self.repo_name,
            self.task_id,
        )
