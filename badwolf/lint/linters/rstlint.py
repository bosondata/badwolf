# -*- coding: utf-8 -*-
import os
import logging

import restructuredtext_lint as rstlinter

from badwolf.lint import Problem
from badwolf.lint.linters import Linter


logger = logging.getLogger(__name__)


class RestructuredTextLinter(Linter):
    name = 'rstlint'
    default_pattern = '*.rst'

    def lint_files(self, files):
        cwd = os.getcwd()
        os.chdir(self.working_dir)
        for path in files:
            errors = rstlinter.lint_file(path, 'utf-8')
            for error in errors:
                msg = '{}: {}'.format(error.type, error.message)
                yield Problem(
                    error.source,
                    error.line,
                    msg,
                    self.name
                )
        os.chdir(cwd)
