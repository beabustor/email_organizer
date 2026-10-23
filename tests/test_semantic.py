import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from email_organizer.core import connect
from email_organizer.content import save_raw
from email_organizer.semantic import fit, classify, neural_vectors
from email_organizer.plans import create, approve
from email_organizer.evaluation import evaluate
from test_content import message


class SemanticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.db = connect(self.folder / 'test.sqlite')
        self.addCleanup(self.db.close)

    def populate(self):
        for i in range(16):
            text = ('Factura contabilidad banco impuestos importe euros' if i < 8 else 'Viaje turismo hotel playa vacaciones avión') + f' ejemplo {i}'
            save_raw(self.db, 'local', str(i), message(text).as_bytes())
        save_raw(self.db, 'local', 'empty', b'Subject: Empty\n\n')

    def test_full_body_not_just_identical_subject_and_coverage(self):
        self.populate()
        metadata = fit(self.db, self.folder / 'model', max_topics=2)
        self.assertEqual(metadata['analyzed_messages'], 16)
        self.assertEqual(self.db.execute('SELECT count(*) FROM semantic_results').fetchone()[0], 17)
        rows = self.db.execute('SELECT id,labels,status FROM semantic_results').fetchall()
        labels = {r['id']: json.loads(r['labels']) for r in rows}
        self.assertNotEqual(labels['0'], labels['9'])
        self.assertEqual(labels['empty'], ['Organizador/Revision necesaria'])
        classify(self.db, self.folder / 'model')
        self.assertEqual(self.db.execute('SELECT count(*) FROM semantic_results').fetchone()[0], 17)

    def test_new_mail_uses_frozen_structure(self):
        self.populate()
        metadata = fit(self.db, self.folder / 'model', max_topics=2)
        save_raw(self.db, 'local', 'new', message('Factura banco contabilidad importe euros').as_bytes())
        classify(self.db, self.folder / 'model')
        row = self.db.execute("SELECT * FROM semantic_results WHERE id='new'").fetchone()
        self.assertEqual(row['model_version'], metadata['version'])
        self.assertTrue(json.loads(row['labels']))

    def test_long_neural_text_all_tokens_and_cache(self):
        import numpy as np
        class Tokenizer:
            def encode(self, text, **kwargs):
                return list(range(len(text.split())))
            def decode(self, tokens, **kwargs):
                return ' '.join(str(t) for t in tokens)
        class Encoder:
            tokenizer = Tokenizer()
            max_seq_length = 32
            def __init__(self):
                self.tokens = []
            def encode(self, chunks, **kwargs):
                self.tokens += [int(t) for c in chunks for t in c.split()]
                return np.array([[1., 0.] for _ in chunks])
        model = Encoder()
        def encode(model, slices):
            model.tokens += [t for chunk in slices for t in chunk]
            return np.array([[1., 0.] for _ in slices])
        with patch('email_organizer.semantic.neural_encoder', return_value=model), patch('email_organizer.semantic.encode_token_chunks', side_effect=encode):
            vectors = neural_vectors(['word ' * 1001], 'test', self.folder)
            self.assertEqual(model.tokens, list(range(1001)))
            self.assertEqual(vectors.shape, (1, 2))
            neural_vectors(['word ' * 1001], 'test', self.folder)
            self.assertEqual(len(model.tokens), 1001)

    def test_report_escapes_html_and_csv_and_human_evaluation(self):
        item = message('Texto de turismo hotel playa')
        item.replace_header('Subject', '=HYPERLINK("x") <script>alert(1)</script>')
        save_raw(self.db, 'local', '1', item.as_bytes())
        fit(self.db, self.folder / 'model')
        identifier = create(self.db, self.folder / 'plans')
        report = (self.folder / 'plans' / (identifier + '.html')).read_text()
        self.assertNotIn('<script>alert', report)
        path = self.folder / 'plans' / (identifier + '.csv')
        with path.open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        self.assertTrue(rows[0]['asunto'].startswith("'="))
        rows[0]['etiquetas_correctas'] = rows[0]['etiquetas']
        with path.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
        result = evaluate(self.db, path)
        self.assertEqual(result['exact_match'], 1.)
        self.assertFalse(result['independent_test'])
        self.assertLess(result['exact_match_interval_95'][0], 1.)

    def test_stale_plan_rejected(self):
        self.populate()
        fit(self.db, self.folder / 'model')
        identifier = create(self.db, self.folder / 'plans')
        save_raw(self.db, 'local', '0', message('Cuerpo modificado').as_bytes())
        with self.assertRaises(ValueError):
            approve(self.db, identifier, all_rows=True)

    def test_no_content_stops_instead_of_claiming_analysis(self):
        with self.assertRaises(ValueError):
            fit(self.db, self.folder / 'model')

    def test_image_only_mail_has_explicit_review_result(self):
        save_raw(self.db, 'local', 'image-only', b'Content-Type: image/png\nContent-Transfer-Encoding: base64\n\naGVsbG8=')
        result = fit(self.db, self.folder / 'model')
        self.assertEqual(result['analyzed_messages'], 0)
        row = self.db.execute('SELECT * FROM semantic_results').fetchone()
        self.assertEqual(row['status'], 'review')
        self.assertEqual(json.loads(row['labels']), ['Organizador/Revision necesaria'])
