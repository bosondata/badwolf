# badwolf

[What is badwolf](https://en.wikipedia.org/wiki/Bad_Wolf)

## Installation

```bash
$ python setup.py install
```

for development:

```bash
$ pip install -r dev-requirements.txt
$ python setup.py develop
```

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

## Test configuration file

Configuration file use YAML format, filename should be ``.badwolf.yml``

Fields:

1. ``dockerfile``: Dockfile name for build docker image, ``str``
2. ``script``: Test scipt(s), ``str`` or ``list``
3. ``after_success``: command(s) to run after success, ``str`` or ``list``
3. ``after_failure``: command(s) to run after failure, ``str`` or ``list``
