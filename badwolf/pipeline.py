# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import shutil
import logging

import git
from flask import current_app, url_for

from badwolf.spec import Specification
from badwolf.extensions import bitbucket
from badwolf.bitbucket import BuildStatus, BitbucketAPIError, PullRequest, Changesets
from badwolf.utils import to_text, sanitize_sensitive_data
from badwolf.cloner import RepositoryCloner
from badwolf.builder import Builder
from badwolf.lint.processor import LintProcessor
from badwolf.exceptions import (
    BadwolfException,
    SpecificationNotFound,
    BuildDisabled,
    InvalidSpecification,
)


logger = logging.getLogger(__name__)


class Pipeline(object):
    '''badwolf build/lint pipeline'''
    def __init__(self, context):
        self.context = context
        self.commit_hash = context.source['commit']['hash']
        self.build_status = BuildStatus(
            bitbucket,
            context.source['repository']['full_name'],
            self.commit_hash,
            'badwolf/test',
            url_for('log.build_log', sha=self.commit_hash, _external=True)
        )

    def start(self):
        '''Start Pipeline'''
        logger.info('Pipeline started for repository %s', self.context.repository)
        try:
            self.clone()
            self.parse_spec()
            self.build()
            self.lint()
        except git.GitCommandError as git_err:
            logger.exception('Git command error')
            self._report_git_error(git_err)
        except BitbucketAPIError:
            logger.exception('Error calling BitBucket API')
        except BadwolfException:
            pass
        finally:
            self.clean()

    def _report_git_error(self, exc):
        self.build_status.update('FAILED', description='Git clone repository failed')
        content = ':broken_heart: **Git error**: {}'.format(to_text(exc))
        content = sanitize_sensitive_data(content)
        if self.context.pr_id:
            pr = PullRequest(bitbucket, self.context.repository)
            pr.comment(
                self.context.pr_id,
                content
            )
        else:
            cs = Changesets(bitbucket, self.context.repository)
            cs.comment(
                self.commit_hash,
                content
            )

    def clone(self):
        '''Clone Git repository to local'''
        logger.info('Cloning repository %s', self.context.repository)
        RepositoryCloner(self.context).clone()

    def parse_spec(self):
        '''Parse repository build/lint spec'''
        logger.info('Parsing specification for repository %s', self.context.repository)
        conf_file = os.path.join(self.context.clone_path, current_app.config['BADWOLF_PROJECT_CONF'])
        try:
            spec = Specification.parse_file(conf_file)
        except OSError:
            logger.warning(
                'No project configuration file found for repo: %s',
                self.context.repository
            )
            raise SpecificationNotFound()

        branch = self.context.source['branch']['name']
        if self.context.type == 'commit' and not spec.is_branch_enabled(branch):
            logger.info(
                'Ignore tests since branch %s test is not enabled. Allowed branches: %s',
                branch,
                spec.branch
            )
            raise BuildDisabled()
        if not spec.scripts and not spec.linters:
            logger.warning('No script(s) or linter(s) to run')
            raise InvalidSpecification()
        self.spec = spec

    def build(self):
        '''Build project'''
        if self.spec.scripts:
            logger.info('Running build for repository %s', self.context.repository)
            Builder(self.context, self.spec).run()

    def lint(self):
        '''Lint codes'''
        if self.context.pr_id and self.spec.linters:
            logger.info('Running lint for repository %s', self.context.repository)
            LintProcessor(self.context, self.spec).process()

    def clean(self):
        '''Clean local files'''
        logger.info('Cleaning local files for repository %s', self.context.repository)
        try:
            shutil.rmtree(os.path.dirname(self.context.clone_path), ignore_errors=True)
        except OSError:
            logger.exception('Error clean local files')
