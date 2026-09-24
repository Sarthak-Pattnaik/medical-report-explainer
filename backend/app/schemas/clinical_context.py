from typing import Literal, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

Confidence = Literal["low", "medium", "high"]

class ClinicalContextItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    text: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )

    source_text: str | None = Field(
        ...,
        max_length=4000
    )

    confidence: Confidence


class ClinicalContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    medical_history: list[ClinicalContextItem]
    symptoms: list[ClinicalContextItem]
    medications: list[ClinicalContextItem]
    clinical_findings: list[ClinicalContextItem]
    recommendations: list[ClinicalContextItem]
    
    # Notice: No default values here (no `= None` or `= Field(default_factory=list)`)
    # This ensures they remain REQUIRED in the JSON schema sent to Groq.
    relevant_context: list[ClinicalContextItem]
    context_notes: list[str]

    @model_validator(mode="before")
    @classmethod
    def normalize_optional_fields(cls, data: Any) -> Any:
        """
        This runs before Pydantic validates the input. 
        It ensures that if Groq (or your app code) omits these fields or passes `null`/None, 
        they are automatically converted to empty arrays.
        """
        if isinstance(data, dict):
            # Normalize relevant_context
            if data.get("relevant_context") is None:
                data["relevant_context"] = []
                
            # Normalize context_notes
            if data.get("context_notes") is None:
                data["context_notes"] = []
                
        return data