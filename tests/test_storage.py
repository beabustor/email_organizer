import sqlite3
import tempfile
import unittest
from pathlib import Path

from email_organizer.core import connect
from email_organizer.locking import database_lock


class StorageTests(unittest.TestCase):
    def test_existing_legacy_database_migrates_without_loss(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'old.sqlite'
            db = sqlite3.connect(path)
            db.execute('CREATE TABLE messages (source TEXT,id TEXT,sender TEXT,subject TEXT,date TEXT,unsubscribe TEXT,precedence TEXT,protected INTEGER,category TEXT,candidate INTEGER,reason TEXT,approved INTEGER DEFAULT 0,applied INTEGER DEFAULT 0,PRIMARY KEY(source,id))')
            db.execute("INSERT INTO messages(source,id,subject) VALUES ('local','one','Existing')")
            db.commit(); db.close()
            db = connect(path)
            self.assertEqual(db.execute('SELECT subject FROM messages').fetchone()[0], 'Existing')
            self.assertIn('cleanup_reason', {r[1] for r in db.execute('PRAGMA table_info(semantic_results)')})
            db.close()

    def test_parallel_process_lock_and_release(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'db.sqlite'
            with database_lock(path):
                with self.assertRaises(ValueError):
                    with database_lock(path):
                        self.fail('No debe adquirir dos veces')
            with database_lock(path):
                pass
