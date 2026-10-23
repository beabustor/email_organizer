"""Pide clave API con entrada oculta; solo nombra grupos con consentimiento."""
import getpass
import os
import subprocess
import sys
import warnings


def main():
    args = sys.argv[1:]
    command = [sys.executable, '-m', 'email_organizer.cli', 'name-topics', *args]
    if '--help' in args or '-h' in args:
        return subprocess.call(command)
    if '--consent-send-examples' not in args:
        print('Lee la guía y añade --consent-send-examples solo si autorizas enviar ejemplos al proveedor.', file=sys.stderr)
        return 2
    task_env = os.environ.copy()
    if not task_env.get('EMAIL_ORGANIZER_AI_KEY'):
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            try:
                key = getpass.getpass('Clave API (oculta, no se guarda): ').strip()
            except (getpass.GetPassWarning, EOFError):
                print('Necesitas una terminal interactiva con entrada oculta.', file=sys.stderr)
                return 2
        if not key:
            return 2
        task_env['EMAIL_ORGANIZER_AI_KEY'] = key
    try:
        return subprocess.call(command, env=task_env)
    finally:
        task_env.pop('EMAIL_ORGANIZER_AI_KEY', None)


if __name__ == '__main__':
    raise SystemExit(main())
