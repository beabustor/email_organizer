import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path


def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript('''
      CREATE TABLE IF NOT EXISTS messages (
        source TEXT, id TEXT, sender TEXT, subject TEXT, date TEXT,
        unsubscribe TEXT, precedence TEXT, protected INTEGER,
        category TEXT, candidate INTEGER, reason TEXT, approved INTEGER DEFAULT 0,
        applied INTEGER DEFAULT 0, PRIMARY KEY(source,id));
      CREATE TABLE IF NOT EXISTS events (
        timestamp TEXT, source TEXT, id TEXT, action TEXT, detail TEXT);
    ''')
    return db


def load_rules(path):
    rules = json.loads(Path(path).read_text(encoding='utf-8'))
    for key in ('newsletter_days', 'notification_days', 'bulk_days'):
        if not isinstance(rules[key], int) or rules[key] < 1:
            raise ValueError(f'{key} debe ser un entero positivo')
    for key in ('protected_words', 'notification_senders', 'protected_senders'):
        if not isinstance(rules[key], list) or any(not isinstance(x, str) or not x.strip() for x in rules[key]):
            raise ValueError(f'{key} debe contener textos no vacíos')
    return rules


def classify(message, rules, now=None):
    now = now or datetime.now(timezone.utc)
    text = (message['sender'] + ' ' + message['subject']).casefold()
    try:
        date = datetime.fromisoformat(message['date'])
        age = (now - date).days if date.tzinfo else None
    except (ValueError, TypeError):
        age = None
    if message['protected'] or any(w.casefold() in text for w in rules['protected_words']) or any(s.casefold() in message['sender'].casefold() for s in rules['protected_senders']):
        return 'Conservar', False, 'Destacado, importante o posible documento sensible'
    if message['unsubscribe']:
        category, threshold = 'Newsletters', rules['newsletter_days']
    elif any(s.casefold() in message['sender'].casefold() for s in rules['notification_senders']):
        category, threshold = 'Notificaciones', rules['notification_days']
    elif message['precedence'].casefold() in ('bulk', 'list', 'junk'):
        category, threshold = 'Correo masivo', rules['bulk_days']
    else:
        return 'Otros', False, 'Sin criterio suficiente; conservar para revisión'
    candidate = age is not None and age >= threshold
    return category, candidate, f'{category}; antigüedad {age if age is not None else "desconocida"} días; umbral {threshold}'


def store(db, source, identifier, metadata):
    db.execute('''INSERT OR IGNORE INTO messages
      (source,id,sender,subject,date,unsubscribe,precedence,protected)
      VALUES (?,?,?,?,?,?,?,?)''', (source, identifier, *[metadata[k] for k in ('sender', 'subject', 'date', 'unsubscribe', 'precedence', 'protected')]))


def run(db, rules, batch_size=200):
    if batch_size < 1:
        raise ValueError('El lote debe ser positivo')
    total = db.execute('SELECT count(*) FROM messages WHERE category IS NULL').fetchone()[0]
    done, start = 0, time.monotonic()
    while True:
        rows = db.execute('SELECT * FROM messages WHERE category IS NULL LIMIT ?', (batch_size,)).fetchall()
        if not rows:
            break
        with db:
            for row in rows:
                category, candidate, reason = classify(row, rules)
                db.execute('UPDATE messages SET category=?,candidate=?,reason=? WHERE source=? AND id=?', (category, candidate, reason, row['source'], row['id']))
        done += len(rows)
        rate = done / max(time.monotonic() - start, .001)
        print(f'{done}/{total}; {rate:.1f} correos/s; quedan ~{(total-done)/rate:.1f}s de clasificación local', flush=True)
    return done
