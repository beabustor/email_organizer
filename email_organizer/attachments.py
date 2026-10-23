"""Lectores pasivos en proceso separado, con presupuestos y estado explícito."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile
from xml.etree import ElementTree

MAX_BYTES = 16 * 1024 * 1024
MAX_TEXT = 1_000_000
MAX_PAGES = 100


def ocr_image(image):
    from PIL import Image
    command = shutil.which('tesseract')
    if not command:
        raise ValueError('needs_ocr: instala Tesseract con idiomas eng y spa')
    if image.width * image.height > 20_000_000:
        raise ValueError('limit: imagen de más de 20 megapíxeles')
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'image.png'
        image.convert('RGB').save(path)
        options = []
        local_data = Path('data/ocr')
        if all((local_data / (lang + '.traineddata')).is_file() for lang in ('eng', 'spa')):
            options = ['--tessdata-dir', str(local_data.resolve())]
        result = subprocess.run([command, str(path), 'stdout', *options, '-l', 'eng+spa', '--psm', '3'], capture_output=True, timeout=15)
        if result.returncode:
            raise ValueError('needs_ocr: comprueba instalación de Tesseract e idiomas eng/spa')
        return result.stdout.decode('utf-8', errors='replace')


def read_document(kind, payload, charset='utf-8'):
    method, texts = kind, []
    if kind == 'text':
        return payload.decode(charset or 'utf-8', errors='strict'), 'text'
    if kind == 'html':
        from .content import html_text
        return html_text(payload.decode(charset or 'utf-8', errors='strict')), 'html-text'
    if kind == 'docx':
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            infos = archive.infolist()
            if sum(x.file_size for x in infos) > MAX_BYTES or len(infos) > 1000:
                raise ValueError('limit: expansión ZIP demasiado grande')
            if any('vbaproject' in x.filename.lower() for x in infos):
                raise ValueError('unsupported: documento con macros')
            names = [x.filename for x in infos if x.filename.startswith('word/') and x.filename.endswith('.xml') and any(token in x.filename for token in ('document.xml', 'footnotes.xml', 'endnotes.xml', 'header', 'footer'))]
            if 'word/document.xml' not in names:
                raise ValueError('unsupported: no es un DOCX válido')
            for name in names:
                data = archive.read(name)
                if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
                    raise ValueError('unsupported: declaraciones XML no permitidas')
                root = ElementTree.fromstring(data)
                texts.append('\n'.join(node.text or '' for node in root.iter() if node.tag.endswith('}t')))
        return '\n'.join(texts), 'docx-xml'
    if kind == 'pdf':
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(payload), strict=False)
        if reader.is_encrypted:
            raise ValueError('encrypted: PDF protegido')
        if len(reader.pages) > MAX_PAGES:
            raise ValueError('limit: demasiadas páginas PDF')
        rendered = None
        try:
            for index, page in enumerate(reader.pages):
                text = page.extract_text() or ''
                if len(text.strip()) < 20 or len(page.images) > 0:
                    # PDFs escaneados o mixtos: OCR de toda la página, no solo su capa de texto.
                    if rendered is None:
                        import pypdfium2
                        rendered = pypdfium2.PdfDocument(payload)
                    pdf_page = rendered[index]
                    bitmap = pdf_page.render(scale=2)
                    try:
                        text = ocr_image(bitmap.to_pil())
                    finally:
                        bitmap.close(); pdf_page.close()
                    method = 'pdf+ocr-eng-spa'
                texts.append(text)
        finally:
            if rendered is not None:
                rendered.close()
        return '\n'.join(texts), method
    if kind == 'image':
        from PIL import Image, ImageSequence
        Image.MAX_IMAGE_PIXELS = 20_000_000
        with Image.open(io.BytesIO(payload)) as image:
            if getattr(image, 'n_frames', 1) > MAX_PAGES:
                raise ValueError('limit: demasiados fotogramas')
            for frame in ImageSequence.Iterator(image):
                texts.append(ocr_image(frame))
        return '\n'.join(texts), 'ocr-eng-spa'
    raise ValueError('unsupported: formato no compatible')


def extract_attachment(part):
    filename = str(part.get_filename() or '')
    mime = part.get_content_type()
    suffix = Path(filename).suffix.lower()
    payload = part.get_payload(decode=True) or b''
    info = {'name': filename, 'type': mime, 'size_bytes': len(payload), 'analyzed': False, 'status': 'unsupported', 'method': ''}
    kind = ('pdf' if mime == 'application/pdf' or suffix == '.pdf' else
            'docx' if suffix == '.docx' or mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' else
            'html' if mime == 'text/html' or suffix in ('.html', '.htm') else 'text' if mime in ('text/plain', 'text/csv') or suffix in ('.txt', '.csv') else
            'image' if mime.startswith('image/') else None)
    if not kind or len(payload) > MAX_BYTES:
        info['status'] = 'limit' if len(payload) > MAX_BYTES else 'unsupported'
        return '', info
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'input'
        path.write_bytes(payload)
        try:
            result = subprocess.run([sys.executable, '-m', 'email_organizer.attachments', kind, str(path), part.get_content_charset() or 'utf-8'],
                                    capture_output=True, timeout=60)
            if result.returncode:
                info['status'] = 'worker_error'
                return '', info
            outcome = json.loads(result.stdout)
            info.update({key: outcome[key] for key in ('status', 'method', 'analyzed')})
            return outcome.get('text', ''), info
        except subprocess.TimeoutExpired:
            info['status'] = 'timeout'
        except (ValueError, OSError):
            info['status'] = 'worker_error'
    return '', info


def worker():
    if os.name != 'nt':
        import resource
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
            resource.setrlimit(resource.RLIMIT_AS, (768 * 1024**2, 768 * 1024**2))
        except (ValueError, OSError):
            pass
    try:
        payload = Path(sys.argv[2]).read_bytes()
        if len(payload) > MAX_BYTES:
            raise ValueError('limit: archivo demasiado grande')
        text, method = read_document(sys.argv[1], payload, sys.argv[3])
        text = text.replace('\x00', '').strip()
        status = 'complete' if text else 'no_text'
        if len(text) > MAX_TEXT:
            status, text = 'limit', text[:MAX_TEXT]
        outcome = {'text': text, 'method': method, 'status': status, 'analyzed': status == 'complete'}
    except Exception as error:
        status = 'error'
        if isinstance(error, ValueError) and str(error).split(':', 1)[0] in ('needs_ocr', 'limit', 'encrypted', 'unsupported'):
            status = str(error).split(':', 1)[0]
        outcome = {'text': '', 'method': '', 'status': status, 'analyzed': False}
    print(json.dumps(outcome, ensure_ascii=True))


if __name__ == '__main__':
    worker()
