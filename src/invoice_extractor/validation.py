from decimal import Decimal

from .models import Invoice

TOLERANCE = Decimal("0.01")


def find_issues(invoice: Invoice) -> list[str]:
    """Cross-check the numbers on an invoice. An empty list means it adds up."""
    if not invoice.line_items:
        return ["No line items found"]

    issues: list[str] = []

    for number, item in enumerate(invoice.line_items, start=1):
        expected = item.quantity * item.unit_price
        if abs(expected - item.amount) > TOLERANCE:
            issues.append(
                f"Line {number}: {item.quantity} x {item.unit_price} = {expected}, "
                f"but amount is {item.amount}"
            )

    items_sum = sum((item.amount for item in invoice.line_items), Decimal("0"))
    if abs(items_sum - invoice.subtotal) > TOLERANCE:
        issues.append(
            f"Line items add up to {items_sum}, but subtotal is {invoice.subtotal}"
        )

    expected_total = invoice.subtotal + invoice.tax
    if abs(expected_total - invoice.total) > TOLERANCE:
        issues.append(
            f"Subtotal + tax = {expected_total}, but total is {invoice.total}"
        )

    return issues
