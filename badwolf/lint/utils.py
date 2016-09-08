# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import subprocess
from xml.etree import ElementTree


def in_path(name):
    """
    Check whether a command line tool
    exists in the system path.
    """
    for dirname in os.environ['PATH'].split(os.pathsep):
        if os.path.exists(os.path.join(dirname, name)):
            return True
    return False


def npm_exists(name, cwd=None):
    """
    Check whether a cli tool exists in a node_modules/.bin
    dir in os.cwd
    """
    cwd = cwd or os.getcwd()
    path = os.path.join(cwd, 'node_modules', '.bin', name)
    return os.path.exists(path)


def run_command(command, split=False, include_errors=False, cwd=None):
    """Run command in subprocess and return exit code and output"""
    env = os.environ.copy()
    if include_errors:
        error_pipe = subprocess.STDOUT
    else:
        error_pipe = subprocess.PIPE

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=error_pipe,
        shell=False,
        universal_newlines=True,
        cwd=cwd,
        env=env
    )
    if split:
        output = process.stdout.readlines()
    else:
        output = process.stdout.read()

    return_code = process.wait()
    return return_code, output


def parse_checkstyle(xml):
    tree = ElementTree.fromstring(xml)
    for f in tree.iterfind('file'):
        filename = f.get('name')
        for err in f.iterfind('error'):
            severity = err.get('severity')
            if severity == 'info':
                continue

            line = err.get('line')
            message = err.get('message')
            if ',' in line:
                lines = [int(x) for x in line.split(',') if x != 'undefined']
            else:
                if line == 'undefined':
                    continue
                lines = [int(line)]

            for line in lines:
                yield (filename, line, message)
