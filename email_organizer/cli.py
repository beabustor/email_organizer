import argparse
import csv
import hashlib
import mailbox
from email.utils import parsedate_to_datetime
from pathlib import Path

from .core import connect, load_rules, run, store


def metadata(headers, protected=False):
    try:
        date = parsedate_to_datetime(headers.get('date', '')).isoformat()
    except (ValueError, TypeError, IndexError):
        date = ''
    return dict(sender=headers.get('from', ''), subject=headers.get('subject', ''), date=date,
                unsubscribe=headers.get('list-unsubscribe', ''), precedence=headers.get('precedence', ''), protected=int(protected))


def main():
    parser = argparse.ArgumentParser(description='Organiza correo localmente. Nunca borra mensajes.')
    parser.add_argument('--db', default='data/organizer.sqlite')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('import-mbox', help='Importa cabeceras de un archivo MBOX')
    p.add_argument('file')
    p = sub.add_parser('classify', help='Genera propuestas locales sin modificar Gmail')
    p.add_argument('--rules', default='config/criterios.json')
    p.add_argument('--batch-size', type=int, default=200)
    p.add_argument('--recalculate', action='store_true', help='Recalcula propuestas no aplicadas y elimina sus aprobaciones')
    p = sub.add_parser('review', help='Exporta todas las propuestas a CSV')
    p.add_argument('--output', default='data/review.csv')
    p = sub.add_parser('approve', help='Aprueba únicamente IDs seleccionados en un CSV revisado')
    p.add_argument('file', help='CSV generado por review; escribe si en la columna aprobar')
    for name in ('gmail-sync', 'gmail-apply'):
        p = sub.add_parser(name)
        p.add_argument('--credentials', default='data/credentials.json')
        if name == 'gmail-apply':
            p.add_argument('--confirm', action='store_true', help='Aplica las etiquetas de las propuestas aprobadas')
    args = parser.parse_args()
    db = connect(args.db)
    try:
        if args.command == 'import-mbox':
            source = 'mbox:' + hashlib.sha256(str(Path(args.file).resolve()).encode()).hexdigest()[:16]
            box = mailbox.mbox(args.file, create=False)
            try:
                for msg in box:
                    identifier = hashlib.sha256(msg.as_bytes()).hexdigest()
                    with db:
                        store(db, source, identifier, metadata({k.lower(): str(v) for k, v in msg.items()}, 'F' in msg.get('X-Status', '')))
            finally:
                box.close()
            print('Cabeceras importadas; contenido y adjuntos no guardados en la base de datos.')
        elif args.command == 'classify':
            rules = load_rules(args.rules)
            if args.recalculate:
                with db:
                    db.execute('UPDATE messages SET category=NULL,candidate=NULL,reason=NULL,approved=0 WHERE applied=0')
            run(db, rules, args.batch_size)
        elif args.command == 'review':
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            def safe(value):
                value = str(value)
                return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value
            with open(args.output, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['source', 'id', 'remitente', 'asunto', 'categoria', 'revisar_para_borrar', 'motivo', 'aprobar'])
                for row in db.execute('SELECT * FROM messages WHERE category IS NOT NULL ORDER BY candidate DESC,category'):
                    writer.writerow([row['source'], row['id'], safe(row['sender']), safe(row['subject']), row['category'], row['candidate'], row['reason'], ''])
            print(f'Propuestas guardadas en {args.output}. Escribe si en aprobar solo para los mensajes elegidos.')
        elif args.command == 'approve':
            count = 0
            with open(args.file, newline='', encoding='utf-8-sig') as f, db:
                for row in csv.DictReader(f):
                    if row['aprobar'].strip().casefold() in ('si', 'sí'):
                        count += db.execute("UPDATE messages SET approved=1 WHERE source=? AND id=? AND category IS NOT NULL AND category!='Conservar' AND applied=0", (row['source'], row['id'])).rowcount
            print(f'{count} propuestas aprobadas. Aún no se ha modificado Gmail.')
        else:
            if args.command == 'gmail-apply' and not args.confirm:
                parser.error('Es necesario --confirm; revisa primero el CSV y ejecuta approve.')
            from .gmail import service, sync, apply
            api = service(args.credentials)
            if args.command == 'gmail-sync':
                sync(db, api, metadata)
            else:
                apply(db, api)
    finally:
        db.close()


if __name__ == '__main__':
    main()
