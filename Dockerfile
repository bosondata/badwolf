FROM ubuntu:16.04
MAINTAINER Messense Lv "messense@icloud.com"

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV NPM_CONFIG_LOGLEVEL warn

ENV DOCKER_HOST 'unix://var/run/docker.sock'
ENV BADWOLF_DEBUG 'false'
ENV SECRET_KEY ''
ENV SENTRY_DSN ''
ENV DOCKER_API_TIMEOUT 600
ENV DOCKER_RUN_TIMEOUT 1200
ENV AUTO_MERGE_ENABLED 'true'
ENV AUTO_MERGE_APPROVAL_COUNT 3
ENV BITBUCKET_USERNAME ''
ENV BITBUCKET_PASSWORD ''
ENV MAIL_SERVER ''
ENV MAIL_PORT 587
ENV MAIL_USERNAME ''
ENV MAIL_PASSWORD ''
ENV MAIL_SENDER_NAME 'badwolf'
ENV MAIL_SENDER_ADDRESS ''

COPY . /src
WORKDIR /src

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    shellcheck \
    libffi-dev \
    python \
    python-dev \
    python-pip \
    python3 \
    python3-dev \
    python3-setuptools \
    python3-pip \
    git \
    libssl-dev \
    && pip3 install -U pip setuptools wheel \
    && git config --global user.email "badwolf@localhost" \
    && git config --global user.name "badwolf"

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash - \
    && apt-get install -y nodejs \
    && npm config set color false -g \
    && npm install -g jscs eslint csslint sass-lint jsonlint stylelint eslint-plugin-react eslint-plugin-react-native

RUN pip install -Ur requirements.txt && \
    pip3 install -Ur requirements.txt \
    && pip3 install . \
    && rm -rf /var/lib/apt/list/* /tmp/* /var/tmp/*

EXPOSE 8000

ENTRYPOINT /usr/local/bin/badwolf runserver --port 8000
