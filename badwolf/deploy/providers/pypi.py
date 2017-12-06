# -*- coding: utf-8 -*-
import logging

from badwolf.utils import run_command
from badwolf.deploy.providers import Provider


logger = logging.getLogger(__name__)


class PypiProvider(Provider):
    name = 'pypi'

    def deploy(self):
        username = self.config.get('username')
        password = self.config.get('password')
        repository = self.config.get('repository')
        command = [
            'twine',
            'upload',
        ]
        if repository:
            command.extend([
                '--repository',
                repository,
                '--repository-url',
                repository
            ])
        if username:
            command.extend([
                '--username',
                username
            ])
        if password:
            command.extend([
                '--password',
                password,
            ])
        command.extend([
            '--skip-existing',
            self.config['distributions']
        ])
        exit_code, output = run_command(
            command,
            include_errors=True,
            cwd=self.working_dir,
            env=self.context.environment
        )
        return exit_code == 0, output

    def url(self):
        pkg_name = self.config.get('package', self.context.repo_name)
        return '{}/pypi/{}'.format(self.config['repository'], pkg_name)
