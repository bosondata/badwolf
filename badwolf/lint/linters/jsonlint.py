# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import re

from badwolf.lint import Problem
from badwolf.lint.linters import Linter
from badwolf.lint.utils import in_path, npm_exists, run_command


_LINE_RE = re.compile(r'^(.+)?: line (\d+), col \d+, (.+)$', re.I)


class JSONLinter(Linter):
    name = 'jsonlint'
    default_pattern = '*.json'

    def is_usable(self):
        return in_path('jsonlint') or npm_exists('jsonlint', self.working_dir)

    def lint_files(self, files):
        for file in files:
            command = self.create_command(file)
            _, output = run_command(command, split=True, include_errors=True, cwd=self.working_dir)
            if not output:
                continue

            for line in output:
                parsed = self._parse_line(line)
                if not parsed:
                    continue

                filename, line, message = parsed
                yield Problem(filename, line, message, self.name)

    def create_command(self, file):
        cmd = 'jsonlint'
        if npm_exists('jsonlint', self.working_dir):
            cmd = os.path.join(self.working_dir, 'node_modules', '.bin', 'jsonlint')
        command = [cmd, '-q', '-c', file]
        return command

    def _parse_line(self, line):
        match = _LINE_RE.match(line)
        if not match:
            return

        return match.group(1), int(match.group(2)), match.group(3).strip()
