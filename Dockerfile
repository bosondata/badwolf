FROM messense/badwolf-test-runner:python
MAINTAINER Messense Lv "messense@icloud.com"
ADD dev-requirements.txt /tmp/dev-requirements.txt
ADD requirements.txt /tmp/requirements.txt
RUN pip install -U pip && \
    pip install -r /tmp/dev-requirements.txt && \
    rm -rf /var/lib/apt/list/* /tmp/* /var/tmp/*
