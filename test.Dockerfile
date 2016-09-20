FROM messense/badwolf-test-runner:python
MAINTAINER Messense Lv "messense@icloud.com"

ENV NPM_CONFIG_LOGLEVEL warn
ENV NODE_VERSION 5.6.0

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash - \
    && apt-get install -y nodejs

RUN add-apt-repository "deb http://archive.ubuntu.com/ubuntu trusty-backports restricted main universe" \
    && apt-get update \
    && apt-get install -y shellcheck libffi-dev \
    && pip install -U pip tox \
    && npm config set color false -g \
    && npm install -g jscs eslint csslint sass-lint jsonlint stylelint \
    && rm -rf /var/lib/apt/list/* /tmp/* /var/tmp/*
