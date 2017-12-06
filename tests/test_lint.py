# -*- coding: utf-8 -*-
import os
import unittest.mock as mock

import pytest
from unidiff import PatchSet

from badwolf.spec import Specification
from badwolf.context import Context
from badwolf.lint.processor import LintProcessor
from badwolf.utils import ObjectDict


CURR_PATH = os.path.abspath(os.path.dirname(__file__))
FIXTURES_PATH = os.path.join(CURR_PATH, 'fixtures')


@pytest.fixture(scope='function')
def pr_context():
    return Context(
        'deepanalyzer/badwolf',
        None,
        'pullrequest',
        'message',
        {
            'repository': {'full_name': 'deepanalyzer/badwolf'},
            'branch': {'name': 'master'},
            'commit': {'hash': '000000'}
        },
        {'commit': {'hash': '111111'}},
        pr_id=1
    )


def test_no_linters_ignore(app, pr_context):
    spec = Specification()
    lint = LintProcessor(pr_context, spec, '/tmp')
    with mock.patch.object(lint, 'load_changes') as load_changes:
        lint.process()
        load_changes.assert_not_called()


def test_load_changes_failed_ignore(app, pr_context, caplog):
    spec = Specification()
    spec.linters.append('flake8')
    lint = LintProcessor(pr_context, spec, '/tmp')
    with mock.patch.object(lint, 'load_changes') as load_changes:
        load_changes.return_value = None
        lint.process()

        assert load_changes.called

    assert 'Load changes failed' in caplog.text


def test_no_changed_files_ignore(app, pr_context, caplog):
    diff = """diff --git a/removed_file b/removed_file
deleted file mode 100644
index 1f38447..0000000
--- a/removed_file
+++ /dev/null
@@ -1,3 +0,0 @@
-This content shouldn't be here.
-
-This file will be removed.
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='flake8', pattern=None))
    lint = LintProcessor(pr_context, spec, '/tmp')
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes:
        load_changes.return_value = patch
        lint.process()

        assert load_changes.called

    assert 'No changed files found' in caplog.text


def test_flake8_lint_a_py(app, pr_context):
    diff = """diff --git a/a.py b/a.py
new file mode 100644
index 0000000..fdeea15
--- /dev/null
+++ b/a.py
@@ -0,0 +1,6 @@
+# -*- coding: utf-8 -*-
+from __future__ import absolute_import, unicode_literals
+
+
+def add(a, b):
+    return a+ b
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='flake8', pattern=None))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'flake8'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 1
    problem = lint.problems[0]
    assert problem.filename == 'a.py'
    assert problem.line == 6


def test_eslint_lint_a_js(app, pr_context):
    diff = """diff --git a/.eslintrc b/.eslintrc
new file mode 100644
index 0000000..45e5d69
--- /dev/null
+++ b/.eslintrc
@@ -0,0 +1,5 @@
+{
+    "rules": {
+        "quotes": [2, "single"]
+    }
+}
diff --git a/a.js b/a.js
new file mode 100644
index 0000000..f119a7f
--- /dev/null
+++ b/a.js
@@ -0,0 +1 @@
+console.log("bar")
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='eslint', pattern=None))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'eslint'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 1
    problem = lint.problems[0]
    assert problem.filename == 'a.js'
    assert problem.line == 1


def test_pycodestyle_lint_a_py(app, pr_context):
    diff = """diff --git a/a.py b/a.py
new file mode 100644
index 0000000..fdeea15
--- /dev/null
+++ b/a.py
@@ -0,0 +1,6 @@
+# -*- coding: utf-8 -*-
+from __future__ import absolute_import, unicode_literals
+
+
+def add(a, b):
+    return a+ b
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='pycodestyle', pattern=None))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'pycodestyle'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 1
    problem = lint.problems[0]
    assert problem.filename == 'a.py'
    assert problem.line == 6


def test_jsonlint_a_json(app, pr_context):
    diff = """diff --git a/a.json b/a.json
new file mode 100644
index 0000000..266e19f
--- /dev/null
+++ b/a.json
@@ -0,0 +1 @@
+{"a": 1,}
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='jsonlint', pattern=None))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'jsonlint'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 1
    problem = lint.problems[0]
    assert problem.filename == 'a.json'
    assert problem.line == 1


def test_jsonlint_a_json_changes_in_range(app, pr_context):
    diff = """diff --git a/b.json b/b.json
index 6ebebfe..6be8d74 100644
--- a/b.json
+++ b/b.json
@@ -1,3 +1,4 @@
 {
     "a": 1
+    "b": 2
 }
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='jsonlint', pattern=None))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'jsonlint'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 1
    problem = lint.problems[0]
    assert problem.filename == 'b.json'
    assert problem.line == 2


def test_jsonlint_a_json_changes_out_of_range(app, pr_context):
    diff = """diff --git a/c.json b/c.json
index 9b90002..c36a2a4 100644
--- a/c.json
+++ b/c.json
@@ -3,4 +3,5 @@
     "b": 2,
     c: 3,
     d: 4
+    e: 5
 }
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='jsonlint', pattern=None))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'jsonlint'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 0


def test_shellcheck_a_sh(app, pr_context):
    diff = """diff --git a/a.sh b/a.sh
new file mode 100644
index 0000000..9fb9840
--- /dev/null
+++ b/a.sh
@@ -0,0 +2 @@
+#!/bin/sh
+$foo=42
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='shellcheck', pattern=None))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'shellcheck'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) > 0
    problem = lint.problems[0]
    assert problem.filename == 'a.sh'
    assert problem.line == 2


def test_csslint_a_css(app, pr_context):
    diff = """diff --git a/a.css b/a.css
new file mode 100644
index 0000000..5512dae
--- /dev/null
+++ b/a.css
@@ -0,0 +1 @@
+.a {}
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='csslint', pattern=None))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'csslint'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 1
    problem = lint.problems[0]
    assert problem.filename == 'a.css'
    assert problem.line == 1


def test_flake8_lint_a_py_with_custom_glob_pattern(app, pr_context):
    diff = """diff --git a/b.pyx b/b.pyx
new file mode 100644
index 0000000..fdeea15
--- /dev/null
+++ b/b.pyx
@@ -0,0 +1,6 @@
+# -*- coding: utf-8 -*-
+from __future__ import absolute_import, unicode_literals
+
+
+def add(a, b):
+    return a+ b
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='flake8', pattern='*.pyx'))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'flake8'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 1
    problem = lint.problems[0]
    assert problem.filename == 'b.pyx'
    assert problem.line == 6


def test_flake8_lint_a_py_with_custom_regex_pattern(app, pr_context):
    diff = """diff --git a/b.pyx b/b.pyx
new file mode 100644
index 0000000..fdeea15
--- /dev/null
+++ b/b.pyx
@@ -0,0 +1,6 @@
+# -*- coding: utf-8 -*-
+from __future__ import absolute_import, unicode_literals
+
+
+def add(a, b):
+    return a+ b
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='flake8', pattern='^.*\.pyx$'))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'flake8'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 1
    problem = lint.problems[0]
    assert problem.filename == 'b.pyx'
    assert problem.line == 6


def test_yamllint_a_yml(app, pr_context):
    diff = """diff --git a/a.yml b/a.yml
new file mode 100644
index 0000000..1eccee8
--- /dev/null
+++ b/a.yml
@@ -0,0 +1,3 @@
+---
+a: 1
+a: 2
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='yamllint', pattern=None))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'yamllint'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 1
    problem = lint.problems[0]
    assert problem.filename == 'a.yml'
    assert problem.line == 3


def test_flake8_lint_a_py_with_multi_custom_glob_patterns(app, pr_context):
    diff = """diff --git a/b.pyx b/b.pyx
new file mode 100644
index 0000000..fdeea15
--- /dev/null
+++ b/b.pyx
@@ -0,0 +1,6 @@
+# -*- coding: utf-8 -*-
+from __future__ import absolute_import, unicode_literals
+
+
+def add(a, b):
+    return a+ b
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='flake8', pattern='*.py *.pyx'))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'flake8'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 1
    problem = lint.problems[0]
    assert problem.filename == 'b.pyx'
    assert problem.line == 6


def test_bandit_lint_a_py(app, pr_context):
    diff = """diff --git a/a.py b/a.py
new file mode 100644
index 0000000..719cd56
--- /dev/null
+++ b/a.py
@@ -0,0 +1,4 @@
+try:
+    a = 1
+except Exception:
+    pass
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='bandit'))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'bandit'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 1
    problem = lint.problems[0]
    assert problem.filename == 'a.py'
    assert problem.line == 3
    assert not problem.is_error


def test_rstlint_a_rst(app, pr_context):
    diff = """diff --git a/a.rst b/a.rst
new file mode 100644
index 0000000..4e46cf9
--- /dev/null
+++ b/a.rst
@@ -0,0 +1,2 @@
+Hello World
+====
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='rstlint'))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'rstlint'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 1
    problem = lint.problems[0]
    assert problem.filename == 'a.rst'
    assert problem.line == 2


def test_pylint_lint_a_py(app, pr_context):
    diff = """diff --git a/a.py b/a.py
new file mode 100644
index 0000000..fdeea15
--- /dev/null
+++ b/a.py
@@ -0,0 +1,6 @@
+# -*- coding: utf-8 -*-
+from __future__ import absolute_import, unicode_literals
+
+
+def add(a, b):
+    return a+ b
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='pylint', pattern=None))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'pylint'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 4
    problem = lint.problems[0]
    assert problem.filename == 'a.py'


def test_sasslint_lint_a_scss(app, pr_context):
    diff = """diff --git a/a.scss b/a.scss
new file mode 100644
index 0000000..48b3ebe
--- /dev/null
+++ b/a.scss
@@ -0,0 +1,3 @@
+.test {
+    background-color: "#FFF"
+}
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='sasslint', pattern=None))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'sasslint'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 3
    problem = lint.problems[0]
    assert problem.filename == 'a.scss'


def test_stylelint_lint_a_scss(app, pr_context):
    diff = """diff --git a/a.scss b/a.scss
new file mode 100644
index 0000000..e545209
--- /dev/null
+++ b/a.scss
@@ -0,0 +1 @@
+a[id="foo"] { content: "x"; }
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='stylelint', pattern=None))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'stylelint'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 2
    problem = lint.problems[0]
    assert problem.filename == 'a.scss'


def test_mypy_lint_a_py(app, pr_context):
    diff = """diff --git a/a.py b/a.py
new file mode 100644
index 0000000..87604af
--- /dev/null
+++ b/a.py
@@ -0,0 +1,5 @@
+def p() -> None:
+    print('hello')
+
+
+a = p()
"""

    spec = Specification()
    spec.linters.append(ObjectDict(name='mypy', pattern=None))
    lint = LintProcessor(pr_context, spec, os.path.join(FIXTURES_PATH, 'mypy'))
    patch = PatchSet(diff.split('\n'))
    with mock.patch.object(lint, 'load_changes') as load_changes,\
            mock.patch.object(lint, 'update_build_status') as build_status,\
            mock.patch.object(lint, '_report') as report:
        load_changes.return_value = patch
        build_status.return_value = None
        report.return_value = (1, 2)
        lint.problems.set_changes(patch)
        lint.process()

        assert load_changes.called

    assert len(lint.problems) == 1
    problem = lint.problems[0]
    assert problem.line == 5
    assert problem.filename == 'a.py'
