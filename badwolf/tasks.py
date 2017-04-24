# -*- coding: utf-8 -*-
import time
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
try:
    import re2 as re
except ImportError:
    import re

from badwolf.extensions import sentry, bitbucket
from badwolf.bitbucket import PullRequest, BuildStatus, BitbucketAPIError
from badwolf.pipeline import Pipeline


logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=5 * multiprocessing.cpu_count())
_MERGE_COMMIT_RE = re.compile(r'[mM]erged?.*?pull request #(\d+)')


def _run_task(_task_func, *args, **kwargs):
    from badwolf.wsgi import app

    logger.debug('Running task func %r', _task_func.__name__)
    try:
        with app.app_context():
            _task_func(*args, **kwargs)
    except Exception:
        logger.exception('Error running task func: %s', _task_func)
        sentry.captureException()


def async_task(f):
    def delay(*args, **kwargs):
        # return _run_task(f, *args, **kwargs)
        return executor.submit(_run_task, f, *args, **kwargs)
    f.delay = delay
    return f


@async_task
def start_pipeline(context):
    Pipeline(context).start()


@async_task
def check_pr_mergeable(context):
    repo = bitbucket.get('2.0/repositories/{}'.format(context.repository))
    main_branch = repo['mainbranch']['name']
    current_branch = context.source['branch']['name']
    if current_branch != 'master' and current_branch != main_branch:
        logger.info('Current branch %s is not main branch %s', current_branch, main_branch)
        return

    time.sleep(5)  # wait for Bitbucket merge process ready
    pr = PullRequest(bitbucket, context.repository)
    open_prs = pr.list(state='OPEN')['values']
    if not open_prs:
        logger.debug('No opening pull requests found')
        return

    for open_pr in open_prs:
        check_mergeable(context, pr, open_pr)


def check_mergeable(context, pr_api, pr_info):
    pr_id = pr_info['id']
    merge_status = BuildStatus(
        bitbucket,
        pr_info['source']['repository']['full_name'],
        pr_info['source']['commit']['hash'],
        'badwolf/pr/mergeable',
        'https://bitbucket.org/{}/pull-requests/{}'.format(context.repository, pr_id)
    )
    notify = False
    status = {'state': None}
    try:
        status = merge_status.get()
    except BitbucketAPIError as e:
        if e.code != 404:
            raise
        notify = True
    else:
        if status['state'] == 'SUCCESSFUL':
            notify = True

    diff = pr_api.diff(pr_id, raw=True)
    if '+<<<<<<< destination:' not in diff:
        # Mergeable
        logger.info('Pull request #%s is mergeable', pr_id)
        if status['state'] != 'SUCCESSFUL':
            merge_status.update('SUCCESSFUL', 'Pull request is mergeable')
        return

    # Unmergeable
    if not notify:
        return

    logger.info('Pull request #%s is not mergeable', pr_id)
    merge_status.update('FAILED', 'Pull request is not mergeable')
    comment = (':umbrella: The latest upstream changes(presumably {}) made this pull request unmergeable. '
               'Please resolve the merge conflicts.')
    matches = _MERGE_COMMIT_RE.search(context.message)
    if matches:
        comment = comment.format('pull request #{}'.format(matches.group(1)))
    else:
        comment = comment.format('commit {}'.format(context.source['commit']['hash']))
    pr_api.comment(pr_id, comment)
