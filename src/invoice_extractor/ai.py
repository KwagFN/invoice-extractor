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

RETRY = types.HttpRetryOptions(
    attempts=5, initial_delay=4.0, http_status_codes=[429, 500, 502, 503, 504]
)


class ExtractionError(Exception):
    """Raised when the AI response cannot be turned into a valid Invoice."""


class InvoiceExtractor(Protocol):
    def extract(self, text: str) -> Invoice: ...

    def extract_pdf(self, data: bytes) -> Invoice: ...


def make_client(api_key: str) -> genai.Client:
    """Gemini client that retries rate limits (429) and server errors."""
    return genai.Client(
        api_key=api_key, http_options=types.HttpOptions(retry_options=RETRY)
    )


class GeminiExtractor:
    def __init__(self, client: genai.Client, model: str = DEFAULT_MODEL) -> None:
        self.client = client
        self.model = model

    def extract(self, text: str) -> Invoice:
        return self._generate(text)

    def extract_pdf(self, data: bytes) -> Invoice:
        """For scanned PDFs without a text layer: the model reads the pages."""
        pdf = types.Part.from_bytes(data=data, mime_type="application/pdf")
        return self._generate([pdf])

    def _generate(self, contents: str | list[types.Part]) -> Invoice:
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
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
