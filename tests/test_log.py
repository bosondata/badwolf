# -*- coding: utf-8 -*-
from flask import url_for


def test_view_build_log(test_client):
    test_client.get(url_for('log.build_log', sha='123456'))


def test_view_lint_log(test_client):
    test_client.get(url_for('log.lint_log', sha='123456'))
