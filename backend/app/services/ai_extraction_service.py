from dotenv import load_dotenv

load_dotenv()

import json
import os
import re
import time

from google import genai
from google.genai import errors

from app.schemas.structured_data import (
    StructuredMedicalData,
)

def validate_extraction_result(
    structured_data: dict,
) -> dict:
    """
    Adds warnings for potentially incomplete
    or ambiguous extracted parameters.
    """

    parameters = structured_data.get(
        "parameters",
        []
    )

    notes = structured_data.setdefault(
        "extraction_notes",
        []
    )

    for parameter in parameters:
        name = parameter.get("name", "Unknown")
        value = parameter.get("value")
        unit = parameter.get("unit")
        confidence = parameter.get("confidence")

        if value is None:
            notes.append(
                f"{name}: No numeric value was extracted."
            )

        if not unit:
            notes.append(
                f"{name}: Unit is missing."
            )

        if confidence == "low":
            notes.append(
                f"{name}: Extraction has low confidence "
                "and should be verified."
            )

    return structured_data

class AIExtractionService:
    """
    Extracts structured medical parameters from
    medical report text using an AI model.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.model_names = [
        "gemini-2.5-pro",
        "gemini-pro-latest",
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-3.7-flash"
        ]

        self.max_retries = 2

    def _generate_with_fallback(
    self,
    prompt: str
):
        last_error = None

        for model_name in self.model_names:

            for attempt in range(self.max_retries + 1):

                try:
                    print(
                    f"Trying model: {model_name} "
                    f"(attempt {attempt + 1})"
                    )

                    response = (
                    self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    )

                    return response

                except errors.ServerError as error:
                    last_error = error

                    print(
                    f"Temporary error with "
                    f"{model_name}: {error}"
                    )

                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)

                except errors.ClientError as error:
                    last_error = error

                    print(
                    f"Client error with "
                    f"{model_name}: {error}"
                    )

                    # Move to the next model immediately
                    break

        raise RuntimeError(
        "All AI models failed."
        ) from last_error

    def _build_prompt(self, extracted_text: str) -> str:
        return f"""
You are a medical report data extraction assistant.

Your task is to extract only the medical parameters
explicitly present in the provided report text.

Rules:
1. Do not invent or estimate values.
2. Extract numeric test results when available.
3. Preserve the units and reference ranges.
4. Use "unknown" when the flag cannot be determined.
5. Use low confidence when the text is unclear.
6. Do not provide a medical diagnosis.
7. Return only valid JSON.
8. If no reliable parameters are found, return
   an empty parameters list.
9. Never invent, guess, or silently correct a value or unit.
10. Preserve ambiguous units exactly as they appear in
    the source text.
11. Do not infer low, high, normal, or critical flags
    unless explicitly stated or supported by a provided
    reference range.
12. For combined measurements such as blood pressure,
    split the values only when the source clearly
    supports the interpretation.
13. Preserve the original source text for every parameter.
14. Assign low confidence when OCR or report text is unclear.
15. Add an extraction note whenever a unit, value, or
    interpretation is uncertain.
16. Do not provide a diagnosis or treatment recommendation.
17. Extract only information explicitly present in the report.

Required JSON structure:
{{
  "parameters": [
    {{
      "name": "Hemoglobin",
      "value": 11.2,
      "unit": "g/dL",
      "flag": "low",
      "reference_range": "12.0-15.5",
      "source_text": "Original supporting text",
      "confidence": "high"
    }}
  ],
  "extraction_notes": []
}}

Medical report text:
---
{extracted_text}
---
"""

    def _clean_json_response(
        self,
        response_text: str
    ) -> str:
        """
        Removes Markdown code fences if the model
        returns JSON inside them.
        """

        cleaned_text = response_text.strip()

        cleaned_text = re.sub(
        r"```json\s*",
        "",
        cleaned_text,
        flags=re.IGNORECASE,
        )

        cleaned_text = re.sub(
        r"```",
        "",
        cleaned_text,
        )

        # Extract the JSON object
        start_index = cleaned_text.find("{")
        end_index = cleaned_text.rfind("}")

        if start_index == -1 or end_index == -1:
            raise ValueError(
            "No valid JSON object found in AI response."
            )

        return cleaned_text[
        start_index:end_index + 1
        ].strip()

    def extract(
        self,
        extracted_text: str
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

        response = self._generate_with_fallback(
            prompt
        )

        response_text = response.text

        if not response_text:
            raise ValueError(
                "The AI model returned an empty response."
            )

        cleaned_json = self._clean_json_response(
            response_text
        )

        parsed_data = json.loads(cleaned_json)

        validated_data = StructuredMedicalData.model_validate(
            parsed_data
        )

        return validated_data