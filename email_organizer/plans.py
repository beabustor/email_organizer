"""Planes inmutables, aprobación ligada al contenido, aplicación y reversión."""
import csv
import hashlib
import html
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def proposal(row):
    return digest([row['source'], row['id'], row['model_version'], row['content_hash'], json.loads(row['labels'])])


def create(db, folder, source=None):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    rows = db.execute('''SELECT s.* FROM semantic_results s JOIN content c ON c.source=s.source AND c.id=s.id
        WHERE c.status NOT IN ('deleted','error')''' + (' AND s.source=?' if source else '') + ' ORDER BY s.source,s.id', (source,) if source else ()).fetchall()
    if not rows:
        raise ValueError('No hay resultados semánticos. Ejecuta analyze primero.')
    sources = {r['source'] for r in rows}
    if len(sources) != 1:
        raise ValueError('Crea un plan para una sola cuenta con --source')
    identifier = secrets.token_hex(12)
    hashes = [proposal(row) for row in rows]
    with db:
        db.execute('INSERT INTO plans VALUES (?,?,?,?,?)', (identifier, datetime.now(timezone.utc).isoformat(), next(iter(sources)), 'draft', digest(hashes)))
        for row, hashed in zip(rows, hashes):
            db.execute('''INSERT INTO operations(plan_id,source,id,proposal_hash,content_hash,labels) VALUES (?,?,?,?,?,?)''',
                       (identifier, row['source'], row['id'], hashed, row['content_hash'], row['labels']))
    report(db, identifier, folder)
    return identifier


def check(db, operation):
    row = db.execute('SELECT * FROM semantic_results WHERE source=? AND id=?', (operation['source'], operation['id'])).fetchone()
    content = db.execute('SELECT * FROM content WHERE source=? AND id=?', (operation['source'], operation['id'])).fetchone()
    if not row or proposal(row) != operation['proposal_hash'] or row['labels'] != operation['labels'] or not content or (content['content_hash'] or '') != operation['content_hash'] or content['status'] in ('deleted', 'error'):
        raise ValueError('Plan obsoleto o mensaje no disponible: vuelve a analizar y revisar un plan nuevo.')
    labels = json.loads(operation['labels'])
    if not isinstance(labels, list) or not labels or len(labels) > 8 or any(not isinstance(name, str) or not name.startswith('Organizador/') or len(name) > 240 or any(ord(c) < 32 for c in name) for name in labels):
        raise ValueError('Etiquetas fuera de los límites permitidos')


def report(db, identifier, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    rows = db.execute('''SELECT o.*,m.sender,m.subject,s.status,s.score,s.cleanup_reason,s.size_bytes,c.status AS content_status,c.attachments,c.text
        FROM operations o JOIN messages m ON m.source=o.source AND m.id=o.id
        JOIN semantic_results s ON s.source=o.source AND s.id=o.id
        LEFT JOIN content c ON c.source=o.source AND c.id=o.id WHERE plan_id=? ORDER BY o.source,o.id''', (identifier,)).fetchall()
    path = folder / (identifier + '.csv')
    def safe(value):
        value = str(value)
        return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['plan', 'source', 'id', 'proposal_hash', 'remitente', 'asunto', 'etiquetas', 'estado', 'similitud_no_probabilidad', 'contenido', 'motivo_limpieza', 'bytes_original', 'aprobar', 'etiquetas_correctas', 'idioma'])
        for row in rows:
            writer.writerow([identifier, row['source'], row['id'], row['proposal_hash'], safe(row['sender']), safe(row['subject']), safe(' | '.join(json.loads(row['labels']))), row['status'], row['score'], row['content_status'], safe(row['cleanup_reason']), row['size_bytes'], '', '', ''])
    counts = {}
    for row in rows:
        for label in json.loads(row['labels']):
            counts[label] = counts.get(label, 0) + 1
    summary = ''.join(f'<li>{html.escape(name)}: {count}</li>' for name, count in sorted(counts.items()))
    entries = ''.join('<tr>' + ''.join(f'<td>{html.escape(str(value))}</td>' for value in (r['sender'], r['subject'], ' | '.join(json.loads(r['labels'])), r['content_status'], r['status'], round(r['score'], 3), r['cleanup_reason'])) + '<td><details><summary>Texto (primeros 1500 caracteres)</summary>' + html.escape((r['text'] or '')[:1500]) + '</details></td></tr>' for r in rows)
    candidate_bytes = sum(r['size_bytes'] for r in rows if any(name.endswith('/Candidatos a borrar') for name in json.loads(r['labels'])))
    content = f'''<!doctype html><html lang="es"><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>Plan de organización</title><style>body{{font:16px system-ui;margin:2rem}}td,th{{padding:.6rem;border:1px solid #ddd;text-align:left}}table{{border-collapse:collapse}}li{{margin:.3rem}}</style>
<h1>Plan de organización local</h1><p>Plan {identifier}. {len(rows)} mensajes con resultado.
Previsualización generada antes de aplicar; no es una vista en vivo de Gmail. La similitud no es precisión medida. Revisión necesaria es una clasificación pendiente de decisión humana.
Los adjuntos se conservan en el original, pero no se han interpretado.</p><ul>{summary}</ul>
<p>Tamaño de originales candidatos: {candidate_bytes / 1024**2:.2f} MiB, sin contar dos veces mensajes multietiqueta. No es ahorro real ni una estimación de CO₂: no se ha borrado nada y hay copia local.</p>
<p>Abre el CSV del mismo nombre para aprobar filas o aportar etiquetas correctas para evaluación. No publiques estos archivos: contienen datos privados.</p>
<table><tr><th>Remitente</th><th>Asunto</th><th>Etiquetas propuestas</th><th>Contenido</th><th>Estado</th><th>Similitud</th><th>Limpieza</th><th>Ejemplo</th></tr>{entries}</table></html>'''
    (folder / (identifier + '.html')).write_text(content, encoding='utf-8')
    return path


def approve(db, identifier, csv_file=None, all_rows=False):
    plan = db.execute('SELECT * FROM plans WHERE id=?', (identifier,)).fetchone()
    if not plan:
        raise ValueError('No existe el plan')
    ops = db.execute('SELECT * FROM operations WHERE plan_id=?', (identifier,)).fetchall()
    if digest([op['proposal_hash'] for op in sorted(ops, key=lambda r: (r['source'], r['id']))]) != plan['digest']:
        raise ValueError('El plan fue modificado; crea otro')
    chosen = set()
    if csv_file:
        with open(csv_file, newline='', encoding='utf-8-sig') as stream:
            for row in csv.DictReader(stream):
                if row['aprobar'].strip().casefold() in ('si', 'sí'):
                    if row['plan'] != identifier:
                        raise ValueError('CSV de otro plan')
                    chosen.add((row['source'], row['id'], row['proposal_hash']))
    pending = [o for o in ops if o['state'] == 'pending']
    selected = [o for o in pending if all_rows or (o['source'], o['id'], o['proposal_hash']) in chosen]
    if not all_rows and len(selected) != len(chosen):
        raise ValueError('CSV obsoleto o contiene IDs/hashes desconocidos')
    for op in selected:
        check(db, op)
    with db:
        for op in selected:
            db.execute('UPDATE operations SET approved=1 WHERE plan_id=? AND source=? AND id=?', (identifier, op['source'], op['id']))
        db.execute("UPDATE plans SET state='approved' WHERE id=?", (identifier,))
    return len(selected)


def apply(db, api, identifier, max_changes=100, undo=False):
    from .gmail import execute
    if not 1 <= max_changes <= 1000:
        raise ValueError('Máximo de cambios debe estar entre 1 y 1000')
    plan = db.execute('SELECT * FROM plans WHERE id=?', (identifier,)).fetchone()
    if not plan:
        raise ValueError('Plan inexistente')
    users = api.users()
    source = 'gmail:' + execute(users.getProfile(userId='me'))['emailAddress']
    if source != plan['source']:
        raise ValueError('La cuenta conectada no coincide con el plan')
    if not undo and plan['state'] not in ('approved', 'applying'):
        raise ValueError('El plan no está aprobado o ya se ha iniciado su reversión')
    states = ('applied', 'inflight', 'undoing') if undo else ('pending', 'inflight')
    placeholders = ','.join('?' for _ in states)
    ops = db.execute(f'''SELECT * FROM operations WHERE plan_id=? AND approved=1 AND state IN ({placeholders})
        ORDER BY source,id LIMIT ?''', (identifier, *states, max_changes)).fetchall()
    if not undo:
        for op in ops:
            check(db, op)
    labels = {x['name']: x['id'] for x in execute(users.labels().list(userId='me')).get('labels', [])}
    if undo:
        with db:
            db.execute("UPDATE plans SET state='undoing' WHERE id=?", (identifier,))
    changed = 0
    for op in ops:
        current = execute(users.messages().get(userId='me', id=op['id'], format='minimal'))
        existing = set(current.get('labelIds', []))
        if not undo and existing & {'STARRED', 'IMPORTANT', 'SENT', 'DRAFT', 'TRASH', 'SPAM'}:
            with db:
                db.execute("UPDATE operations SET state='skipped',error='Mensaje protegido' WHERE plan_id=? AND source=? AND id=?", (identifier, source, op['id']))
            continue
        if undo:
            intended = json.loads(op['added'] or '[]')
            removals = [label for label in intended if label in existing]
            with db:
                db.execute("UPDATE operations SET state='undoing' WHERE plan_id=? AND source=? AND id=?", (identifier, source, op['id']))
            if removals:
                execute(users.messages().modify(userId='me', id=op['id'], body={'removeLabelIds': removals}))
            state, additions = 'undone', intended
        else:
            names = json.loads(op['labels'])
            hierarchy = dict.fromkeys('/'.join(name.split('/')[:i]) for name in names for i in range(1, len(name.split('/')) + 1))
            # Cada grupo temático ofrece su subcarpeta de limpieza, aunque esté vacía.
            for name in names:
                if name.startswith('Organizador/Temas/') and not name.endswith('/Candidatos a borrar'):
                    hierarchy[name + '/Candidatos a borrar'] = None
            if len(labels) + len(set(hierarchy) - labels.keys()) > 900:
                raise ValueError('Demasiadas etiquetas; simplifica la estructura antes de aplicar')
            for name in hierarchy:
                if name not in labels:
                    labels[name] = execute(users.labels().create(userId='me', body={'name': name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}))['id']
            additions = json.loads(op['added']) if op['state'] == 'inflight' else [labels[name] for name in names if labels[name] not in existing]
            # Intento durable ANTES de modificar Gmail: recuperación idempotente tras fallo.
            with db:
                db.execute("UPDATE operations SET state='inflight',added=? WHERE plan_id=? AND source=? AND id=?", (json.dumps(additions), identifier, source, op['id']))
                db.execute("UPDATE plans SET state='applying' WHERE id=?", (identifier,))
            missing = [label for label in additions if label not in existing]
            if missing:
                execute(users.messages().modify(userId='me', id=op['id'], body={'addLabelIds': missing}))
            state = 'applied'
        with db:
            db.execute('UPDATE operations SET state=? WHERE plan_id=? AND source=? AND id=?', (state, identifier, source, op['id']))
            db.execute('INSERT INTO events VALUES (?,?,?,?,?)', (datetime.now(timezone.utc).isoformat(), source, op['id'], state, json.dumps({'plan': identifier, 'labels': additions})))
        changed += 1
        if changed % 50 == 0:
            print(f'{changed}/{len(ops)} operaciones', flush=True)
    print(f'{changed} operaciones completadas; máximo de esta ejecución: {max_changes}. Sin borrar ni archivar correos.', flush=True)
    return changed
