"""OAuth de escritorio. Tokens exclusivamente en el llavero del sistema."""
import json

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
ACCOUNT = 'default'


def service(credentials_file):
    import keyring
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    backend = type(keyring.get_keyring()).__module__
    if not backend.startswith(('keyring.backends.macOS', 'keyring.backends.Windows', 'keyring.backends.SecretService', 'keyring.backends.kwallet')):
        raise RuntimeError('Configura un llavero seguro del sistema; no se guardarán tokens en texto plano.')
    saved = keyring.get_password('email-organizer', ACCOUNT)
    creds = Credentials.from_authorized_user_info(json.loads(saved), SCOPES) if saved else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
        creds = flow.run_local_server(host='localhost', port=0)
    keyring.set_password('email-organizer', ACCOUNT, creds.to_json())
    return build('gmail', 'v1', credentials=creds, cache_discovery=False)


def execute(request):
    # Cliente oficial: reintentos con backoff para 429 y errores transitorios.
    return request.execute(num_retries=5)


def sync(db, api, metadata):
    from .core import store
    profile = execute(api.users().getProfile(userId='me'))
    source = 'gmail:' + profile['emailAddress']
    token = None
    count = 0
    while True:
        page = execute(api.users().messages().list(userId='me', maxResults=200, pageToken=token, q='-in:trash -in:spam'))
        for item in page.get('messages', []):
            if db.execute('SELECT 1 FROM messages WHERE source=? AND id=?', (source, item['id'])).fetchone():
                continue
            msg = execute(api.users().messages().get(userId='me', id=item['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date', 'List-Unsubscribe', 'Precedence']))
            headers = {h['name'].lower(): h['value'] for h in msg.get('payload', {}).get('headers', [])}
            labels = set(msg.get('labelIds', []))
            with db:
                store(db, source, item['id'], metadata(headers, bool(labels & {'STARRED', 'IMPORTANT', 'SENT', 'DRAFT'})))
            count += 1
        print(f'Gmail: {count} mensajes nuevos importados', flush=True)
        token = page.get('nextPageToken')
        if not token:
            break
    return source


def apply(db, api):
    from datetime import datetime, timezone
    profile = execute(api.users().getProfile(userId='me'))
    source = 'gmail:' + profile['emailAddress']
    labels = {x['name']: x['id'] for x in execute(api.users().labels().list(userId='me')).get('labels', [])}
    rows = db.execute('SELECT * FROM messages WHERE source=? AND approved=1 AND applied=0', (source,)).fetchall()
    for row in rows:
        # Revalidar la protección actual antes de escribir en Gmail.
        current = execute(api.users().messages().get(userId='me', id=row['id'], format='minimal'))
        if set(current.get('labelIds', [])) & {'STARRED', 'IMPORTANT', 'SENT', 'DRAFT', 'TRASH', 'SPAM'}:
            print(f'Omitido mensaje protegido: {row["id"]}')
            continue
        names = ['Organizador/' + row['category']]
        if row['topic']:
            names.append('Organizador/Temas/' + row['topic'])
        if row['entity']:
            names.append('Organizador/Entidades/' + row['entity'])
        if row['candidate']:
            names.append('Organizador/Revisar para borrar')
        # Crear padres de la jerarquía, sin aplicar esos padres al mensaje.
        hierarchy = dict.fromkeys('/'.join(name.split('/')[:i]) for name in names for i in range(1, len(name.split('/')) + 1))
        missing = set(hierarchy) - labels.keys()
        if len(labels) + len(missing) > 900:
            raise RuntimeError('Límite preventivo de 900 etiquetas: revisa la ontología y entidades antes de continuar.')
        for name in hierarchy:
            if name not in labels:
                labels[name] = execute(api.users().labels().create(userId='me', body={'name': name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}))['id']
        additions = [labels[name] for name in names if labels[name] not in current.get('labelIds', [])]
        if additions:
            execute(api.users().messages().modify(userId='me', id=row['id'], body={'addLabelIds': additions}))
        with db:
            db.execute('UPDATE messages SET applied=1 WHERE source=? AND id=?', (source, row['id']))
            db.execute('INSERT INTO events VALUES (?,?,?,?,?)', (datetime.now(timezone.utc).isoformat(), source, row['id'], 'labels_added', json.dumps(additions)))
    print('Etiquetado terminado. Ningún correo se ha borrado ni archivado.')
