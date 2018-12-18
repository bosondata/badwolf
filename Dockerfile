FROM ubuntu:16.04

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV NPM_CONFIG_LOGLEVEL warn

RUN echo 'deb http://ppa.launchpad.net/deadsnakes/ppa/ubuntu xenial main' > /etc/apt/sources.list.d/deadsnakes-ubuntu-ppa-xenial.list \
    && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 6A755776 \
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
    python3.6 \
    python3.6-dev \
    git \
    libssl-dev \
    openssh-client \
    libre2-dev \
    && curl -sSL https://bootstrap.pypa.io/get-pip.py | python3.5 \
    && curl -sSL https://bootstrap.pypa.io/get-pip.py | python3.6 \
    && pip2 install -U pip setuptools wheel \
    && python3.6 -m pip install -U pip setuptools wheel cython gunicorn \
    && python3.6 -m pip install https://github.com/andreasvc/pyre2/archive/master.zip \
    && git config --global user.email "badwolf@localhost" \
    && git config --global user.name "badwolf" \
    && curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash \
    && apt-get install git-lfs \
    && curl -sSL -o /usr/bin/hadolint https://github.com/hadolint/hadolint/releases/download/v1.15.0/hadolint-Linux-x86_64 \
    && chmod a+x /usr/bin/hadolint

RUN curl -sL https://deb.nodesource.com/setup_8.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g \
    eslint csslint sass-lint jsonlint stylelint \
    eslint-plugin-react eslint-plugin-react-native \
    babel-eslint

# Install Docker
RUN curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-17.12.1-ce.tgz && \
    tar --strip-components=1 -xvzf docker-17.12.1-ce.tgz -C /usr/local/bin && \
    rm docker-17.12.1-ce.tgz

RUN pip2 install -U flake8 pycodestyle pep8-naming pylint flake8-import-order flake8-network-timeout flake8-comprehensions \
    && python3.5 -m pip install -U flake8 pycodestyle pep8-naming pylint flake8-import-order flake8-network-timeout flake8-comprehensions \
    && python3.6 -m pip install -U badwolf \
    && rm -rf /var/lib/apt/list/* /tmp/* /var/tmp/*

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/gunicorn", "--bind", "0.0.0.0:8000", "--threads", "20", "--access-logfile", "-", "badwolf.wsgi:app"]
