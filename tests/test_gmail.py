import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from email_organizer.core import connect, store
from email_organizer.gmail import apply


class GmailTest(unittest.TestCase):
    def test_only_approved_current_account_and_no_delete(self):
        with tempfile.TemporaryDirectory() as folder:
            db = connect(Path(folder) / 'test.sqlite')
            item = dict(sender='news@example.org', subject='News', date='', unsubscribe='yes', precedence='', protected=0)
            for source, identifier, approved in [('gmail:me@example.org', 'selected', 1), ('gmail:me@example.org', 'unapproved', 0), ('gmail:other@example.org', 'other-account', 1), ('gmail:me@example.org', 'now-starred', 1)]:
                store(db, source, identifier, item)
                db.execute('UPDATE messages SET category=?,candidate=1,approved=? WHERE source=? AND id=?', ('Newsletters', approved, source, identifier))
            db.commit()
            api = MagicMock()
            users = api.users.return_value
            users.getProfile.return_value.execute.return_value = {'emailAddress': 'me@example.org'}
            labels = users.labels.return_value
            labels.list.return_value.execute.return_value = {'labels': [{'name': 'Organizador/Newsletters', 'id': 'L1'}, {'name': 'Organizador/Revisar para borrar', 'id': 'L2'}]}
            messages = users.messages.return_value
            messages.get.side_effect = lambda **kwargs: MagicMock(**{'execute.return_value': {'labelIds': ['STARRED'] if kwargs['id'] == 'now-starred' else ['INBOX']}})
            apply(db, api)
            messages.modify.assert_called_once_with(userId='me', id='selected', body={'addLabelIds': ['L1', 'L2']})
            messages.delete.assert_not_called()
            messages.trash.assert_not_called()
            self.assertEqual(db.execute('SELECT count(*) FROM events').fetchone()[0], 1)
            messages.modify.reset_mock()
            apply(db, api)
            messages.modify.assert_not_called()
            db.close()
