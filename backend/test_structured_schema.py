from app.schemas.structured_data import (
    StructuredMedicalData,
)


def test_valid_structured_data():
    data = StructuredMedicalData(
        parameters=[
            {
                "name": "Hemoglobin",
                "value": 11.2,
                "unit": "g/dL",
                "flag": "low",
                "reference_range": "12.0-15.5",
                "source_text": "Hemoglobin Low 11.2",
                "confidence": "high",
            }
        ],
        extraction_notes=[
            "Extraction should be verified by the user."
        ],
    )

    assert len(data.parameters) == 1
    assert data.parameters[0].name == "Hemoglobin"
    assert data.parameters[0].value == 11.2
    assert data.parameters[0].flag == "low"


def test_default_values():
    data = StructuredMedicalData()

    assert data.parameters == []
    assert data.extraction_notes == []


def test_invalid_flag():
    try:
        StructuredMedicalData(
            parameters=[
                {
                    "name": "Hemoglobin",
                    "value": 11.2,
                    "flag": "invalid_flag",
                }
            ]
        )

        assert False, "Invalid flag should raise an error"

    except ValueError:
        assert True