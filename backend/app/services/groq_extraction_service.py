import json
import logging
import os
import time

from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    Groq,
    InternalServerError,
    RateLimitError,
)

from app.schemas.structured_data import (
    StructuredMedicalData,
    StructuredParameter,
)
from app.services.text_chunking import (
    split_into_chunks,
    strip_repeated_lines,
)

load_dotenv()

logger = logging.getLogger(__name__)

# Tokens reserved for each answer. Reasoning tokens share
# this budget, so reasoning effort is kept low.
MAX_COMPLETION_TOKENS = 3000

# Attempts per chunk when Groq reports its rate limit.
MAX_ATTEMPTS = 3

# Longest single wait, and the most time spent on one report.
MAX_WAIT_SECONDS = 60
MAX_TOTAL_SECONDS = 300


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


def _retry_after_seconds(error: RateLimitError) -> float:
    """
    Read how long Groq asks us to wait, within sensible bounds.
    """

    try:
        wait = float(error.response.headers.get("retry-after", 20))
    except (TypeError, ValueError):
        wait = 20.0

    return min(max(wait, 1.0), MAX_WAIT_SECONDS)


def _remove_duplicates(
    parameters: list[StructuredParameter],
) -> list[StructuredParameter]:
    """
    The same result can appear in two parts of a long report,
    for example on a summary page. Keep the first copy.
    """

    seen = set()
    unique = []

    for parameter in parameters:
        key = (
            parameter.name.strip().lower(),
            parameter.value,
            (parameter.unit or "").strip().lower(),
        )

        if key not in seen:
            seen.add(key)
            unique.append(parameter)

    return unique


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

        # Retries are handled in _extract_chunk_with_retry,
        # so the client's own automatic retries are turned off.
        self.client = Groq(
            api_key=api_key,
            max_retries=0,
        )

        self.model_name = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b",
        )

    def _build_prompt(
        self,
        extracted_text: str,
    ) -> str:

        return f"""
You are a medical report data extraction assistant.

Extract only medical parameters explicitly
present in the supplied report text.

The text may be one part of a longer report.
Extract only what appears in this part.

Rules:
1. Never invent values, units, or reference ranges.
2. Preserve ambiguous units exactly as written.
3. Do not silently correct OCR errors.
4. Do not infer medical flags without supporting
   report information.
5. Keep source_text short: copy only the line
   the value came from.
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
        pages: list[str] | None = None,
    ) -> StructuredMedicalData:
        """
        Extract parameters from the whole report. Long reports
        are cleaned and split into chunks so that each request
        stays within Groq's tokens-per-minute limit.
        """

        if not extracted_text.strip():
            return StructuredMedicalData(
                extraction_notes=[
                    "No text was available for extraction."
                ]
            )

        chunks = split_into_chunks(
            strip_repeated_lines(pages or [extracted_text])
        )

        started = time.monotonic()
        parameters = []
        notes = []
        failed = 0

        for index, chunk in enumerate(chunks, start=1):
            result = self._extract_chunk_with_retry(chunk, started)

            if result is None:
                failed += 1
                notes.append(
                    f"Part {index} of {len(chunks)} of the report "
                    "could not be processed."
                )
                continue

            parameters.extend(result.parameters)
            notes.extend(result.extraction_notes)

        logger.info(
            "Groq extraction: %d chunks, %d failed",
            len(chunks),
            failed,
        )

        if failed == len(chunks):
            raise RuntimeError(
                "Groq could not process any part of the report."
            )

        return StructuredMedicalData(
            parameters=_remove_duplicates(parameters),
            extraction_notes=list(dict.fromkeys(notes)),
        )

    def _extract_chunk_with_retry(
        self,
        chunk: str,
        started: float,
    ) -> StructuredMedicalData | None:
        """
        Extract one chunk. On a rate limit, wait as long as Groq
        asks and try again. Returns None if the chunk fails.
        """

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return self._extract_chunk(chunk)

            except RateLimitError as error:
                wait = _retry_after_seconds(error)
                elapsed = time.monotonic() - started

                if (
                    attempt == MAX_ATTEMPTS
                    or elapsed + wait > MAX_TOTAL_SECONDS
                ):
                    logger.warning(
                        "Groq rate limit: skipping this part"
                    )
                    return None

                logger.info(
                    "Groq rate limit: waiting %.0f seconds",
                    wait,
                )
                time.sleep(wait)

            except (APIConnectionError, InternalServerError):
                # Network problem or a Groq server error:
                # usually temporary, so wait briefly and retry.
                if attempt == MAX_ATTEMPTS:
                    logger.exception(
                        "Groq unavailable: skipping this part"
                    )
                    return None

                time.sleep(2 ** attempt)

            except Exception:
                logger.exception(
                    "Groq could not process a part of the report"
                )
                return None

        return None

    def _extract_chunk(
        self,
        chunk: str,
    ) -> StructuredMedicalData:

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
                        f"{self._build_prompt(chunk)}\n\n"
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
            reasoning_effort="low",
            max_completion_tokens=MAX_COMPLETION_TOKENS,
        )

        response_text = response.choices[0].message.content

        if not response_text:
            raise ValueError(
                "Groq returned an empty response."
            )

        parsed_data = json.loads(response_text)

        return StructuredMedicalData.model_validate(parsed_data)