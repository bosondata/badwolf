# -*- coding: utf-8 -*-
import time
import logging

import requests
from flask import url_for

from badwolf.extensions import bitbucket, sentry
from badwolf.utils import run_command
from badwolf.bitbucket import BitbucketAPIError, BuildStatus
from badwolf.deploy.providers.script import ScriptProvider
from badwolf.deploy.providers.pypi import PypiProvider


logger = logging.getLogger(__name__)


class Deployer(object):
    PROVIDERS = {
        'script': ScriptProvider,
        'pypi': PypiProvider,
    }

    def __init__(self, context, spec, providers, working_dir=None):
        self.context = context
        self.spec = spec
        self.working_dir = working_dir or context.clone_path
        self.providers = providers

    def deploy(self):
        if not self.providers:
            logger.info('No deploy provider active')
            return

        commit_hash = self.context.source['commit']['hash']
        run_after_deploy = False
        notification = self.spec.notification
        slack_webhook = notification.slack_webhook

        for provider_config in self.providers:
            provider_name = provider_config.provider
            provider_class = self.PROVIDERS.get(provider_name)
            if not provider_class:
                logger.warning('Provider %s not found', provider_name)
                continue

            provider = provider_class(self.working_dir, provider_config)
            if not provider.is_usable():
                logger.warning('Provider %s is not usable', provider_name)
                continue

            build_status = BuildStatus(
                bitbucket,
                self.context.source['repository']['full_name'],
                commit_hash,
                'badwolf/deploy/{}'.format(provider_name),
                url_for('log.build_log', sha=commit_hash, task_id=self.context.task_id, _external=True)
            )
            self._update_build_status(build_status, 'INPROGRESS', '{} deploy in progress'.format(provider_name))
            succeed, output = provider.deploy()
            logger.info('Provider %s deploy %s,  output: \n%s',
                        provider_name, 'succeed' if succeed else 'failed', output)

            state = 'SUCCESSFUL' if succeed else 'FAILED'
            self._update_build_status(build_status, state, '{} deploy {}'.format(provider_name, state.lower()))
            if succeed:
                run_after_deploy = True
                if slack_webhook and slack_webhook.on_success == 'always':
                    trigger_slack_webhook(slack_webhook.webhooks, self.context, provider, True)
            else:
                if slack_webhook and slack_webhook.on_failure == 'always':
                    trigger_slack_webhook(slack_webhook.webhooks, self.context, provider, False)

        # after deploy
        if not run_after_deploy or not self.spec.after_deploy:
            return

        for script in self.spec.after_deploy:
            exit_code, output = run_command(script, shell=True)
            logger.info('After deploy command `%s` exit code: %s, output: \n %s', script, exit_code, output)

    def _update_build_status(self, build_status, state, description=None):
        try:
            build_status.update(state, description=description)
        except BitbucketAPIError:
            logger.exception('Error calling Bitbucket API')
            sentry.captureException()


def trigger_slack_webhook(webhooks, context, provider, succeed):
    actor = context.actor
    if succeed:
        title = '{} deploy succeed'.format(provider.name)
        color = 'good'
    else:
        title = '{} deploy failed'.format(provider.name)
        color = 'warning'
    fields = []
    fields.append({
        'title': 'Repository',
        'value': '<https://bitbucket.org/{repo}|{repo}>'.format(repo=context.repository),
        'short': True,
    })
    if context.type == 'tag':
        fields.append({
            'title': 'Tag',
            'value': '<https://bitbucket.org/{repo}/commits/tag/{tag}|{tag}>'.format(
                repo=context.repository,
                tag=context.source['branch']['name']
            ),
            'short': True,
        })
    else:
        fields.append({
            'title': 'Branch',
            'value': '<https://bitbucket.org/{repo}/src?at={branch}|{branch}>'.format(
                repo=context.repository,
                branch=context.source['branch']['name']
            ),
            'short': True,
        })
    if context.type in {'branch', 'tag'}:
        fields.append({
            'title': 'Commit',
            'value': '<https://bitbucket.org/{repo}/commits/{sha}|{sha}>'.format(
                repo=context.repository,
                sha=context.source['commit']['hash'],
            ),
            'short': False
        })
    attachment = {
        'fallback': title,
        'title': title,
        'color': color,
        'fields': fields,
        'footer': context.repo_name,
        'ts': int(time.time()),
        'author_name': actor['display_name'],
        'author_link': actor['links']['html']['href'],
        'author_icon': actor['links']['avatar']['href'],
    }
    if context.type in {'branch', 'tag'}:
        attachment['text'] = context.message
    payload = {'attachments': [attachment]}
    session = requests.Session()
    for webhook in webhooks:
        logger.info('Triggering Slack webhook %s', webhook)
        res = session.post(webhook, json=payload, timeout=10)
        try:
            res.raise_for_status()
        except requests.RequestException:
            logger.exception('Error triggering Slack webhook %s', webhook)
            sentry.captureException()
