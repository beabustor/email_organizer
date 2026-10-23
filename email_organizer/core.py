import sqlite3
import os
from pathlib import Path


def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    new_file = not Path(path).exists()
    db = sqlite3.connect(path)
    if new_file and os.name != 'nt':
        Path(path).chmod(0o600)
    db.row_factory = sqlite3.Row
    db.executescript('''
      CREATE TABLE IF NOT EXISTS messages (
        source TEXT, id TEXT, sender TEXT, subject TEXT, date TEXT,
        unsubscribe TEXT, precedence TEXT, protected INTEGER,
        category TEXT, candidate INTEGER, reason TEXT, approved INTEGER DEFAULT 0,
        applied INTEGER DEFAULT 0, PRIMARY KEY(source,id));
      CREATE TABLE IF NOT EXISTS events (
        timestamp TEXT, source TEXT, id TEXT, action TEXT, detail TEXT);
      CREATE TABLE IF NOT EXISTS ai_cache (cache_key TEXT PRIMARY KEY, result TEXT);
      CREATE TABLE IF NOT EXISTS content (
        source TEXT, id TEXT, raw BLOB, text TEXT, main_text TEXT, attachments TEXT,
        content_hash TEXT, status TEXT, error TEXT, thread_id TEXT, parser_version TEXT,
        PRIMARY KEY(source,id));
      CREATE TABLE IF NOT EXISTS sync_state (source TEXT PRIMARY KEY, history_id TEXT);
      CREATE TABLE IF NOT EXISTS semantic_results (
        source TEXT, id TEXT, model_version TEXT, content_hash TEXT, labels TEXT,
        score REAL, status TEXT, PRIMARY KEY(source,id));
      CREATE TABLE IF NOT EXISTS plans (
        id TEXT PRIMARY KEY, created TEXT, source TEXT, state TEXT, digest TEXT);
      CREATE TABLE IF NOT EXISTS operations (
        plan_id TEXT, source TEXT, id TEXT, proposal_hash TEXT, content_hash TEXT,
        labels TEXT, approved INTEGER DEFAULT 0, state TEXT DEFAULT 'pending',
        added TEXT, error TEXT, PRIMARY KEY(plan_id,source,id));
      CREATE INDEX IF NOT EXISTS operations_message ON operations(source,id,state);
    ''')
    columns = {row[1] for row in db.execute('PRAGMA table_info(messages)')}
    for name, definition in {'topic': 'TEXT', 'entity': "TEXT DEFAULT ''", 'confidence': 'REAL', 'topic_reason': 'TEXT'}.items():
        if name not in columns:
            db.execute(f'ALTER TABLE messages ADD COLUMN {name} {definition}')
    db.commit()
    semantic_columns = {row[1] for row in db.execute('PRAGMA table_info(semantic_results)')}
    for name, definition in {'cleanup_reason': "TEXT DEFAULT ''", 'size_bytes': 'INTEGER DEFAULT 0'}.items():
        if name not in semantic_columns:
            db.execute(f'ALTER TABLE semantic_results ADD COLUMN {name} {definition}')
    db.commit()
    return db



def store(db, source, identifier, metadata):
    db.execute('''INSERT INTO messages (source,id,sender,subject,date,unsubscribe,precedence,protected)
        VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(source,id) DO UPDATE SET
        sender=excluded.sender,subject=excluded.subject,date=excluded.date,unsubscribe=excluded.unsubscribe,
        precedence=excluded.precedence,protected=excluded.protected''',
        (source, identifier, *[metadata[k] for k in ('sender', 'subject', 'date', 'unsubscribe', 'precedence', 'protected')]))
