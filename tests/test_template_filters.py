# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from flask import render_template_string


def test_nl2br_filter(app):
    s = '{{ "\n"|nl2br }}'
    rs = render_template_string(s)
    assert rs == '<p><br/>\n</p>'


def test_blankspace2nbsp_filter(app):
    s = '{{ " \t"|blankspace2nbsp }}'
    rs = render_template_string(s)
    assert rs == '&nbsp;' * 5
