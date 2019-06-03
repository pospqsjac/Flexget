from __future__ import absolute_import, division, unicode_literals

import io
import logging
import os
import re
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

from sqlalchemy import Column, Integer, Unicode

from flexget import options, plugin
from flexget.db_schema import versioned_base
from flexget.entry import Entry
from flexget.event import event
from flexget.manager import Session

log = logging.getLogger('tail')
Base = versioned_base('tail', 0)


class TailPosition(Base):
    __tablename__ = 'tail'
    id = Column(Integer, primary_key=True)
    task = Column(Unicode)
    filename = Column(Unicode)
    position = Column(Integer)


class InputTail(object):
    """
    Parse any text for entries using regular expression.

    ::

      file: <file>
      entry:
        <field>: <regexp to match value>
      format:
        <field>: <python string formatting>

    Note: each entry must have at least two fields, title and url

    You may wish to specify encoding used by file so file can be properly
    decoded. List of encodings
    at http://docs.python.org/library/codecs.html#standard-encodings.

    Example::

      tail:
        file: ~/irclogs/some/log
        entry:
          title: 'TITLE: (.*) URL:'
          url: 'URL: (.*)'
        encoding: utf8
    """

    schema = {
        'type': 'object',
        'properties': {
            'file': {'type': 'string', 'format': 'file'},
            'encoding': {'type': 'string'},
            'entry': {
                'type': 'object',
                'properties': {
                    'url': {'type': 'string', 'format': 'regex'},
                    'title': {'type': 'string', 'format': 'regex'},
                },
                'required': ['url', 'title'],
            },
            'format': {'type': 'object', 'additionalProperties': {'type': 'string'}},
        },
        'required': ['file', 'entry'],
        'additionalProperties': False,
    }

    def format_entry(self, entry, d):
        for k, v in d.items():
            entry[k] = v % entry

    def on_task_input(self, task, config):

        # Let details plugin know that it is ok if this task doesn't produce any entries
        task.no_entries_ok = True

        filename = os.path.expanduser(config['file'])
        encoding = config.get('encoding', 'utf-8')
        with Session() as session:
            db_pos = (
                session.query(TailPosition)
                .filter(TailPosition.task == task.name)
                .filter(TailPosition.filename == filename)
                .first()
            )
            if db_pos:
                last_pos = db_pos.position
            else:
                last_pos = 0

            with io.open(filename, 'r', encoding=encoding, errors='replace') as file:
                if task.options.tail_reset == filename or task.options.tail_reset == task.name:
                    if last_pos == 0:
                        log.info('Task %s tail position is already zero' % task.name)
                    else:
                        log.info(
                            'Task %s tail position (%s) reset to zero' % (task.name, last_pos)
                        )
                        last_pos = 0

                if os.path.getsize(filename) < last_pos:
                    log.info(
                        'File size is smaller than in previous execution, resetting to beginning of the file'
                    )
                    last_pos = 0

                file.seek(last_pos)

                log.debug('continuing from last position %s' % last_pos)

                entry_config = config.get('entry')
                format_config = config.get('format', {})

                # keep track what fields have been found
                used = {}
                entries = []
                entry = Entry()

                # now parse text

                for line in file:
                    if not line:
                        break

                    for field, regexp in entry_config.items():
                        # log.debug('search field: %s regexp: %s' % (field, regexp))
                        match = re.search(regexp, line)
                        if match:
                            # check if used field detected, in such case start with new entry
                            if field in used:
                                if entry.isvalid():
                                    log.info(
                                        'Found field %s again before entry was completed. \
                                              Adding current incomplete, but valid entry and moving to next.'
                                        % field
                                    )
                                    self.format_entry(entry, format_config)
                                    entries.append(entry)
                                else:
                                    log.info(
                                        'Invalid data, entry field %s is already found once. Ignoring entry.'
                                        % field
                                    )
                                # start new entry
                                entry = Entry()
                                used = {}

                            # add field to entry
                            entry[field] = match.group(1)
                            used[field] = True
                            log.debug('found field: %s value: %s' % (field, entry[field]))

                        # if all fields have been found
                        if len(used) == len(entry_config):
                            # check that entry has at least title and url
                            if not entry.isvalid():
                                log.info(
                                    'Invalid data, constructed entry is missing mandatory fields (title or url)'
                                )
                            else:
                                self.format_entry(entry, format_config)
                                entries.append(entry)
                                log.debug('Added entry %s' % entry)
                                # start new entry
                                entry = Entry()
                                used = {}
                last_pos = file.tell()
            if db_pos:
                db_pos.position = last_pos
            else:
                session.add(TailPosition(task=task.name, filename=filename, position=last_pos))
        return entries


@event('plugin.register')
def register_plugin():
    plugin.register(InputTail, 'tail', api_ver=2)


@event('options.register')
def register_parser_arguments():
    options.get_parser('execute').add_argument(
        '--tail-reset',
        action='store',
        dest='tail_reset',
        default=False,
        metavar='FILE|TASK',
        help='reset tail position for a file',
    )
