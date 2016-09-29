# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import atexit
import logging
from concurrent.futures import ProcessPoolExecutor

from badwolf.extensions import sentry
from badwolf.pipeline import Pipeline


logger = logging.getLogger(__name__)

executor = ProcessPoolExecutor(max_workers=10)


@atexit.register
def _shutdown_executor():
    try:
        executor.shutdown()
    except Exception:
        pass


def _run_task(_task_func, *args, **kwargs):
    logger.debug('Running task func %r', _task_func.__name__)
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
def start_pipeline(context):
    Pipeline(context).start()
