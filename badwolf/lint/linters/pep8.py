# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import logging

from badwolf.lint import Problem
from badwolf.lint.linters import Linter
from badwolf.lint.utils import in_path, run_command


logger = logging.getLogger(__name__)


class PEP8Linter(Linter):
    name = 'pep8'

    def is_usable(self):
        return in_path('pep8')

    def match_file(self, filename):
        base = os.path.basename(filename)
        _, ext = os.path.splitext(base)
        return ext.lower() == '.py'

    def lint_files(self, files):
        command = ['pep8']
        command += files
        _, output = run_command(command, split=True, cwd=self.working_dir)
        if not output:
            raise StopIteration()

        for line in output:
            filename, line, message = self._parse_line(line)
            yield Problem(filename, line, message, self.name)

    def _parse_line(self, line):
        """pep8 only generates results as stdout.
        Parse the output for real data."""
        parts = line.split(':', 3)
        message = parts[3].strip()
        return parts[0], int(parts[1]), message
