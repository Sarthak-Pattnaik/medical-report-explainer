from app.services.extraction_normalizer import (
    normalize_rule_based_data,
)


def test_normalize_rule_based_data():
    rule_based_data = {
        "hemoglobin": {
            "value": 11.2,
            "flag": "low",
        },
        "fasting_glucose": {
            "value": 116.0,
            "flag": "high",
        },
    }

    result = normalize_rule_based_data(
        rule_based_data
    )

    assert len(result.parameters) == 2
    assert result.parameters[0].value == 11.2
    assert result.parameters[0].confidence == "low"