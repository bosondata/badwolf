# -*- coding: utf-8 -*-
from raven.contrib.flask import Sentry
from flask_mail import Mail

from badwolf.bitbucket import FlaskBitbucket


# Sentry
sentry = Sentry()

# Flask-Mail
mail = Mail()

# Bitbucket API
bitbucket = FlaskBitbucket()
