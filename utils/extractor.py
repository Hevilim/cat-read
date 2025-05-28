import io
import chardet
from docx import Document
import fitz  # PyMuPDF


def parse(file_bytes, mime_type=None):
    try:
        if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            # DOCX
            doc = Document(io.BytesIO(file_bytes))
            return '\n'.join([p.text for p in doc.paragraphs])

        elif mime_type == 'application/pdf':
            # PDF
            text = ''
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text()
            return text

        elif mime_type == 'text/plain':
            # Определение кодировки
            result = chardet.detect(file_bytes)
            encoding = result['encoding']
            print(f"[DEBUG] Определена кодировка: {encoding}")
            return file_bytes.decode(encoding, errors='ignore')

        else:
            return file_bytes.decode("utf-8", errors="ignore")

    except Exception as e:
        print("Ошибка при извлечении текста:", e)
        return ""