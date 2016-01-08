# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging

from flask import Blueprint, request

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
    commit_hash = latest_change['commits'][0]['hash']
    commit_message = latest_change['commits'][0]['message']
    if 'ci skip' in commit_message.lower():
        logger.info('ci skip found, ignore tests.')
        return

    if not latest_change['new'] or latest_change['new']['type'] != 'branch':
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
    if 'ci skip' in title:
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
