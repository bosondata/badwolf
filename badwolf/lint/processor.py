# -*- coding: utf-8 -*-
import time
import logging

from flask import url_for
from unidiff import UnidiffParseError

from badwolf.extensions import bitbucket, sentry
from badwolf.bitbucket import PullRequest, BitbucketAPIError, BuildStatus
from badwolf.lint import Problems
from badwolf.lint.linters.eslint import ESLinter
from badwolf.lint.linters.flake8 import Flake8Linter
from badwolf.lint.linters.pycodestyle import PyCodeStyleLinter
from badwolf.lint.linters.csslint import CSSLinter
from badwolf.lint.linters.shellcheck import ShellCheckLinter
from badwolf.lint.linters.jsonlint import JSONLinter
from badwolf.lint.linters.yamllint import YAMLLinter
from badwolf.lint.linters.bandit import BanditLinter
from badwolf.lint.linters.rstlint import RestructuredTextLinter
from badwolf.lint.linters.pylint import PylintLinter
from badwolf.lint.linters.sasslint import SassLinter
from badwolf.lint.linters.stylelint import StyleLinter
from badwolf.lint.linters.mypy import MypyLinter


logger = logging.getLogger(__name__)


class LintProcessor(object):
    LINTERS = {
        'eslint': ESLinter,
        'flake8': Flake8Linter,
        'pep8': PyCodeStyleLinter,
        'pycodestyle': PyCodeStyleLinter,
        'csslint': CSSLinter,
        'shellcheck': ShellCheckLinter,
        'jsonlint': JSONLinter,
        'yamllint': YAMLLinter,
        'bandit': BanditLinter,
        'rstlint': RestructuredTextLinter,
        'pylint': PylintLinter,
        'sasslint': SassLinter,
        'stylelint': StyleLinter,
        'mypy': MypyLinter,
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
            url_for('log.lint_log', sha=commit_hash, ts=int(time.time()), _external=True)
        )

    def load_changes(self):
        try:
            changes = self.pr.diff(self.context.pr_id)
        except (BitbucketAPIError, UnidiffParseError):
            logger.exception('Error getting pull request diff from API')
            sentry.captureException()
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

        total_problems = len(self.problems)
        self.problems.limit_to_changes()
        in_diff_problems = len(self.problems)

        # Report error and cleanup outdated lint comments
        submitted_problems, fixed_problems = self._report()
        if total_problems > 0:
            if in_diff_problems == total_problems:
                description = 'Found {} new issues'.format(total_problems)
            else:
                description = 'Found {} issues'.format(total_problems)
                description += ', {} issues in diff'.format(in_diff_problems)
                if submitted_problems > 0:
                    description += ', {} new issues'.format(submitted_problems)
            if fixed_problems > 0:
                description += ' {} issues fixed'.format(fixed_problems)
        else:
            description = 'No code issues found'

        has_error = any(p for p in self.problems if p.is_error)
        if has_error:
            logger.info('Lint failed: %s', description)
            self.update_build_status('FAILED', description)
        else:
            logger.info('Lint successful: %s', description)
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
            sentry.captureException()
            comments = []

        existing_comments_ids = {}
        for comment in comments:
            inline = comment.get('inline')
            if not inline:
                continue

            raw = comment['content']['raw']
            if not raw.startswith(':broken_heart: **'):
                continue
            filename = inline['path']
            line = inline['to'] or inline['from']
            if line is None:
                continue
            existing_comments_ids[(filename, line, raw)] = comment['id']

        if len(self.problems) == 0:
            return 0, 0

        revision_before = self.context.target['commit']['hash']
        revision_after = self.context.source['commit']['hash']
        lint_comments = set()
        problem_count = 0
        for problem in self.problems:
            content = ':broken_heart: **{}**: {}'.format(problem.linter, problem.message)
            comment_tuple = (problem.filename, problem.line, content)
            lint_comments.add(comment_tuple)
            if comment_tuple in existing_comments_ids:
                continue

            comment_kwargs = {
                'filename': problem.filename,
                'anchor': revision_after,
                'dest_rev': revision_before,
            }
            if problem.has_line_change:
                comment_kwargs['line_to'] = problem.line
            else:
                comment_kwargs['line_from'] = problem.line
            try:
                self.pr.comment(
                    self.context.pr_id,
                    content,
                    **comment_kwargs
                )
            except BitbucketAPIError:
                logger.exception('Error creating inline comment for pull request')
                sentry.captureException()
            else:
                problem_count += 1

        logger.info(
            'Code lint result: %d problems found, %d submitted',
            len(self.problems),
            problem_count
        )

        outdated_cleaned = 0
        outdated_comments = set(existing_comments_ids.keys()) - lint_comments
        logger.info('%d outdated lint comments found', len(outdated_comments))
        for comment in outdated_comments:
            # Delete comment
            try:
                self.pr.delete_comment(self.context.pr_id, existing_comments_ids[comment])
                outdated_cleaned += 1
            except BitbucketAPIError:
                logger.exception('Error deleting pull request comment')
                sentry.captureException()
        return problem_count, outdated_cleaned

    def update_build_status(self, state, description=None):
        try:
            self.build_status.update(state, description=description)
        except BitbucketAPIError:
            logger.exception('Error calling Bitbucket API')
            sentry.captureException()
