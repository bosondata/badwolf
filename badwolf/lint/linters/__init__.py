# -*- coding: utf-8 -*-
import os
import re
import sys
import logging
import fnmatch


logger = logging.getLogger(__name__)


class Linter(object):
    name = ''
    default_pattern = ''

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
        pattern = self.options.get('pattern') or self.default_pattern
        if not pattern:
            return True

        globs = pattern.split()
        for glob in globs:
            if fnmatch.fnmatch(filename, glob):
                # 先尝试 glob 匹配
                return True
        try:
            if re.match(pattern, filename, re.I):
                # 否则尝试正则表达式匹配
                return True
        except re.error:
            pass
        return False

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


class PythonLinter(Linter):
    default_pattern = '*.py'

    @property
    def python_name(self):
        current_python = '{}.{}'.format(sys.version_info.major, sys.version_info.minor)
        python_version = self.options.get('python_version', current_python)
        return 'python{}'.format(python_version)
