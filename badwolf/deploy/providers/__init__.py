# -*- coding: utf-8 -*-


class Provider(object):
    name = ''

    def __init__(self, working_dir, config, context):
        self.working_dir = working_dir
        self.config = config
        self.context = context

    def is_usable(self):
        return True

    def deploy(self):
        raise NotImplementedError()

    def url(self):
        return None
