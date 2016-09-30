# -*- coding: utf-8 -*-
from __future__ import absolute_import
import signal

import click
from flask import url_for

import badwolf


@click.group()
@click.version_option(version=badwolf.__version__)
def manage():
    """badwolf - A continuous integration and code lint review system for BitBucket"""
    try:
        import faulthandler
        faulthandler.register(signal.SIGUSR1)
    except ImportError:
        pass


@manage.command()
@click.option('--host', '-h', type=str,
              default='0.0.0.0', help='Server host')
@click.option('--port', '-p', type=int,
              default=8000, help='Server port')
@click.option('--reload', is_flag=True,
              default=False, help='Auto reload when codes changed')
@click.option('--debug', is_flag=True,
              default=False, help='Use debugger')
def runserver(host, port, reload, debug):
    """Starts a development server"""
    from werkzeug.serving import run_simple
    from badwolf.wsgi import app

    app.debug = debug

    run_simple(
        host,
        port,
        app,
        use_reloader=reload,
        use_debugger=debug,
        threaded=True,
    )


@manage.command()
def shell():
    """Runs a Python shell inside application context"""
    from badwolf.wsgi import app

    app.debug = True
    context = {
        'app': app,
    }

    with app.app_context():
        # Try ptpython
        try:
            from ptpython.ipython import embed
            embed(user_ns=context, vi_mode=True)
            return
        except ImportError:
            pass

        # Try bpython
        try:
            from bpython import embed
            embed(locals_=context)
            return
        except ImportError:
            pass

        # Try ipython
        try:
            try:
                # 0.10.x
                from IPython.Shell import IPShellEmbed
                ipshell = IPShellEmbed(banner='Welcome to badwolf shell\n')
                ipshell(global_ns=dict(), local_ns=context)
            except ImportError:
                # 0.12+
                from IPython import embed
                embed(banner1='Welcome to badwolf shell\n', user_ns=context)
            return
        except ImportError:
            pass

        # Use basic python shell
        import code

        code.interact(local=context)


@manage.command()
@click.argument('repo', required=True)
def register_webhook(repo):
    '''Register badwolf webhook on BitBucket for REPO'''
    from badwolf.wsgi import app
    from badwolf.extensions import bitbucket
    from badwolf.bitbucket import Hooks

    with app.app_context():
        webhook_url = url_for('webhook.webhook_push', _external=True)
        hooks = Hooks(bitbucket, repo)
        existing_hooks = hooks.list()
        existing_urls = [hook['url'] for hook in existing_hooks['values']]
        if webhook_url in existing_urls:
            click.echo('Webhook {} already registered'.format(webhook_url))
            return

        hooks.add('badwolf', webhook_url, events=(
            'repo:push',
            'repo:commit_comment_created',
            'pullrequest:created',
            'pullrequest:updated',
            'pullrequest:approved',
            'pullrequest:comment_created',
        ))
        click.echo('Webhook {} registered'.format(webhook_url))
