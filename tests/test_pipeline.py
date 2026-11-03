import shutil
from decimal import Decimal
from pathlib import Path

from factories import make_invoice
from fpdf import FPDF

from invoice_extractor.ai import ExtractionError
from invoice_extractor.pipeline import process_file, process_folder

SAMPLES = Path(__file__).parent.parent / "samples"
ACME = SAMPLES / "acme_INV-1001.pdf"


class FakeExtractor:
    """Returns a fixed invoice (or raises a fixed error) and records each call."""

    def __init__(self, invoice=None, error=None):
        self.invoice = invoice or make_invoice()
        self.error = error
        self.calls = []

    def extract(self, text):
        return self._answer("text")

    def extract_pdf(self, data):
        return self._answer("pdf")

    def _answer(self, kind):
        self.calls.append(kind)
        if self.error:
            raise self.error
        return self.invoice


def test_consistent_invoice_is_ok():
    result = process_file(ACME, FakeExtractor())

    assert result.status == "OK"
    assert result.issues == ()


def test_invoice_whose_numbers_do_not_add_up_needs_review():
    extractor = FakeExtractor(make_invoice(total=Decimal("99.00")))

    result = process_file(ACME, extractor)

    assert result.status == "NEEDS REVIEW"
    assert result.issues == ("Subtotal + tax = 27.50, but total is 99.00",)


def test_extraction_error_marks_the_file_as_failed():
    extractor = FakeExtractor(error=ExtractionError("bad json"))

    result = process_file(ACME, extractor)

    assert result.status == "FAILED"
    assert result.error == "ExtractionError: bad json"
    assert result.invoice is None


def test_pdf_without_text_is_sent_to_the_ai_as_a_pdf(tmp_path):
    scan = FPDF()
    scan.add_page()
    scan.output(str(tmp_path / "scan.pdf"))
    extractor = FakeExtractor()

    process_file(tmp_path / "scan.pdf", extractor)

    assert extractor.calls == ["pdf"]


def test_one_broken_file_does_not_stop_the_batch(tmp_path):
    (tmp_path / "broken.pdf").write_bytes(b"this is not a pdf")
    shutil.copy(ACME, tmp_path / "good.pdf")

    results = process_folder(tmp_path, FakeExtractor(), sleep=lambda _: None)

    assert [result.status for result in results] == ["FAILED", "OK"]


def test_pauses_between_files_but_not_before_the_first():
    sleeps = []

    results = process_folder(
        SAMPLES, FakeExtractor(), delay_seconds=4.0, sleep=sleeps.append
    )

    assert len(results) == 4
    assert sleeps == [4.0, 4.0, 4.0]
