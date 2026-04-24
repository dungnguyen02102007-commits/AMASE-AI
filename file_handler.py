"""
Handles reading CV files: PDF, DOCX, TXT.
Returns clean extracted text with error handling.
"""

from pathlib import Path
from typing import Tuple
import PyPDF2
from docx import Document
from config import ERROR_UNSUPPORTED_FORMAT, ERROR_EMPTY_FILE


SUPPORTED_FORMATS = {".pdf", ".docx", ".txt"}


def read_cv_file(file_path: str) -> Tuple[str, str]:
    """
    Reads a CV file and returns (extracted_text, file_format).
    Raises ValueError with user-facing message on failure.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(ERROR_UNSUPPORTED_FORMAT)

    try:
        if suffix == ".pdf":
            text = _read_pdf(path)
        elif suffix == ".docx":
            text = _read_docx(path)
        elif suffix == ".txt":
            text = _read_txt(path)
        else:
            raise ValueError(ERROR_UNSUPPORTED_FORMAT)
    except (PyPDF2.errors.PdfReadError, Exception) as e:
        raise ValueError(f"{ERROR_EMPTY_FILE} Detail: {str(e)}")

    if not text or len(text.strip()) < 50:
        raise ValueError(ERROR_EMPTY_FILE)

    return text.strip(), suffix.lstrip(".")


def _read_pdf(path: Path) -> str:
    text_parts = []
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        if reader.is_encrypted:
            raise ValueError(
                "The PDF is password-protected. "
                "Please provide an unlocked version."
            )
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_parts.append(extracted)
    return "\n".join(text_parts)


def _read_docx(path: Path) -> str:
    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _read_txt(path: Path) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()
