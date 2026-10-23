import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from email_organizer.content import extract, save_raw, reextract
from email_organizer.attachments import read_document
from email_organizer.core import connect
from email_organizer.semantic import fit
from test_content import message


def docx(text):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('word/document.xml', '<w:document xmlns:w="urn:word"><w:p><w:t>' + text + '</w:t></w:p></w:document>')
    return stream.getvalue()


def pdf(text):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    writer = PdfWriter()
    page = writer.add_blank_page(width=600, height=400)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
    content = DecodedStreamObject()
    content.set_data(('BT /F1 16 Tf 30 300 Td (' + text + ') Tj ET').encode('ascii'))
    page[NameObject('/Contents')] = writer._add_object(content)
    stream = io.BytesIO(); writer.write(stream)
    return stream.getvalue()


class AttachmentTests(unittest.TestCase):
    def test_docx_attachment_only_is_classification_evidence(self):
        item = message('')
        item.add_attachment(docx('Factura contabilidad banco importe impuesto documento financiero'), maintype='application', subtype='vnd.openxmlformats-officedocument.wordprocessingml.document', filename='documento.docx')
        with tempfile.TemporaryDirectory() as folder:
            db = connect(Path(folder) / 'db.sqlite')
            save_raw(db, 'local', '1', item.as_bytes())
            row = db.execute('SELECT * FROM content').fetchone()
            self.assertIn('Factura contabilidad', row['text'])
            self.assertEqual(row['status'], 'complete')
            self.assertTrue(json.loads(row['attachments'])[0]['analyzed'])
            fit(db, Path(folder) / 'model')
            self.assertEqual(db.execute('SELECT status FROM semantic_results').fetchone()[0], 'proposed')
            db.close()

    def test_pdf_text_extracted_without_ocr(self):
        item = message('')
        item.add_attachment(pdf('Invoice accounting bank payment financial document'), maintype='application', subtype='pdf', filename='invoice.pdf')
        _, text, _, attachments, status, _ = extract(item.as_bytes())
        self.assertIn('Invoice accounting', text)
        self.assertEqual(status, 'complete')
        self.assertTrue(attachments[0]['analyzed'])

    def test_unknown_attachment_forces_partial_even_with_good_body(self):
        item = message('El cuerpo habla de un viaje pero no sabemos qué contiene el adjunto')
        item.add_attachment(b'unknown', maintype='application', subtype='octet-stream', filename='documento.bin')
        result = extract(item.as_bytes())
        self.assertEqual(result[4], 'partial')
        self.assertEqual(result[3][0]['status'], 'unsupported')

    def test_missing_ocr_is_not_silently_ignored(self):
        from PIL import Image
        stream = io.BytesIO(); Image.new('RGB', (100, 100), 'white').save(stream, format='PNG')
        with patch('email_organizer.attachments.shutil.which', return_value=None):
            with self.assertRaisesRegex(ValueError, 'needs_ocr'):
                read_document('image', stream.getvalue())

    def test_macros_and_zip_bombs_rejected(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr('word/document.xml', '<document/>')
            archive.writestr('word/vbaProject.bin', b'never run')
        with self.assertRaisesRegex(ValueError, 'macros'):
            read_document('docx', stream.getvalue())
        with patch('email_organizer.attachments.MAX_BYTES', 10):
            with self.assertRaisesRegex(ValueError, 'limit'):
                read_document('docx', docx('text'))

    def test_upgrade_reextracts_original_without_download(self):
        with tempfile.TemporaryDirectory() as folder:
            db = connect(Path(folder) / 'db.sqlite')
            item = message('')
            item.add_attachment(b'Invoice bank payment financial account', maintype='text', subtype='plain', filename='invoice.txt')
            save_raw(db, 'local', 'one', item.as_bytes())
            db.execute("UPDATE content SET parser_version='mime-1',text='' WHERE id='one'")
            db.commit()
            self.assertEqual(reextract(db), 1)
            self.assertIn('Invoice bank', db.execute('SELECT text FROM content').fetchone()[0])
            self.assertEqual(reextract(db), 0)
            db.close()
