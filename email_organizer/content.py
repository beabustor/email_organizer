"""Extracción MIME pasiva: nunca abre enlaces ni ejecuta adjuntos."""
import base64
import hashlib
import json
import mailbox
import re
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path

PARSER_VERSION = 'mime-2-attachments'


class PlainHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'head'):
            self.hidden += 1
        if tag in ('br', 'p', 'div', 'li', 'tr'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'head'):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def html_text(value):
    parser = PlainHTML()
    parser.feed(value)
    return ''.join(parser.parts)


def extract(raw):
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    attachments, errors = [], []

    def attached(part):
        from .attachments import extract_attachment
        if len(attachments) >= 20:
            attachments.append({'name': str(part.get_filename() or ''), 'type': part.get_content_type(), 'analyzed': False, 'status': 'limit', 'method': ''})
            return ''
        text, info = extract_attachment(part)
        attachments.append(info)
        return ('\n[Adjunto: ' + info['name'] + ']\n' + text) if text else ''

    def visit(part):
        if part.get_content_disposition() == 'attachment' or part.get_filename():
            return attached(part)
        if part.is_multipart():
            children = list(part.iter_parts())
            # alternative contiene representaciones del mismo contenido, no mensajes distintos.
            if part.get_content_subtype() == 'alternative':
                preferred = sorted(children, key=lambda p: p.get_content_type() != 'text/plain')
                alternatives = []
                for child in preferred:
                    text = visit(child)
                    normalized = ' '.join(text.split())
                    if not normalized:
                        continue
                    if any(normalized in ' '.join(existing.split()) for existing in alternatives):
                        continue
                    # Si HTML contiene más contenido que la versión plana, no perder ese contenido.
                    alternatives = [existing for existing in alternatives if ' '.join(existing.split()) not in normalized]
                    alternatives.append(text)
                return '\n\n'.join(alternatives)
            return '\n'.join(visit(child) for child in children)
        kind = part.get_content_type()
        if kind not in ('text/plain', 'text/html'):
            return attached(part)
        payload = part.get_payload(decode=True) or b''
        try:
            text = payload.decode(part.get_content_charset() or 'utf-8', errors='strict')
        except (LookupError, UnicodeDecodeError):
            errors.append('Codificación inválida; reemplazos UTF-8')
            text = payload.decode('utf-8', errors='replace')
        return html_text(text) if kind == 'text/html' else text

    text = visit(msg).replace('\x00', '')
    text = re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', text).strip()
    # Vista auxiliar; text conserva el cuerpo completo y es lo que analiza el motor.
    main = '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('>'))
    main = re.split(r'(?m)^-- \s*$|^On .+ wrote:\s*$|^El .+ escribió:\s*$', main)[0].strip()
    status = 'partial' if errors or msg.defects or any(not item['analyzed'] for item in attachments) else 'complete'
    if not text:
        status = 'no_text'
    return msg, text, main, attachments, status, '; '.join(errors)


def save_raw(db, source, identifier, raw, thread_id='', protected=None):
    from .cli import metadata
    from .core import store
    msg, text, main, attachments, status, error = extract(raw)
    evidence = hashlib.sha256(raw)
    evidence.update((PARSER_VERSION + text + json.dumps(attachments, sort_keys=True)).encode('utf-8'))
    digest = evidence.hexdigest()
    with db:
        protected_value = protected if protected is not None else ('F' in str(msg.get('X-Status', '')) or str(msg.get('Importance', '')).lower() == 'high')
        store(db, source, identifier, metadata({k.lower(): str(v) for k, v in msg.items()}, protected_value))
        old = db.execute('SELECT content_hash FROM content WHERE source=? AND id=?', (source, identifier)).fetchone()
        db.execute('''INSERT OR REPLACE INTO content VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                   (source, identifier, raw, text, main, json.dumps(attachments), digest, status, error, thread_id or str(msg.get('In-Reply-To', msg.get('Message-ID', identifier))), PARSER_VERSION))
        if not old or old['content_hash'] != digest:
            db.execute('DELETE FROM semantic_results WHERE source=? AND id=?', (source, identifier))
            db.execute('UPDATE operations SET approved=0 WHERE source=? AND id=? AND state=?', (source, identifier, 'pending'))
    return status


def reextract(db, source=None, retry=False):
    where = "c.raw IS NOT NULL AND c.status NOT IN ('deleted','error')"
    params = []
    if not retry:
        where += ' AND c.parser_version!=?'
        params.append(PARSER_VERSION)
    if source:
        where += ' AND c.source=?'
        params.append(source)
    identifiers = db.execute(f'SELECT c.source,c.id FROM content c WHERE {where}', params).fetchall()
    for index, identifier in enumerate(identifiers):
        row = db.execute('''SELECT c.*,m.protected FROM content c JOIN messages m ON m.source=c.source AND m.id=c.id
                         WHERE c.source=? AND c.id=?''', (identifier['source'], identifier['id'])).fetchone()
        save_raw(db, row['source'], row['id'], row['raw'], row['thread_id'], bool(row['protected']))
        if (index + 1) % 100 == 0:
            print(f'Contenido reextraído {index+1}/{len(identifiers)}', flush=True)
    return len(identifiers)


def import_mbox(db, filename):
    path = Path(filename).resolve()
    source = 'mbox:' + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    box = mailbox.mbox(path, create=False)
    count = 0
    try:
        for key in box.iterkeys():
            raw = box.get_bytes(key, from_=False)
            identifier = hashlib.sha256(raw).hexdigest()
            if db.execute('SELECT 1 FROM content WHERE source=? AND id=?', (source, identifier)).fetchone():
                continue
            save_raw(db, source, identifier, raw)
            count += 1
            if count % 200 == 0:
                print(f'MBOX: {count} mensajes completos importados', flush=True)
    finally:
        box.close()
    return source


def sync_full(db, api, include_spam_trash=True):
    """Primera enumeración completa; después history.list y reconciliación si caduca."""
    from .gmail import execute
    users = api.users()
    profile = execute(users.getProfile(userId='me'))
    source = 'gmail:' + profile['emailAddress']
    previous = db.execute('SELECT history_id FROM sync_state WHERE source=?', (source,)).fetchone()
    known = {r['id'] for r in db.execute("SELECT id FROM content WHERE source=? AND status NOT IN ('error','deleted')", (source,))}
    handled = set()
    count = 0

    def fetch(identifier, force=False):
        nonlocal count
        if identifier in handled or (identifier in known and not force):
            return
        try:
            item = execute(users.messages().get(userId='me', id=identifier, format='raw'))
            raw = base64.urlsafe_b64decode(item['raw'] + '=' * (-len(item['raw']) % 4))
            labels = item.get('labelIds', [])
            save_raw(db, source, identifier, raw, item.get('threadId', identifier), bool(set(labels) & {'STARRED', 'IMPORTANT', 'SENT', 'DRAFT'}))
        except Exception as error:
            if getattr(getattr(error, 'resp', None), 'status', None) == 404:
                with db:
                    db.execute("INSERT INTO content(source,id,status) VALUES (?,?,'deleted') ON CONFLICT(source,id) DO UPDATE SET status='deleted'", (source, identifier))
                handled.add(identifier)
                return
            # Un mensaje desaparecido se registra como error de adquisición, no como leído.
            with db:
                db.execute('''INSERT INTO content(source,id,status,error) VALUES (?,?,'error',?)
                    ON CONFLICT(source,id) DO UPDATE SET status='error',error=excluded.error''',
                           (source, identifier, type(error).__name__))
            raise RuntimeError(f'No se pudo importar {identifier}; repite para reanudar (sin avanzar cursor).') from None
        handled.add(identifier)
        count += 1
        if count % 100 == 0:
            print(f'Gmail: {count} mensajes descargados/actualizados', flush=True)

    def refresh_labels(identifier):
        if identifier in handled:
            return
        if identifier not in known:
            fetch(identifier)
            return
        current = execute(users.messages().get(userId='me', id=identifier, format='minimal'))
        with db:
            db.execute('UPDATE messages SET protected=? WHERE source=? AND id=?',
                       (int(bool(set(current.get('labelIds', [])) & {'STARRED', 'IMPORTANT', 'SENT', 'DRAFT'})), source, identifier))
        handled.add(identifier)

    # Reintentar fallos incluso aunque una página de history ya no los incluya.
    for row in db.execute("SELECT id FROM content WHERE source=? AND status='error'", (source,)).fetchall():
        fetch(row['id'], force=True)
    incremental = bool(previous and include_spam_trash)
    token = None
    history_cursor = profile.get('historyId', '')
    if incremental:
        try:
            while True:
                page = execute(users.history().list(userId='me', startHistoryId=previous['history_id'], pageToken=token))
                for event in page.get('history', []):
                    for entry in event.get('messagesAdded', []):
                        fetch(entry['message']['id'])
                    for kind in ('labelsAdded', 'labelsRemoved'):
                        for entry in event.get(kind, []):
                            refresh_labels(entry['message']['id'])
                    for entry in event.get('messagesDeleted', []):
                        with db:
                            db.execute("UPDATE content SET status='deleted' WHERE source=? AND id=?", (source, entry['message']['id']))
                history_cursor = page.get('historyId', history_cursor)
                token = page.get('nextPageToken')
                if not token:
                    break
        except Exception as error:
            if getattr(getattr(error, 'resp', None), 'status', None) != 404:
                raise
            incremental, token = False, None
    if not incremental:
        remote_ids = set()
        while True:
            page = execute(users.messages().list(userId='me', maxResults=500, pageToken=token, includeSpamTrash=include_spam_trash))
            for item in page.get('messages', []):
                remote_ids.add(item['id'])
                fetch(item['id'])
            token = page.get('nextPageToken')
            if not token:
                break
        if include_spam_trash:
            with db:
                for identifier in known - remote_ids:
                    db.execute("UPDATE content SET status='deleted' WHERE source=? AND id=?", (source, identifier))
    if include_spam_trash and history_cursor:
        with db:
            db.execute('INSERT OR REPLACE INTO sync_state VALUES (?,?)', (source, history_cursor))
    total = db.execute('SELECT count(*) FROM content WHERE source=?', (source,)).fetchone()[0]
    print(f'Descarga terminada: {total} registros locales; {count} descargados/actualizados. Revisa la cobertura de adjuntos en el informe.', flush=True)
    return source
