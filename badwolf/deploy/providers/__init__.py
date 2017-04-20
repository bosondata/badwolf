# -*- coding: utf-8 -*-


class Provider(object):
    name = ''

    def __init__(self, working_dir, config):
        self.working_dir = working_dir
        self.config = config

    def is_usable(self):
        return True

    def deploy(self):
        raise NotImplementedError()
