import csv
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from .pipeline import Result

INVOICE_FIELDS = [
    "file",
    "status",
    "details",
    "invoice_number",
    "issue_date",
    "vendor_name",
    "customer_name",
    "currency",
    "subtotal",
    "tax",
    "total",
]
LINE_ITEM_FIELDS = [
    "file",
    "invoice_number",
    "description",
    "quantity",
    "unit_price",
    "amount",
]


def money(value: Decimal) -> str:
    return f"{value:.2f}"


def write_reports(results: Iterable[Result], output_dir: Path) -> tuple[Path, Path]:
    """Write invoices.csv (one row per file) and line_items.csv (one per item)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    invoices_path = output_dir / "invoices.csv"
    items_path = output_dir / "line_items.csv"

    with (
        invoices_path.open("w", newline="", encoding="utf-8-sig") as invoices_file,
        items_path.open("w", newline="", encoding="utf-8-sig") as items_file,
    ):
        invoices = csv.DictWriter(invoices_file, fieldnames=INVOICE_FIELDS)
        items = csv.DictWriter(items_file, fieldnames=LINE_ITEM_FIELDS)
        invoices.writeheader()
        items.writeheader()

        for result in results:
            row = {
                "file": result.path.name,
                "status": result.status,
                "details": result.error or " | ".join(result.issues),
            }
            invoice = result.invoice
            if invoice is not None:
                row |= {
                    "invoice_number": invoice.invoice_number,
                    "issue_date": invoice.issue_date.isoformat(),
                    "vendor_name": invoice.vendor_name,
                    "customer_name": invoice.customer_name,
                    "currency": invoice.currency,
                    "subtotal": money(invoice.subtotal),
                    "tax": money(invoice.tax),
                    "total": money(invoice.total),
                }
                for item in invoice.line_items:
                    items.writerow(
                        {
                            "file": result.path.name,
                            "invoice_number": invoice.invoice_number,
                            "description": item.description,
                            "quantity": item.quantity,
                            "unit_price": money(item.unit_price),
                            "amount": money(item.amount),
                        }
                    )
            invoices.writerow(row)

    return invoices_path, items_path