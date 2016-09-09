# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import logging

from flask import Blueprint, current_app, send_from_directory


logger = logging.getLogger(__name__)
blueprint = Blueprint('log', __name__)


@blueprint.route('/build/<sha>', methods=['GET'])
def build_log(sha):
    log_dir = os.path.join(current_app.config['BADWOLF_LOG_DIR'], sha)
    return send_from_directory(log_dir, 'build.html')


@blueprint.route('/lint/<sha>', methods=['GET'])
def lint_log(sha):
    log_dir = os.path.join(current_app.config['BADWOLF_LOG_DIR'], sha)
    return send_from_directory(log_dir, 'lint.html')
