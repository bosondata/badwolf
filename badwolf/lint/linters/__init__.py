# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import logging


logger = logging.getLogger(__name__)


class Linter(object):
    name = ''

    def __init__(self, working_dir, problems, options=None):
        self.working_dir = working_dir
        self.problems = problems
        self.options = options or {}

    def is_usable(self):
        """Whether this linter should be usable or not"""
        return True

    def match_file(self, filename):
        """Used to check if files can be handled by this linter,
        Often this will just file extension checks."""
        return True

    def lint_files(self, files):
        """Lint all matched files, should yield all problems found"""
        pass

    def execute(self, files):
        """Execute the linter against the files"""
        matched_files = [f for f in files if self.match_file(f)]
        if not matched_files:
            logger.info('No matched files found for linter %s', self.name)
            return

        logger.info('Running linter %s against %d files', self.name, len(matched_files))
        for problem in self.lint_files(matched_files):
            self.problems.add(problem)

    def __repr__(self):
        return '<{} linter>'.format(self.name)

    def _relativize_filename(self, filename):
        if not os.path.isabs(filename):
            return filename

        old = self.working_dir
        if not old.endswith(os.path.sep):
            old = '{}{}'.format(old, os.path.sep)
        return filename.replace(old, '')
