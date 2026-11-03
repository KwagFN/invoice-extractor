import csv
from pathlib import Path

from factories import make_invoice

from invoice_extractor.pipeline import Result
from invoice_extractor.report import write_reports


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def test_writes_one_row_per_invoice_and_one_per_line_item(tmp_path):
    issue = "Subtotal + tax = 27.50, but total is 99.00"
    results = [
        Result(Path("a.pdf"), make_invoice()),
        Result(Path("b.pdf"), make_invoice(), (issue,)),
    ]

    invoices_path, items_path = write_reports(results, tmp_path)

    invoices = read_rows(invoices_path)
    assert [row["status"] for row in invoices] == ["OK", "NEEDS REVIEW"]
    assert invoices[0]["total"] == "27.50"
    assert invoices[1]["details"] == issue
    assert len(read_rows(items_path)) == 4


def test_failed_file_keeps_the_error_and_leaves_invoice_columns_empty(tmp_path):
    results = [Result(Path("broken.pdf"), error="ExtractionError: bad json")]

    invoices_path, items_path = write_reports(results, tmp_path)

    row = read_rows(invoices_path)[0]
    assert row["status"] == "FAILED"
    assert row["details"] == "ExtractionError: bad json"
    assert row["invoice_number"] == ""
    assert read_rows(items_path) == []