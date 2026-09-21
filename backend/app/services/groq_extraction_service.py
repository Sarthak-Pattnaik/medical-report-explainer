import json
import os

from dotenv import load_dotenv
from groq import Groq

from app.schemas.structured_data import (
    StructuredMedicalData,
)

load_dotenv()


def patch_schema_for_strict_mode(schema: dict) -> dict:
    """
    Recursively patch Pydantic's JSON schema to comply with 
    Groq/OpenAI strict mode requirements.
    """
    if not isinstance(schema, dict):
        return schema

    # 1. Remove keys that strict mode explicitly rejects
    schema.pop("title", None)
    schema.pop("default", None)

    # 2. If this is an object, enforce strict properties and required arrays
    if schema.get("type") == "object" or "properties" in schema:
        schema["additionalProperties"] = False
        if "properties" in schema:
            schema["required"] = list(schema["properties"].keys())

    # 3. Recursively traverse all nested dictionaries and lists
    for key, value in schema.items():
        if isinstance(value, dict):
            patch_schema_for_strict_mode(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    patch_schema_for_strict_mode(item)
                    
    return schema


class GroqExtractionService:
    """
    Extracts structured medical parameters
    using Groq-hosted language models.
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(
            api_key=api_key
        )

        # Update to a model from YOUR list
        self.model_name = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b", # or "openai/gpt-oss-20b"
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
5. Preserve original source text.
6. Assign low confidence to unclear information.
7. Do not provide diagnoses or treatment advice.
8. Return only valid JSON.
9. Follow the requested JSON structure exactly.

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

        # Generate and recursively patch the schema for strict mode
        raw_schema = StructuredMedicalData.model_json_schema()
        strict_schema = patch_schema_for_strict_mode(raw_schema)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a medical report data extraction assistant. "
                        "Extract information explicitly present in the report and output valid JSON only.\n\n"
                        "Rules:\n"
                        "1. Never invent medical values.\n"
                        "2. Never diagnose the patient or recommend treatment.\n"
                        "3. Preserve ambiguous or suspicious units exactly as written.\n"
                        "4. Do not infer flags without explicit reference ranges.\n"
                        "5. You must return a valid JSON object matching the required schema. Do not wrap the JSON in Markdown code blocks (no ```json code fence).\n"
                        "6. Always return a valid JSON object, even if no parameters are found."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"{self._build_prompt(extracted_text)}\n\n"
                        "Provide the extracted medical data as a valid JSON object matching the requested fields."
                    ),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "medical_report_extraction",
                    "schema": strict_schema,
                    "strict": True,
                },
            },
            temperature=0,
            max_tokens=8192,
        )

        response_text = response.choices[0].message.content

        if not response_text:
            raise ValueError(
                "Groq returned an empty response."
            )

        parsed_data = json.loads(response_text)

        return StructuredMedicalData.model_validate(parsed_data)