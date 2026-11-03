from decimal import Decimal
from types import SimpleNamespace

import pytest

from invoice_extractor.ai import ExtractionError, GeminiExtractor
from invoice_extractor.models import Invoice

VALID_RESPONSE = """
{
  "invoice_number": "INV-1001",
  "issue_date": "2026-10-15",
  "vendor_name": "Acme Supplies LLC",
  "customer_name": "Blue Bakery Inc.",
  "currency": "USD",
  "line_items": [
    {"description": "Flour 25kg bag", "quantity": 4, "unit_price": 18.9, "amount": 75.6}
  ],
  "subtotal": 75.6,
  "tax": 6.05,
  "total": 81.65
}
"""


class FakeModels:
    """Stands in for client.models: records each call and returns a fixed text."""

    def __init__(self, response_text):
        self.response_text = response_text
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(text=self.response_text)


def make_extractor(response_text):
    models = FakeModels(response_text)
    client = SimpleNamespace(models=models)
    return GeminiExtractor(client, model="test-model"), models


def test_returns_validated_invoice():
    extractor, _ = make_extractor(VALID_RESPONSE)

    invoice = extractor.extract("invoice text")

    assert invoice.invoice_number == "INV-1001"
    assert invoice.total == Decimal("81.65")


def test_sends_text_schema_and_instructions_to_the_model():
    extractor, models = make_extractor(VALID_RESPONSE)

    extractor.extract("TOTAL DUE: USD 81.65")

    call = models.calls[0]
    assert call["model"] == "test-model"
    assert call["contents"] == "TOTAL DUE: USD 81.65"
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].response_json_schema == Invoice.model_json_schema()
    assert "do not calculate, correct or round" in call["config"].system_instruction


def test_raises_on_empty_response():
    extractor, _ = make_extractor(None)

    with pytest.raises(ExtractionError, match="empty response"):
        extractor.extract("invoice text")


def test_raises_when_response_is_not_a_valid_invoice():
    extractor, _ = make_extractor('{"invoice_number": "INV-1001"}')

    with pytest.raises(ExtractionError, match="not a valid invoice"):
        extractor.extract("invoice text")


def test_scanned_pdf_is_sent_as_a_pdf_part():
    extractor, models = make_extractor(VALID_RESPONSE)

    extractor.extract_pdf(b"%PDF-1.4 fake")

    [part] = models.calls[0]["contents"]
    assert part.inline_data.mime_type == "application/pdf"
    assert part.inline_data.data == b"%PDF-1.4 fake"
