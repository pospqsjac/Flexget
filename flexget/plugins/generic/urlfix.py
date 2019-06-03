from __future__ import absolute_import, division, unicode_literals

import logging
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

from flexget import plugin
from flexget.event import event
from flexget.utils.log import log_once

log = logging.getLogger('urlfix')


class UrlFix(object):
    """
    Automatically fix broken urls.
    """

    schema = {'type': 'boolean'}

    @plugin.priority(plugin.PRIORITY_LAST)
    def on_task_input(self, task, config):
        if config is False:
            return
        for entry in task.entries:
            if '&amp;' in entry['url']:
                log_once('Corrected `%s` url (replaced &amp; with &)' % entry['title'], logger=log)
                entry['url'] = entry['url'].replace('&amp;', '&')


@event('plugin.register')
def register_plugin():
    plugin.register(UrlFix, 'urlfix', builtin=True, api_ver=2)
