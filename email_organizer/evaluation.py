"""Acuerdo con etiquetas humanas; no confundir con validación independiente."""
import csv
import json
import math


def interval(successes, total):
    if not total:
        return [0., 1.]
    z, p = 1.96, successes / total
    center = (p + z*z / (2*total)) / (1 + z*z / total)
    margin = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / (1 + z*z/total)
    return [max(0., center-margin), min(1., center+margin)]


def evaluate(db, filename):
    pairs, seen, languages = [], set(), []
    with open(filename, newline='', encoding='utf-8-sig') as stream:
        for row in csv.DictReader(stream):
            if not row.get('etiquetas_correctas', '').strip():
                continue
            key = (row['source'], row['id'])
            if key in seen:
                raise ValueError('Hay mensajes duplicados en la evaluación')
            seen.add(key)
            op = db.execute('SELECT * FROM operations WHERE plan_id=? AND source=? AND id=?', (row['plan'], *key)).fetchone()
            if not op or op['proposal_hash'] != row['proposal_hash']:
                raise ValueError('Evaluación de un plan desconocido o modificado')
            expected = {x.strip() for x in row['etiquetas_correctas'].split('|') if x.strip()}
            actual = set(json.loads(op['labels']))
            pairs.append((expected, actual))
            language = row.get('idioma', '').strip().lower()
            languages.append(language if language in ('es', 'en', 'mixto', 'otro') else 'desconocido')
    if not pairs:
        raise ValueError('No hay etiquetas humanas: rellena etiquetas_correctas con rutas completas separadas por |.')
    labels = sorted(set().union(*(a | b for a, b in pairs)))
    metrics = {}
    for label in labels:
        tp = sum(label in a and label in b for a, b in pairs)
        fp = sum(label not in a and label in b for a, b in pairs)
        fn = sum(label in a and label not in b for a, b in pairs)
        p, r = tp/max(tp+fp, 1), tp/max(tp+fn, 1)
        metrics[label] = {'precision': p, 'recall': r, 'f1': 2*p*r/max(p+r, 1e-12), 'support': tp+fn,
                          'predicted': tp+fp, 'precision_interval_95': interval(tp, tp+fp)}
    exact = sum(a == b for a, b in pairs)
    by_language = {}
    for language in set(languages):
        subset = [pair for pair, lang in zip(pairs, languages) if lang == language]
        matched = sum(a == b for a, b in subset)
        by_language[language] = {'reviewed': len(subset), 'exact_match': matched/len(subset), 'interval_95': interval(matched, len(subset))}
    return {'reviewed': len(pairs), 'exact_match': exact/len(pairs), 'exact_match_interval_95': interval(exact, len(pairs)), 'by_language': by_language,
            'macro_f1': sum(x['f1'] for x in metrics.values())/len(metrics), 'per_label': metrics,
            'independent_test': False,
            'warning': 'Acuerdo con ejemplos revisados de un plan. No demuestra generalización: la taxonomía pudo descubrirse sobre estos mismos mensajes. Reserva correo futuro independiente.'}
