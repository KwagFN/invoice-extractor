import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from invoice_extractor.ai import DEFAULT_MODEL, GeminiExtractor
from invoice_extractor.pdf_text import extract_text
from invoice_extractor.validation import find_issues

def main() -> None:
    load_dotenv()
    pdf_path = Path(sys.argv[1])

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    extractor = GeminiExtractor(client, model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL))

    invoice = extractor.extract(extract_text(pdf_path))
    print(invoice.model_dump_json(indent=2))
    print("Issues:", find_issues(invoice) or "none")


if __name__ == "__main__":
    main()