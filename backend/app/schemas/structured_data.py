from typing import Literal, Optional

from pydantic import BaseModel, Field


Flag = Literal[
    "low",
    "high",
    "normal",
    "critical",
    "unknown",
]

Confidence = Literal[
    "low",
    "medium",
    "high",
]


class StructuredParameter(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    value: float | None = None

    unit: str | None = Field(
        default=None,
        max_length=50,
    )

    flag: Optional[str]

    reference_range: str | None = Field(
        default=None,
        max_length=200,
    )

    source_text: str | None = Field(
        default=None,
        max_length=2000,
    )

    confidence: Confidence = "low"


class StructuredMedicalData(BaseModel):
    parameters: list[StructuredParameter] = Field(
        default_factory=list
    )

    extraction_notes: list[str] = Field(
        default_factory=list
    )