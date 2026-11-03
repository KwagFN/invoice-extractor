from pathlib import Path

from fpdf import FPDF

from invoice_extractor.pdf_text import extract_text

SAMPLES = Path(__file__).parent.parent / "samples"


def test_extracts_text_from_english_invoice():
    text = extract_text(SAMPLES / "acme_INV-1001.pdf")

    assert "INV-1001" in text
    assert "Blue Bakery Inc." in text
    assert "132.73" in text


def test_keeps_portuguese_accents_and_number_format():
    text = extract_text(SAMPLES / "padaria_FAT-0789.pdf")

    assert "Padaria Pão Quente" in text
    assert "R$ 815,54" in text


def test_returns_empty_string_for_pdf_without_text(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    path = tmp_path / "scanned.pdf"
    pdf.output(str(path))

    assert extract_text(path) == ""
