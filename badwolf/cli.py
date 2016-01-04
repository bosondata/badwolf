# -*- coding: utf-8 -*-
from __future__ import absolute_import
import click


@click.group()
def manage():
    pass


@manage.command()
@click.option('--host', '-h', type=str,
              default='0.0.0.0', help='Server host')
@click.option('--port', '-p', type=int,
              default=8000, help='Server port')
def runserver(host, port):
    """Starts a development server"""
    from werkzeug.serving import run_simple
    from badwolf.wsgi import app

    app.debug = True

    run_simple(
        host,
        port,
        app,
        use_reloader=True,
        use_debugger=True,
    )


@manage.command()
def shell():
    """Runs a Python shell inside application context"""
    from badwolf.wsgi import app

    app.debug = True
    context = {
        'app': app,
    }

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
