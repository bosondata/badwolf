#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


readme = 'README.md'
if os.path.exists('README.rst'):
    readme = 'README.rst'
with open(readme) as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = [l for l in f.read().splitlines() if l]


setup(
    name='badwolf',
    version='0.15.0',
    author='messense',
    author_email='messense@icloud.com',
    packages=find_packages(exclude=('tests', 'tests.*')),
    keywords='ci, bitbucket',
    description='Docker based continuous integration and code lint review system for BitBucket',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=requirements,
    include_package_data=True,
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    entry_points='''
        [console_scripts]
        badwolf=badwolf.cli:manage
    ''',
)
