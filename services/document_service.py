import base64
import html
import re
import uuid
import zlib
import zipfile
from pathlib import Path
from config import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES, UPLOAD_DIR

class DocumentError(Exception):
    pass

def _safe_name(name):
    return re.sub(r"[^A-Za-z0-9._ -]", "_", Path(name).name)

def _basic_docx_text(path):
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
        xml = re.sub(r"</w:p[^>]*>", "\n", xml)
        xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
        text = re.sub(r"<[^>]+>", "", xml)
        return html.unescape(text)
    except Exception as exc:
        raise DocumentError("This DOCX file could not be read.") from exc

def _pdf_literal(value):
    value = re.sub(r"\\([()\\])", r"\1", value)
    return value.replace("\\n", "\n").replace("\\r", "\n").replace("\\t", "\t")

def _basic_pdf_text(path):
    raw = path.read_bytes()
    streams = re.findall(rb"stream\r?\n(.*?)\r?\nendstream", raw, re.S)
    chunks = []
    for stream in streams or [raw]:
        candidates = [stream]
        try:
            candidates.append(zlib.decompress(stream))
        except Exception:
            pass
        for candidate in candidates:
            decoded = candidate.decode("latin-1", errors="ignore")
            matches = re.findall(r"\((?:\\.|[^\\)])*\)\s*(?:Tj|'|\")", decoded)
            matches += re.findall(r"\[(.*?)\]\s*TJ", decoded, re.S)
            for match in matches:
                if "(" in match and ")" in match:
                    chunks.extend(_pdf_literal(item) for item in re.findall(r"\(((?:\\.|[^\\)])*)\)", match))
                else:
                    chunks.append(_pdf_literal(match))
    text = " ".join(part.strip() for part in chunks if part.strip())
    if not text:
        raise DocumentError("No selectable text was found in this PDF. A scanned PDF needs OCR support.")
    return text

def _extract_text(path, extension):
    if extension == "txt":
        return path.read_text(encoding="utf-8", errors="replace")
    if extension == "docx":
        try:
            from docx import Document
            return "\n".join(paragraph.text for paragraph in Document(path).paragraphs)
        except ImportError:
            return _basic_docx_text(path)
    if extension == "pdf":
        try:
            from pypdf import PdfReader
            return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        except ImportError:
            return _basic_pdf_text(path)
    raise DocumentError("Unsupported file type.")

def save_upload(content, filename):
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise DocumentError("Only PDF, DOCX, and TXT files are supported.")
    raw = base64.b64decode(content.split(",", 1)[-1])
    if len(raw) > MAX_UPLOAD_BYTES:
        raise DocumentError("File is larger than the 15 MB limit.")
    document_id = str(uuid.uuid4())
    path = UPLOAD_DIR / f"{document_id}_{_safe_name(filename)}"
    path.write_bytes(raw)
    text = _extract_text(path, extension).strip()
    if not text:
        raise DocumentError("No readable text was found in this document.")
    return {"id": document_id, "name": filename, "extension": extension, "size_kb": round(len(raw)/1024, 1), "text": text[:150000]}

def delete_upload(document_id):
    """Remove a locally stored uploaded document by its generated identifier."""
    if not document_id or not re.fullmatch(r"[0-9a-f-]{36}", document_id):
        return False
    removed = False
    for path in UPLOAD_DIR.glob(f"{document_id}_*"):
        path.unlink(missing_ok=True)
        removed = True
    return removed