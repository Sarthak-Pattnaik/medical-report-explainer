
import json

from app.services.explanation_service import (
    GroqExplanationService
)


# Sample structured data.
structured_data = {
    "parameters": [
        {
            "name": "Hemoglobin",
            "value": 12.5,
            "unit": "g/dL",
            "flag": "low",
            "reference_range": "13.0-17.0 g/dL",
            "source_text": "Hemoglobin: 12.5 g/dL (13.0-17.0)",
            "confidence": "high"
        },
        {
            "name": "WBC",
            "value": 7500,
            "unit": "cells/mcL",
            "flag": "normal",
            "reference_range": "4000-11000 cells/mcL",
            "source_text": "WBC: 7500 cells/mcL",
            "confidence": "high"
        }
    ],
    "extraction_method": "groq"
}


# Sample clinical context.
clinical_context = {
    "medical_history": [
        {
            "text": "History of asthma",
            "source_text": "Past medical history: Asthma",
            "confidence": "high"
        }
    ],
    "symptoms": [
        {
            "text": "Cough for 3 days",
            "source_text": "Cough for 3 days",
            "confidence": "high"
        }
    ],
    "medications": [
        {
            "text": "Albuterol",
            "source_text": "Medication: Albuterol",
            "confidence": "high"
        }
    ],
    "clinical_findings": [
        {
            "text": "Wheezing on examination",
            "source_text": "Chest: Wheezing present",
            "confidence": "high"
        }
    ],
    "recommendations": [],
    "relevant_context": [],
    "context_notes": []
}


# Sample OCR text.
extracted_text = """
Patient Report

Hemoglobin: 12.5 g/dL (Reference: 13.0-17.0 g/dL)
WBC: 7500 cells/mcL (Reference: 4000-11000 cells/mcL)

Past medical history: Asthma
Cough for 3 days
Medication: Albuterol
Chest: Wheezing present
"""


def main():

    service = GroqExplanationService()

    explanation = service.explain(
        extracted_text=extracted_text,
        structured_data=structured_data,
        clinical_context=clinical_context
    )

    # Convert the Pydantic object to a dictionary.
    result = explanation.model_dump()

    print("\n--- MEDICAL EXPLANATION ---\n")

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
