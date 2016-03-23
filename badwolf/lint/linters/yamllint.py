# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging

from badwolf.lint import Problem
from badwolf.lint.linters import Linter
from badwolf.lint.utils import in_path, run_command


logger = logging.getLogger(__name__)


class YAMLLinter(Linter):
    name = 'yamllint'
    default_pattern = '*.yml'

    def is_usable(self):
        return in_path('yamllint')

    def lint_files(self, files):
        command = ['yamllint', '-f', 'parsable']
        command += files
        _, output = run_command(command, split=True, cwd=self.working_dir)
        if not output:
            raise StopIteration()

        for line in output:
            filename, line, message = self._parse_line(line)
            is_error = not message.startswith('[warning]')
            yield Problem(filename, line, message, self.name, is_error)

    def _parse_line(self, line):
        parts = line.split(':', 3)
        message = parts[3].strip()
        return parts[0], int(parts[1]), message
