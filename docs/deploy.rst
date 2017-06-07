.. _deploy:

自动化部署
=================

支持的部署方式
-----------------

1. 命令行脚本 script
2. Pypi/PypiCloud

项目接入
------------------

请先参考 :ref:`构建和测试 <build>` 文档接入项目，对于部署，可配置的项有：

============================= ===================== ===================================================================
选项名                        类型                  说明
============================= ===================== ===================================================================
deploy.provider               string                部署服务提供方，如 script, pypi 等
deploy.branch                 string/list           开启部署的分支，默认为空
deploy.tag                    boolean               是否开启 tag 部署
after_deploy                  string/list           部署成功后运行的命令
============================= ===================== ===================================================================

script
---------

.. code-block:: yaml

    deploy:
      tag: true
      provider: script
      script:
        - echo 'Deploying'
        - etc.

Pypi
------------

可配置的项有：

============================= ===================== ===================================================================
选项名                        类型                  说明
============================= ===================== ===================================================================
username                      string                用户名
password                      string                密码
repository                    string                Pypi 仓库，默认为官方仓库
============================= ===================== ===================================================================

对于密码等敏感信息，可以使用 secure token 配置，可以使用 `badwolf encrypt` 命令生成，如：

.. code-block:: bash

    badwolf encrypt my_secret_key

然后将生成的 token 以 `secure: <token>` 的形式插入 `.badwolf.yml` 中，如：

.. code-block:: yaml

    after_success: python setup.py sdist bdist_wheel > /dev/null
    deploy:
      tag: true
      provider: pypi
      username: pypi
      password:
        secure: my_secure_token
      repository: https://pypi.example.com


配置多个 provider
-------------------

.. code-block:: yaml

    after_success: python setup.py sdist bdist_wheel > /dev/null
    deploy:
      - tag: true
        provider: script
        script:
          - echo 'Deploying'
          - etc.
      - branch: master
        provider: pypi
        username: pypi
        password:
          secure: my_secure_token

以上多个 deploy provider 将有序执行。
