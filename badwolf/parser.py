# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import io

import yaml
try:
    from yaml import CLoader as _Loader
except ImportError:
    from yaml import Loader as _Loader


def _get_list(value):
    if isinstance(value, list):
        return value
    return [value]


def parse_configuration(path):
    with io.open(path) as f:
        conf = yaml.load(f.read(), Loader=_Loader)

    script = _get_list(conf.get('script', []))
    dockerfile = conf.get('dockerfile', 'Dockerfile')
    after_success = _get_list(conf.get('after_success', []))
    after_failure = _get_list(conf.get('after_failure', []))
    notification = conf.get('notification', {})
    if not isinstance(notification, dict):
        notification = {
            'email': [],
        }
    else:
        notification['email'] = _get_list(notification.get('email', []))

    config = {
        'script': script,
        'dockerfile': dockerfile,
        'after_success': after_success,
        'after_failure': after_failure,
        'notification': notification,
    }
    return config
