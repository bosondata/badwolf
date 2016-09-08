# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import logging

from flask import Blueprint, current_app, abort


logger = logging.getLogger(__name__)
blueprint = Blueprint('log', __name__)


@blueprint.route('/build/<sha>', methods=['GET'])
def build_log(sha):
    log_dir = os.path.join(current_app.config['BADWOLF_LOG_DIR'], sha)
    log_html = os.path.join(log_dir, 'build.html')
    if not os.path.exists(log_html):
        abort(404)

    with open(log_html) as f:
        return f.read()


@blueprint.route('/lint/<sha>', methods=['GET'])
def lint_log(sha):
    log_dir = os.path.join(current_app.config['BADWOLF_LOG_DIR'], sha)
    log_html = os.path.join(log_dir, 'lint.html')
    if not os.path.exists(log_html):
        abort(404)

    with open(log_html) as f:
        return f.read()
