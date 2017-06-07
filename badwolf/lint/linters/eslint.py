# -*- coding: utf-8 -*-
import os

try:
    from is_minified_js import is_likely_minified
except ImportError:
    def is_likely_minified(_path):
        return False

from badwolf.utils import run_command
from badwolf.lint import Problem
from badwolf.lint.linters import Linter
from badwolf.lint.utils import in_path, npm_exists, parse_checkstyle


class ESLinter(Linter):
    name = 'eslint'
    default_pattern = '*.js'

    def is_usable(self):
        return in_path('eslint') or npm_exists('eslint', self.working_dir)

    def match_file(self, filename):
        # 过滤掉压缩过的 JavaScript 文件
        if filename.lower().endswith('.min.js'):
            return False
        if is_likely_minified(os.path.join(self.working_dir, filename)):
            return False
        return super(ESLinter, self).match_file(filename)

    def lint_files(self, files):
        command = self.create_command(files)
        _, output = run_command(command, cwd=self.working_dir)
        if not output:
            raise StopIteration()

        problems = parse_checkstyle(output)
        for filename, line, message in problems:
            yield Problem(self._relativize_filename(filename), line, message, self.name)

    def create_command(self, files):
        cmd = 'eslint'
        if npm_exists('eslint', self.working_dir):
            cmd = os.path.join(self.working_dir, 'node_modules', '.bin', 'eslint')
        command = [cmd, '--format', 'checkstyle']
        command += files
        return command
