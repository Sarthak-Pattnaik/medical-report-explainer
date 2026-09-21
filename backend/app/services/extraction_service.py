from dotenv import load_dotenv

load_dotenv()

import logging
import traceback

from app.services.groq_extraction_service import (
    GroqExtractionService,
)

from app.services.ai_extraction_service import (
    AIExtractionService,
)

from app.services.structured_extraction_service import (
    extract_structured_data,
)

from app.services.extraction_normalizer import (
    normalize_rule_based_data,
)

from app.schemas.structured_data import (
    StructuredMedicalData,
)


logger = logging.getLogger(__name__)


def validate_extraction_result(
    structured_data: dict,
) -> dict:
    """
    Adds warnings for missing values, missing units,
    and low-confidence extraction results.
    """

    parameters = structured_data.get(
        "parameters",
        [],
    )

    notes = structured_data.setdefault(
        "extraction_notes",
        [],
    )

    for parameter in parameters:
        name = parameter.get(
            "name",
            "Unknown",
        )

        value = parameter.get("value")
        unit = parameter.get("unit")
        confidence = parameter.get(
            "confidence"
        )

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


def extract_medical_data(
    extracted_text: str,
) -> tuple[dict, str]:
    """
    Extracts medical data using the following priority:

    1. Groq
    2. Gemini
    3. Rule-based extraction

    Returns:
        tuple[dict, str]:
            Structured data and extraction method.
    """

    # --------------------------------------------------
    # 1. Try Groq
    # --------------------------------------------------

    try:
        logger.info(
            "Trying Groq extraction..."
        )

        groq_service = GroqExtractionService()

        groq_result = groq_service.extract(
            extracted_text
        )

        groq_data = groq_result.model_dump()

        groq_data = validate_extraction_result(
            groq_data
        )

        logger.info(
            "Groq extraction successful."
        )

        return groq_data, "groq"

    except Exception as error:
        logger.warning(
            "Groq extraction failed: %s",
            error,
        )

        traceback.print_exc()

    # --------------------------------------------------
    # 2. Try Gemini
    # --------------------------------------------------

    try:
        logger.info(
            "Trying Gemini extraction..."
        )

        gemini_service = AIExtractionService()

        gemini_result = gemini_service.extract(
            extracted_text
        )

        gemini_data = gemini_result.model_dump()

        gemini_data = validate_extraction_result(
            gemini_data
        )

        logger.info(
            "Gemini extraction successful."
        )

        return gemini_data, "gemini"

    except Exception as error:
        logger.warning(
            "Gemini extraction failed: %s",
            error,
        )

        traceback.print_exc()

    # --------------------------------------------------
    # 3. Try rule-based extraction
    # --------------------------------------------------

    try:
        logger.info(
            "Trying rule-based extraction..."
        )

        fallback_result = extract_structured_data(
            extracted_text
        )

        normalized_result = (
            normalize_rule_based_data(
                fallback_result
            )
        )

        rule_based_data = (
            normalized_result.model_dump()
        )

        logger.info(
            "Rule-based extraction completed."
        )

        return rule_based_data, "rule_based"

    except Exception as error:
        logger.error(
            "Rule-based extraction failed: %s",
            error,
        )

        traceback.print_exc()

    # --------------------------------------------------
    # 4. All methods failed
    # --------------------------------------------------

    empty_result = StructuredMedicalData(
        parameters=[],
        extraction_notes=[
            "All extraction methods failed."
        ],
    )

    return empty_result.model_dump(), "failed"