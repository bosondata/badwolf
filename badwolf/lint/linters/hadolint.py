# -*- coding: utf-8 -*-
import os

from badwolf.utils import run_command
from badwolf.lint import Problem
from badwolf.lint.linters import Linter
from badwolf.lint.utils import in_path


class HadoLinter(Linter):
    name = 'hadolint'
    default_pattern = '*Dockerfile*'

    def is_usable(self):
        return in_path('hadolint')

    def lint_files(self, files):
        for file in files:
            command = ['hadolint', file]
            _, output = run_command(
                command,
                split=True,
                include_errors=True,
                cwd=self.working_dir,
                env={
                    'HOME': os.getenv('HOME', '/'),
                    'XDG_CONFIG_HOME': os.getenv('XDG_CONFIG_HOME', '/')
                }
            )
            if not output:
                continue

            for line in output:
                parsed = self._parse_line(line)
                if not parsed:
                    continue

                filename, line, message = parsed
                yield Problem(filename, line, message, self.name)

    def _parse_line(self, line):
        parts = line.split(' ', 1)
        if len(parts) != 2:
            return

        location, message = parts
        if ':' in location:
            filename, line = location.split(':', 1)
            line = int(line)
        else:
            filename = location
            line = 1
        return filename, line, message
