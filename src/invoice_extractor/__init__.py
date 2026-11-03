import argparse
import logging
import os
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

from .ai import DEFAULT_MODEL, GeminiExtractor, make_client
from .pipeline import process_folder
from .report import write_reports


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract invoice data from PDFs with AI and check the numbers."
    )
    parser.add_argument("folder", type=Path, help="folder with the PDF invoices")
    parser.add_argument(
        "--output", type=Path, default=Path("output"), help="default: output"
    )
    parser.add_argument(
        "--delay", type=float, default=4.0, help="seconds between AI calls"
    )
    args = parser.parse_args()

    load_dotenv()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    client = make_client(os.environ["GEMINI_API_KEY"])
    extractor = GeminiExtractor(client, model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL))
    results = process_folder(args.folder, extractor, delay_seconds=args.delay)
    if not results:
        print(f"No PDF files found in {args.folder}")
        sys.exit(1)

    invoices_path, items_path = write_reports(results, args.output)
    counts = Counter(result.status for result in results)
    print(
        f"{len(results)} invoices: {counts['OK']} OK, "
        f"{counts['NEEDS REVIEW']} need review, {counts['FAILED']} failed"
    )
    print(f"Saved {invoices_path} and {items_path}")

    if counts["FAILED"]:
        sys.exit(1)