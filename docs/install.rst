.. _install:

安装配置
==============

安装 Docker
-----------------

请参考 `Docker 官方文档 <https://docs.docker.com/engine/installation/linux/ubuntulinux/>`_ 安装最新版本的 Docker

Standalone 模式
---------------------

系统依赖：

1. Python 2.7 和 Python 3.4+
2. Docker
3. Nodejs

可以通过以下 shell 命令配置系统：

.. code-block:: bash

    curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
    sudo apt-get install -y software-properties-common python-dev python-software-properties python-setuptools python-pip git nodejs shellcheck
    sudo npm install -g jscs eslint csslint sass-lint jsonlint eslint-plugin-react eslint-plugin-react-native

然后使用 pip 安装 badwolf：

.. code-block:: bash

    pip install -U badwolf

最后，通过以下命令启动 server：

.. code-block:: bash

    badwolf runserver --port 8000

Docker 模式
------------------

获取 Docker 镜像
~~~~~~~~~~~~~~~~~~~~~~

从 Docker Hub 上拉取镜像：

.. code-block:: bash

    docker pull messense/badwolf

如果需要自行构建 Docker 镜像，可以在代码根目录中运行：

.. code-block:: bash

    docker build --rm -t messense/badwolf .

运行
~~~~~~~~~~~

.. code-block:: bash

    docker run \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    --volume /var/lib/badwolf/log:/var/lib/badwolf/log \
    --volume /tmp/badwolf:/tmp/badwolf \
    --env-file ~/.badwolfrc \
    --publish=8000:8000 \
    --detach=true \
    --restart=always \
    --name=badwolf \
    messense/badwolf

其中 `~/.badwolfrc` 为 Docker 环境变量配置文件，配置示例：

.. code-block:: bash

    SERVER_NAME=badwolf.example.com:8000
    SECRET_KEY=top-secret
    SECURE_TOKEN_KEY=\x18\xd5\xb5\xd0\xae\x9f\x05\xb3\x7fAO\x89h*\xd9\x8d.u\xa3\xf0U\xa22\xffOc\xe3\x19J\xeaX1
    MAIL_SERVER=smtp.mailgun.org
    MAIL_PORT=587
    MAIL_USERNAME=badwolf@example.com
    MAIL_PASSWORD=password
    MAIL_SENDER_ADDRESS=badwolf@example.com
    BITBUCKET_USERNAME=username
    BITBUCKET_PASSWORD=password
    SENTRY_DSN=http://username:password@sentry.example.com/1


配置 badwolf
------------------

对于 standalone 模式，可以通过多种方式配置：

1. 在 badwolf 运行用户的 `~/.badwolf.conf.py` 中配置
2. 通过 `BADWOLF_CONF` 环境变量指定配置文件路径，并在此文件配置
3. 通过各个独立环境变量配置

Docker 模式一般使用独立环境变量进行配置。

可供配置的项请参考 :ref:`配置选项 <settings>` 文档。

Docker 镜像和容器日常清理
-------------------------------

批量删除停止的无用的容器：

.. code-block:: bash

    docker rm $(docker ps -a -q)

批量删除无用的镜像：

.. code-block:: bash

    docker rmi $(docker images -q -f dangling=true)
