# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import time
import logging
import smtplib

import requests

from badwolf.extensions import mail, sentry


logger = logging.getLogger(__name__)
session = requests.Session()


def send_mail(recipients, subject, html):
    logger.info('Sending email to %s', recipients)
    try:
        mail.send_message(
            subject=subject,
            recipients=recipients,
            html=html,
        )
    except smtplib.SMTPException:
        logger.exception('Error sending email to %s', recipients)
        sentry.captureException()


def trigger_slack_webhook(webhooks, context):
    if context['exit_code'] == 0:
        color = 'good'
        title = ':sparkles: <{}|Test succeed for repository {}>'.format(
            context['build_log_url'],
            context['context'].repository,
        )
    else:
        color = 'warning'
        title = ':broken_heart: <{}|Test failed for repository {}>'.format(
            context['build_log_url'],
            context['context'].repository,
        )
    fields = []
    fields.append({
        'title': 'Repository',
        'value': '<https://bitbucket.org/{repo}|{repo}>'.format(repo=context['context'].repository),
        'short': True,
    })
    fields.append({
        'title': 'Branch',
        'value': '<https://bitbucket.org/{repo}/src?at={branch}|{branch}>'.format(
            repo=context['context'].repository,
            branch=context['branch'],
        ),
        'short': True,
    })
    if context['context'].type == 'commit':
        fields.append({
            'title': 'Commit',
            'value': '<https://bitbucket.org/{repo}/commits/{sha}|{sha}>'.format(
                repo=context['context'].repository,
                sha=context['context'].source['commit']['hash'],
            ),
            'short': False
        })
    elif context['context'].type == 'pullrequest':
        fields.append({
            'title': 'Pull Request',
            'value': '<https://bitbucket.org/{repo}/pull-requests/{pr_id}|{title}>'.format(
                repo=context['context'].repository,
                pr_id=context['context'].pr_id,
                title=context['context'].message,
            ),
            'short': False
        })

    actor = context['context'].actor
    attachment = {
        'fallback': title,
        'title': title,
        'color': color,
        'title_link': context['build_log_url'],
        'fields': fields,
        'footer': context['context'].repo_name,
        'ts': int(time.time()),
        'author_name': actor['display_name'],
        'author_link': actor['links']['html']['href'],
        'author_icon': actor['links']['avatar']['href'],
    }
    if context['context'].type == 'commit':
        attachment['text'] = context['context'].message
    payload = {'attachments': [attachment]}
    for webhook in webhooks:
        logger.info('Triggering Slack webhook %s', webhook)
        res = session.post(webhook, json=payload, timeout=10)
        try:
            res.raise_for_status()
        except requests.RequestException:
            logger.exception('Error triggering Slack webhook %s', webhook)
            sentry.captureException()
