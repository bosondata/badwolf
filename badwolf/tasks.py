# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import uuid
import atexit
import shutil
import logging
import tempfile
from concurrent.futures import ProcessPoolExecutor

import git
from docker import Client
from flask import current_app

from badwolf.parser import parse_configuration


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
def run_test(repo_full_name, git_clone_url, commit_hash):
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
        return

    project_conf = parse_configuration(conf_file)
    dockerfile = os.path.join(clone_path, project_conf['dockerfile'])
    if not os.path.exists(dockerfile):
        logger.warning('No Dockerfile found for repo: %s', repo_full_name)
        return

    docker = Client()
    docker_image_name = repo_name
    docker_image = docker.images(docker_image_name)
    if not docker_image:
        logger.info('Running `docker build`...')
        res = docker.build(clone_path, tag=docker_image_name, rm=True)
        for line in res:
            logger.info('`docker build` : %s', line)

    script = project_conf['script']
    if not script:
        logger.warning('No script to run')
        return

    command = ';'.join(script)
    command = "/bin/sh -c '{}'".format(command)
    logger.info('Running test script: %s', command)

    container = docker.create_container(
        docker_image_name,
        command=command,
        working_dir='/mnt/app',
        volumes=['/mnt/app'],
        host_config=docker.create_host_config(binds={
            '/mnt/app': {
                'bind': clone_path,
                'mode': 'rw',
            },
        })
    )
    container_id = container['Id']
    logger.info('Created container %s from image %s', container_id, docker_image_name)

    docker.start(container_id)
    output = list(docker.logs(container_id))
    logger.info('Docker output: %s', ''.join(output))

    exit_code = docker.wait(container_id)
    if exit_code == 0:
        # Success
        logger.info('Test succeed for repo: %s', repo_full_name)
    else:
        # Failed
        logger.info('Test failed for repo: %s, exit code: %s', repo_full_name, exit_code)

    # Cleanup
    shutil.rmtree(os.path.dirname(clone_path))
