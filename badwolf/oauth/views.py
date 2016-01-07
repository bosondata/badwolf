# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging

from flask import Blueprint, request, current_app, redirect, jsonify

from badwolf.bitbucket import Bitbucket, BitbucketAPIError, OAuth2Dispatcher


logger = logging.getLogger(__name__)
blueprint = Blueprint('oauth', __name__)


@blueprint.route('/bitbucket', methods=['GET'])
def redirect_to_bitbucket():
    oauth = OAuth2Dispatcher(
        current_app.config['BITBUCKET_OAUTH_KEY'],
        current_app.config['BITBUCKET_OAUTH_SECRET'],
    )
    auth_url = oauth.get_authorization_url()
    return redirect(auth_url)


@blueprint.route('/bitbucket/callback', methods=['GET'])
def bitbucket_oauth_callback():
    oauth = OAuth2Dispatcher(
        current_app.config['BITBUCKET_OAUTH_KEY'],
        current_app.config['BITBUCKET_OAUTH_SECRET'],
    )
    code = request.args.get('code')
    try:
        oauth.grant_access_token(code)
    except BitbucketAPIError:
        return 'Failed'

    bitbucket = Bitbucket(oauth)
    data = bitbucket.get('1.0/user')
    return jsonify(data)
