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

## Run Celery worker

```bash
$ celery worker -A badwolf.worker -l info
```

## Interactive shell

```bash
$ badwolf shell
```
