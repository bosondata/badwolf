# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals


class Problem(object):
    def __init__(self, filename, line, message, linter, is_error=True):
        self.filename = filename
        self.line = line
        self.message = message
        self.linter = linter
        self.is_error = is_error

    def __hash__(self):
        return hash(self.__str__())

    def __repr__(self):
        return '<Problem {}:{} {}>'.format(
            self.filename,
            self.line,
            self.message
        )

    def __str__(self):
        return '{}:{} {}'.format(self.filename, self.line, self.message)


class Problems(object):
    """Lint problems"""
    def __init__(self):
        self._items = set()
        self._changes = None

    def add(self, problem):
        self._items.add(problem)

    def set_changes(self, changes):
        self._changes = changes

    def limit_to_changes(self):
        changes = self._changes
        if not changes:
            return

        def has_line_changes(item):
            for patched_file in changes:
                if patched_file.path != item.filename:
                    continue

                for hunk in patched_file:
                    if not hunk.is_valid():
                        continue

                    for line in hunk.target_lines():
                        if not line.is_added:
                            continue
                        if item.line == line.target_line_no:
                            return True

            return False

        self._items = [item for item in self._items if has_line_changes(item)]

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        for item in self._items:
            yield item

    def __getitem__(self, key):
        return self._items[key]
