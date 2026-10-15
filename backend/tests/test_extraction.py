import os

import pytest

from app.services.extraction import ExtractionError, extract_text_from_pdf

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample.pdf")


def test_extract_text_from_valid_pdf() -> None:
    text = extract_text_from_pdf(FIXTURE)
    assert "DocSage test fixture" in text


def test_extract_text_missing_file_raises() -> None:
    with pytest.raises(ExtractionError):
        extract_text_from_pdf("/nonexistent/path.pdf")


def test_extract_text_corrupt_file_raises(tmp_path) -> None:
    bad = tmp_path / "corrupt.pdf"
    bad.write_bytes(b"not a real pdf")
    with pytest.raises(ExtractionError):
        extract_text_from_pdf(str(bad))