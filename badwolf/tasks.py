# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import uuid
import shutil
import logging
import tempfile

import git
from celery import shared_task


logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_test(self, repo_full_name, git_clone_url, commit_hash):
    task_id = self.id if hasattr(self, 'id') else str(uuid.uuid4())
    repo_name = repo_full_name.split('/')[-1]
    clone_path = os.path.join(
        tempfile.gettempdir(),
        'badwolf',
        task_id,
        repo_name
    )

    logger.info('Cloning %s to %s...', git_clone_url, clone_path)
    git.Git().clone(git_clone_url, clone_path)

    # Cleanup
    shutil.rmtree(os.path.dirname(clone_path))
