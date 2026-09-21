from typing import Any

from app.schemas.structured_data import (
    StructuredMedicalData,
)


def normalize_rule_based_data(
    data: dict[str, Any],
) -> StructuredMedicalData:
    """
    Converts the existing rule-based extraction
    format into the standardized AI format.
    """

    parameters = []
    extraction_notes = []

    for name, details in data.items():

        if not isinstance(details, dict):
            continue

        value = details.get("value")
        flag = details.get("flag")

        parameters.append(
            {
                "name": name,
                "value": value,
                "unit": details.get("unit"),
                "flag": flag,
                "reference_range": details.get(
                    "reference_range"
                ),
                "source_text": details.get(
                    "source_text"
                ),
                "confidence": "low",
            }
        )

    return StructuredMedicalData(
        parameters=parameters,
        extraction_notes=extraction_notes,
    )