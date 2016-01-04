# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging

from flask import Blueprint, request

from badwolf.tasks import run_test


logger = logging.getLogger(__name__)
blueprint = Blueprint('webhook', __name__)

_EVENT_HANDLERS = {}


def register_event_handler(event_key):
    def register(func):
        _EVENT_HANDLERS[event_key] = func
        return func
    return register


@blueprint.route('/webhook/push', methods=['POST'])
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


@register_event_handler('repo:push')
def handle_repo_push(payload):
    changes = payload['push']['changes']
    if not changes:
        return

    repo = payload['repository']
    scm = repo['scm']
    if scm.lower() != 'git':
        return

    commit_hash = changes[0]['commits'][0]['hash']
    repo_name = repo['full_name']
    git_clone_url = 'git@bitbucket.org:{}.git'.format(repo_name)
    run_test.delay(repo_name, git_clone_url, commit_hash, payload)
