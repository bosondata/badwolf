# -*- coding: utf-8 -*-
import logging

from badwolf.utils import run_command
from badwolf.deploy.providers import Provider


logger = logging.getLogger(__name__)


class PypiProvider(Provider):
    name = 'pypi'

    def deploy(self):
        username = self.config['username']
        password = self.config['password']
        repository = self.config['repository']
        command = [
            'twine',
            'upload',
            '--repository',
            repository,
            '--repository-url',
            repository,
            '--username',
            username,
            '--password',
            password,
            '--skip-existing',
            self.config['distributions']
        ]
        exit_code, output = run_command(command, include_errors=True, cwd=self.working_dir)
        return exit_code == 0, output
