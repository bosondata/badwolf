FROM ubuntu:16.04

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV NPM_CONFIG_LOGLEVEL warn

RUN echo 'deb http://ppa.launchpad.net/fkrull/deadsnakes/ubuntu xenial main' > /etc/apt/sources.list.d/fkrull-ubuntu-deadsnakes-xenial.list \
    && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys DB82666C \
    && curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    shellcheck \
    libffi-dev \
    python \
    python-dev \
    python-pip \
    python-pkg-resources \
    python3 \
    python3-dev \
    python3-setuptools \
    python3-pip \
    python3-pkg-resources \
    python3.6 \
    python3.6-dev \
    git \
    git-lfs \
    libssl-dev \
    openssh-client \
    && pip3 install -U pip tox

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g \
    jscs eslint csslint sass-lint jsonlint stylelint \
    eslint-plugin-react eslint-plugin-react-native \
    babel-eslint \
    && rm -rf /var/lib/apt/list/* /tmp/* /var/tmp/*
