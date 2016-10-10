# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json
import logging

from flask import Blueprint, request, current_app, url_for

from badwolf.context import Context
from badwolf.tasks import start_pipeline
from badwolf.extensions import bitbucket
from badwolf.bitbucket import BitbucketAPIError, PullRequest, BuildStatus


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
    logger.debug(
        'Incoming Bitbucket webhook request, event key: %s, payload: %s',
        event_key,
        json.dumps(payload, ensure_ascii=False)
    )
    if not payload:
        return ''

    handler = _EVENT_HANDLERS.get(event_key)
    if handler:
        return handler(payload) or ''
    return ''


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
    if not latest_change['commits']:
        logger.warning('Can not find any commits')
        return

    commit_hash = latest_change['commits'][0]['hash']
    commit_message = latest_change['commits'][0]['message']
    if 'ci skip' in commit_message.lower():
        logger.info('ci skip found, ignore tests.')
        return

    rebuild = False
    if 'ci rebuild' in commit_message.lower():
        rebuild = True

    repo_name = repo['full_name']

    context = Context(
        repo_name,
        payload['actor'],
        'commit',
        commit_message,
        {
            'repository': {'full_name': repo_name},
            'branch': {'name': latest_change['new']['name']},
            'commit': {'hash': commit_hash},
        },
        rebuild=rebuild,
    )
    start_pipeline.delay(context)


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
    description = pr['description'] or ''
    if 'ci skip' in title or 'ci skip' in description:
        logger.info('ci skip found, ignore tests.')
        return

    if pr['state'] != 'OPEN':
        logger.info('Pull request state is not OPEN, ignore tests.')
        return

    rebuild = False
    if 'ci rebuild' in title.lower() or 'ci rebuild' in description.lower():
        rebuild = True

    source = pr['source']
    target = pr['destination']

    context = Context(
        repo['full_name'],
        payload['actor'],
        'pullrequest',
        title,
        source,
        target,
        rebuild=rebuild,
        pr_id=pr['id']
    )
    start_pipeline.delay(context)


@register_event_handler('pullrequest:approved')
def handle_pull_request_approved(payload):
    if not current_app.config['AUTO_MERGE_ENABLED']:
        return

    repo = payload['repository']
    pr = payload['pullrequest']
    pr_id = pr['id']
    title = pr['title']
    description = pr['description'] or ''
    if 'merge skip' in title.lower() or 'merge skip' in description.lower():
        logger.info('merge skip found, ignore auto merge.')
        return

    pull_request = PullRequest(
        bitbucket,
        repo['full_name']
    )
    try:
        pr_info = pull_request.get(pr_id)
    except BitbucketAPIError:
        logger.exception('Error calling Bitbucket API')
        return

    if pr_info['state'] != 'OPEN':
        return

    participants = pr_info['participants']
    approved_users = [u for u in participants if u['approved']]
    if len(approved_users) < current_app.config['AUTO_MERGE_APPROVAL_COUNT']:
        return

    commit_hash = pr_info['source']['commit']['hash']

    build_status = BuildStatus(
        bitbucket,
        pr_info['source']['repository']['full_name'],
        commit_hash,
        'badwolf/test',
        url_for('log.build_log', sha=commit_hash, _external=True)
    )
    message = 'Auto merge pull request #{}: {}'.format(pr_id, title)
    try:
        status = build_status.get()
        if status['state'] == 'SUCCESSFUL':
            pull_request.merge(pr_id, message)
    except BitbucketAPIError:
        logger.exception('Error calling Bitbucket API')


@register_event_handler('repo:commit_comment_created')
def handle_repo_commit_comment(payload):
    comment = payload['comment']
    comment_content = comment['content']['raw']

    retry = 'ci retry' in comment_content
    rebuild = 'ci rebuild' in comment_content
    nocache = 'no cache' in comment_content
    if not (retry or rebuild):
        return

    commit_hash = payload['commit']['hash']
    repo = payload['repository']
    repo_name = repo['full_name']

    context = Context(
        repo_name,
        payload['actor'],
        'commit',
        payload['commit']['message'],
        {
            'repository': {'full_name': repo_name},
            'branch': {'name': 'master'},
            'commit': {'hash': commit_hash},
        },
        rebuild=rebuild,
        nocache=nocache,
        clone_depth=0,  # Force a full git clone
    )
    start_pipeline.delay(context)


@register_event_handler('pullrequest:comment_created')
def handle_pull_request_comment(payload):
    comment = payload['comment']
    comment_content = comment['content']['raw'].lower()
    retry = 'ci retry' in comment_content
    rebuild = 'ci rebuild' in comment_content
    cleanup_lint = 'cleanup lint' in comment_content
    nocache = 'no cache' in comment_content
    if not (retry or rebuild or cleanup_lint):
        return

    repo = payload['repository']
    pr = payload['pullrequest']
    title = pr['title']

    if pr['state'] != 'OPEN':
        logger.info('Pull request state is not OPEN, ignore tests.')
        return

    source = pr['source']
    target = pr['destination']

    context = Context(
        repo['full_name'],
        payload['actor'],
        'pullrequest',
        title,
        source,
        target,
        rebuild=rebuild,
        pr_id=pr['id'],
        cleanup_lint=cleanup_lint,
        nocache=nocache
    )
    start_pipeline.delay(context)
