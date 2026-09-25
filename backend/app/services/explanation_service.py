
import json
import os

from dotenv import load_dotenv
from groq import Groq

from app.schemas.explanation import MedicalExplanation


load_dotenv()


class GroqExplanationService:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        self.client = Groq(api_key=api_key)

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        )

    def explain(
        self,
        extracted_text: str,
        structured_data: dict,
        clinical_context: dict
    ) -> MedicalExplanation:

        # Prepare the input data for the model.
        # Limit the raw OCR text to avoid excessively large prompts.
        input_data = {
            "structured_data": structured_data,
            "clinical_context": clinical_context,
            "original_report_text": extracted_text[:15000]
        }

        system_prompt = """
You are a medical report explanation assistant.

Your task is to explain the information explicitly present
in a medical report in clear, simple language for a patient.

IMPORTANT SAFETY AND ACCURACY RULES:

1. Explain the report for educational purposes only.
   Do not diagnose diseases or predict outcomes.

2. Do not prescribe treatments, recommend medication changes,
   or tell the patient to start or stop any medication.

3. Use only the supplied report data for patient-specific claims.
   Do not invent test results, values, units, reference ranges,
   medical history, symptoms, or clinical findings.

4. Explain what a medical test generally measures using
   established general medical knowledge. Clearly distinguish
   this general explanation from what the patient's result
   specifically establishes.

5. Use the exact values, units, flags, and reference ranges
   supplied in structured_data. Do not independently create
   a reference range when one is missing.

6. If the report does not provide sufficient information
   to interpret a result, explicitly state this limitation.

7. Do not assume that an abnormal result establishes a disease.
   Explain that individual results may require interpretation
   by a qualified healthcare professional in clinical context.

8. Respect negations and uncertainty in the original report.
   For example, "no fever" must never be explained as
   "fever", and a suspected finding must not be described
   as confirmed.

9. Explain medical history, symptoms, medications, findings,
   and recommendations only when they are present in the
   supplied clinical_context or original report.

10. Do not invent medication indications, dosages,
    treatment plans, or reasons for prescribing medications.

11. Do not interpret a listed recommendation as proof that
    the patient has a particular disease.

12. Keep explanations concise, understandable, and factual.
    Explain technical terms in everyday language.

13. The confidence field represents confidence that the
    explanation is accurately grounded in the supplied data.
    It does not represent diagnostic certainty.

14. Include important observations only when they are
    directly supported by the report. Do not exaggerate
    the significance of any finding.

15. If there are no parameters or clinical context items
    to explain, return empty arrays for the corresponding
    fields rather than inventing information.

16. Do not independently diagnose or grade an injury
    based on examination findings. Explain what the
    documented finding generally indicates, and distinguish
    it from the diagnosis explicitly stated in the report.

17. Do not classify a numerical result as normal, abnormal,
    high, or low unless the supplied report provides the
    corresponding flag or reference range. If providing
    general medical context, clearly label it as general
    information rather than a patient-specific conclusion.

18. Do not infer the reason a medication was prescribed
    unless the report explicitly states the indication.
    Explain its general use separately when appropriate.

19. Preserve inequalities and uncertainty exactly.
    For example, "less than 2 seconds" must not be converted
    into an exact value of 2.0 seconds.

20. Before returning the response, check grammar, spacing,
    and punctuation. Ensure that words are separated
    correctly and that the explanation is readable.

Return the result strictly according to the supplied
JSON schema. Do not include Markdown or text outside JSON.
"""

        user_prompt = f"""
Explain the following medical report.

INPUT DATA:
{json.dumps(input_data, ensure_ascii=False)}

For every parameter in structured_data.parameters:

- Identify the parameter by its exact name.
- Summarize the reported result, including the value,
  unit, flag, and reference range when available.
- Explain what the test generally measures.
- Explain what the supplied result indicates, without
  diagnosing or making unsupported clinical conclusions.
- Explain why the test is generally relevant.
- Include limitations where appropriate.
- Preserve the source_text when it is supplied.
- Assign a grounding confidence level.

For every relevant item in clinical_context:

- Explain the item's meaning in plain language.
- Preserve its category and source_text where supplied.
- Do not turn symptoms or medical history into diagnoses.
- Do not infer medication indications or treatment outcomes.

Also provide:

- A brief overall report_summary.
- A list of important_observations supported by the report.
- General limitations relevant to interpreting this report.
- The educational disclaimer from the schema.

Return only the JSON object matching the provided schema.
"""

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "medical_explanation",
                    "schema": MedicalExplanation.model_json_schema(),
                    "strict": True
                }
            },
            temperature=0.2,
            max_completion_tokens=6000
        )

        response_content = completion.choices[0].message.content

        if not response_content:
            raise ValueError(
                "Groq returned an empty explanation response"
            )

        # Parse the JSON response.
        explanation_data = json.loads(response_content)

        # Validate the response against our Pydantic schema.
        explanation = MedicalExplanation.model_validate(
            explanation_data
        )

        return explanation
