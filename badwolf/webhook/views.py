# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from flask import Blueprint


blueprint = Blueprint('webhook', __name__)


@blueprint.route('/webhook/push', methods=['POST'])
def webhook_push():
    pass
