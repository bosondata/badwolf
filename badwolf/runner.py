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
from badwolf.parser import parse_configuration


logger = logging.getLogger(__name__)


class TestRunner(object):
    """Badwolf test runner"""

    def __init__(self, repo_full_name, git_clone_url, commit_hash, payload):
        self.repo_full_name = repo_full_name
        self.repo_name = repo_full_name.split('/')[-1]
        self.git_clone_url = git_clone_url
        self.commit_hash = commit_hash
        self.payload = payload
        self.task_id = str(uuid.uuid4())

        bitbucket_client = bitbucket.Bitbucket(bitbucket.BasicAuthDispatcher(
            current_app.config['BITBUCKET_USERNAME'],
            current_app.config['BITBUCKET_PASSWORD']
        ))
        self.build_status = bitbucket.BuildStatus(
            bitbucket_client,
            repo_full_name,
            commit_hash,
            'BADWOLF-{}'.format(self.task_id[:10]),
            'http://badwolf.bosondata.net',
        )

        self.docker = Client(
            base_url=current_app.config['DOCKER_HOST'],
            timeout=current_app.config['DOCKER_API_TIMEOUT'],
        )

    def run(self):
        start_time = time.time()
        latest_change = self.validate_payload()
        if not latest_change:
            return

        self.branch = latest_change['new']['name']
        self.clone_repository()
        if not self.validate_settings():
            shutil.rmtree(os.path.dirname(self.clone_path), ignore_errors=True)
            return

        docker_image_name = self.get_docker_image()
        if not docker_image_name:
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
            'task_id': self.task_id,
            'repo_full_name': self.repo_full_name,
            'repo_name': self.repo_name,
            'commit_hash': self.commit_hash,
            'commit_message': latest_change['commits'][0]['message'],
            'logs': ''.join(output),
            'exit_code': exit_code,
            'branch': self.branch,
            'scripts': self.project_conf['script'],
            'elapsed_time': int(end_time - start_time),
        }
        self.send_notifications(context)

    def validate_payload(self):
        latest_change = self.payload['push']['changes'][0]
        if not latest_change['new'] or latest_change['new']['type'] != 'branch':
            return
        return latest_change

    def clone_repository(self):
        self.clone_path = os.path.join(
            tempfile.gettempdir(),
            'badwolf',
            self.task_id,
            self.repo_name
        )

        logger.info('Cloning %s to %s...', self.git_clone_url, self.clone_path)
        git.Git().clone(self.git_clone_url, self.clone_path)
        logger.info('Checkout commit %s', self.commit_hash)
        git.Git(self.clone_path).checkout(self.commit_hash)

    def validate_settings(self):
        conf_file = os.path.join(self.clone_path, current_app.config['BADWOLF_PROJECT_CONF'])
        if not os.path.exists(conf_file):
            logger.warning(
                'No project configuration file found for repo: %s',
                self.repo_full_name
            )
            return False

        self.project_conf = project_conf = parse_configuration(conf_file)
        if project_conf['branch'] and self.branch not in project_conf['branch']:
            logger.info(
                'Ignore tests since branch %s test is not enabled. Allowed branches: %s',
                self.branch,
                project_conf['branch']
            )
            return False

        script = project_conf['script']
        if not script:
            logger.warning('No script to run')
            return False
        return True

    def get_docker_image(self):
        docker_image_name = self.repo_full_name.replace('/', '-')
        docker_image = self.docker.images(docker_image_name)
        if not docker_image:
            dockerfile = os.path.join(self.clone_path, self.project_conf['dockerfile'])
            if not os.path.exists(dockerfile):
                logger.warning(
                    'No Dockerfile: %s found for repo: %s',
                    dockerfile,
                    self.repo_full_name
                )
                shutil.rmtree(os.path.dirname(self.clone_path), ignore_errors=True)
                try:
                    self.build_status.update('FAILED')
                except bitbucket.BitbucketAPIError:
                    logger.exception('Error calling Bitbucket API')
                return

            logger.info('Running `docker build`...')
            res = self.docker.build(
                self.clone_path,
                tag=docker_image_name,
                rm=True,
                dockerfile=self.project_conf['dockerfile'],
            )
            for line in res:
                logger.info('`docker build` : %s', line)

        return docker_image_name

    def run_tests_in_container(self, docker_image_name):
        command = '/bin/sh -c badwolf-run'
        container = self.docker.create_container(
            docker_image_name,
            command=command,
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
            self.docker.remove_container(container_id, force=True)

        return exit_code, output

    def update_build_status(self, state):
        try:
            self.build_status.update(state)
        except bitbucket.BitbucketAPIError:
            logger.exception('Error calling Bitbucket API')

    def send_notifications(self, context):
        exit_code = context['exit_code']
        notification = self.project_conf['notification']
        emails = notification['email']
        if not emails:
            return

        from badwolf.tasks import send_mail

        if exit_code == 0:
            send_mail(
                emails,
                'Test succeed for repo: {}, commit: {}'.format(self.repo_full_name, self.commit_hash),
                'test_success',
                context
            )
        else:
            send_mail(
                emails,
                'Test failed for repo: {}, commit: {}'.format(self.repo_full_name, self.commit_hash),
                'test_failure',
                context
            )
