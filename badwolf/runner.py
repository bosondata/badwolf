# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import time
import uuid
import shutil
import logging
import tempfile

import git
from flask import current_app
from docker import Client
from docker.errors import APIError, DockerException

import badwolf.bitbucket as bitbucket
from badwolf.utils import to_text
from badwolf.spec import Specification


logger = logging.getLogger(__name__)


class TestContext(object):
    """Test context"""
    def __init__(self, repository, clone_url, actor, type, message, source, target=None):
        self.repository = repository
        self.clone_url = clone_url
        self.actor = actor
        self.type = type
        self.message = message
        self.source = source
        self.target = target


class TestRunner(object):
    """Badwolf test runner"""

    def __init__(self, context, lock):
        self.context = context
        self.lock = lock
        self.repo_full_name = context.repository
        self.repo_name = context.repository.split('/')[-1]
        self.task_id = str(uuid.uuid4())

        bitbucket_client = bitbucket.Bitbucket(bitbucket.BasicAuthDispatcher(
            current_app.config['BITBUCKET_USERNAME'],
            current_app.config['BITBUCKET_PASSWORD']
        ))
        self.build_status = bitbucket.BuildStatus(
            bitbucket_client,
            context.repository,
            context.source['commit']['hash'],
            'BADWOLF',
            'http://badwolf.bosondata.net',
        )

        self.docker = Client(
            base_url=current_app.config['DOCKER_HOST'],
            timeout=current_app.config['DOCKER_API_TIMEOUT'],
        )

    def run(self):
        start_time = time.time()
        self.branch = self.context.source['branch']['name']

        try:
            self.clone_repository()
        except git.GitCommandError:
            logger.exception('Git command error')
            return

        if not self.validate_settings():
            shutil.rmtree(os.path.dirname(self.clone_path), ignore_errors=True)
            return

        self.update_build_status('INPROGRESS')
        docker_image_name = self.get_docker_image()
        if not docker_image_name:
            self.update_build_status('FAILED')
            return

        exit_code, output = self.run_tests_in_container(docker_image_name)
        if exit_code == 0:
            # Success
            logger.info('Test succeed for repo: %s', self.repo_full_name)
            self.update_build_status('SUCCESSFUL')
        else:
            # Failed
            logger.info(
                'Test failed for repo: %s, exit code: %s',
                self.repo_full_name,
                exit_code
            )
            self.update_build_status('FAILED')

        shutil.rmtree(os.path.dirname(self.clone_path), ignore_errors=True)
        end_time = time.time()

        context = {
            'context': self.context,
            'task_id': self.task_id,
            'logs': ''.join(map(to_text, output)),
            'exit_code': exit_code,
            'branch': self.branch,
            'scripts': self.spec.scripts,
            'elapsed_time': int(end_time - start_time),
        }
        self.send_notifications(context)

    def clone_repository(self):
        self.clone_path = os.path.join(
            tempfile.gettempdir(),
            'badwolf',
            self.task_id,
            self.repo_name
        )

        logger.info('Cloning %s to %s...', self.context.clone_url, self.clone_path)
        git.Git().clone(self.context.clone_url, self.clone_path)

        if self.context.target:
            logger.info('Checkout branch %s', self.context.target['branch']['name'])
            git.Git(self.clone_path).checkout(self.context.target['branch']['name'])

            logger.info(
                'Mergeing branch %s into %s',
                self.context.source['branch']['name'],
                self.context.target['branch']['name']
            )
            git.Git(self.clone_path).merge(
                'origin/{}'.format(self.context.source['branch']['name'])
            )
        else:
            logger.info('Checkout commit %s', self.context.source['commit']['hash'])
            git.Git(self.clone_path).checkout(self.context.source['commit']['hash'])

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

        if not spec.scripts:
            logger.warning('No script to run')
            return False
        return True

    def get_docker_image(self):
        docker_image_name = self.repo_full_name.replace('/', '-')
        with self.lock:
            docker_image = self.docker.images(docker_image_name)
            if not docker_image:
                dockerfile = os.path.join(self.clone_path, self.spec.dockerfile)
                if not os.path.exists(dockerfile):
                    logger.warning(
                        'No Dockerfile: %s found for repo: %s',
                        dockerfile,
                        self.repo_full_name
                    )
                    shutil.rmtree(os.path.dirname(self.clone_path), ignore_errors=True)
                    return

                logger.info('Running `docker build`...')
                res = self.docker.build(
                    self.clone_path,
                    tag=docker_image_name,
                    rm=True,
                    dockerfile=self.spec.dockerfile,
                )
                for line in res:
                    logger.info('`docker build` : %s', line)

        return docker_image_name

    def run_tests_in_container(self, docker_image_name):
        command = '/bin/sh -c badwolf-run'
        environment = {}
        if self.spec.environments:
            # TODO: Support run in multiple environments
            environment = self.spec.environments[0]

        # TODO: Add more test context related env vars
        environment['BADWOLF_BRANCH'] = self.branch

        container = self.docker.create_container(
            docker_image_name,
            command=command,
            environment=environment,
            working_dir='/mnt/src',
            volumes=['/mnt/src'],
            host_config=self.docker.create_host_config(binds={
                self.clone_path: {
                    'bind': '/mnt/src',
                    'mode': 'rw',
                },
            })
        )
        container_id = container['Id']
        logger.info('Created container %s from image %s', container_id, docker_image_name)

        try:
            self.docker.start(container_id)
            exit_code = self.docker.wait(container_id)
            output = list(self.docker.logs(container_id))
        except (APIError, DockerException) as e:
            exit_code = -1
            output = [str(e)]

            logger.exception('Docker error')
        finally:
            try:
                self.docker.remove_container(container_id, force=True)
            except (APIError, DockerException):
                logger.exception('Error removing docker container')

        return exit_code, output

    def update_build_status(self, state):
        try:
            self.build_status.update(state)
        except bitbucket.BitbucketAPIError:
            logger.exception('Error calling Bitbucket API')

    def send_notifications(self, context):
        exit_code = context['exit_code']
        notification = self.spec.notification
        emails = notification['emails']
        if not emails:
            return

        from badwolf.tasks import send_mail

        if exit_code == 0:
            send_mail(
                emails,
                'Test succeed for repository {}'.format(self.repo_full_name),
                'test_success',
                context
            )
        else:
            send_mail(
                emails,
                'Test failed for repository {}'.format(self.repo_full_name),
                'test_failure',
                context
            )
