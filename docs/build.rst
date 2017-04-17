.. _build:

构建和测试
===============

项目接入
-----------------

在项目根目录中提供 `.badwolf.yml` 文件，用于配置 CI 环境等，使用 YAML 语法。

可配置的项有：


============================= ===================== ===================================================================
选项名                        类型                  说明
============================= ===================== ===================================================================
image                         string                用于构建的 Docker 镜像，提供此选项时可不提供 `dockerfile` 选项
docker                        boolean               挂载外部的 Docker sock 到容器中以便使用 Docker, 默认为 false
dockerfile                    string                用于构建 Docker 镜像的 dockerfile 文件名称, 默认为 Dockerfile
branch                        string/list           仅在这些分支上运行构建和测试
script                        string/list           构建/测试的命令
after_success                 string/list           构建/测试成功后运行的命令
after_failure                 string/list           构建/测试失败后运行的命令
service                       string/list           构建/测试前启动的服务，需要在 Dockerfile 中配置安装对应的软件包
env                           string                环境变量，如: `env: X=1 Y=2 Z=3`
linter                        string/list           启用的代码检查工具
notification.email            string/list           邮件通知地址列表
notification.slack_webhook    string/list           Slack webhook 地址列表
privileged                    boolean               使用特权模式启动 Docker 容器
============================= ===================== ===================================================================

请注意，当 `image` 和 `dockerfile` 选项同时提供时， `image` 选项优先使用。

然后，在 BitBucket 项目设置中配置 webhook，假设部署机器的可访问地址为：http://badwolf.example.com:8000，
则 webhook 地址应配置为：`http://badwolf.example.com:8000/webhook/push`。

也可以使用 `badwolf register_webhook REPO` 命令自动配置 webhook，如：

.. code-block:: bash

    badwolf register_webhook deepanalyzer/badwolf

构建运行时环境变量
----------------------

============================= ===================================================================
变量名                        值
============================= ===================================================================
DEBIAN_FRONTEND               noninteractive
HOME                          /root
SHELL                         /bin/sh
TERM                          xterm-256color
CI                            true
CI_NAME                       badwolf
DOCKER_HOST                   unix:///var/run/docker.sock（开启 Docker 功能时存在）
BADWOLF_COMMIT                构建仓库的 git commit sha
BADWOLF_BUILD_DIR             构建目录路径（仓库克隆路径）
BADWOLF_REPO_SLUG             仓库 slug
BADWOLF_TAG                   git tag 名称（如果有）
BADWOLF_BRANCH                git 分支名称
BADWOLF_PULL_REQUEST          Bitbucket Pull Request ID（如果有）
============================= ===================================================================

Tips
-----------

* 在 commit 的 message 中包含 `ci skip` 跳过测试
* 在评论中包含 `ci retry` 重跑测试
* 在评论或 commit message 或 Pull Request 的标题/描述中包含 `ci rebuild` 重新构建 Docker 镜像，同时包含 `no cache` 禁用 Docker 构建缓存
* 在 Pull Request 的标题/描述中包含 `merge skip` 或者 `wip` 或者 `working in progress` 禁用自动合并 Pull Request 功能
