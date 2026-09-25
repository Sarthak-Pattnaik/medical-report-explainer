from app.schemas.explanation import MedicalExplanation


sample = MedicalExplanation(
    report_summary=(
        "The report contains a hemoglobin result "
        "of 11.2 g/dL, marked as low."
    ),
    parameter_explanations=[
        {
            "parameter_name": "Hemoglobin",
            "result_summary": "11.2 g/dL — marked low.",
            "what_it_measures": (
                "Hemoglobin is a protein in red blood "
                "cells that carries oxygen."
            ),
            "what_your_result_means": (
                "The result is below the reference "
                "range stated in the report."
            ),
            "why_it_matters": (
                "It helps assess the blood's "
                "oxygen-carrying capacity."
            ),
            "limitations": [
                "Interpretation depends on the "
                "laboratory reference range."
            ],
            "source_text": "Hemoglobin: 11.2 g/dL",
            "confidence": "high"
        }
    ],
    clinical_context_explanations=[],
    important_observations=[],
    limitations=[],
)

print(sample.model_dump_json(indent=2))