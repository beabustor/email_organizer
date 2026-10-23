"""Descarga solo datos eng/spa oficiales, verificando el hash Git del archivo."""
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request


def main():
    folder = Path('data/ocr')
    folder.mkdir(parents=True, exist_ok=True)
    for language in ('eng', 'spa'):
        url = f'https://api.github.com/repos/tesseract-ocr/tessdata_fast/contents/{language}.traineddata'
        with urllib.request.urlopen(urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json'}), timeout=30) as response:
            info = json.load(response)
        download = info['download_url']
        parsed = urllib.parse.urlsplit(download)
        if parsed.scheme != 'https' or parsed.hostname != 'raw.githubusercontent.com' or not parsed.path.startswith('/tesseract-ocr/tessdata_fast/'):
            raise ValueError('Destino de datos OCR inesperado')
        with urllib.request.urlopen(download, timeout=60) as response:
            data = response.read(20 * 1024**2 + 1)
        if len(data) > 20 * 1024**2 or len(data) != info['size']:
            raise ValueError('Tamaño de datos OCR no válido')
        actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if actual != info['sha']:
            raise ValueError('Verificación de datos OCR fallida; no se guarda el archivo')
        temporary = folder / (language + '.tmp')
        temporary.write_bytes(data)
        temporary.replace(folder / (language + '.traineddata'))
        print(f'{language}: descargado y verificado contra el hash Git oficial.')
    print('Datos locales listos. También necesitas el ejecutable Tesseract instalado y en PATH.')


if __name__ == '__main__':
    main()
