"""OAuth de escritorio. Tokens exclusivamente en el llavero del sistema."""
import json

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
ACCOUNT = 'default'


def service(credentials_file, writable=True):
    import keyring
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    backend = type(keyring.get_keyring()).__module__
    if not backend.startswith(('keyring.backends.macOS', 'keyring.backends.Windows', 'keyring.backends.SecretService', 'keyring.backends.kwallet')):
        raise RuntimeError('Configura un llavero seguro del sistema; no se guardarán tokens en texto plano.')
    scopes = SCOPES if writable else ['https://www.googleapis.com/auth/gmail.readonly']
    account = ACCOUNT if writable else 'readonly'
    saved = keyring.get_password('email-organizer', account)
    creds = Credentials.from_authorized_user_info(json.loads(saved), scopes) if saved else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
        creds = flow.run_local_server(host='localhost', port=0)
    keyring.set_password('email-organizer', account, creds.to_json())
    return build('gmail', 'v1', credentials=creds, cache_discovery=False)


def execute(request):
    # Cliente oficial: reintentos con backoff para 429 y errores transitorios.
    return request.execute(num_retries=5)
