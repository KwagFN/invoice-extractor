from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from invoice_extractor.models import Invoice

AI_RESPONSE = """
{
  "invoice_number": "INV-001",
  "issue_date": "2026-10-15",
  "vendor_name": "Acme Supplies",
  "customer_name": "Blue Bakery",
  "currency": "USD",
  "line_items": [
    {"description": "Flour 25kg", "quantity": 2, "unit_price": "10.50", "amount": 21}
  ],
  "subtotal": 21.00,
  "tax": 2.10,
  "total": 23.10
}
"""


def test_parses_json_into_typed_invoice():
    invoice = Invoice.model_validate_json(AI_RESPONSE)

    assert invoice.issue_date == date(2026, 10, 15)
    assert invoice.total == Decimal("23.10")
    assert invoice.line_items[0].unit_price == Decimal("10.50")


def test_rejects_invalid_currency():
    bad = AI_RESPONSE.replace('"USD"', '"US Dollar"')

    with pytest.raises(ValidationError):
        Invoice.model_validate_json(bad)


def test_rejects_impossible_date():
    bad = AI_RESPONSE.replace("2026-10-15", "2026-13-45")

    with pytest.raises(ValidationError):
        Invoice.model_validate_json(bad)


def test_field_description_are_in_the_json_schema():
    schema = Invoice.model_json_schema()

    assert "ISO 4217" in schema["properties"]["currency"]["description"]
