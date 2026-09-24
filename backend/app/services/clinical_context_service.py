import os
from unittest import result

from dotenv import load_dotenv
from groq import Groq

from app.schemas.clinical_context import ClinicalContext


load_dotenv()


class GroqClinicalContextService:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(api_key=api_key)

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        )

    def extract(
        self,
        extracted_text: str
    ) -> ClinicalContext:

        if not extracted_text.strip():
            return ClinicalContext()

        prompt = f"""
You are extracting clinical context from a medical report.

Your task is to extract ONLY information that is explicitly
present in the provided report text.

Do NOT diagnose the patient.
Do NOT infer medical conditions.
Do NOT invent symptoms, medications, history, findings,
recommendations, or other information.

Preserve uncertainty and negation.

For example:
- "No history of diabetes" must NOT be extracted as
  "Diabetes".
- "Rule out pneumonia" must NOT be treated as a confirmed
  diagnosis.
- "Possible infection" must preserve the uncertainty.
- If something is not mentioned, leave its category empty.

Extract the following categories:

1. medical_history
  past or existing medical conditions,
  surgeries, allergies, or other medical history.
  Do NOT include medications here.

2. symptoms
   Symptoms, complaints, or reasons for consultation explicitly
   mentioned in the report.

3. medications
   medications, drugs, inhalers, therapies,
   or treatment regimens explicitly mentioned.

4. clinical_findings
  objective findings from physical examination,
  vital signs, laboratory tests, imaging, or diagnostic tests,
  including explicitly stated normal or negative findings.

5. recommendations
   Follow-up instructions, referrals, additional tests, or other
   recommendations explicitly written in the report.

6. relevant_context
  contextual information such as travel history,
  exposure history, family history, smoking history, fasting status,
  pregnancy status, or other background information that is not itself
  a clinical finding, symptom, medication, recommendation, or medical
  history item.

7. context_notes
   Important extraction limitations, ambiguity, uncertainty,
   or OCR-related issues.

For categories 1 through 6, every extracted item must be an object where:
- "text" contains the concise extracted information.
- "source_text" contains the relevant text from the report.
- "confidence" indicates confidence in the extraction (low, medium, high).

For category 7 (context_notes), provide a simple list of plain strings.

Keep each "text" field concise and avoid repeating the full
source sentence.

Use "source_text" only for the relevant supporting text.

Do not duplicate the same item across multiple categories unless
the report explicitly presents it in different contexts.

If a category has no information, return an empty array.

Always return every required top-level field, even when empty.

Medical report text:

---BEGIN REPORT---
{extracted_text}
---END REPORT---
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract structured clinical context "
                        "from medical documents. Return only "
                        "information explicitly supported by the "
                        "provided text."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_completion_tokens=4096,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "clinical_context_extraction",
                    "schema": ClinicalContext.model_json_schema(),
                    "strict": True,
                }
            }
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "Groq returned an empty clinical context response."
            )

        result = ClinicalContext.model_validate_json(content)
        if result.relevant_context is None:
            result.relevant_context = []

        if result.context_notes is None:
            result.context_notes = []

        return result