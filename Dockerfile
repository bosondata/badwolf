FROM python:2.7
MAINTAINER Messense Lv "messense@icloud.com"
COPY . /app
WORKDIR /app
RUN pip install -i http://pypi.douban.com/simple/ --trusted-host=pypi.douban.com -r dev-requirements.txt
