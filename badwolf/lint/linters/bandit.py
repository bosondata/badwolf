# -*- coding: utf-8 -*-
import os
import io
import csv
import logging

from badwolf.utils import run_command
from badwolf.lint import Problem
from badwolf.lint.linters import Linter
from badwolf.lint.utils import in_path


logger = logging.getLogger(__name__)


class BanditLinter(Linter):
    name = 'bandit'
    default_pattern = '*.py'

    def is_usable(self):
        return in_path('bandit')

    def lint_files(self, files):
        command = ['bandit', '-f', 'csv']
        ini_conf = os.path.join(self.working_dir, '.bandit')
        if os.path.exists(ini_conf):
            command.extend(['--ini', '.bandit'])
        command += files
        _, output = run_command(command, cwd=self.working_dir)
        if not output:
            raise StopIteration()

        reader = csv.DictReader(io.StringIO(output))
        for row in reader:
            msg = '[{}] {}'.format(row['test_name'], row['issue_text'])
            is_error = row['issue_severity'] != 'LOW'
            yield Problem(
                row['filename'],
                int(row['line_number']),
                msg,
                self.name,
                is_error
            )
