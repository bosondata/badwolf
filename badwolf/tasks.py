# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import atexit
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from flask import render_template

from badwolf.extensions import mail, sentry


logger = logging.getLogger(__name__)

executor = ProcessPoolExecutor(max_workers=10)
# per repository lock
_LOCKS = {}


@atexit.register
def _shutdown_executor():
    try:
        executor.shutdown()
    except Exception:
        pass


def _run_task(_task_func, *args, **kwargs):
    try:
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
def send_mail(recipients, subject, template, context):
    logger.info('Sending email to %s', recipients)
    html = render_template('mail/' + template + '.html', **context)
    mail.send_message(
        subject=subject,
        recipients=recipients,
        html=html,
    )


@async_task
def run_test(context):
    from badwolf.runner import TestRunner

    lock = _LOCKS.setdefault(context.repository, multiprocessing.Lock())
    runner = TestRunner(context, lock)
    runner.run()
