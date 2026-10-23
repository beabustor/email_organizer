import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from email_organizer.core import connect
from email_organizer.content import save_raw
from email_organizer.semantic import fit
from email_organizer.plans import create, approve
from email_organizer.automation import authorize, refresh
from email_organizer.naming import name_topics
from test_content import message


class AdvancedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.db = connect(self.folder / 'test.sqlite')
        self.addCleanup(self.db.close)
        self.source = 'gmail:me@example.org'
        for i in range(4):
            save_raw(self.db, self.source, str(i), message('Montaña senderismo bosque naturaleza ruta').as_bytes())
        self.model_dir = self.folder / 'model'
        self.meta = fit(self.db, self.model_dir, self.source, max_topics=1)
        self.plan = create(self.db, self.folder / 'plans')
        approve(self.db, self.plan, all_rows=True)

    def test_naming_changes_version_and_invalidates_old_plans(self):
        def sender(provider, model, payload, prompt):
            return {'names': [{'id': t['id'], 'path': 'Ocio/Senderismo'} for t in payload['topics']]}
        version = name_topics(self.db, self.model_dir, 'openai', 'test', sender=sender)
        self.assertNotEqual(version, self.meta['version'])
        self.assertTrue((self.model_dir / version / 'ontology.skos.jsonld').exists())
        with self.assertRaises(ValueError):
            approve(self.db, self.plan, all_rows=True)

    def test_naming_invalid_path_leaves_active_model(self):
        def sender(*args):
            return {'names': [{'id': 0, 'path': '../../escape'}]}
        with self.assertRaises(ValueError):
            name_topics(self.db, self.model_dir, 'openai', 'test', sender=sender)
        self.assertEqual(json.loads((self.model_dir / 'active.json').read_text())['version'], self.meta['version'])

    def test_policy_only_new_known_noncleanup_results(self):
        path = self.folder / 'policy.json'
        policy = authorize(self.db, self.plan, path)
        self.assertFalse(policy['quality_proven'])
        save_raw(self.db, self.source, 'new', message('Senderismo montaña bosque naturaleza').as_bytes())
        with patch('email_organizer.content.sync_full', return_value=self.source), patch('email_organizer.plans.apply', return_value=1) as apply:
            identifier = refresh(self.db, MagicMock(), self.model_dir, path, MagicMock())
        applied = self.db.execute('SELECT id FROM operations WHERE plan_id=? AND approved=1', (identifier,)).fetchall()
        self.assertEqual([row['id'] for row in applied], ['new'])
        apply.assert_called_once()

    def test_policy_wrong_version_does_not_apply(self):
        path = self.folder / 'policy.json'
        policy = authorize(self.db, self.plan, path)
        policy['version'] = 'changed'
        path.write_text(json.dumps(policy))
        with patch('email_organizer.content.sync_full', return_value=self.source), patch('email_organizer.plans.apply') as apply:
            with self.assertRaises(ValueError):
                refresh(self.db, MagicMock(), self.model_dir, path, MagicMock())
        apply.assert_not_called()
