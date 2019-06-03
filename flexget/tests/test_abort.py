from __future__ import absolute_import, division, unicode_literals

from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin


class TestAbort(object):
    config = """
        tasks:
          test:
            # causes on_task_abort to be called
            disable: builtins

            # causes abort
            abort: yes

            # another event hookup with this plugin
            headers:
              test: value
    """

    def test_abort(self, execute_task):
        execute_task('test', abort=True)
