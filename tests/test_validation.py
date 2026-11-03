from decimal import Decimal

from invoice_extractor.models import Invoice, LineItem
from invoice_extractor.validation import find_issues


def make_invoice(**overrides) -> Invoice:
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


def test_consistent_invoice_has_no_issues():
    assert find_issues(make_invoice()) == []


def test_flags_line_whose_amount_does_not_match():
    wrong_line = LineItem(
        description="Flour",
        quantity=Decimal("2"),
        unit_price=Decimal("10.50"),
        amount=Decimal("12.00"),
    )
    invoice = make_invoice(
        line_items=[wrong_line],
        subtotal=Decimal("12.00"),
        tax=Decimal("0"),
        total=Decimal("12.00"),
    )

    assert find_issues(invoice) == ["Line 1: 2 x 10.50 = 21.00, but amount is 12.00"]


def test_flags_subtotal_that_does_not_match_line_items():
    issues = find_issues(
        make_invoice(subtotal=Decimal("30.00"), total=Decimal("32.50"))
    )

    assert issues == ["Line items add up to 25.00, but subtotal is 30.00"]


def test_flags_total_that_does_not_match_subtotal_plus_tax():
    issues = find_issues(make_invoice(total=Decimal("99.00")))

    assert issues == ["Subtotal + tax = 27.50, but total is 99.00"]


def test_accepts_rounding_differences_of_one_cent():
    line = LineItem(
        description="Thirds",
        quantity=Decimal("3"),
        unit_price=Decimal("3.333"),
        amount=Decimal("10.00"),
    )
    invoice = make_invoice(
        line_items=[line],
        subtotal=Decimal("10.00"),
        tax=Decimal("0"),
        total=Decimal("10.00"),
    )

    assert find_issues(invoice) == []


def test_flags_invoice_without_line_items():
    invoice = make_invoice(line_items=[], subtotal=Decimal("0"), total=Decimal("0"))

    assert find_issues(invoice) == ["No line items found"]
