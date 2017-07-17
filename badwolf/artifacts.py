# -*- coding: utf-8 -*-
import os

from flask import Blueprint, current_app, send_from_directory, abort


blueprint = Blueprint('artifacts', __name__)


@blueprint.route('/<user>/<repo>/<branch>/<filename>')
def download_artifacts(user, repo, branch, filename):
    artifacts_path = os.path.join(
        current_app.config['BADWOLF_ARTIFACTS_DIR'],
        user,
        repo,
        branch,
    )
    if os.path.exists(os.path.join(artifacts_path, filename)):
        return send_from_directory(artifacts_path, filename)
    abort(404)
