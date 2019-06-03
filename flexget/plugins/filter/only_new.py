from __future__ import absolute_import, division, unicode_literals

import logging
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

from flexget import plugin
from flexget.event import event

log = logging.getLogger('only_new')


class FilterOnlyNew(object):
    """Causes input plugins to only emit entries that haven't been seen on previous runs."""

    schema = {'type': 'boolean'}

    def on_task_start(self, task, config):
        """Make sure the remember_rejected plugin is available"""
        # Raises an error if plugin isn't available
        plugin.get('remember_rejected', self)

    def on_task_learn(self, task, config):
        """Reject all entries so remember_rejected will reject them next time"""
        if not config or not task.entries:
            return
        log.verbose(
            'Rejecting entries after the task has run so they are not processed next time.'
        )
        for entry in task.entries:
            entry.reject('Already processed entry', remember=True)


@event('plugin.register')
def register_plugin():
    plugin.register(FilterOnlyNew, 'only_new', api_ver=2)
