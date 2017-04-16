FROM ubuntu:16.04

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV NPM_CONFIG_LOGLEVEL warn

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
    python-pkg-resources \
    python3 \
    python3-dev \
    python3-setuptools \
    python3-pip \
    python3-pkg-resources \
    git \
    libssl-dev \
    openssh-client \
    libre2-dev \
    && pip2 install -U pip setuptools wheel \
    && pip3 install -U pip setuptools wheel cython \
    && pip3 install https://github.com/andreasvc/pyre2/archive/master.zip \
    && git config --global user.email "badwolf@localhost" \
    && git config --global user.name "badwolf" \
    && curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash \
    && apt-get install git-lfs

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g \
    jscs eslint csslint sass-lint jsonlint stylelint \
    eslint-plugin-react eslint-plugin-react-native \
    babel-eslint

RUN pip2 install -U flake8 pep8 pep8-naming pylint flake8-import-order && \
    pip3 install -U badwolf \
    && rm -rf /var/lib/apt/list/* /tmp/* /var/tmp/*

EXPOSE 8000

ENTRYPOINT /usr/local/bin/badwolf runserver --port 8000
