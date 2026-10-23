"""Candidatos conservadores y explicables; nunca órdenes de borrado."""
import json
from datetime import datetime, timezone
from pathlib import Path


def load(path=None):
    if path is None:
        path = 'data/cleanup.json' if Path('data/cleanup.json').exists() else 'config/cleanup.json'
    rules = json.loads(Path(path).read_text(encoding='utf-8'))
    for name in ('newsletter_days', 'notification_days'):
        if not isinstance(rules[name], int) or rules[name] < 1:
            raise ValueError('Antigüedad de limpieza inválida')
    for name in ('protected_words', 'protected_senders', 'notification_senders'):
        if not isinstance(rules[name], list) or any(not isinstance(x, str) or not x.strip() for x in rules[name]):
            raise ValueError('Criterios de limpieza no válidos')
    return rules


def candidate(row, rules, now=None):
    text = ((row['subject'] or '') + '\n' + (row['text'] or '')).casefold()
    if row['protected'] or any(x.casefold() in row['sender'].casefold() for x in rules['protected_senders']):
        return False, 'Protegido por importancia o remitente'
    if any(x.casefold() in text for x in rules['protected_words']):
        return False, 'Posible contenido sensible o documento: conservar'
    if row['content_status'] != 'complete':
        return False, 'Contenido incompleto o no interpretable: revisar'
    if rules.get('protect_unanalyzed_attachments', True) and json.loads(row['attachments'] or '[]'):
        return False, 'Tiene adjuntos no analizados: conservar'
    try:
        date = datetime.fromisoformat(row['date'])
        if date.tzinfo is None:
            raise ValueError('Fecha sin zona')
        days = ((now or datetime.now(timezone.utc)) - date).days
    except (ValueError, TypeError):
        return False, 'Antigüedad desconocida'
    if row['unsubscribe'] and days >= rules['newsletter_days']:
        return True, f'Newsletter de {days} días; sin señales de protección detectadas. Requiere revisión.'
    if any(x.casefold() in row['sender'].casefold() for x in rules['notification_senders']) and days >= rules['notification_days']:
        return True, f'Notificación de {days} días; sin señales de protección detectadas. Requiere revisión.'
    return False, 'No cumple criterios conservadores de limpieza'
