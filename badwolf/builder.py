# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import io
import time
import logging

import deansi
from flask import current_app, render_template, url_for
from requests.exceptions import ReadTimeout
from docker import Client
from docker.errors import APIError, DockerException
from markupsafe import Markup

from badwolf.utils import to_text, to_binary, sanitize_sensitive_data
from badwolf.extensions import bitbucket
from badwolf.bitbucket import BuildStatus, BitbucketAPIError
from badwolf.notification import send_mail, trigger_slack_webhook


logger = logging.getLogger(__name__)


class Builder(object):
    """Badwolf build runner"""

    def __init__(self, context, spec, docker_version='auto'):
        self.context = context
        self.spec = spec
        self.repo_name = context.repository.split('/')[-1]
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
        context = {
            'context': self.context,
            'build_log_url': url_for('log.build_log', sha=self.commit_hash, _external=True),
            'branch': self.branch,
            'scripts': self.spec.scripts,
            'ansi_termcolor_style': deansi.styleSheet(),
        }

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
            return

        exit_code, output = self.run_in_container(docker_image_name)
        if exit_code == 0:
            # Success
            logger.info('Test succeed for repo: %s', self.context.repository)
            self.update_build_status('SUCCESSFUL', '1 of 1 test succeed')
        else:
            # Failed
            logger.info(
                'Test failed for repo: %s, exit code: %s',
                self.context.repository,
                exit_code
            )
            self.update_build_status('FAILED', '1 of 1 test failed')

        context.update({
            'logs': Markup(deansi.deansi(output)),
            'exit_code': exit_code,
            'elapsed_time': int(time.time() - start_time),
        })
        self.send_notifications(context)

    def get_docker_image(self):
        docker_image_name = self.context.repository.replace('/', '-')
        output = []
        docker_image = self.docker.images(docker_image_name)
        if not docker_image or self.context.rebuild:
            dockerfile = os.path.join(self.context.clone_path, self.spec.dockerfile)
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
                    self.context.repository
                )
                dockerfile_content = 'FROM messense/badwolf-test-runner:python\n'
                fileobj = io.BytesIO(dockerfile_content.encode('utf-8'))
                build_options['fileobj'] = fileobj
            else:
                build_options['dockerfile'] = self.spec.dockerfile

            build_success = False
            logger.info('Building Docker image %s', docker_image_name)
            self.update_build_status('INPROGRESS', 'Building Docker image')
            res = self.docker.build(self.context.clone_path, **build_options)
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

    def run_in_container(self, docker_image_name):
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
            'BADWOLF_REPO_SLUG': self.context.repository,
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
                    self.context.clone_path: {
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
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'build.html')
        with open(log_file, 'wb') as f:
            f.write(to_binary(html))

        if exit_code == 0:
            subject = 'Test succeed for repository {}'.format(self.context.repository)
        else:
            subject = 'Test failed for repository {}'.format(self.context.repository)
        notification = self.spec.notification
        emails = notification['emails']
        if emails:
            send_mail(emails, subject, html)

        slack_webhooks = notification['slack_webhooks']
        if slack_webhooks:
            message = render_template('slack_webhook/' + template + '.md', **context)
            trigger_slack_webhook(slack_webhooks, message)
