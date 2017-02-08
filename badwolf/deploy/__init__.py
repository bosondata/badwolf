# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging

import six

from badwolf.deploy.providers.script import ScriptProvider
from badwolf.deploy.providers.pypi import PypiProvider


logger = logging.getLogger(__name__)


class Deployer(object):
    PROVIDERS = {
        'script': ScriptProvider,
        'pypi': PypiProvider,
    }

    def __init__(self, context, spec, working_dir=None):
        self.context = context
        self.spec = spec
        self.working_dir = working_dir or context.clone_path

        deploy_config = spec.deploy.copy()
        deploy_config.pop('branch', None)
        deploy_config.pop('tag', None)
        self.config = deploy_config

    def deploy(self):
        if not self.config:
            logger.info('No deploy provider configured')
            return

        for provider_name, provider_config in six.iteritems(self.config):
            provider_class = self.PROVIDERS.get(provider_name)
            if not provider_class:
                logger.warning('Provider %s not found', provider_name)
                continue

            provider = provider_class(self.working_dir, provider_config)
            if not provider.is_usable():
                logger.warning('Provider %s is not usable', provider_name)
                continue

            succeed, output = provider.deploy()
            logger.info('Provider %s deploy %s,  output: \n%s',
                        provider_name, 'succeed' if succeed else 'failed', output)
