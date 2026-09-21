import os

from anthropic import Anthropic
from dotenv import load_dotenv

from app.schemas.structured_data import (
    StructuredMedicalData,
)

load_dotenv()


class AnthropicExtractionService:
    """
    Extracts structured medical parameters
    using Anthropic Claude.
    """

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not configured."
            )

        self.client = Anthropic(
            api_key=api_key
        )

        self.model_name = os.getenv(
            "ANTHROPIC_MODEL",
            "claude-haiku-4-5",
        )

    def _build_prompt(
        self,
        extracted_text: str,
    ) -> str:

        return f"""
You are a medical report data extraction assistant.

Extract only medical parameters explicitly
present in the supplied report text.

Rules:
1. Never invent values, units, or reference ranges.
2. Preserve ambiguous units exactly as written.
3. Do not silently correct OCR errors.
4. Do not infer medical flags without supporting
   report information.
5. Preserve the original source text.
6. Use low confidence for unclear information.
7. Do not provide diagnoses or treatment advice.
8. Return structured data matching the schema.

Report text:
---
{extracted_text}
---
"""

    def extract(
        self,
        extracted_text: str,
    ) -> StructuredMedicalData:

        if not extracted_text.strip():
            return StructuredMedicalData(
                extraction_notes=[
                    "No text was available for extraction."
                ]
            )

        prompt = self._build_prompt(
            extracted_text
        )

        response = self.client.messages.parse(
            model=self.model_name,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            output_format=StructuredMedicalData,
        )

        result = response.parsed_output

        if result is None:
            raise ValueError(
                "Anthropic returned no parsed output."
            )

        return result