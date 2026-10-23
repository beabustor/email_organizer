"""Solicita una clave oculta para un único proceso; nunca la guarda en archivos."""
import getpass
import os
import subprocess
import sys
import warnings


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ('ai-ontology', 'ai-classify'):
        print('Uso: python scripts/run_ai.py ai-ontology|ai-classify [opciones del comando]', file=sys.stderr)
        return 2
    if '--help' in args or '-h' in args:
        return subprocess.call([sys.executable, '-m', 'email_organizer.cli', *args])
    if '--consent-send-headers' not in args:
        print('Lee la guía y añade --consent-send-headers solo si autorizas enviar esos datos.', file=sys.stderr)
        return 2
    task_env = os.environ.copy()
    if not task_env.get('EMAIL_ORGANIZER_AI_KEY'):
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            try:
                key = getpass.getpass('Clave API (entrada oculta, no se guarda): ').strip()
            except (getpass.GetPassWarning, EOFError):
                print('Se necesita un terminal interactivo con entrada oculta.', file=sys.stderr)
                return 2
        if not key:
            print('No se ha indicado una clave; cancelado.', file=sys.stderr)
            return 2
        task_env['EMAIL_ORGANIZER_AI_KEY'] = key
    try:
        return subprocess.call([sys.executable, '-m', 'email_organizer.cli', *args], env=task_env)
    finally:
        task_env.pop('EMAIL_ORGANIZER_AI_KEY', None)


if __name__ == '__main__':
    raise SystemExit(main())
