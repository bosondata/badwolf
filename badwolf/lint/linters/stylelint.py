# -*- coding: utf-8 -*-
import os
import json

from badwolf.utils import run_command
from badwolf.lint import Problem
from badwolf.lint.linters import Linter
from badwolf.lint.utils import in_path, npm_exists


class StyleLinter(Linter):
    name = 'stylelint'
    default_pattern = '*.css *.scss *.less *.sss'

    def is_usable(self):
        return in_path('stylelint') or npm_exists('stylelint', self.working_dir)

    def match_file(self, filename):
        # 过滤掉压缩过的 CSS 文件
        if filename.lower().endswith('.min.css'):
            return False
        return super(StyleLinter, self).match_file(filename)

    def lint_files(self, files):
        command = self.create_command(files)
        _, output = run_command(command, cwd=self.working_dir)
        if not output:
            raise StopIteration()

        try:
            problems = json.loads(output)
        except ValueError:
            raise StopIteration()

        for source in problems:
            for problem in source['warnings']:
                yield Problem(
                    self._relativize_filename(source['source']),
                    problem['line'],
                    problem['text'],
                    self.name
                )

    def create_command(self, files):
        cmd = 'stylelint'
        if npm_exists('stylelint', self.working_dir):
            cmd = os.path.join(self.working_dir, 'node_modules', '.bin', 'stylelint')
        command = [cmd, '--no-color', '-f', 'json']
        command += files
        return command
