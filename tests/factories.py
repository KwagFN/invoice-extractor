from decimal import Decimal

from invoice_extractor.models import Invoice, LineItem

def make_invoice(**overrides) -> Invoice:
    """A consistent invoice by default; each test overrides only what it checks."""
    data = {
        "invoice_number": "INV-001",
        "issue_date": "2026-10-15",
        "vendor_name": "Acme Supplies",
        "customer_name": "Blue Bakery",
        "currency": "USD",
        "line_items": [
            LineItem(
                description="Flour",
                quantity=Decimal("2"),
                unit_price=Decimal("10.50"),
                amount=Decimal("21.00"),
            ),
            LineItem(
                description="Sugar",
                quantity=Decimal("1"),
                unit_price=Decimal("4.00"),
                amount=Decimal("4.00"),
            ),
        ],
        "subtotal": Decimal("25.00"),
        "tax": Decimal("2.50"),
        "total": Decimal("27.50"),
    }
    data.update(overrides)
    return Invoice(**data)