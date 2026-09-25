from typing import Literal, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


Confidence = Literal["low", "medium", "high"]


class ParameterExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parameter_name: str = Field(
        ...,
        min_length=1,
        max_length=200
    )

    result_summary: str = Field(
        ...,
        max_length=1000
    )

    what_it_measures: str = Field(
        ...,
        max_length=2000
    )

    what_your_result_means: str = Field(
        ...,
        max_length=2000
    )

    why_it_matters: str = Field(
        ...,
        max_length=2000
    )

    # Removed default_factory=list
    limitations: list[str]

    # Removed default=None, forced to use ...
    source_text: str | None = Field(
        ...,
        max_length=4000
    )

    # Removed = "low"
    confidence: Confidence

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("limitations") is None:
                data["limitations"] = []
        return data


class ClinicalContextExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    item: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )

    explanation: str = Field(
        ...,
        max_length=2000
    )

    # Removed default=None, forced to use ...
    source_text: str | None = Field(
        ...,
        max_length=4000
    )

    # Removed = "low"
    confidence: Confidence


class MedicalExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_summary: str = Field(
        ...,
        max_length=4000
    )

    # Removed default_factory=list
    parameter_explanations: list[ParameterExplanation]

    # Removed default_factory=list
    clinical_context_explanations: list[ClinicalContextExplanation]

    # Removed default_factory=list
    important_observations: list[str]

    # Removed default_factory=list
    limitations: list[str]

    # Removed the default string assignment. The LLM is forced to output a string,
    # and the validator below will inject the standard disclaimer if it misses it.
    disclaimer: str = Field(
        ...,
        max_length=1000
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        """
        Normalizes missing or null arrays to empty lists [],
        and injects the default educational disclaimer if missing.
        """
        if isinstance(data, dict):
            list_fields = [
                "parameter_explanations", 
                "clinical_context_explanations", 
                "important_observations", 
                "limitations"
            ]
            for field in list_fields:
                if data.get(field) is None:
                    data[field] = []

            # Ensure the disclaimer is always present and standard
            if not data.get("disclaimer"):
                data["disclaimer"] = (
                    "This explanation is for educational purposes "
                    "and is not a diagnosis or a substitute for "
                    "professional medical advice."
                )
                
        return data