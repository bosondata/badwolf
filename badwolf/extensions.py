# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from raven.contrib.flask import Sentry
sentry = Sentry()

from flask_mail import Mail
mail = Mail()

from badwolf.bitbucket import FlaskBitbucket

bitbucket = FlaskBitbucket()
