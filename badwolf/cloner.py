# -*- coding: utf-8 -*-
import os
import logging

import git

from badwolf.extensions import bitbucket


logger = logging.getLogger(__name__)


class RepositoryCloner(object):
    '''Repository cloner

    Clone repository from BitBucket to local
    '''
    def __init__(self, context):
        self.context = context
        self.commit_hash = context.source['commit']['hash']

    def clone(self):
        clone_path = self.context.clone_path
        source_repo = self.context.source['repository']['full_name']
        if self.context.clone_depth > 0:
            # Use shallow clone to speed up
            clone_kwargs = dict(
                depth=self.context.clone_depth,
                branch=self.context.source['branch']['name']
            )
            if self.context.type == 'commit':
                # ci retry on commit
                clone_kwargs['no_single_branch'] = True
            bitbucket.clone(
                source_repo,
                clone_path,
                **clone_kwargs
            )
        else:
            # Full clone for ci retry in single commit
            bitbucket.clone(source_repo, clone_path)

        gitcmd = git.Git(clone_path)
        if self.context.target:
            self._merge_pull_request(gitcmd)
        else:
            # Push to branch or ci retry comment on some commit
            if not self.is_commit_exists(gitcmd, self.commit_hash):
                logger.info('Unshallowing a shallow cloned repository')
                output = gitcmd.fetch('--unshallow')
                logger.info('%s', output)
            logger.info('Checkout commit %s', self.commit_hash)
            gitcmd.checkout(self.commit_hash)

        gitmodules = os.path.join(clone_path, '.gitmodules')
        if os.path.exists(gitmodules):
            output = gitcmd.submodule('update', '--init', '--recursive')
            logger.info('%s', output)

    def _merge_pull_request(self, gitcmd):
        # Pull Request
        source_repo = self.context.source['repository']['full_name']
        target_repo = self.context.target['repository']['full_name']
        target_branch = self.context.target['branch']['name']
        if source_repo == target_repo:
            target_remote = 'origin'
        else:
            # Pull Reuqest across forks
            target_remote = target_repo.split('/', 1)[0]
            gitcmd.remote('add', target_remote, bitbucket.get_git_url(target_repo))
        gitcmd.fetch(target_remote, target_branch)
        gitcmd.checkout('FETCH_HEAD')
        gitcmd.merge('origin/{}'.format(self.context.source['branch']['name']))

    @staticmethod
    def is_commit_exists(gitcmd, sha):
        output = gitcmd.rev_parse('--quiet', '--verify', '%s^{commit}' % sha, with_exceptions=False)
        return bool(output.strip())

    @staticmethod
    def get_conflicted_files(repo_path):
        gitcmd = git.Git(repo_path)
        try:
            return gitcmd.diff('--name-only', '--diff-filter=U')
        except git.GitCommandError:
            logger.exception('Error get conflicted files by git diff command')
            return None
