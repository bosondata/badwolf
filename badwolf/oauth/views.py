# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging

from flask import Blueprint, request, current_app, redirect, jsonify

from badwolf.oauth.bitbucket import Bitbucket, BitbucketAPIError


logger = logging.getLogger(__name__)
blueprint = Blueprint('oauth', __name__)


@blueprint.route('/bitbucket', methods=['GET'])
def redirect_to_bitbucket():
    bitbucket = Bitbucket(
        current_app.config['BITBUCKET_OAUTH_KEY'],
        current_app.config['BITBUCKET_OAUTH_SECRET'],
    )
    auth_url = bitbucket.get_authorization_url()
    return redirect(auth_url)


@blueprint.route('/bitbucket/callback', methods=['GET'])
def bitbucket_oauth_callback():
    bitbucket = Bitbucket(
        current_app.config['BITBUCKET_OAUTH_KEY'],
        current_app.config['BITBUCKET_OAUTH_SECRET'],
    )
    code = request.args.get('code')
    try:
        bitbucket.grant_access_token(code)
    except BitbucketAPIError:
        return 'Failed'

    data = bitbucket.get('1.0/user')
    return jsonify(data)
