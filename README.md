# badwolf

[What is badwolf](https://en.wikipedia.org/wiki/Bad_Wolf)

Features:

1. Run tests in Docker container
2. Supports multiple test scripts
3. Supports multiple after success/failure scripts
4. Supports E-mail notification
5. Supports code linting

## Requirements

1. Python 2.7 or Python 3.4+
2. Docker
3. NodeJS

## Installation

```bash
$ python setup.py install
```

for development:

```bash
$ pip install -r dev-requirements.txt
$ python setup.py develop
```

## Deploy

### Standalone

You can configure the system by shell:

```bash
curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
sudo apt-get install -y software-properties-common python-dev python-software-properties python-setuptools python-pip git nodejs shellcheck
sudo npm install -g jscs eslint csslint sass-lint jsonlint eslint-plugin-react eslint-plugin-react-native
```

Then install `badwolf` by `pip install -U badwolf` and run it:

```bash
badwolf runserver --port 8000
```

### Docker

Build Docker image:

```bash
docker build -t badwolf .
```

Run it:

```bash
docker run \
--volume /var/run/docker.sock:/var/run/docker.sock \
--volume /var/lib/badwolf/log:/var/lib/badwolf/log \
--volume /tmp/badwolf:/tmp/badwolf \
--env-file ~/.badwolfrc \
--publish=8000:8000 \
--detach=true \
--restart=always \
--name=badwolf \
badwolf
```

The `~/.badwolfrc` file is environment variable configuraiton file for Docker.

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

| Name         | Description                                                                                                     |
|--------------|-----------------------------------------------------------------------------------------------------------------|
| flake8       | Lint Python codes with [flake8](http://flake8.readthedocs.org/en/latest/)                                       |
| pep8         | Lint Python codes with [pep8](http://pep8.readthedocs.org/en/latest/)                                           |
| jscs         | Lint JavaScript codes with [jscs](http://jscs.info/)                                                            |
| eslint       | Lint ECMAScript 6 codes with [eslint](http://eslint.org/)                                                       |
| csslint      | Lint CSS codes with [csslint](http://csslint.net/)                                                              |
| shellcheck   | Lint bash/sh/zsh shell scripts with [shellcheck](https://github.com/koalaman/shellcheck)                        |
| yamllint     | Lint YAML codes with [yamllint](https://github.com/adrienverge/yamllint)                                        |
| jsonlint     | Lint JSON codes with [jsonlint](https://github.com/zaach/jsonlint)                                              |
| bandit       | Lint Python codes with [bandit](https://github.com/openstack/bandit)                                            |
| rstlint      | Lint RestructuredText codes with [restructuredtext-lint](https://github.com/twolfson/restructuredtext-lint)     |
| pylint       | Lint Python codes with [pylint](https://docs.pylint.org)                                                        |
| sasslint     | Lint SASS codes with [sass-lint](https://github.com/sasstools/sass-lint)                                        |
| stylelint    | Lint stylesheet codes with [stylelint](http://stylelint.io/)                                                    |

## License

MIT
