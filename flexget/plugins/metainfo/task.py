from __future__ import absolute_import, division, unicode_literals

import logging
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

from flexget import plugin
from flexget.event import event

log = logging.getLogger('metainfo_task')


class MetainfoTask(object):
    """
    Set 'task' field for entries.
    """

    schema = {'type': 'boolean'}

    def on_task_metainfo(self, task, config):
        # check if explicitly disabled (value set to false)
        if config is False:
            return

        for entry in task.entries:
            entry['task'] = task.name


@event('plugin.register')
def register_plugin():
    plugin.register(MetainfoTask, 'metainfo_task', api_ver=2, builtin=True)
