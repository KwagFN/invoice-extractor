import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .ai import InvoiceExtractor
from .models import Invoice
from .pdf_text import extract_text
from .validation import find_issues

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Result:
    path: Path
    invoice: Invoice | None = None
    issues: tuple[str, ...] = ()
    error: str | None = None

    @property
    def status(self) -> str:
        if self.error is not None:
            return "FAILED"
        if self.issues:
            return "NEEDS REVIEW"
        return "OK"

def process_file(path: Path, extractor: InvoiceExtractor) -> Result:
    try:
        text = extract_text(path)
        if text:
            invoice = extractor.extract(text)
        else:
            logger.info("%s has no text lyer, sending the PDF itself", path.name)
            invoice = extractor.extract_pdf(path.read_bytes())
    except Exception as exc:
        logger.exception("Could not process %s", path.name)
        return Result(path, error=f"{type(exc).__name__}: {exc}")

    return Result(path, invoice, tuple(find_issues(invoice)))

def process_folder(
    folder: Path,
    extractor: InvoiceExtractor,
    delay_seconds: float = 4.0,
    sleep: Callable[[float], None] = time.sleep,
) -> list[Result]:
    results: list[Result] = []
    for index, path in enumerate(sorted(folder.glob("*.pdf"))):
        if index > 0:
            sleep(delay_seconds)
        logger.info("Processing %s", path.name)
        results.append(process_file(path, extractor))
    return results