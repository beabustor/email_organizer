"""Automatización limitada a etiquetas y estructura expresamente aprobadas."""
import json
from pathlib import Path


def authorize(db, identifier, filename, max_changes=100):
    from .plans import check
    if not 1 <= max_changes <= 1000:
        raise ValueError('El límite debe estar entre 1 y 1000')
    plan = db.execute('SELECT * FROM plans WHERE id=?', (identifier,)).fetchone()
    if not plan or plan['state'] not in ('approved', 'applying'):
        raise ValueError('Primero revisa y aprueba un plan de esta estructura')
    ops = db.execute('SELECT * FROM operations WHERE plan_id=? AND approved=1', (identifier,)).fetchall()
    allowed, versions = set(), set()
    for op in ops:
        check(db, op)
        row = db.execute('SELECT * FROM semantic_results WHERE source=? AND id=?', (op['source'], op['id'])).fetchone()
        versions.add(row['model_version'])
        if row['status'] == 'proposed':
            allowed.update(x for x in json.loads(row['labels']) if not x.endswith('/Candidatos a borrar'))
    if len(versions) != 1 or not allowed:
        raise ValueError('No hay una sola estructura válida aprobada para automatizar')
    policy = {'source': plan['source'], 'version': versions.pop(), 'allowed_labels': sorted(allowed),
              'max_changes': max_changes, 'approved_plan': identifier, 'quality_proven': False,
              'baseline_ids': [row['id'] for row in db.execute('SELECT id FROM messages WHERE source=? ORDER BY id', (plan['source'],))]}
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(policy, ensure_ascii=False, indent=2), encoding='utf-8')
    return policy


def refresh(db, api, directory, policy_file=None, write_api=None):
    from .content import sync_full
    from .semantic import classify, read_model
    from .plans import create, approve, apply
    source = sync_full(db, api)
    model, _ = read_model(directory)
    if model['source'] not in (None, source):
        raise ValueError('El modelo pertenece a otra cuenta')
    classify(db, directory, source)
    if not policy_file:
        return create(db, Path(directory).parent / 'plans', source)
    policy = json.loads(Path(policy_file).read_text(encoding='utf-8'))
    if not isinstance(policy.get('max_changes'), int) or not 1 <= policy['max_changes'] <= 1000 or not isinstance(policy.get('allowed_labels'), list):
        raise ValueError('Política con límites inválidos')
    if policy['source'] != source or policy['version'] != model['version']:
        raise ValueError('La política no corresponde a esta cuenta/versión. Requiere nueva revisión y aprobación.')
    if not write_api:
        raise ValueError('No se ha autorizado acceso de escritura para la automatización')
    # Recuperar intentos propios pendientes antes de crear otro plan del mismo mensaje.
    previous = db.execute("SELECT DISTINCT plan_id FROM operations WHERE source=? AND state='inflight'", (source,)).fetchall()
    if previous:
        return apply(db, write_api, previous[0]['plan_id'], policy['max_changes'])
    identifier = create(db, Path(directory).parent / 'plans', source)
    selected = []
    baseline_ids = set(policy.get('baseline_ids', []))
    allowed_labels = set(policy['allowed_labels'])
    for op in db.execute('SELECT * FROM operations WHERE plan_id=?', (identifier,)).fetchall():
        result = db.execute('SELECT status FROM semantic_results WHERE source=? AND id=?', (source, op['id'])).fetchone()
        already = db.execute("SELECT 1 FROM operations WHERE source=? AND id=? AND plan_id!=? AND state IN ('applied','skipped','undone')", (source, op['id'], identifier)).fetchone()
        labels = set(json.loads(op['labels']))
        if op['id'] not in baseline_ids and not already and result['status'] == 'proposed' and labels <= allowed_labels and not any(x.endswith('/Candidatos a borrar') for x in labels):
            selected.append(op)
    # Aprobar únicamente el subconjunto de categorías autorizadas; ningún candidato de limpieza.
    with db:
        for op in selected[:policy['max_changes']]:
            db.execute('UPDATE operations SET approved=1 WHERE plan_id=? AND source=? AND id=?', (identifier, source, op['id']))
        db.execute("UPDATE plans SET state='approved' WHERE id=?", (identifier,))
    apply(db, write_api, identifier, policy['max_changes'])
    return identifier
