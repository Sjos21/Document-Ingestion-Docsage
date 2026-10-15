"""PDF text extraction service.

Raises ExtractionError on any failure so callers (worker_tasks/ingest.py)
can catch one exception type and set Document.status=failed with a clear
reason, instead of letting raw PyMuPDF exceptions crash the job.
"""
from __future__ import annotations

import fitz  # PyMuPDF


class ExtractionError(Exception):
    """Raised when a PDF cannot be parsed or yields no extractable text."""


def extract_text_from_pdf(file_path: str) -> str:
    """Extract concatenated text from all pages of a PDF.

    Raises:
        ExtractionError: missing, corrupt, encrypted, zero-page, or
            no extractable text (e.g. scanned image PDF â€” OCR deferred).
    """
    try:
        doc = fitz.open(file_path)
    except fitz.FileDataError as exc:
        raise ExtractionError(f"corrupt or unreadable PDF: {exc}") from exc
    except (FileNotFoundError, fitz.FileNotFoundError) as exc:
        raise ExtractionError(f"file not found: {exc}") from exc

    try:
        if doc.is_encrypted:
            raise ExtractionError("PDF is encrypted; password-protected files unsupported")
        if doc.page_count == 0:
            raise ExtractionError("PDF has zero pages")
        pages = [page.get_text("text") for page in doc]
    finally:
        doc.close()

    full_text = "\n\n".join(p.strip() for p in pages if p.strip())
    if not full_text:
        raise ExtractionError(
            "no extractable text found -- likely a scanned/image-only PDF "
            "(OCR deferred to a later phase)"
        )
    return full_text
