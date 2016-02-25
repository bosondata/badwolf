# badwolf

[What is badwolf](https://en.wikipedia.org/wiki/Bad_Wolf)

Features:

1. Run tests in Docker container
2. Supports multiple test scripts
3. Supports multiple after success/failure scripts
4. Supports E-mail notification
5. Supports code linting

## Installation

```bash
$ python setup.py install
```

for development:

```bash
$ pip install -r dev-requirements.txt
$ python setup.py develop
```

## Configuration

There are several ways to configure badwolf, settings loading by orders below:

1. Try to load from ``~/.badwolf.conf.py``
2. Try to use ``BADWOLF_CONF`` environment variable to set configuration file path and load it
3. Dict or a file path passed to ``badwolf.create_app`` function

## Run server for development

```bash
$ badwolf runserver
```

## Interactive shell

```bash
$ badwolf shell
```

## Run tests

```bash
$ py.test -v
```

Open interactive shell when test failed:

```bash
$ py.test -v -s --pdb
```

## Packaging and release

Build a distribution:

```bash
$ python setup.py release
```

Upload package to PyPI cloud:

```bash
twine upload -r bosondata dist/*
```

## Test configuration file

Configuration file use YAML format, filename should be ``.badwolf.yml``

Fields:

1. ``dockerfile``: Dockfile name for build docker image, ``str``
2. ``script``: Test scipt(s), ``str`` or ``list``
3. ``after_success``: command(s) to run after success, ``str`` or ``list``
4. ``after_failure``: command(s) to run after failure, ``str`` or ``list``
5. ``service``: service(s) to start before run script(s), ``str`` or ``list``
6. ``env``: envrionment variable(s), ``str`` or ``list``, only the first item will be used currently. Eg: ``env: X=1 Y=2 Z=3``
7. ``linter``: code linter(s), ``str`` or ``list``

``Dockerfile`` should set ``FROM`` as ``messense/badwolf-test-runner`` in order to use [badwolf-runner](https://bitbucket.org/deepanalyzer/badwolf-runner/overview) to run tests.
But surely you can build your own docker image and use it as long as you put ``badwolf-run`` binary in its executable path.

if no ``Dockerfile`` found, badwolf will use ``messense/badwolf-test-runner`` as default Docker image to run tests.

## Available linters

1. ``flake8``: Lint Python codes with flake8
2. ``pep8``: Lint Python codes with pep8
3. ``jscs``: Lint JavaScript codes with jscs
4. ``eslint``: Lint ECMAScript 6 codes with eslint
5. ``csslint``: Lint CSS codes with csslint
6. ``shellcheck``: Lint bash/sh/zsh shell scripts with shellcheck
7. ``yamllint``: Lint YAML codes with yamllint
8. ``jsonlint``: Lint JSON codes with jsonlint
9. ``bandit``: Lint Python codes with bandit
