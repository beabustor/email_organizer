import tempfile
import unittest
from pathlib import Path

from email_organizer.core import connect, store, run, load_rules
from email_organizer.taxonomy import organize, topic_for, TOPICS
from email_organizer.discovery import inventory, discover, validate_topics
from email_organizer.ai import refine


class DiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = connect(Path(self.temp.name) / 'db.sqlite')
        self.addCleanup(self.db.close)
        self.item = dict(sender='Equipo <news@example.org>', subject='Un tema desconocido', date='', unsubscribe='', precedence='', protected=0)
        for i in range(4):
            store(self.db, 'local', str(i), self.item | {'subject': 'Otro tema' if i == 3 else self.item['subject']})
        self.db.commit()
        run(self.db, load_rules('config/criterios.json'))
        organize(self.db, min_entity_messages=2)

    def test_inventory_covers_all_and_groups_duplicates(self):
        info = inventory(self.db)
        self.assertEqual(info['total_messages'], 4)
        self.assertEqual(len(info['groups']), 2)
        self.assertEqual(sum(x['count'] for x in info['groups']), 4)

    def test_ontology_partial_then_resumed_complete(self):
        path = Path(self.temp.name) / 'ontology.json'
        requests = []
        def fake(provider, model, payload):
            requests.append(payload)
            return {'topics': {'Personal/Conversaciones': []}}
        state = discover(self.db, 'openai', 'test', path, max_calls=1, batch_size=1, requester=fake)
        self.assertFalse(state['complete_headers'])
        self.assertEqual(state['processed_messages'], 3)
        state = discover(self.db, 'openai', 'test', path, max_calls=1, batch_size=1, requester=fake)
        self.assertTrue(state['complete_headers'])
        self.assertEqual(state['processed_messages'], 4)
        self.assertTrue(requests[1]['previous_topics'])

    def test_invalid_ontology_rejected(self):
        with self.assertRaises(ValueError):
            validate_topics({'inventada/sin/limite': []})

    def test_topic_and_entity(self):
        self.assertEqual(topic_for(self.item | {'subject': 'Factura mensual'})[0], 'Finanzas/Facturas')
        row = self.db.execute('SELECT * FROM messages LIMIT 1').fetchone()
        self.assertEqual(row['entity'], 'example.org')
        self.assertEqual(row['topic'], 'Pendiente de revision')

    def test_ai_cache_batch_and_no_action_authority(self):
        calls = []
        def fake(provider, model, payload):
            calls.append(payload)
            self.assertNotIn('sender', str(payload))
            return {'results': [{'id': x['id'], 'topic': 'Personal/Conversaciones', 'confidence': .9} for x in payload['messages']]}
        self.assertEqual(refine(self.db, TOPICS, 'openai', 'test', requester=fake), (1, 4))
        self.assertEqual(self.db.execute('SELECT sum(approved) FROM messages').fetchone()[0], 0)
        self.assertEqual(len(calls[0]['messages']), 2)
        organize(self.db, min_entity_messages=2)
        self.assertEqual(refine(self.db, TOPICS, 'openai', 'test', requester=fake), (0, 4))

    def test_ai_rejects_invented_topic_entire_batch(self):
        def fake(provider, model, payload):
            return {'results': [{'id': x['id'], 'topic': 'Borrar/todo', 'confidence': 1} for x in payload['messages']]}
        with self.assertRaises(ValueError):
            refine(self.db, TOPICS, 'openai', 'test', requester=fake)
        self.assertEqual(self.db.execute("SELECT count(*) FROM messages WHERE topic='Pendiente de revision'").fetchone()[0], 4)

    def test_migration_old_database_preserves_messages(self):
        self.assertEqual({r[1] for r in self.db.execute('PRAGMA table_info(messages)')} & {'topic','entity','confidence','topic_reason'}, {'topic','entity','confidence','topic_reason'})
