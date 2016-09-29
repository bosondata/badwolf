# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import io

import yaml
try:
    from yaml import CLoader as _Loader
except ImportError:
    from yaml import Loader as _Loader

from badwolf.utils import ObjectDict


class Specification(object):
    def __init__(self):
        self.services = []
        self.scripts = []
        self.dockerfile = 'Dockerfile'
        self.after_success = []
        self.after_failure = []
        self.notification = ObjectDict(
            emails=[],
            slack_webhooks=[],
        )
        self.branch = set()
        self.environments = []
        self.linters = []
        self.privileged = False

    @classmethod
    def parse_file(cls, path):
        if hasattr(path, 'read') and callable(path.read):
            # File-like obj
            conf = yaml.load(path.read(), Loader=_Loader)
        else:
            with io.open(path) as f:
                conf = yaml.load(f.read(), Loader=_Loader)

        return cls.parse(conf)

    @classmethod
    def parse(cls, conf):
        services = cls._get_list(conf.get('service', []))
        scripts = cls._get_list(conf.get('script', []))
        dockerfile = conf.get('dockerfile', 'Dockerfile')
        after_success = cls._get_list(conf.get('after_success', []))
        after_failure = cls._get_list(conf.get('after_failure', []))
        notification = conf.get('notification', {})
        branch = set(cls._get_list(conf.get('branch', [])))
        env = cls._get_list(conf.get('env', []))
        env_map_list = []
        for _env in env:
            envs = _env.split()
            env_map = {}
            for env_str in envs:
                key, val = env_str.split('=', 1)
                env_map[key] = val
            env_map_list.append(env_map)

        linters = cls._parse_linters(cls._get_list(conf.get('linter', [])))
        privileged = conf.get('privileged', False)

        spec = cls()
        spec.services = services
        spec.scripts = scripts
        spec.dockerfile = dockerfile.strip()
        spec.after_success = after_success
        spec.after_failure = after_failure
        spec.branch = branch
        spec.environments = env_map_list
        spec.linters = linters
        spec.privileged = bool(privileged)
        if isinstance(notification, dict):
            if 'email' in notification:
                spec.notification.emails = cls._get_list(notification['email'])
            if 'slack_webhook' in notification:
                spec.notification.slack_webhooks = cls._get_list(notification['slack_webhook'])
        return spec

    @classmethod
    def _get_list(cls, value):
        if isinstance(value, list):
            return value
        return [value]

    @classmethod
    def _parse_linters(cls, linters):
        ret = []
        for linter in linters:
            info = ObjectDict()
            if isinstance(linter, dict):
                name = linter.get('name')
                pattern = linter.get('pattern')
                if not name:
                    continue

                info.update(linter)
            else:
                name = linter
                pattern = None

            info['name'] = name.strip()
            info['pattern'] = pattern
            ret.append(info)

        return ret

    def is_branch_enabled(self, branch):
        if not self.branch:
            return True
        return branch in self.branch
