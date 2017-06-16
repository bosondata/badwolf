# -*- coding: utf-8 -*-
import json
import logging

from docker import DockerClient
from flask import Blueprint, request, current_app, url_for, jsonify

from badwolf.context import Context
from badwolf.tasks import start_pipeline, check_pr_mergeable
from badwolf.extensions import bitbucket, sentry
from badwolf.bitbucket import BitbucketAPIError, PullRequest, BuildStatus, Hooks


logger = logging.getLogger(__name__)
blueprint = Blueprint('webhook', __name__)

_EVENT_HANDLERS = {}
_RUNNING_PIPELINES = {}


def register_event_handler(event_key):
    def register(func):
        _EVENT_HANDLERS[event_key] = func
        return func
    return register


def _cancel_outdated_pipelines(context):
    from docker.errors import NotFound
    docker = DockerClient(
        base_url=current_app.config['DOCKER_HOST'],
        timeout=current_app.config['DOCKER_API_TIMEOUT'],
        version='auto',
    )
    containers = docker.containers.list(filters=dict(
        status='running',
        label='repo={}'.format(context.repository),
    ))
    if not containers:
        return

    for container in containers:
        labels = container.labels
        if context.type == 'tag':
            continue
        if context.pr_id and labels.get('pull_request') != context.pr_id:
            continue
        if context.type == 'branch' and labels.get('branch') != context.source['branch']['name']:
            continue

        task_id = labels.get('task_id')
        if not task_id:
            continue

        future = _RUNNING_PIPELINES.get(task_id)
        if not future or future.cancelled():
            continue

        logger.info('Cancelling outdated pipeline for %s with task_id %s', context.repository, task_id)
        # cancel the future and remove the container
        try:
            container.remove(force=True)
        except NotFound:
            pass
        future.cancel()


@blueprint.route('/register/<user>/<repo>', methods=['POST'])
def register_webhook(user, repo):
    full_name = '{}/{}'.format(user, repo)
    webhook_url = url_for('.webhook_push', _external=True)
    hooks = Hooks(bitbucket, full_name)
    existing_hooks = hooks.list()
    existing_urls = [hook['url'] for hook in existing_hooks['values']]
    if webhook_url in existing_urls:
        return jsonify({'message': 'already registered'})

    hooks.add('badwolf', webhook_url, events=(
        'repo:push',
        'repo:commit_comment_created',
        'pullrequest:created',
        'pullrequest:updated',
        'pullrequest:approved',
        'pullrequest:comment_created',
    ))
    return jsonify({'message': 'success'}), 201


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

    for change in changes:
        if not change['new']:
            logger.info('No new changes found')
            continue

        repo_name = repo['full_name']
        push_type = change['new']['type']
        rebuild = False
        if push_type == 'tag':
            commit_hash = change['new']['target']['hash']
            commit_message = change['new']['target']['message']
        elif push_type == 'branch':
            if not change['commits']:
                logger.warning('Can not find any commits')
                continue
            commit_hash = change['commits'][0]['hash']
            commit_message = change['commits'][0]['message']
            if 'ci skip' in commit_message.lower():
                logger.info('ci skip found, ignore tests.')
                continue
            if 'ci rebuild' in commit_message.lower():
                rebuild = True
        else:
            logger.error('Unsupported push type: %s', push_type)
            continue

        source = {
            'repository': {'full_name': repo_name},
            'branch': {'name': change['new']['name']},
            'commit': {'hash': commit_hash}
        }
        context = Context(
            repo_name,
            payload['actor'],
            push_type,
            commit_message,
            source,
            rebuild=rebuild,
        )
        _cancel_outdated_pipelines(context)
        future = start_pipeline.delay(context)
        future.add_done_callback(lambda fut: _RUNNING_PIPELINES.pop(context.task_id, None))
        _RUNNING_PIPELINES[context.task_id] = future
        if push_type == 'branch':
            check_pr_mergeable.delay(context)


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
    _cancel_outdated_pipelines(context)
    future = start_pipeline.delay(context)
    future.add_done_callback(lambda fut: _RUNNING_PIPELINES.pop(context.task_id, None))
    _RUNNING_PIPELINES[context.task_id] = future


@register_event_handler('pullrequest:approved')
def handle_pull_request_approved(payload):
    if not current_app.config['AUTO_MERGE_ENABLED']:
        return

    repo = payload['repository']
    pr = payload['pullrequest']
    pr_id = pr['id']
    title = pr['title'].lower()
    description = (pr['description'] or '').lower()

    for keyword in ('wip', 'merge skip', 'working in progress'):
        if keyword in title or keyword in description:
            logger.info('%s found, ignore auto merge.', keyword)
            return

    pull_request = PullRequest(
        bitbucket,
        repo['full_name']
    )
    try:
        pr_info = pull_request.get(pr_id)
    except BitbucketAPIError as exc:
        logger.exception('Error calling Bitbucket API')
        if exc.code != 404:
            sentry.captureException()
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
    message = 'Auto merge pull request #{}: {}'.format(pr_id, pr['title'])
    if description:
        message += '\n\n{}'.format(pr['description'])
    try:
        status = build_status.get()
        if status['state'] == 'SUCCESSFUL':
            pull_request.merge(pr_id, message)
    except BitbucketAPIError:
        logger.exception('Error calling Bitbucket API')
        sentry.captureException()


@register_event_handler('repo:commit_comment_created')
def handle_repo_commit_comment(payload):
    comment = payload['comment']
    comment_content = comment['content']['raw'].lower()

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
        'commit',  # set to commit for ci retry on commit
        payload['commit']['message'],
        {
            'repository': {'full_name': repo_name},
            'branch': {'name': 'master'},
            'commit': {'hash': commit_hash},
        },
        rebuild=rebuild,
        nocache=nocache,
    )
    start_pipeline.delay(context)


@register_event_handler('pullrequest:comment_created')
def handle_pull_request_comment(payload):
    comment = payload['comment']
    comment_content = comment['content']['raw'].lower()
    retry = 'ci retry' in comment_content
    rebuild = 'ci rebuild' in comment_content
    nocache = 'no cache' in comment_content
    if not (retry or rebuild):
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
        nocache=nocache
    )
    _cancel_outdated_pipelines(context)
    future = start_pipeline.delay(context)
    future.add_done_callback(lambda fut: _RUNNING_PIPELINES.pop(context.task_id, None))
    _RUNNING_PIPELINES[context.task_id] = future
