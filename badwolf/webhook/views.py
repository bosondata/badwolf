# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging

from flask import Blueprint, request, current_app

import badwolf.bitbucket as bitbucket
from badwolf.runner import TestContext
from badwolf.tasks import run_test


logger = logging.getLogger(__name__)
blueprint = Blueprint('webhook', __name__)

_EVENT_HANDLERS = {}


def register_event_handler(event_key):
    def register(func):
        _EVENT_HANDLERS[event_key] = func
        return func
    return register


@blueprint.route('/push', methods=['POST'])
def webhook_push():
    event_key = request.headers.get('X-Event-Key')
    if not event_key:
        return 'Bad request', 400

    payload = request.get_json(force=True)
    logger.info(
        'Incoming Bitbucket webhook request, event key: %s, payload: %s',
        event_key,
        payload
    )
    if not payload:
        return ''

    handler = _EVENT_HANDLERS.get(event_key)
    if handler:
        return handler(payload) or ''
    return ''


@blueprint.route('/run', methods=['POST'])
def run_test_at_commit():
    repo_name = request.form.get('repo')
    commit_hash = request.form.get('commit')
    if not repo_name:
        return 'Needs repository name', 400

    if '/' not in repo_name:
        repo_name = 'deepanalyzer/{}'.format(repo_name)

    if not commit_hash:
        return 'Needs commit hash', 400

    git_clone_url = 'git@bitbucket.org:{}.git'.format(repo_name)
    context = TestContext(
        repo_name,
        git_clone_url,
        {},
        'commit',
        'Forced rerun',
        {
            'branch': {'name': 'master'},
            'commit': {'hash': commit_hash},
        }
    )
    run_test.delay(context)
    return 'Success'


@register_event_handler('repo:push')
def handle_repo_push(payload):
    changes = payload['push']['changes']
    if not changes:
        return

    repo = payload['repository']
    scm = repo['scm']
    if scm.lower() != 'git':
        logger.info('Unsupported version system: %s', scm)
        return

    latest_change = changes[0]
    if not latest_change['new'] or latest_change['new']['type'] != 'branch':
        logger.info('Unsupported push type: %s', latest_change['new']['type'])
        return

    commit_hash = latest_change['commits'][0]['hash']
    commit_message = latest_change['commits'][0]['message']
    if 'ci skip' in commit_message.lower():
        logger.info('ci skip found, ignore tests.')
        return

    repo_name = repo['full_name']
    git_clone_url = 'git@bitbucket.org:{}.git'.format(repo_name)

    context = TestContext(
        repo_name,
        git_clone_url,
        payload['actor'],
        'commit',
        commit_message,
        {
            'branch': {'name': latest_change['new']['name']},
            'commit': {'hash': commit_hash},
        }
    )
    run_test.delay(context)


@register_event_handler('pullrequest:created')
@register_event_handler('pullrequest:updated')
def handle_pull_request(payload):
    repo = payload['repository']
    scm = repo['scm']
    if scm.lower() != 'git':
        logger.info('Unsupported version system: %s', scm)
        return

    pr = payload['pullrequest']
    title = pr['title']
    description = pr['description']
    if 'ci skip' in title or 'ci skip' in description:
        logger.info('ci skip found, ignore tests.')
        return

    if pr['state'] != 'OPEN':
        logger.info('Pull request state is not OPEN, ignore tests.')
        return

    source = pr['source']
    target = pr['destination']

    context = TestContext(
        repo['full_name'],
        'git@bitbucket.org:{}.git'.format(repo['full_name']),
        payload['actor'],
        'pullrequest',
        title,
        source,
        target
    )
    run_test.delay(context)


@register_event_handler('pullrequest:approved')
def handle_pull_request_approved(payload):
    if not current_app.config['AUTO_MERGE_ENABLED']:
        return

    repo = payload['repository']
    pr = payload['pullrequest']
    pr_id = pr['id']
    title = pr['title']
    description = pr['description']
    if 'merge skip' in title or 'merge skip' in description:
        logger.info('merge skip found, ignore auto merge.')
        return

    bitbucket_client = bitbucket.Bitbucket(bitbucket.BasicAuthDispatcher(
        current_app.config['BITBUCKET_USERNAME'],
        current_app.config['BITBUCKET_PASSWORD']
    ))
    pull_request = bitbucket.PullRequest(
        bitbucket_client,
        repo['full_name']
    )
    try:
        pr_info = pull_request.get(pr_id)
    except bitbucket.BitbucketAPIError:
        logger.exception('Error calling Bitbucket API')
        return

    if pr_info['state'] != 'OPEN':
        return

    participants = pr_info['participants']
    approved_users = [u for u in participants if u['approved']]
    if len(approved_users) < current_app.config['AUTO_MERGE_APPROVAL_COUNT']:
        return

    build_status = bitbucket.BuildStatus(
        bitbucket_client,
        repo['full_name'],
        pr_info['source']['commit']['hash'],
        'BADWOLF',
        'http://badwolf.bosondata.net'
    )
    message = 'Auto merge pull request #{}: {}'.format(pr_id, title)
    try:
        status = build_status.get()
        if status['state'] == 'SUCCESSFUL':
            pull_request.merge(pr_id, message)
    except bitbucket.BitbucketAPIError:
        logger.exception('Error calling Bitbucket API')


@register_event_handler('repo:commit_comment_created')
def handle_repo_commit_comment(payload):
    comment = payload['comment']
    comment_content = comment['content']['raw']
    if 'ci retry' not in comment_content:
        return

    commit_hash = payload['commit']['hash']
    repo = payload['repository']
    repo_name = repo['full_name']
    git_clone_url = 'git@bitbucket.org:{}.git'.format(repo_name)

    context = TestContext(
        repo_name,
        git_clone_url,
        payload['actor'],
        'commit',
        payload['commit']['message'],
        {
            'branch': {'name': 'master'},
            'commit': {'hash': commit_hash},
        }
    )
    run_test.delay(context)


@register_event_handler('pullrequest:comment_created')
def handle_pull_request_comment(payload):
    comment = payload['comment']
    comment_content = comment['content']['raw']
    if 'ci retry' not in comment_content:
        return

    repo = payload['repository']
    pr = payload['pullrequest']
    title = pr['title']
    description = pr['description']
    if 'ci skip' in title or 'ci skip' in description:
        logger.info('ci skip found, ignore tests.')
        return

    if pr['state'] != 'OPEN':
        logger.info('Pull request state is not OPEN, ignore tests.')
        return

    source = pr['source']
    target = pr['destination']

    context = TestContext(
        repo['full_name'],
        'git@bitbucket.org:{}.git'.format(repo['full_name']),
        payload['actor'],
        'pullrequest',
        title,
        source,
        target
    )
    run_test.delay(context)
