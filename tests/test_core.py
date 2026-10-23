import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from email_organizer.core import classify, connect, load_rules, run, store


class RulesTest(unittest.TestCase):
    def setUp(self):
        self.rules = load_rules('config/criterios.json')
        self.now = datetime(2026, 10, 23, tzinfo=timezone.utc)
        self.message = dict(sender='news@example.org', subject='Novedades', date='2020-01-01T00:00:00+00:00', unsubscribe='<https://example.org/unsubscribe>', precedence='', protected=0)

    def test_old_newsletter_candidate(self):
        self.assertEqual(classify(self.message, self.rules, self.now)[:2], ('Newsletters', True))

    def test_protection_overrides_age(self):
        for change in ({'subject': 'Factura mensual'}, {'protected': 1}, {'subject': 'Security alert'}):
            self.assertEqual(classify(self.message | change, self.rules, self.now)[:2], ('Conservar', False))

    def test_missing_date_and_recent_never_candidates(self):
        for date in ('', 'malformed', '2026-10-22T00:00:00+00:00', '2020-01-01T00:00:00'):
            self.assertFalse(classify(self.message | {'date': date}, self.rules, self.now)[1])

    def test_personal_old_mail_kept(self):
        self.assertEqual(classify(self.message | {'unsubscribe': ''}, self.rules, self.now)[:2], ('Otros', False))

    def test_restart_and_duplicate_import_preserve_progress(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'test.sqlite'
            db = connect(path)
            for i in range(5):
                store(db, 'test', str(i), self.message)
            db.commit()
            self.assertEqual(run(db, self.rules, 2), 5)
            db.close()
            db = connect(path)
            store(db, 'test', '0', self.message)
            db.commit()
            self.assertEqual(run(db, self.rules, 2), 0)
            self.assertEqual(db.execute('SELECT count(*) FROM messages').fetchone()[0], 5)
            db.close()


if __name__ == '__main__':
    unittest.main()
