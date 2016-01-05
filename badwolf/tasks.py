# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import uuid
import time
import atexit
import shutil
import logging
import tempfile
from concurrent.futures import ProcessPoolExecutor

import git
from docker import Client
from docker.errors import APIError, DockerException
from flask import current_app, render_template

from badwolf.parser import parse_configuration
from badwolf.extensions import mail


logger = logging.getLogger(__name__)

executor = ProcessPoolExecutor(max_workers=10)


@atexit.register
def _shutdown_executor():
    try:
        executor.shutdown()
    except Exception:
        pass


def async_task(f):
    def delay(*args, **kwargs):
        return executor.submit(f, *args, **kwargs)
    f.delay = delay
    return f


@async_task
def send_mail(recipients, subject, template, context):
    logger.info('Sending email to %s', recipients)
    html = render_template('mail/' + template + '.html', **context)
    mail.send_message(
        subject=subject,
        recipients=recipients,
        html=html,
    )


@async_task
def run_test(repo_full_name, git_clone_url, commit_hash, payload):
    start_time = time.time()
    latest_change = payload['push']['changes'][0]
    if not latest_change['new'] or latest_change['new']['type'] != 'branch':
        return

    branch = latest_change['new']['name']
    task_id = str(uuid.uuid4())
    repo_name = repo_full_name.split('/')[-1]
    clone_path = os.path.join(
        tempfile.gettempdir(),
        'badwolf',
        task_id,
        repo_name
    )

    logger.info('Cloning %s to %s...', git_clone_url, clone_path)
    git.Git().clone(git_clone_url, clone_path)
    logger.info('Checkout commit %s', commit_hash)
    git.Git(clone_path).checkout(commit_hash)

    conf_file = os.path.join(clone_path, current_app.config['BADWOLF_PROJECT_CONF'])
    if not os.path.exists(conf_file):
        logger.warning('No project configuration file found for repo: %s', repo_full_name)
        shutil.rmtree(os.path.dirname(clone_path))
        return

    project_conf = parse_configuration(conf_file)
    if project_conf['branch'] and branch not in project_conf['branch']:
        logger.info(
            'Ignore tests since branch %s test is not enabled. Allowed branches: %s',
            branch,
            project_conf['branch']
        )
        shutil.rmtree(os.path.dirname(clone_path))
        return

    dockerfile = os.path.join(clone_path, project_conf['dockerfile'])
    if not os.path.exists(dockerfile):
        logger.warning('No Dockerfile: %s found for repo: %s', dockerfile, repo_full_name)
        shutil.rmtree(os.path.dirname(clone_path))
        return

    script = project_conf['script']
    if not script:
        logger.warning('No script to run')
        shutil.rmtree(os.path.dirname(clone_path))
        return

    docker = Client(base_url=current_app.config['DOCKER_HOST'])
    docker_image_name = repo_full_name.replace('/', '-')
    docker_image = docker.images(docker_image_name)
    if not docker_image:
        logger.info('Running `docker build`...')
        res = docker.build(clone_path, tag=docker_image_name, rm=True)
        for line in res:
            logger.info('`docker build` : %s', line)

    command = '/bin/sh -c badwolf-run'
    container = docker.create_container(
        docker_image_name,
        command=command,
        working_dir='/mnt/src',
        volumes=['/mnt/src'],
        host_config=docker.create_host_config(binds={
            clone_path: {
                'bind': '/mnt/src',
                'mode': 'rw',
            },
        })
    )
    container_id = container['Id']
    logger.info('Created container %s from image %s', container_id, docker_image_name)

    try:
        docker.start(container_id)
        exit_code = docker.wait(container_id)
        end_time = time.time()

        output = list(docker.logs(container_id))
        logger.info('%s', ''.join(output))
    except (APIError, DockerException):
        logger.exception('Docker error')
    finally:
        docker.remove_container(container_id, force=True)

    notification = project_conf['notification']
    emails = notification['email']
    context = {
        'task_id': task_id,
        'repo_full_name': repo_full_name,
        'repo_name': repo_name,
        'commit_hash': commit_hash,
        'logs': ''.join(output),
        'exit_code': exit_code,
        'branch': branch,
        'scripts': script,
        'elapsed_time': int(end_time - start_time),
    }
    if exit_code == 0:
        # Success
        logger.info('Test succeed for repo: %s', repo_full_name)
        if emails:
            send_mail(
                emails,
                'Test succeed for repo: {}, commit: {}'.format(repo_full_name, commit_hash),
                'test_success',
                context
            )
    else:
        # Failed
        logger.info('Test failed for repo: %s, exit code: %s', repo_full_name, exit_code)
        if emails:
            send_mail(
                emails,
                'Test failed for repo: {}, commit: {}'.format(repo_full_name, commit_hash),
                'test_failure',
                context
            )

    # Cleanup
    shutil.rmtree(os.path.dirname(clone_path))
