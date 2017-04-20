# -*- coding: utf-8 -*-
import logging
import smtplib

from badwolf.extensions import mail, sentry


logger = logging.getLogger(__name__)


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
