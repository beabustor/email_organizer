import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from email_organizer.core import connect
from email_organizer.content import save_raw
from email_organizer.plans import create, approve, apply
from email_organizer.semantic import fit
from email_organizer.cleanup import candidate, load
from test_content import message


class PlansTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.db = connect(self.folder / 'test.sqlite')
        self.addCleanup(self.db.close)
        for identifier in ('one', 'two'):
            save_raw(self.db, 'gmail:me@example.org', identifier, message('Cocina recetas ingredientes gastronomía horno').as_bytes())
        fit(self.db, self.folder / 'model')
        self.identifier = create(self.db, self.folder / 'plans')
        self.api = MagicMock()
        self.users = self.api.users.return_value
        self.users.getProfile.return_value.execute.return_value = {'emailAddress': 'me@example.org'}
        self.label_map, self.message_labels = {}, {'one': {'INBOX', 'PREEXISTING'}, 'two': {'INBOX'}}
        self.users.labels.return_value.list.return_value.execute.side_effect = lambda **kw: {'labels': [{'name': name, 'id': key} for name, key in self.label_map.items()]}
        def make_label(**kwargs):
            name = kwargs['body']['name']
            identifier = 'Label' + str(len(self.label_map))
            self.label_map[name] = identifier
            return MagicMock(**{'execute.return_value': {'id': identifier}})
        self.users.labels.return_value.create.side_effect = make_label
        self.users.messages.return_value.get.side_effect = lambda **kwargs: MagicMock(**{'execute.return_value': {'labelIds': list(self.message_labels[kwargs['id']])}})
        def modify(**kwargs):
            labels = self.message_labels[kwargs['id']]
            body = kwargs['body']
            def execute(**kw):
                labels.update(body.get('addLabelIds', []))
                labels.difference_update(body.get('removeLabelIds', []))
                return {}
            return MagicMock(**{'execute.side_effect': execute})
        self.users.messages.return_value.modify.side_effect = modify

    def test_requires_approval_and_correct_account(self):
        with self.assertRaises(ValueError):
            apply(self.db, self.api, self.identifier)
        approve(self.db, self.identifier, all_rows=True)
        self.users.getProfile.return_value.execute.return_value = {'emailAddress': 'other@example.org'}
        with self.assertRaises(ValueError):
            apply(self.db, self.api, self.identifier)
        self.users.messages.return_value.modify.assert_not_called()

    def test_cap_repeat_and_undo_preserves_existing(self):
        approve(self.db, self.identifier, all_rows=True)
        self.assertEqual(apply(self.db, self.api, self.identifier, max_changes=1), 1)
        self.assertEqual(apply(self.db, self.api, self.identifier, max_changes=1), 1)
        self.assertEqual(apply(self.db, self.api, self.identifier), 0)
        self.assertTrue(any(x.endswith('/Candidatos a borrar') for x in self.label_map))
        self.assertEqual(apply(self.db, self.api, self.identifier, undo=True), 2)
        self.assertEqual(self.message_labels['one'], {'INBOX', 'PREEXISTING'})
        self.assertEqual(self.message_labels['two'], {'INBOX'})
        self.users.messages.return_value.delete.assert_not_called()
        self.users.messages.return_value.trash.assert_not_called()

    def test_starred_remote_skipped(self):
        approve(self.db, self.identifier, all_rows=True)
        self.message_labels['one'].add('STARRED')
        self.assertEqual(apply(self.db, self.api, self.identifier), 1)
        self.assertEqual(self.db.execute("SELECT state FROM operations WHERE id='one'").fetchone()[0], 'skipped')

    def test_crash_after_remote_write_recovers(self):
        approve(self.db, self.identifier, all_rows=True)
        original = self.users.messages.return_value.modify.side_effect
        crashed = False
        def crash(**kwargs):
            request = original(**kwargs)
            def execute(**kw):
                nonlocal crashed
                request.execute()
                if not crashed:
                    crashed = True
                    raise OSError('simulated crash after remote success')
                return {}
            return MagicMock(**{'execute.side_effect': execute})
        self.users.messages.return_value.modify.side_effect = crash
        with self.assertRaises(OSError):
            apply(self.db, self.api, self.identifier, max_changes=1)
        self.assertEqual(self.db.execute("SELECT state FROM operations WHERE id='one'").fetchone()[0], 'inflight')
        self.users.messages.return_value.modify.side_effect = original
        self.assertEqual(apply(self.db, self.api, self.identifier, max_changes=1), 1)
        self.assertEqual(apply(self.db, self.api, self.identifier, undo=True), 1)
        self.assertEqual(self.message_labels['one'], {'INBOX', 'PREEXISTING'})

    def test_sensitive_body_blocks_cleanup_and_newsletter_has_reason(self):
        from email_organizer.semantic import load_documents
        item = message('Recetas ingredientes cocina horno consejos culinarios')
        item['List-Unsubscribe'] = '<mailto:leave@example.org>'
        save_raw(self.db, 'gmail:me@example.org', 'old-news', item.as_bytes())
        row = next(r for r in load_documents(self.db) if r['id'] == 'old-news')
        self.assertTrue(candidate(row, load())[0])
        item.set_content('Factura médica con importe importante')
        save_raw(self.db, 'gmail:me@example.org', 'sensitive', item.as_bytes())
        row = next(r for r in load_documents(self.db) if r['id'] == 'sensitive')
        self.assertFalse(candidate(row, load())[0])

    def test_mutated_hash_cannot_be_approved(self):
        self.db.execute("UPDATE operations SET proposal_hash='changed' WHERE plan_id=?", (self.identifier,))
        self.db.commit()
        with self.assertRaises(ValueError):
            approve(self.db, self.identifier, all_rows=True)

    def test_changed_actions_rejected_even_with_original_hash(self):
        approve(self.db, self.identifier, all_rows=True)
        self.db.execute('UPDATE operations SET labels=? WHERE plan_id=?', (json.dumps(['Organizador/Changed']), self.identifier))
        self.db.commit()
        with self.assertRaises(ValueError):
            apply(self.db, self.api, self.identifier)
        self.users.messages.return_value.modify.assert_not_called()
