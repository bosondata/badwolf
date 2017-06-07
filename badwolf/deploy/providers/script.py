# -*- coding: utf-8 -*-

from badwolf.utils import run_command
from badwolf.deploy.providers import Provider


class ScriptProvider(Provider):
    name = 'script'

    def deploy(self):
        exit_codes, outputs = [], []
        for script in self.config.script:
            exit_code, output = run_command(script, include_errors=True, cwd=self.working_dir, shell=True)
            exit_codes.append(exit_code)
            outputs.append(output)
        return all(code == 0 for code in exit_codes), '\n\n'.join(outputs)
