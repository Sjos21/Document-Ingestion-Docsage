"""Run once to (re)generate tests/fixtures/sample.pdf using PyMuPDF."""
import fitz

doc = fitz.open()
page = doc.new_page()
page.insert_text(
    (72, 72),
    "DocSage test fixture.\n\n"
    "This is a small sample PDF used by the ingestion test suite. "
    "It contains enough text to produce at least one chunk after "
    "chunking and embedding, so the round-trip upload -> extract -> "
    "chunk -> embed -> indexed pipeline can be exercised end to end.",
)
doc.save("tests/fixtures/sample.pdf")
doc.close()
print("wrote tests/fixtures/sample.pdf")