import logging

from sqlalchemy.orm.exc import NoResultFound

from flexget import plugin
from flexget.event import event
from flexget.manager import Session

from . import db

log = logging.getLogger(__name__)


class EntryList:
    schema = {'type': 'string'}

    @staticmethod
    def get_list(config):
        return db.DBEntrySet(config)

    def on_task_input(self, task, config):
        return list(db.DBEntrySet(config))

    def search(self, task, entry, config=None):
        entries = []
        with Session() as session:
            try:
                entry_list = db.get_list_by_exact_name(config, session=session)
            except NoResultFound:
                log.warning('Entry list with name \'%s\' does not exist', config)
            else:
                for search_string in entry.get('search_strings', [entry['title']]):
                    log.debug(
                        'searching for entry that matches %s in entry_list %s',
                        search_string,
                        config,
                    )
                    search_string = search_string.replace(' ', '%').replace('.', '%')
                    query = entry_list.entries.filter(
                        db.EntryListEntry.title.like('%' + search_string + '%')
                    )
                    entries += [e.entry for e in query.all()]
            finally:
                return entries


@event('plugin.register')
def register_plugin():
    plugin.register(EntryList, 'entry_list', api_ver=2, interfaces=['task', 'list', 'search'])
