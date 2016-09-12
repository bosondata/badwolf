# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
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


def trigger_slack_webhook(webhooks, message):
    payload = {'text': message}
    for webhook in webhooks:
        logger.info('Triggering Slack webhook %s', webhook)
        res = session.post(webhook, json=payload, timeout=10)
        try:
            res.raise_for_status()
        except requests.RequestException:
            logger.exception('Error triggering Slack webhook %s', webhook)
            sentry.captureException()
