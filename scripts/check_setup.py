"""Diagnóstico local sin imprimir secretos ni contactar servicios."""
import importlib.metadata
import os
import platform
import sqlite3
import sys
from pathlib import Path


def main():
    print('Sistema:', platform.system())
    print('Python:', platform.python_version(), '(compatible)' if sys.version_info >= (3, 11) else '(requiere 3.11 o posterior)')
    print('Entorno virtual:', 'sí' if sys.prefix != sys.base_prefix else 'no')
    print('SQLite:', sqlite3.sqlite_version)
    print('Directorio del proyecto:', 'correcto' if Path('pyproject.toml').exists() else 'abre la terminal en la raíz del repositorio')
    for package in ('google-api-python-client', 'google-auth-oauthlib', 'keyring'):
        try:
            print(package + ':', importlib.metadata.version(package))
        except importlib.metadata.PackageNotFoundError:
            print(package + ': no instalado')
    print('JSON OAuth local:', 'presente' if Path('data/credentials.json').is_file() else 'no encontrado')
    print('Variable API IA:', 'presente' if os.environ.get('EMAIL_ORGANIZER_AI_KEY') else 'ausente (opcional; puedes usar scripts/run_ai.py)')
    try:
        import keyring
        backend = type(keyring.get_keyring()).__module__
        compatible = backend.startswith(('keyring.backends.macOS', 'keyring.backends.Windows', 'keyring.backends.SecretService', 'keyring.backends.kwallet'))
        print('Backend del llavero:', backend)
        print('Backend admitido por el conector:', 'sí; acceso aún no probado' if compatible else 'no; requiere configuración')
    except Exception:
        print('Llavero: no se pudo detectar; revisa tu configuración local.')
    print('No se han leído valores de credenciales, autorizado cuentas ni modificado Gmail.')


if __name__ == '__main__':
    main()
