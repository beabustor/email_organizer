"""Punto de entrada para usuarios: prepara .venv y abre el asistente local."""
import os
from pathlib import Path
import subprocess
import sys
import venv


def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)
    if sys.version_info < (3, 11):
        raise SystemExit('Instala Python 3.11 o posterior desde python.org.')
    python = root / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        print('Preparando entorno privado de Python…', flush=True)
        venv.EnvBuilder(with_pip=True).create(root / '.venv')
    marker = root / '.venv' / 'email-organizer-0.3-ready'
    if not marker.exists():
        print('Instalando bibliotecas de Gmail y machine learning; no se conecta ninguna cuenta.', flush=True)
        subprocess.run([str(python), '-m', 'pip', 'install', '-e', '.[gmail,semantic,attachments]'], check=True)
        marker.write_text('0.3', encoding='utf-8')
    return subprocess.call([str(python), '-m', 'email_organizer.wizard'])


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('\nDetenido. Se conservan los pasos ya guardados.')
