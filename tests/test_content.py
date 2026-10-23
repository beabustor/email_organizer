import base64
import json
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path
from unittest.mock import MagicMock

from email_organizer.core import connect
from email_organizer.content import extract, save_raw, sync_full, import_mbox


def message(text='Texto del cuerpo completo'):
    item = EmailMessage()
    item['From'] = 'Equipo <newsletter@example.org>'
    item['Subject'] = 'Mensaje de ejemplo'
    item['Date'] = 'Wed, 01 Jan 2020 10:00:00 +0000'
    item.set_content(text)
    return item


class ContentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = connect(Path(self.temp.name) / 'test.sqlite')
        self.addCleanup(self.db.close)

    def test_alternative_html_tracking_never_requested(self):
        item = message('Información principal\n> Texto citado')
        item.add_alternative('<html><script>malicious()</script><img src="https://bad.example"><p>Información principal</p><p>&gt; Texto citado</p></html>', subtype='html')
        _, text, main, attachments, status, _ = extract(item.as_bytes())
        self.assertIn('Información principal', text)
        self.assertEqual(text.count('Información principal'), 1)
        self.assertNotIn('malicious', text)
        self.assertIn('Texto citado', text)
        self.assertNotIn('Texto citado', main)
        self.assertEqual(status, 'complete')

    def test_html_only_and_binary_attachment_preserved_not_executed(self):
        item = EmailMessage()
        item.set_content('<style>hidden</style><p>Reserva confirmada</p><script>run()</script>', subtype='html')
        item.add_attachment(b'FAKE-PDF', maintype='application', subtype='pdf', filename='document.pdf')
        save_raw(self.db, 'mbox:test', '1', item.as_bytes())
        row = self.db.execute('SELECT * FROM content').fetchone()
        self.assertIn('Reserva confirmada', row['text'])
        self.assertNotIn('run()', row['text'])
        self.assertIn(b'FAKE', base64.b64decode(b'RkFLRQ=='))
        self.assertFalse(json.loads(row['attachments'])[0]['analyzed'])
        self.assertIn(b'application/pdf', row['raw'])

    def test_content_change_invalidates_results(self):
        save_raw(self.db, 'local', '1', message().as_bytes())
        self.db.execute("INSERT INTO semantic_results(source,id) VALUES ('local','1')")
        self.db.commit()
        save_raw(self.db, 'local', '1', message('Contenido cambiado').as_bytes())
        self.assertEqual(self.db.execute('SELECT count(*) FROM semantic_results').fetchone()[0], 0)

    def test_empty_and_bad_charset_explicit(self):
        _, text, _, _, status, _ = extract(b'Content-Type: text/plain; charset=unknown\n\n\xff')
        self.assertEqual(status, 'partial')
        self.assertTrue(text)
        self.assertEqual(extract(b'Subject: Empty\n\n')[4], 'no_text')

    def test_richer_html_alternative_is_not_lost(self):
        item = message('Resumen breve')
        item.add_alternative('<p>Resumen breve</p><p>Cancelación de la reserva y devolución completa.</p>', subtype='html')
        text = extract(item.as_bytes())[1]
        self.assertIn('Cancelación', text)
        self.assertEqual(text.count('Resumen breve'), 1)

    def test_mbox_idempotent(self):
        import mailbox
        filename = Path(self.temp.name) / 'sample.mbox'
        box = mailbox.mbox(filename)
        box.add(message())
        box.close()
        import_mbox(self.db, filename)
        import_mbox(self.db, filename)
        self.assertEqual(self.db.execute('SELECT count(*) FROM content').fetchone()[0], 1)

    def test_full_gmail_then_history_no_redownload(self):
        api = MagicMock()
        users = api.users.return_value
        users.getProfile.return_value.execute.return_value = {'emailAddress': 'me@example.org', 'historyId': '10'}
        users.messages.return_value.list.return_value.execute.return_value = {'messages': [{'id': 'one'}]}
        users.messages.return_value.get.return_value.execute.return_value = {'raw': base64.urlsafe_b64encode(message().as_bytes()).decode(), 'threadId': 'thread', 'labelIds': ['STARRED']}
        sync_full(self.db, api)
        self.assertEqual(self.db.execute('SELECT protected FROM messages').fetchone()[0], 1)
        users.history.return_value.list.return_value.execute.return_value = {'historyId': '11'}
        users.messages.return_value.get.reset_mock()
        sync_full(self.db, api)
        users.messages.return_value.get.assert_not_called()
        self.assertEqual(self.db.execute('SELECT history_id FROM sync_state').fetchone()[0], '11')

    def test_failed_download_keeps_cursor_retryable(self):
        api = MagicMock()
        users = api.users.return_value
        users.getProfile.return_value.execute.return_value = {'emailAddress': 'me@example.org', 'historyId': '10'}
        users.messages.return_value.list.return_value.execute.return_value = {'messages': [{'id': 'failed'}]}
        users.messages.return_value.get.return_value.execute.side_effect = OSError('no network')
        with self.assertRaises(RuntimeError):
            sync_full(self.db, api)
        self.assertEqual(self.db.execute('SELECT count(*) FROM sync_state').fetchone()[0], 0)
        self.assertEqual(self.db.execute('SELECT status FROM content').fetchone()[0], 'error')

    def test_label_change_does_not_redownload_original(self):
        save_raw(self.db, 'gmail:me@example.org', 'one', message().as_bytes())
        self.db.execute("INSERT INTO sync_state VALUES ('gmail:me@example.org','10')")
        self.db.commit()
        api = MagicMock()
        users = api.users.return_value
        users.getProfile.return_value.execute.return_value = {'emailAddress': 'me@example.org', 'historyId': '11'}
        users.history.return_value.list.return_value.execute.return_value = {'historyId': '11', 'history': [{'labelsAdded': [{'message': {'id': 'one'}}]}]}
        users.messages.return_value.get.return_value.execute.return_value = {'labelIds': ['IMPORTANT']}
        sync_full(self.db, api)
        users.messages.return_value.get.assert_called_once_with(userId='me', id='one', format='minimal')
        self.assertEqual(self.db.execute('SELECT protected FROM messages').fetchone()[0], 1)
