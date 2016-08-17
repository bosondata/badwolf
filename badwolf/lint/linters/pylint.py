# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging

from badwolf.utils import to_text
from badwolf.lint import Problem
from badwolf.lint.linters import PythonLinter
from badwolf.lint.utils import in_path, run_command


logger = logging.getLogger(__name__)


class PylintLinter(PythonLinter):
    name = 'pylint'

    def is_usable(self):
        return in_path('pylint')

    def lint_files(self, files):
        command = [self.python_name, '-m', 'pylint', '-r', 'n', '-f', 'parseable']
        command += files
        _, output = run_command(
            command,
            split=True,
            include_errors=True,
            cwd=self.working_dir
        )
        if not output:
            raise StopIteration()

        for line in output:
            parsed = self._parse_line(to_text(line))
            if parsed is None:
                continue

            filename, line, message = parsed
            yield Problem(filename, line, message, self.name)

    def _parse_line(self, line):
        parts = line.split(':', 3)
        if len(parts) != 3:
            return

        message = parts[2].strip()
        try:
            return parts[0], int(parts[1]), message
        except ValueError:
            return
