# -*- coding: utf-8 -*-
import os
import logging
import configparser

from badwolf.utils import run_command
from badwolf.lint import Problem
from badwolf.lint.linters import PythonLinter
from badwolf.lint.utils import in_path


logger = logging.getLogger(__name__)


class Flake8Linter(PythonLinter):
    name = 'flake8'

    def is_usable(self):
        return in_path('flake8')

    def lint_files(self, files):
        config = self._read_flake8_config()
        import_order_style = config.get('import-order-style', 'pep8')
        command = [
            self.python_name,
            '-m',
            'flake8',
            '--import-order-style',
            import_order_style,
            '--filename',
            '*.py*'
        ]
        command += files
        _, output = run_command(command, split=True, cwd=self.working_dir)
        if not output:
            raise StopIteration()

        for line in output:
            filename, line, message = self._parse_line(line)
            yield Problem(filename, line, message, self.name)

    def _parse_line(self, line):
        """flake8 only generates results as stdout.
        Parse the output for real data."""
        parts = line.split(':', 3)
        if len(parts) == 3:
            message = parts[2].strip()
        else:
            message = parts[3].strip()
        return parts[0], int(parts[1]), message

    def _read_flake8_config(self):
        files = [
            os.path.join(self.working_dir, 'setup.cfg'),
            os.path.join(self.working_dir, 'tox.ini'),
        ]
        parser = configparser.RawConfigParser()
        try:
            parser.read(files)
        except configparser.ParsingError:
            logger.exception('Error parsing flake8 config file %s', files)

        if parser.has_section('flake8'):
            return dict(parser.items('flake8'))
        return {}
