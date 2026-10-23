"""API opcional para nombrar grupos ya descubiertos; nunca ejecuta acciones."""
import hashlib
import json
import os
import urllib.request


def _send(provider, model, payload, system):
    key = os.environ.get('EMAIL_ORGANIZER_AI_KEY')
    if not key:
        raise ValueError('Falta EMAIL_ORGANIZER_AI_KEY; introdúcela en tu entorno local, nunca en Git.')
    content = json.dumps(payload, ensure_ascii=False)
    if provider == 'openai':
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {'Authorization': 'Bearer ' + key}
        body = {'model': model, 'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': content}], 'response_format': {'type': 'json_object'}}
    elif provider == 'anthropic':
        url = 'https://api.anthropic.com/v1/messages'
        headers = {'x-api-key': key, 'anthropic-version': '2023-06-01'}
        body = {'model': model, 'max_tokens': 4096, 'system': system, 'messages': [{'role': 'user', 'content': content}]}
    else:
        raise ValueError('Proveedor no admitido')
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', **headers}, method='POST')
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.load(response)
    text = result['choices'][0]['message']['content'] if provider == 'openai' else ''.join(x.get('text', '') for x in result['content'] if x['type'] == 'text')
    return json.loads(text)
