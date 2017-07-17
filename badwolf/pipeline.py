# -*- coding: utf-8 -*-
import os
import shutil
import logging
import fnmatch
import tarfile

import git
from flask import current_app, url_for
from docker.errors import APIError as DockerAPIError

from badwolf.spec import Specification
from badwolf.extensions import bitbucket, sentry
from badwolf.bitbucket import BuildStatus, BitbucketAPIError, PullRequest, Changesets
from badwolf.utils import sanitize_sensitive_data, run_command
from badwolf.cloner import RepositoryCloner
from badwolf.builder import Builder
from badwolf.lint.processor import LintProcessor
from badwolf.deploy import Deployer
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
            url_for('log.build_log', sha=self.commit_hash, task_id=context.task_id, _external=True)
        )

    def start(self):
        '''Start Pipeline'''
        logger.info('Pipeline started for repository %s', self.context.repository)
        try:
            self.clone()
            self.parse_spec()
            build_success = self.build()
            self.save_artifacts()
            self.lint()
            if build_success:
                self.deploy()
        except git.GitCommandError as git_err:
            logger.exception('Git command error')
            self._report_git_error(git_err)
        except BitbucketAPIError:
            logger.exception('Error calling BitBucket API')
            sentry.captureException()
        except InvalidSpecification as err:
            self._report_error(':umbrella: Invalid badwolf configuration: ' + str(err))
        except BadwolfException:
            pass
        finally:
            self.clean()

    def _report_error(self, content):
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

    def _report_git_error(self, exc):
        def _linkify_file(name):
            return '[`{name}`](#chg-{name})'.format(name=name)

        self.build_status.update('FAILED', description='Git clone repository failed')
        git_error_msg = str(exc)
        content = ':broken_heart: **Git error**: {}'.format(git_error_msg)
        if 'Merge conflict' in git_error_msg:
            # git merge conflicted
            conflicted_files = RepositoryCloner.get_conflicted_files(
                self.context.clone_path
            )
            if conflicted_files:
                conflicted_files = '\n'.join(('* ' + _linkify_file(name) for name in conflicted_files.split('\n')))
                content = ':broken_heart: This branch has conflicts that must be resolved\n\n'
                content += '**Conflicting files**\n\n{}'.format(conflicted_files)

        self._report_error(content)

    def _report_docker_error(self, exc):
        self.build_status.update('FAILED', description='Docker error occurred')
        content = ':broken_heart: **Docker error**: {}'.format(exc.explanation)
        self._report_error(content)

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
        if self.context.type == 'branch' and not spec.is_branch_enabled(branch):
            logger.info(
                'Ignore tests since branch %s test is not enabled. Allowed branches: %s',
                branch,
                spec.branch
            )
            raise BuildDisabled()
        if not spec.scripts and not spec.linters:
            logger.warning('No script(s) or linter(s) to run')
            raise InvalidSpecification('No script or linter to run')
        self.spec = spec

    def build(self):
        '''Build project'''
        if self.spec.scripts:
            logger.info('Running build for repository %s', self.context.repository)
            try:
                return Builder(self.context, self.spec, build_status=self.build_status).run()
            except DockerAPIError as e:
                logger.exception('Docker API error')
                self._report_docker_error(e)
        return False

    def save_artifacts(self):
        '''Save artifacts produced during build'''
        if not self.spec.artifacts.paths or self.context.pr_id:
            return
        try:
            self._save_artifacts()
        except Exception:
            logger.exception('Error saving artifacts for repository %s', self.context.repository)
            sentry.captureException()

    def _save_artifacts(self):
        def _should_exclude(path):
            excluded = self.spec.artifacts.excludes
            if not excluded:
                return False

            for pattern in excluded:
                if fnmatch.fnmatch(path, pattern):
                    return True
            return False

        logger.info('Saving artifacts for repository %s', self.context.repository)
        paths = []
        for path in self.spec.artifacts.paths:
            if '$' not in path:
                paths.append(path)
            else:
                cmd = 'echo {}'.format(path)
                exit_code, output = run_command(cmd, cwd=self.context.clone_path, shell=True)
                if exit_code == 0:
                    paths.extend(x for x in output.strip().split(':') if x and not _should_exclude(x))
        if not paths:
            logger.info('No artifacts paths found for repository %s', self.context.repository)
            return

        artifacts_path = os.path.join(
            current_app.config['BADWOLF_ARTIFACTS_DIR'],
            self.context.repository,
            self.context.source['branch']['name'],
        )
        os.makedirs(artifacts_path, exist_ok=True)
        artifacts_file = os.path.join(artifacts_path, 'artifacts.tar.gz')
        with tarfile.open(artifacts_file, 'w:gz') as tar:
            for path in paths:
                tar.add(os.path.join(self.context.clone_path, path), path)

        run_command('shasum artifacts.tar.gz > SHASUM', cwd=artifacts_path, shell=True)
        logger.info('Saved artifacts to %s', artifacts_path)

    def lint(self):
        '''Lint codes'''
        if self.context.pr_id and self.spec.linters:
            logger.info('Running lint for repository %s', self.context.repository)
            LintProcessor(self.context, self.spec).process()

    def deploy(self):
        '''Deploy'''
        if not self.spec.deploy or self.context.type not in {'branch', 'tag'}:
            return

        providers = []
        branch = self.context.source['branch']['name']
        for provider in self.spec.deploy:
            if (self.context.type == 'branch' and branch in provider.branch) or \
                    (self.context.type == 'tag' and provider.tag):
                providers.append(provider)
        if not providers:
            return
        logger.info('Running %d deploy(s) for repository %s', len(providers), self.context.repository)
        Deployer(self.context, self.spec, providers).deploy()

    def clean(self):
        '''Clean local files'''
        logger.info('Cleaning local files (%s) for repository %s',
                    self.context.clone_path,
                    self.context.repository)
        try:
            shutil.rmtree(self.context.clone_path, ignore_errors=True)
        except OSError:
            logger.exception('Error clean local files')
            sentry.captureException()
