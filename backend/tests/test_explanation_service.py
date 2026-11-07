from app.services.explanation_service import _compact_explanation


FULL_EXPLANATION = {
    "report_summary": "Hemoglobin is below the report's range.",
    "parameter_explanations": [
        {
            "parameter_name": "Hemoglobin",
            "result_summary": "11.8 g/dL, flagged low",
            "what_it_measures": "A long general description...",
            "what_your_result_means": "Below the report's range.",
            "why_it_matters": "Another long description...",
            "limitations": [],
            "source_text": "Hemoglobin 11.8 g/dL 13.0 - 17.0 L",
            "confidence": "high",
        }
    ],
    "clinical_context_explanations": [
        {"category": "remarks", "item": "...", "explanation": "..."}
    ],
    "important_observations": ["Low hemoglobin"],
    "limitations": ["Single report only"],
    "disclaimer": "Educational only.",
}


def test_keeps_patient_specific_parts():
    compact = _compact_explanation(FULL_EXPLANATION)

    assert compact["report_summary"] == FULL_EXPLANATION["report_summary"]
    assert compact["important_observations"] == ["Low hemoglobin"]
    assert compact["limitations"] == ["Single report only"]
    assert compact["parameter_results"] == [
        {
            "parameter_name": "Hemoglobin",
            "what_your_result_means": "Below the report's range.",
        }
    ]


def test_drops_repeated_and_general_parts():
    compact = _compact_explanation(FULL_EXPLANATION)

    assert "clinical_context_explanations" not in compact
    assert "disclaimer" not in compact

    result = compact["parameter_results"][0]
    assert "what_it_measures" not in result
    assert "why_it_matters" not in result
    assert "source_text" not in result


def test_handles_missing_explanation():
    assert _compact_explanation(None) == {}
    assert _compact_explanation({}) == {}