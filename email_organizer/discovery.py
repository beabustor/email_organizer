"""Descubrir la estructura antes de clasificar: cobertura medible y borrador revisable."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from .taxonomy import domain


def inventory(db):
    senders, groups = Counter(), Counter()
    total = 0
    for row in db.execute('SELECT sender,subject FROM messages ORDER BY source,id'):
        sender_domain = domain(row['sender']) or '(desconocido)'
        senders[sender_domain] += 1
        groups[(sender_domain, row['subject'][:300])] += 1
        total += 1
    return {'total_messages': total, 'domains': dict(senders.most_common()),
            'groups': [{'domain': d, 'subject': s, 'count': n} for (d, s), n in groups.most_common()],
            'scope': 'Todas las cabeceras importadas; asuntos truncados a 300 caracteres. Sin cuerpos ni adjuntos.'}


def validate_topics(topics):
    if not isinstance(topics, dict) or not 1 <= len(topics) <= 60:
        raise ValueError('La ontología debe tener entre 1 y 60 hojas')
    for name, words in topics.items():
        parts = name.split('/')
        if len(parts) != 2 or any(not p.strip() or len(p) > 60 or any(ord(c) < 32 for c in p) for p in parts):
            raise ValueError('Cada temática debe tener dos niveles Tema/Subtema, sin caracteres de control')
        if not isinstance(words, list) or any(not isinstance(w, str) or not w.strip() or len(w) > 100 for w in words):
            raise ValueError('Palabras clave no válidas')
    return topics


def discover(db, provider, model, output, max_calls=10, batch_size=50, requester=None):
    from .ai import request_ontology
    requester = requester or request_ontology
    if max_calls < 1 or not 1 <= batch_size <= 100:
        raise ValueError('Se necesita al menos una llamada y lotes de 1 a 100 grupos')
    info = inventory(db)
    groups = info['groups']
    fingerprint = hashlib.sha256(json.dumps(groups, sort_keys=True).encode()).hexdigest()
    path = Path(output)
    state = {'fingerprint': fingerprint, 'provider': provider, 'model': model, 'processed_groups': 0,
             'processed_messages': 0, 'total_messages': info['total_messages'], 'total_groups': len(groups),
             'topics': {}, 'complete_headers': False, 'scope': info['scope'], 'review_required': True}
    if path.exists():
        saved = json.loads(path.read_text(encoding='utf-8'))
        if any(saved.get(k) != state[k] for k in ('fingerprint', 'provider', 'model')):
            raise ValueError('El histórico o modelo ha cambiado. Usa otro archivo de salida para un análisis nuevo.')
        state = saved
    calls = 0
    while state['processed_groups'] < len(groups) and calls < max_calls:
        start = state['processed_groups']
        batch = groups[start:start + batch_size]
        result = requester(provider, model, {'previous_topics': state['topics'], 'groups': batch})
        topics = validate_topics(result['topics'])
        state.update(topics=topics, processed_groups=start + len(batch),
                     processed_messages=state['processed_messages'] + sum(g['count'] for g in batch))
        state['complete_headers'] = state['processed_groups'] == len(groups)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(path)
        calls += 1
        print(f'Ontología: {state["processed_messages"]}/{info["total_messages"]} mensajes representados; {calls}/{max_calls} llamadas. Borrador, no clasificación.', flush=True)
    return state
