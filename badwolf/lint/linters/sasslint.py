# -*- coding: utf-8 -*-
import os

from badwolf.utils import run_command
from badwolf.lint import Problem
from badwolf.lint.linters import Linter
from badwolf.lint.utils import in_path, npm_exists, parse_checkstyle


class SassLinter(Linter):
    name = 'sasslint'
    default_pattern = '*.scss'

    def is_usable(self):
        return in_path('sass-lint') or npm_exists('sass-lint', self.working_dir)

    def lint_files(self, files):
        command = self.create_command(files)
        _, output = run_command(command, cwd=self.working_dir)
        if not output:
            raise StopIteration()

        problems = parse_checkstyle(output)
        for filename, line, message in problems:
            yield Problem(self._relativize_filename(filename), line, message, self.name)

    def create_command(self, files):
        cmd = 'sass-lint'
        if npm_exists('sass-lint', self.working_dir):
            cmd = os.path.join(self.working_dir, 'node_modules', '.bin', 'sass-lint')
        command = [cmd, '-v', '-f', 'checkstyle']
        command += files
        return command
