# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import io

from badwolf.spec import Specification


def test_parse_empty_conf():
    spec = Specification.parse({})
    assert len(spec.scripts) == 0
    assert len(spec.services) == 0
    assert len(spec.after_success) == 0
    assert len(spec.after_failure) == 0
    assert len(spec.branch) == 0
    assert spec.dockerfile == 'Dockerfile'
    assert len(spec.notification.emails) == 0


def test_parse_single_string_conf():
    spec = Specification.parse({
        'service': 'redis-server',
        'script': 'ls',
        'after_success': 'pwd',
        'after_failure': 'exit',
        'notification': {
            'email': 'messense@icloud.com',
        }
    })
    assert spec.services == ['redis-server']
    assert spec.scripts == ['ls']
    assert spec.after_success == ['pwd']
    assert spec.after_failure == ['exit']
    assert spec.notification.emails == ['messense@icloud.com']


def test_parse_file_single_string():
    s = """script: ls
dockerfile: MyDockerfile
service: redis-server
after_success: pwd
after_failure: exit
notification:
  email: messense@icloud.com"""
    f = io.StringIO(s)
    spec = Specification.parse_file(f)
    assert spec.dockerfile == 'MyDockerfile'
    assert spec.services == ['redis-server']
    assert spec.scripts == ['ls']
    assert spec.after_success == ['pwd']
    assert spec.after_failure == ['exit']
    assert spec.notification.emails == ['messense@icloud.com']


def test_parse_file_single_list():
    s = """script:
  - ls
dockerfile: MyDockerfile
service:
  - redis-server
after_success:
  - pwd
after_failure:
  - exit
notification:
  email:
    - messense@icloud.com"""
    f = io.StringIO(s)
    spec = Specification.parse_file(f)
    assert spec.dockerfile == 'MyDockerfile'
    assert spec.services == ['redis-server']
    assert spec.scripts == ['ls']
    assert spec.after_success == ['pwd']
    assert spec.after_failure == ['exit']
    assert spec.notification.emails == ['messense@icloud.com']


def test_parse_file_multi_list():
    s = """script:
  - ls
  - ps
dockerfile: MyDockerfile
service:
  - redis-server
  - postgresql
after_success:
  - pwd
  - rm
after_failure:
  - echo
  - exit
notification:
  email:
    - tech@bosondata.com.cn
    - messense@icloud.com"""
    f = io.StringIO(s)
    spec = Specification.parse_file(f)
    assert spec.dockerfile == 'MyDockerfile'
    assert spec.services == ['redis-server', 'postgresql']
    assert spec.scripts == ['ls', 'ps']
    assert spec.after_success == ['pwd', 'rm']
    assert spec.after_failure == ['echo', 'exit']
    assert spec.notification.emails == ['tech@bosondata.com.cn', 'messense@icloud.com']
