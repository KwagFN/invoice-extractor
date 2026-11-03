from pathlib import Path

from pypdf import PdfReader


def extract_text(path: Path) -> str:
    """Return the text layer of a PDF, or "" when it has none (e.g. a scan)."""
    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()
