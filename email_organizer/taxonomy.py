"""Taxonomía editable y entidades acotadas: sin crear una carpeta por mensaje."""
import re
from email.utils import parseaddr

TOPICS = {
    'Finanzas/Facturas': ['factura', 'invoice', 'recibo', 'receipt'],
    'Finanzas/Banca': ['banco', 'bank', 'transferencia', 'transfer', 'saldo', 'statement'],
    'Finanzas/Impuestos': ['impuesto', 'tax', 'hacienda', 'tributaria'],
    'Finanzas/Seguros': ['seguro', 'insurance', 'póliza', 'poliza'],
    'Compras/Pedidos': ['pedido', 'order confirmation', 'compra', 'purchase'],
    'Compras/Envios': ['envío', 'envio', 'tracking', 'shipment', 'entrega', 'delivery'],
    'Compras/Devoluciones': ['devolución', 'devolucion', 'refund', 'reembolso'],
    'Viajes/Reservas': ['reserva', 'booking', 'reservation', 'hotel'],
    'Viajes/Transporte': ['vuelo', 'flight', 'boarding', 'tren', 'train ticket'],
    'Trabajo/Proyectos': ['proyecto', 'project', 'reunión', 'reunion', 'meeting'],
    'Trabajo/Empleo': ['empleo', 'job', 'vacante', 'entrevista', 'interview'],
    'Educacion/Cursos': ['curso', 'course', 'clase', 'lesson', 'webinar'],
    'Educacion/Centros': ['universidad', 'university', 'colegio', 'school', 'matrícula'],
    'Salud/Citas': ['médico', 'medico', 'medical', 'cita médica', 'appointment', 'clínica'],
    'Salud/Documentos': ['analítica', 'analitica', 'laboratorio', 'prescripción', 'prescription'],
    'Hogar/Suministros': ['electricidad', 'electricity', 'suministro', 'gas bill', 'agua', 'internet bill'],
    'Hogar/Vivienda': ['alquiler', 'rent', 'hipoteca', 'mortgage', 'comunidad'],
    'Cuentas/Seguridad': ['security', 'seguridad', 'password', 'contraseña', 'verification', 'verificación', 'inicio de sesión'],
    'Cuentas/Suscripciones': ['suscripción', 'subscription', 'renovación', 'renewal'],
    'Comunicaciones/Newsletters': [],
    'Comunicaciones/Notificaciones': [],
    'Comunicaciones/Promociones': ['oferta', 'offer', 'descuento', 'discount', 'sale'],
    'Personal/Conversaciones': [],
    'Legal/Documentos': ['contrato', 'contract', 'legal', 'notaría', 'notaria'],
}


def domain(sender):
    address = parseaddr(sender)[1].lower()
    name = address.rsplit('@', 1)[-1] if '@' in address else ''
    return name if re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?', name) and '.' in name else ''


def topic_for(message, topics=TOPICS):
    subject = message['subject'].casefold()
    hits = []
    for topic, words in topics.items():
        if any(re.search(r'(?<!\w)' + re.escape(word.casefold()) + r'(?!\w)', subject) for word in words):
            hits.append(topic)
    if len(hits) == 1:
        return hits[0], .85, 'Regla temática por asunto'
    if len(hits) > 1:
        return 'Pendiente de revision', 0., 'Varias temáticas posibles; requiere revisión o IA'
    if message['unsubscribe']:
        return 'Comunicaciones/Newsletters', .8, 'Cabecera de desuscripción'
    if message['category'] == 'Notificaciones':
        return 'Comunicaciones/Notificaciones', .8, 'Remitente de notificaciones'
    return 'Pendiente de revision', 0., 'Cabeceras insuficientes; requiere revisión o IA'


def organize(db, topics=TOPICS, min_entity_messages=20, max_entities=50):
    if min_entity_messages < 1 or max_entities < 0:
        raise ValueError('Límites de entidades no válidos')
    # Frecuencias globales por cuenta; nunca se deduce una marca a partir del nombre visible.
    counts = {}
    for row in db.execute('SELECT source,sender FROM messages'):
        key = (row['source'], domain(row['sender']))
        if key[1]:
            counts[key] = counts.get(key, 0) + 1
    selected = {}
    for (source, entity), count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])):
        names = selected.setdefault(source, [])
        if count >= min_entity_messages and len(names) < max_entities:
            names.append(entity)
    with db:
        for row in db.execute('SELECT * FROM messages WHERE category IS NOT NULL AND applied=0'):
            topic, confidence, reason = topic_for(row, topics)
            sender_domain = domain(row['sender'])
            entity = sender_domain if sender_domain in selected.get(row['source'], []) else ''
            db.execute('''UPDATE messages SET topic=?,entity=?,confidence=?,topic_reason=?,approved=0
                       WHERE source=? AND id=?''', (topic, entity, confidence, reason, row['source'], row['id']))
    return len(topics)
