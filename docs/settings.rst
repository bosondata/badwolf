.. _settings:

配置选项
==================

所以的配置都是可以通过环境变量进行配置。

基本配置
--------------

========================== ============================== ==================================================
环境变量名称               默认值                         说明
========================== ============================== ==================================================
BADWOLF_DEBUG              False                          debug 模式开关
SERVER_NAME                localhost:8000                 部署服务器域名
SECRET_KEY                 空                             Flask SECRET_KEY
SECURE_TOKEN_KEY           随机生成                       .badwolf.yml 配置文件 secure token key
SENTRY_DSN                 空                             Sentry DSN URL
DOCKER_HOST                unix://var/run/docker.sock     Docker host
DOCKER_API_TIMEOUT         600                            docker-py timeout，单位秒
DOCKER_RUN_TIMEOUT         1200                           Docker 测试运行时长限制，单位秒
AUTO_MERGE_ENABLED         True                           自动合并 PR 功能开关
AUTO_MERGE_APPROVAL_COUNT  3                              自动合并 PR 需要的 Approval 数量
BITBUCKET_USERNAME         空                             BitBucket 用户名
BITBUCKET_PASSWORD         空                             BitBucket 用户密码，支持 app passwords
========================== ============================== ==================================================

其中，`SECURE_TOKEN_KEY` 为 base64 URL-safe 编码的 32 bytes 字符串，可以使用 `os.urandom(32)` 生成：

```python
import os
import base64

print(base64.urlsafe_b64encode(os.urandom(32)))
```

邮件服务器配置
-------------------

========================== ============================== ================================
环境变量名称               默认值                         说明
========================== ============================== ================================
MAIL_SERVER                空                             邮件服务器地址
MAIL_PORT                  587                            邮件服务器端口
MAIL_USE_TLS               True
MAIL_USE_SSL               False
MAIL_USERNAME              空                             邮件账户
MAIL_PASSWORD              空                             邮件账户密码
MAIL_SENDER_NAME           badwolf                        发件人名称
MAIL_SENDER_ADDRESS        空                             发件人邮件地址
========================== ============================== ================================
