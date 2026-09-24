from app.services.clinical_context_service import (
    GroqClinicalContextService
)


sample_text = """
Patient reports fatigue and headache for two weeks.

Past medical history includes hypertension.
Patient is currently taking medication X.

No history of diabetes.

Follow-up recommended after four weeks.
"""


service = GroqClinicalContextService()

result = service.extract(sample_text)

print(
    result.model_dump_json(indent=2)
)