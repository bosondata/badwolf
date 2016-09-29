# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import io
import time
import uuid
import shutil
import logging
import tempfile

import git
import deansi
from flask import current_app, render_template, url_for
from requests.exceptions import ReadTimeout
from docker import Client
from docker.errors import APIError, DockerException
from markupsafe import Markup

from badwolf.utils import to_text, to_binary, sanitize_sensitive_data
from badwolf.spec import Specification
from badwolf.lint.processor import LintProcessor
from badwolf.extensions import bitbucket
from badwolf.bitbucket import BuildStatus, BitbucketAPIError, PullRequest, Changesets
from badwolf.notification import send_mail, trigger_slack_webhook


logger = logging.getLogger(__name__)


class TestContext(object):
    """Test context"""
    def __init__(self, repository, actor, type, message, source,
                 target=None, rebuild=False, pr_id=None, cleanup_lint=False,
                 nocache=False, clone_depth=50):
        self.repository = repository
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


class TestRunner(object):
    """Badwolf test runner"""

    def __init__(self, context, docker_version='auto'):
        self.context = context
        self.repo_full_name = context.repository
        self.repo_name = context.repository.split('/')[-1]
        self.task_id = str(uuid.uuid4())
        self.commit_hash = context.source['commit']['hash']
        self.build_status = BuildStatus(
            bitbucket,
            context.source['repository']['full_name'],
            self.commit_hash,
            'badwolf/test',
            url_for('log.build_log', sha=self.commit_hash, _external=True)
        )

        self.docker = Client(
            base_url=current_app.config['DOCKER_HOST'],
            timeout=current_app.config['DOCKER_API_TIMEOUT'],
            version=docker_version,
        )

    def run(self):
        start_time = time.time()
        self.branch = self.context.source['branch']['name']

        try:
            self.clone_repository()
        except git.GitCommandError as e:
            logger.exception('Git command error')
            self.update_build_status('FAILED', 'Git clone repository failed')
            content = ':broken_heart: **Git error**: {}'.format(to_text(e))
            content = sanitize_sensitive_data(content)
            if self.context.pr_id:
                pr = PullRequest(bitbucket, self.repo_full_name)
                pr.comment(
                    self.context.pr_id,
                    content
                )
            else:
                cs = Changesets(bitbucket, self.repo_full_name)
                cs.comment(
                    self.commit_hash,
                    content
                )

            self.cleanup()
            return

        if not self.validate_settings():
            self.cleanup()
            return

        context = {
            'context': self.context,
            'task_id': self.task_id,
            'build_log_url': url_for('log.build_log', sha=self.commit_hash, _external=True),
            'branch': self.branch,
            'scripts': self.spec.scripts,
            'ansi_termcolor_style': deansi.styleSheet(),
        }

        if self.spec.scripts:
            self.update_build_status('INPROGRESS', 'Test in progress')
            docker_image_name, build_output = self.get_docker_image()
            context.update({
                'build_logs': Markup(build_output),
                'elapsed_time': int(time.time() - start_time),
            })
            if not docker_image_name:
                self.update_build_status('FAILED', 'Build or get Docker image failed')
                context['exit_code'] = -1
                self.send_notifications(context)
                self.cleanup()
                return

            exit_code, output = self.run_tests_in_container(docker_image_name)
            if exit_code == 0:
                # Success
                logger.info('Test succeed for repo: %s', self.repo_full_name)
                self.update_build_status('SUCCESSFUL', '1 of 1 test succeed')
            else:
                # Failed
                logger.info(
                    'Test failed for repo: %s, exit code: %s',
                    self.repo_full_name,
                    exit_code
                )
                self.update_build_status('FAILED', '1 of 1 test failed')

            context.update({
                'logs': Markup(deansi.deansi(output)),
                'exit_code': exit_code,
                'elapsed_time': int(time.time() - start_time),
            })
            self.send_notifications(context)

        # Code linting
        if self.context.pr_id and self.spec.linters:
            lint = LintProcessor(self.context, self.spec, self.clone_path)
            lint.process()

        self.cleanup()

    def clone_repository(self):
        self.clone_path = os.path.join(
            tempfile.gettempdir(),
            'badwolf',
            self.task_id,
            self.repo_name
        )
        source_repo = self.context.source['repository']['full_name']
        if self.context.clone_depth > 0:
            # Use shallow clone to speed up
            bitbucket.clone(source_repo, self.clone_path, depth=50, branch=self.branch)
        else:
            # Full clone for ci retry in single commit
            bitbucket.clone(source_repo, self.clone_path)
        gitcmd = git.Git(self.clone_path)
        if self.context.target:
            # Pull Request
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
            gitcmd.merge('origin/{}'.format(self.branch))
        else:
            # Push to branch or ci retry comment on some commit
            logger.info('Checkout commit %s', self.commit_hash)
            gitcmd.checkout(self.commit_hash)

        gitmodules = os.path.join(self.clone_path, '.gitmodules')
        if os.path.exists(gitmodules):
            gitcmd.submodule('update', '--init', '--recursive')

    def validate_settings(self):
        conf_file = os.path.join(self.clone_path, current_app.config['BADWOLF_PROJECT_CONF'])
        if not os.path.exists(conf_file):
            logger.warning(
                'No project configuration file found for repo: %s',
                self.repo_full_name
            )
            return False

        self.spec = spec = Specification.parse_file(conf_file)
        if self.context.type == 'commit' and spec.branch and self.branch not in spec.branch:
            logger.info(
                'Ignore tests since branch %s test is not enabled. Allowed branches: %s',
                self.branch,
                spec.branch
            )
            return False

        if not spec.scripts and not spec.linters:
            logger.warning('No script(s) or linter(s) to run')
            return False
        return True

    def get_docker_image(self):
        docker_image_name = self.repo_full_name.replace('/', '-')
        output = []
        docker_image = self.docker.images(docker_image_name)
        if not docker_image or self.context.rebuild:
            dockerfile = os.path.join(self.clone_path, self.spec.dockerfile)
            build_options = {
                'tag': docker_image_name,
                'rm': True,
                'stream': True,
                'decode': True,
                'nocache': self.context.nocache,
            }
            if not os.path.exists(dockerfile):
                logger.warning(
                    'No Dockerfile: %s found for repo: %s, using simple runner image',
                    dockerfile,
                    self.repo_full_name
                )
                dockerfile_content = 'FROM messense/badwolf-test-runner:python\n'
                fileobj = io.BytesIO(dockerfile_content.encode('utf-8'))
                build_options['fileobj'] = fileobj
            else:
                build_options['dockerfile'] = self.spec.dockerfile

            build_success = False
            logger.info('Building Docker image %s', docker_image_name)
            self.update_build_status('INPROGRESS', 'Building Docker image')
            res = self.docker.build(self.clone_path, **build_options)
            for log in res:
                if 'errorDetail' in log:
                    msg = log['errorDetail']['message']
                elif 'error' in log:
                    # Deprecated
                    # https://github.com/docker/docker/blob/master/pkg/jsonmessage/jsonmessage.go#L104
                    msg = log['error']
                else:
                    msg = log['stream']
                if 'Successfully built' in msg:
                    build_success = True

                output.append(deansi.deansi(msg))
                logger.info('`docker build` : %s', msg.strip())
            if not build_success:
                return None, ''.join(output)

        return docker_image_name, ''.join(output)

    def run_tests_in_container(self, docker_image_name):
        command = '/bin/sh -c badwolf-run'
        environment = {}
        if self.spec.environments:
            # TODO: Support run in multiple environments
            environment = self.spec.environments[0]

        # TODO: Add more test context related env vars
        environment.update({
            'DEBIAN_FRONTEND': 'noninteractive',
            'CI': 'true',
            'CI_NAME': 'badwolf',
            'BADWOLF_BRANCH': self.branch,
            'BADWOLF_COMMIT': self.commit_hash,
            'BADWOLF_BUILD_DIR': '/mnt/src',
            'BADWOLF_REPO_SLUG': self.repo_full_name,
        })
        if self.context.pr_id:
            environment['BADWOLF_PULL_REQUEST'] = to_text(self.context.pr_id)

        container = self.docker.create_container(
            docker_image_name,
            command=command,
            environment=environment,
            working_dir='/mnt/src',
            volumes=['/mnt/src'],
            host_config=self.docker.create_host_config(
                privileged=self.spec.privileged,
                binds={
                    self.clone_path: {
                        'bind': '/mnt/src',
                        'mode': 'rw',
                    },
                }
            ),
            stdin_open=False,
            tty=True
        )
        container_id = container['Id']
        logger.info('Created container %s from image %s', container_id, docker_image_name)

        output = []
        try:
            self.docker.start(container_id)
            self.update_build_status('INPROGRESS', 'Running tests in Docker container')
            exit_code = self.docker.wait(container_id, current_app.config['DOCKER_RUN_TIMEOUT'])
        except (APIError, DockerException, ReadTimeout) as e:
            exit_code = -1
            output.append(to_text(e))
            logger.exception('Docker error')
        finally:
            try:
                output.append(to_text(self.docker.logs(container_id)))
                self.docker.remove_container(container_id, force=True)
            except (APIError, DockerException, ReadTimeout):
                logger.exception('Error removing docker container')

        return exit_code, ''.join(output)

    def update_build_status(self, state, description=None):
        try:
            self.build_status.update(state, description=description)
        except BitbucketAPIError:
            logger.exception('Error calling Bitbucket API')

    def send_notifications(self, context):
        exit_code = context['exit_code']
        template = 'test_success' if exit_code == 0 else 'test_failure'
        html = render_template('mail/' + template + '.html', **context)
        html = sanitize_sensitive_data(html)

        # Save log html
        log_dir = os.path.join(current_app.config['BADWOLF_LOG_DIR'], self.commit_hash)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, 'build.html')
        with open(log_file, 'wb') as f:
            f.write(to_binary(html))

        if exit_code == 0:
            subject = 'Test succeed for repository {}'.format(self.repo_full_name)
        else:
            subject = 'Test failed for repository {}'.format(self.repo_full_name)
        notification = self.spec.notification
        emails = notification['emails']
        if emails:
            send_mail(emails, subject, html)

        slack_webhooks = notification['slack_webhooks']
        if slack_webhooks:
            message = render_template('slack_webhook/' + template + '.md', **context)
            trigger_slack_webhook(slack_webhooks, message)

    def cleanup(self):
        shutil.rmtree(os.path.dirname(self.clone_path), ignore_errors=True)
