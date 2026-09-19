import re
from typing import Any


PARAMETER_PATTERNS = {
    "hemoglobin": r"Hemoglobin \(Hgb\)\s+([\d.]+)\s+(LOW|HIGH|NORMAL)",
    "hematocrit": r"Hematocrit \(Hct\)\s+([\d.]+)\s+(LOW|HIGH|NORMAL)",
    "fasting_glucose": r"Fasting Glucose\s+([\d.]+)\s+(LOW|HIGH|NORMAL)",
    "hba1c": r"Hemoglobin A1c \(HbA1c\)\s+([\d.]+)\s+(LOW|HIGH|NORMAL)",
    "total_cholesterol": r"Total Cholesterol\s+([\d.]+)\s+(LOW|HIGH|NORMAL)",
    "triglycerides": r"Triglycerides\s+([\d.]+)\s+(LOW|HIGH|NORMAL)",
    "hdl_cholesterol": r'HDL Cholesterol \("Good"\)\s+([\d.]+)\s+(LOW|HIGH|NORMAL)',
    "ldl_cholesterol": r"LDL Cholesterol \(Calculated\)\s+([\d.]+)\s+(LOW|HIGH|NORMAL)",
    "vitamin_d": r"25-Hydroxy Vitamin D \(Total D2 \+ D3\)\s+([\d.]+)\s+(LOW|HIGH|NORMAL)",
    "alt": r"Alanine Aminotransferase \(ALT\)\s+([\d.]+)\s+(LOW|HIGH|NORMAL)",
    "ast": r"Aspartate Aminotransferase \(AST\)\s+([\d.]+)\s+(LOW|HIGH|NORMAL)",
    "tsh": r"TSH \(Thyroid Stimulating Hormone\)\s+([\d.]+)\s+(LOW|HIGH|NORMAL)",
}


def extract_structured_data(text: str) -> dict[str, Any]:
    """
    Extract selected medical parameters from raw report text.

    This is a pattern-based extraction step.
    It does not diagnose medical conditions.
    """

    structured_data: dict[str, Any] = {}

    for parameter, pattern in PARAMETER_PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            continue

        result_value = float(match.group(1))
        flag = match.group(2).lower()

        structured_data[parameter] = {
            "value": result_value,
            "flag": flag,
        }

    return structured_data