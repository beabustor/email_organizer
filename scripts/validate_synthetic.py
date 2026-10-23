"""Comprobación de volumen sin credenciales ni correo real; no mide precisión."""
import argparse
from contextlib import redirect_stdout
from email.message import EmailMessage
import io
import json
from pathlib import Path
import tempfile
import time

from email_organizer.content import save_raw
from email_organizer.core import connect
from email_organizer.semantic import fit
from email_organizer.plans import create


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--messages', type=int, default=30000)
    args = parser.parse_args()
    if args.messages < 1:
        raise ValueError('El número debe ser positivo')
    topics = ['Hotel reservation accommodation travel holiday booking', 'Reserva hotel alojamiento viaje vacaciones estancia',
              'Invoice accounting payment bank finance receipt', 'Factura contabilidad pago banco finanzas recibo',
              'Hiking mountain forest nature trail camping', 'Senderismo montaña bosque naturaleza ruta acampada',
              'Course university lesson education students exam', 'Curso universidad clase educación alumnado examen']
    start = time.monotonic()
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        db = connect(folder / 'db.sqlite')
        for i in range(args.messages):
            msg = EmailMessage()
            msg['From'] = 'synthetic@example.org'
            msg['Subject'] = 'Documento de prueba'
            msg.set_content(topics[i % len(topics)] + f' referencia ficticia {i}')
            save_raw(db, 'synthetic', str(i), msg.as_bytes())
            if (i+1) % 5000 == 0:
                print(f'Importados {i+1}/{args.messages}', flush=True)
        with redirect_stdout(io.StringIO()):
            meta = fit(db, folder / 'model', source='synthetic', backend='lsa')
            plan = create(db, folder / 'plans', source='synthetic')
        classified = db.execute('SELECT count(*) FROM semantic_results').fetchone()[0]
        operations = db.execute('SELECT count(*) FROM operations WHERE plan_id=?', (plan,)).fetchone()[0]
        approved = db.execute('SELECT sum(approved) FROM operations').fetchone()[0]
        assert classified == args.messages and operations == args.messages and approved == 0
        assert meta['analyzed_messages'] == args.messages
        print(json.dumps({'messages': args.messages, 'body_analyzed': meta['analyzed_messages'], 'results': classified,
                          'planned': operations, 'approved': approved, 'backend': 'lsa',
                          'seconds_this_machine': round(time.monotonic()-start, 2),
                          'semantic_accuracy_measured': False}, indent=2))
        db.close()


if __name__ == '__main__':
    main()
