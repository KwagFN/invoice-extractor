from typing import Protocol

from google import genai
from google.genai import types
from pydantic import ValidationError

from .models import Invoice

DEFAULT_MODEL = "gemini-3.5-flash-lite"

INSTRUCTIONS = """\
You extract data from invoices. Copy every value exactly as printed on the \
invoice: do not calculate, correct or round anything, even if the numbers \
look wrong. Write dates as YYYY-MM-DD and amounts as plain numbers, without \
currency symbols or thousands separators (for example, "R$ 1.234,56" \
becomes 1234.56)."""

class ExtractionError(Exception):
    """Raised when the AI response cannot be turned into a valid Invoice."""

class InvoiceExtractor(Protocol):
    def extract(self, text: str) -> Invoice: ...

class GeminiExtractor:
    def __init__(self, client: genai.Client, model: str = DEFAULT_MODEL) -> None:
        self.client = client
        self.model = model

    def extract(self, text: str) -> Invoice:
        response = self.client.models.generate_content(
            model=self.model,
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCTIONS,
                response_mime_type="application/json",
                response_json_schema=Invoice.model_json_schema(),
            ),
        )
        if not response.text:
            raise ExtractionError("The AI returned an empty response")

        try:
            return Invoice.model_validate_json(response.text)
        except ValidationError as exc:
            raise ExtractionError(
                f"The AI response is not a valid invoice: {exc}"
            ) from exc