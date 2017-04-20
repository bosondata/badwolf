# -*- coding: utf-8 -*-
from badwolf.utils import run_command
from badwolf.lint import Problem
from badwolf.lint.linters import Linter
from badwolf.lint.utils import in_path, parse_checkstyle


class ShellCheckLinter(Linter):
    name = 'shellcheck'
    default_pattern = '*.sh'

    def is_usable(self):
        return in_path('shellcheck')

    def lint_files(self, files):
        command = self.create_command(files)
        _, output = run_command(command, cwd=self.working_dir)
        if not output:
            raise StopIteration()

        problems = parse_checkstyle(output)
        for filename, line, message in problems:
            yield Problem(self._relativize_filename(filename), line, message, self.name)

    def create_command(self, files):
        command = ['shellcheck', '-f', 'checkstyle']
        command += files
        return command
