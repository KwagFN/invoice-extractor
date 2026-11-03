"""Generate fictional invoices as PDFs, for demos and tests.

Run with: uv run python scripts/make_samples.py
"""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

OUTPUT_DIR = Path("samples")
CENTS = Decimal("0.01")


@dataclass
class Sample:
    filename: str
    language: str  # "en": table layout, "pt": one line per item
    number: str
    date_text: str
    vendor: str
    customer: str
    currency: str
    items: list[tuple[str, int, Decimal]]  # description, quantity, unit price
    tax_rate: Decimal
    total_error: Decimal = Decimal("0")  # printed total = real total + error


SAMPLES = [
    Sample(
        filename="acme_INV-1001.pdf",
        language="en",
        number="INV-1001",
        date_text="October 15, 2026",
        vendor="Acme Supplies LLC",
        customer="Blue Bakery Inc.",
        currency="USD",
        items=[
            ("Flour 25kg bag", 4, Decimal("18.90")),
            ("Sugar 10kg", 2, Decimal("12.40")),
            ("Yeast 500g", 6, Decimal("3.75")),
        ],
        tax_rate=Decimal("0.08"),
    ),
    Sample(
        filename="northwind_NW-2045.pdf",
        language="en",
        number="NW-2045",
        date_text="2026-10-20",
        vendor="Northwind Traders GmbH",
        customer="Cafe Lumen",
        currency="EUR",
        items=[
            ("Espresso beans 1kg", 10, Decimal("24.50")),
            ("Paper cups (pack of 100)", 5, Decimal("6.20")),
        ],
        tax_rate=Decimal("0.19"),
    ),
    Sample(
        filename="padaria_FAT-0789.pdf",
        language="pt",
        number="FAT-0789",
        date_text="28/10/2026",
        vendor="Distribuidora Sul Ltda",
        customer="Padaria Pão Quente",
        currency="BRL",
        items=[
            ("Farinha de trigo 25kg", 3, Decimal("119.90")),
            ("Manteiga 5kg", 2, Decimal("164.50")),
            ("Fermento 500g", 4, Decimal("22.00")),
        ],
        tax_rate=Decimal("0.05"),
    ),
    Sample(
        filename="bluesky_INV-3310.pdf",
        language="en",
        number="INV-3310",
        date_text="Nov 1, 2026",
        vendor="Blue Sky Print Co.",
        customer="Green Leaf Market",
        currency="USD",
        items=[
            ("Flyers A5 (1000 units)", 2, Decimal("85.00")),
            ("Business cards (500)", 3, Decimal("29.90")),
        ],
        tax_rate=Decimal("0.07"),
        total_error=Decimal("10.00"),  # deliberate mistake: must be flagged
    ),
]


def money(value: Decimal, language: str) -> str:
    text = f"{value:,.2f}"  # 1,234.50
    if language == "pt":
        text = text.replace(",", "_").replace(".", ",").replace("_", ".")  # 1.234,50
    return text


def write_line(pdf: FPDF, text: str, size: int = 11, bold: bool = False) -> None:
    pdf.set_font("Helvetica", "B" if bold else "", size)
    pdf.cell(0, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def render_en(pdf: FPDF, sample: Sample, subtotal: Decimal, tax: Decimal) -> None:
    write_line(pdf, sample.vendor, size=16, bold=True)
    write_line(pdf, f"INVOICE {sample.number}", size=13)
    write_line(pdf, f"Date: {sample.date_text}")
    write_line(pdf, f"Bill to: {sample.customer}")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    with pdf.table(
        col_widths=(90, 20, 40, 40), text_align=("LEFT", "RIGHT", "RIGHT", "RIGHT")
    ) as table:
        table.row(["Description", "Qty", "Unit price", "Amount"])
        for description, qty, price in sample.items:
            amount = qty * price
            table.row([description, str(qty), money(price, "en"), money(amount, "en")])
    pdf.ln(4)

    total = subtotal + tax + sample.total_error
    write_line(pdf, f"Subtotal: {sample.currency} {money(subtotal, 'en')}")
    write_line(
        pdf, f"Tax ({sample.tax_rate:.0%}): {sample.currency} {money(tax, 'en')}"
    )
    write_line(pdf, f"TOTAL DUE: {sample.currency} {money(total, 'en')}", bold=True)


def render_pt(pdf: FPDF, sample: Sample, subtotal: Decimal, tax: Decimal) -> None:
    write_line(pdf, f"FATURA Nº {sample.number}", size=16, bold=True)
    write_line(pdf, f"Emitente: {sample.vendor}")
    write_line(pdf, f"Cliente: {sample.customer}")
    write_line(pdf, f"Data de emissão: {sample.date_text}")
    pdf.ln(4)

    for description, qty, price in sample.items:
        amount = money(qty * price, "pt")
        write_line(pdf, f"{qty} x {description} (R$ {money(price, 'pt')} cada)")
        write_line(pdf, f"      Valor: R$ {amount}")
    pdf.ln(4)

    total = subtotal + tax + sample.total_error
    write_line(pdf, f"Subtotal: R$ {money(subtotal, 'pt')}")
    write_line(pdf, f"Impostos ({sample.tax_rate:.0%}): R$ {money(tax, 'pt')}")
    write_line(pdf, f"Total a pagar: R$ {money(total, 'pt')}", bold=True)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    for sample in SAMPLES:
        subtotal = sum((qty * price for _, qty, price in sample.items), Decimal("0"))
        tax = (subtotal * sample.tax_rate).quantize(CENTS)

        pdf = FPDF()
        pdf.add_page()
        if sample.language == "en":
            render_en(pdf, sample, subtotal, tax)
        else:
            render_pt(pdf, sample, subtotal, tax)

        path = OUTPUT_DIR / sample.filename
        pdf.output(str(path))
        print(f"Created {path}")


if __name__ == "__main__":
    main()
