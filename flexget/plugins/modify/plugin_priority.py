import logging

from flexget import plugin
from flexget.event import event

log = logging.getLogger('p_priority')


class PluginPriority:
    """
        Allows modifying plugin priorities from default values.

        Example:

        plugin_priority:
          ignore: 50
          series: 100
    """

    schema = {'type': 'object', 'additionalProperties': {'type': 'integer'}}

    def __init__(self):
        self.priorities = {}

    def on_task_start(self, task, config):
        self.priorities = {}
        names = []
        for name, priority in config.items():
            names.append(name)
            originals = self.priorities.setdefault(name, {})
            for phase, phase_event in plugin.plugins[name].phase_handlers.items():
                originals[phase] = phase_event.priority
                log.debug('stored %s original value %s' % (phase, phase_event.priority))
                phase_event.priority = priority
                log.debug('set %s new value %s' % (phase, priority))
        log.debug('Changed priority for: %s' % ', '.join(names))

    def on_task_exit(self, task, config):
        if not self.priorities:
            log.debug('nothing changed, aborting restore')
            return
        names = []
        for name in list(config.keys()):
            names.append(name)
            originals = self.priorities[name]
            for phase, priority in originals.items():
                plugin.plugins[name].phase_handlers[phase].priority = priority
        log.debug('Restored priority for: %s' % ', '.join(names))
        self.priorities = {}

    on_task_abort = on_task_exit


@event('plugin.register')
def register_plugin():
    plugin.register(PluginPriority, 'plugin_priority', api_ver=2)
