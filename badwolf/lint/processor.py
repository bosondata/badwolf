# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging

from flask import url_for
from unidiff import UnidiffParseError

from badwolf.extensions import bitbucket
from badwolf.bitbucket import PullRequest, BitbucketAPIError, BuildStatus
from badwolf.lint import Problems
from badwolf.lint.linters.eslint import ESLinter
from badwolf.lint.linters.flake8 import Flake8Linter
from badwolf.lint.linters.jscs import JSCSLinter
from badwolf.lint.linters.pep8 import PEP8Linter
from badwolf.lint.linters.csslint import CSSLinter
from badwolf.lint.linters.shellcheck import ShellCheckLinter
from badwolf.lint.linters.jsonlint import JSONLinter
from badwolf.lint.linters.yamllint import YAMLLinter
from badwolf.lint.linters.bandit import BanditLinter
from badwolf.lint.linters.rstlint import RestructuredTextLinter
from badwolf.lint.linters.pylint import PylintLinter
from badwolf.lint.linters.sasslint import SassLinter
from badwolf.lint.linters.stylelint import StyleLinter


logger = logging.getLogger(__name__)


class LintProcessor(object):
    LINTERS = {
        'eslint': ESLinter,
        'flake8': Flake8Linter,
        'jscs': JSCSLinter,
        'pep8': PEP8Linter,
        'csslint': CSSLinter,
        'shellcheck': ShellCheckLinter,
        'jsonlint': JSONLinter,
        'yamllint': YAMLLinter,
        'bandit': BanditLinter,
        'rstlint': RestructuredTextLinter,
        'pylint': PylintLinter,
        'sasslint': SassLinter,
        'stylelint': StyleLinter,
    }

    def __init__(self, context, spec, working_dir=None):
        self.context = context
        self.spec = spec
        self.working_dir = working_dir or context.clone_path
        self.problems = Problems()
        self.pr = PullRequest(bitbucket, context.repository)
        commit_hash = context.source['commit']['hash']
        self.build_status = BuildStatus(
            bitbucket,
            context.source['repository']['full_name'],
            commit_hash,
            'badwolf/lint',
            url_for('log.lint_log', sha=commit_hash, _external=True)
        )

    def load_changes(self):
        try:
            changes = self.pr.diff(self.context.pr_id)
        except (BitbucketAPIError, UnidiffParseError):
            logger.exception('Error getting pull request diff from API')
            return

        self.problems.set_changes(changes)
        return changes

    def process(self):
        if not self.spec.linters:
            logger.info('No linters configured, ignore lint.')
            return

        logger.info('Running code linting')
        patch = self.load_changes()
        if not patch:
            logger.info('Load changes failed, ignore lint.')
            return

        lint_files = patch.added_files + patch.modified_files
        if not lint_files:
            logger.info('No changed files found, ignore lint')
            return

        self.update_build_status('INPROGRESS', 'Lint in progress')
        files = [f.path for f in lint_files]
        self._execute_linters(files)
        logger.info('%d problems found before limit to changes', len(self.problems))

        self.problems.limit_to_changes()

        has_error = any(p for p in self.problems if p.is_error)
        if len(self.problems):
            description = 'Found {} code issues'.format(len(self.problems))
        else:
            description = 'No code issues found'
            logger.info('No problems found when linting codes')

        # Report error or cleanup lint
        self._report()

        if has_error:
            self.update_build_status('FAILED', description)
        else:
            self.update_build_status('SUCCESSFUL', description)

    def _execute_linters(self, files):
        for linter_option in self.spec.linters:
            name = linter_option.name
            linter_cls = self.LINTERS.get(name)
            if not linter_cls:
                logger.info('Linter %s not found, ignore.', name)
                continue

            linter = linter_cls(self.working_dir, self.problems, linter_option)
            if not linter.is_usable():
                logger.info('Linter %s is not usable, ignore.', name)
                continue

            logger.info('Running %s code linter', name)
            linter.execute(files)

    def _report(self):
        try:
            comments = self.pr.all_comments(self.context.pr_id)
        except BitbucketAPIError:
            logger.exception('Error fetching all comments for pull request')
            comments = []

        hash_set = set()
        for comment in comments:
            inline = comment.get('inline')
            if not inline:
                continue

            raw = comment['content']['raw']
            if self.context.cleanup_lint and raw.startswith(':broken_heart:'):
                # Delete comment
                try:
                    self.pr.delete_comment(self.context.pr_id, comment['id'])
                except BitbucketAPIError:
                    logger.exception('Error deleting pull request comment')
            else:
                filename = inline['path']
                line_to = inline['to']
                hash_set.add(hash('{}{}{}'.format(filename, line_to, raw)))

        if len(self.problems) == 0:
            return

        revision_before = self.context.target['commit']['hash']
        revision_after = self.context.source['commit']['hash']
        problem_count = 0
        for problem in self.problems:
            content = ':broken_heart: **{}**: {}'.format(problem.linter, problem.message)
            comment_hash = hash('{}{}{}'.format(
                problem.filename,
                problem.line,
                content,
            ))
            if comment_hash in hash_set:
                continue

            try:
                self.pr.comment(
                    self.context.pr_id,
                    content,
                    line_to=problem.line,
                    filename=problem.filename,
                    anchor=revision_after,
                    dest_rev=revision_before,
                )
            except BitbucketAPIError:
                logger.exception('Error creating inline comment for pull request')
            else:
                problem_count += 1

        logger.info(
            'Code lint result: %d problems found, %d submited',
            len(self.problems),
            problem_count
        )
        return problem_count

    def update_build_status(self, state, description=None):
        try:
            self.build_status.update(state, description=description)
        except BitbucketAPIError:
            logger.exception('Error calling Bitbucket API')
