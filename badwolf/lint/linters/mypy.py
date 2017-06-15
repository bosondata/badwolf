# -*- coding: utf-8 -*-
import logging

from badwolf.utils import run_command
from badwolf.lint import Problem
from badwolf.lint.linters import PythonLinter
from badwolf.lint.utils import in_path


logger = logging.getLogger(__name__)


class MypyLinter(PythonLinter):
    name = 'mypy'
    default_pattern = '*.py *.pyi'

    def is_usable(self):
        if not in_path('mypy'):
            return False

        # mypy only avaiable in Python 3
        python_version = self.python_name[6:]
        major, *_ = python_version.split('.', 1)
        if int(major) < 3:
            return False
        return True

    def lint_files(self, files):
        command = [
            self.python_name,
            '-m',
            'mypy',
        ]
        command += files
        _, output = run_command(command, split=True, include_errors=True, cwd=self.working_dir)
        if not output:
            raise StopIteration()

        for line in output:
            filename, line, level, message = self._parse_line(line)
            is_error = level == 'error'
            yield Problem(filename, line, message, self.name, is_error=is_error)

    def _parse_line(self, line):
        """mypy only generates results as stdout.
        Parse the output for real data."""
        parts = line.split(':', 3)
        return parts[0], int(parts[1]), parts[2].strip(), parts[3].strip()
