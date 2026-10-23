import argparse
from email.utils import parsedate_to_datetime

from .core import connect


def metadata(headers, protected=False):
    try:
        date = parsedate_to_datetime(headers.get('date', '')).isoformat()
    except (ValueError, TypeError, IndexError):
        date = ''
    return dict(sender=headers.get('from', ''), subject=headers.get('subject', ''), date=date,
                unsubscribe=headers.get('list-unsubscribe', ''), precedence=headers.get('precedence', ''), protected=int(protected))


def main():
    from .workflow import register, execute
    parser = argparse.ArgumentParser(description='Organizador local de contenido: analizar, revisar, aplicar y deshacer. Nunca borra correo.')
    parser.add_argument('--db', default='data/organizer.sqlite')
    sub = parser.add_subparsers(dest='command', required=True)
    register(sub)
    args = parser.parse_args()
    from .locking import database_lock
    with database_lock(args.db):
        db = connect(args.db)
        try:
            execute(args, db)
        finally:
            db.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nDetenido; los lotes guardados se conservan.')
        raise SystemExit(130)
    except Exception as error:
        import sys
        print(str(error) if isinstance(error, ValueError) else f'Operación detenida ({type(error).__name__}); consulta la guía y reanuda.', file=sys.stderr)
        raise SystemExit(1)
