.. _lint:

代码检查
==============

项目接入
--------------

请参考 :ref:`构建和测试 <build>` 文档接入项目，对于代码检查，需要配置 `linter` 选项，如：

单个 linter 示例
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    linter: flake8

多个 linter 示例
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    linter:
      - flake8
      - eslint

自定义文件类型示例
~~~~~~~~~~~~~~~~~~~~~~~

可以通过配置 linter 的 `pattern` 来自定义 linter 需要处理的文件类型，支持 glob/正则表达式，如：

.. code-block:: yaml

    linter: {name: "jsonlint", pattern: "*.mapping"}

支持的代码检查工具
-------------------------

=================== =================== =======================================================
名称                编程语言            官网/文档地址
=================== =================== =======================================================
flake8              Python              http://flake8.readthedocs.org/en/latest/
pep8                Python              http://pep8.readthedocs.org/en/latest/
pylint              Python              http://pep8.readthedocs.org/en/latest/
bandit              Python              https://github.com/openstack/bandit
jscs                JavaScript          http://jscs.info/
eslint              JavaScript          http://eslint.org/
csslint             CSS                 http://csslint.net/
stylelint           CSS/SASS/SCSS       http://stylelint.io/
sasslint            SASS/SCSS           https://github.com/sasstools/sass-lint
shellcheck          bash/zsh            https://github.com/koalaman/shellcheck
yamllint            YAML                https://github.com/adrienverge/yamllint
jsonlint            JSON                https://github.com/zaach/jsonlint
rstlint             RestructuredText    https://github.com/twolfson/restructuredtext-lint
=================== =================== =======================================================
