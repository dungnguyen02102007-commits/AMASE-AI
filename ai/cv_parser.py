"""
cv_parser.py
------------
Extracts raw text from a PDF file.
Supports both pdfplumber (preferred) and PyMuPDF (fitz) as fallback.
"""

import os


def parse_cv(pdf_path: str) -> str:
    """
    Parse a PDF file and return its raw text content.

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        A single string containing all extracted text.

    Raises:
        FileNotFoundError: If the PDF does not exist at the given path.
        RuntimeError: If neither pdfplumber nor PyMuPDF is installed.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"CV file not found: {pdf_path}")

    # Try pdfplumber first — cleaner text layout preservation
    try:
        import pdfplumber

        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return "\n".join(text_parts).strip()

    except ImportError:
        pass  # Fall through to PyMuPDF

    # Fallback: PyMuPDF (fitz)
    try:
        import fitz  # PyMuPDF

        text_parts = []
        doc = fitz.open(pdf_path)
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()

        return "\n".join(text_parts).strip()

    except ImportError:
        raise RuntimeError(
            "No PDF parser found. Install one of:\n"
            "  pip install pdfplumber\n"
            "  pip install pymupdf"
        )


def parse_cv_from_text(text: str) -> str:
    """
    Passthrough for plain-text CVs (useful for testing without a PDF).

    Args:
        text: Raw CV text.

    Returns:
        The same text, stripped of leading/trailing whitespace.
    """
    return text.strip()