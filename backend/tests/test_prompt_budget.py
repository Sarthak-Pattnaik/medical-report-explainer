import json
from types import SimpleNamespace

import httpx
import pytest
from groq import APIStatusError, BadRequestError

from app.services import explanation_service as service_module
from app.services.explanation_service import GroqExplanationService
from app.services.prompt_budget import (
    TOKEN_LIMIT,
    compact_parameter,
    parameter_line,
    select_parameters,
    shorten_text,
    tokens_left,
)
from app.services.text_chunking import estimate_tokens


def param(name, flag=None, **extra):
    return {
        "name": name,
        "value": 1.0,
        "unit": "g/dL",
        "flag": flag,
        "reference_range": "1 - 2",
        "source_text": f"{name} 1.0 g/dL 1 - 2",
        "confidence": "high",
        **extra,
    }


# ---------- helpers ----------

def test_flagged_results_are_picked_first_in_report_order():
    parameters = [
        param("A"),
        param("B", flag="high"),
        param("C"),
        param("D", flag="critical"),
        param("E", flag="L"),
    ]

    picked = select_parameters(parameters, 3)

    assert [p["name"] for p in picked] == ["B", "D", "E"]


def test_all_results_kept_when_under_limit():
    parameters = [param("A"), param("B")]

    assert select_parameters(parameters, 12) == parameters


def test_compact_parameter_drops_confidence_and_shortens_source():
    compact = compact_parameter(param("A", source_text="x" * 500))

    assert "confidence" not in compact
    assert len(compact["source_text"]) == 100
    assert compact["reference_range"] == "1 - 2"


def test_parameter_line():
    line = parameter_line(param("Haemoglobin", flag="low"))

    assert line == "Haemoglobin: 1.0 g/dL | range: 1 - 2 | flag: low"
    assert parameter_line({"name": "X", "value": None}) == "X: not given"


def test_shorten_text_keeps_start_and_end():
    text = "START " + "x" * 5000 + " END"

    short = shorten_text(text, 1000)

    assert len(short) <= 1000
    assert short.startswith("START")
    assert short.endswith("END")
    assert shorten_text("short", 1000) == "short"


def test_tokens_left_is_never_negative():
    assert tokens_left(4500, "x" * 100000) == 0


# ---------- explanation ----------

EXPLANATION = {
    "report_summary": "Summary.",
    "parameter_explanations": [],
    "clinical_context_explanations": [],
    "important_observations": [],
    "limitations": [],
    "disclaimer": "Educational only.",
}


def too_large_error():
    request = httpx.Request("POST", "https://api.groq.com/test")
    response = httpx.Response(413, request=request)
    return APIStatusError("too large", response=response, body=None)


class FakeClient:
    """Returns (or raises) the given results in order and keeps
    every request it receives."""

    def __init__(self, results):
        self.results = iter(results)
        self.requests = []
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self.create)
        )

    def create(self, **request):
        self.requests.append(request)
        result = next(self.results)

        if isinstance(result, Exception):
            raise result

        message = SimpleNamespace(content=result)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def make_service(monkeypatch, results):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(service_module, "search_kb", lambda *a, **k: [])

    service = GroqExplanationService()
    service.client = FakeClient(results)

    return service


def sent_input(request):
    prompt = request["messages"][1]["content"]
    start = prompt.index("INPUT DATA:") + len("INPUT DATA:")
    end = prompt.index("For every parameter")

    return json.loads(prompt[start:end])


def names(data):
    return [line.split(":")[0] for line in data["structured_data"]["parameters"]]


def prompt_tokens(request):
    return sum(estimate_tokens(m["content"]) for m in request["messages"])


def test_small_report_explains_every_result(monkeypatch):
    service = make_service(monkeypatch, [json.dumps(EXPLANATION)])
    parameters = [param("A"), param("B")]

    explanation = service.explain(
        "Report text", {"parameters": parameters}, {}
    )

    data = sent_input(service.client.requests[0])
    assert names(data) == ["A", "B"]
    assert data["original_report_text"] == "Report text"
    assert explanation.limitations == []


def test_large_report_fits_and_says_what_was_left_out(monkeypatch):
    service = make_service(monkeypatch, [json.dumps(EXPLANATION)])
    parameters = [param(f"Test {i}") for i in range(107)]
    parameters[50]["flag"] = "high"

    explanation = service.explain(
        "line\n" * 20000, {"parameters": parameters}, {}
    )

    request = service.client.requests[0]
    data = sent_input(request)
    sent_names = names(data)

    assert len(sent_names) == 12
    assert "Test 50" in sent_names
    assert (
        prompt_tokens(request) + request["max_completion_tokens"]
        < TOKEN_LIMIT
    )
    assert "107 results" in explanation.limitations[-1]


def test_too_large_request_retries_with_less(monkeypatch):
    service = make_service(
        monkeypatch,
        [too_large_error(), too_large_error(), json.dumps(EXPLANATION)],
    )
    parameters = [param(f"Test {i}") for i in range(20)]

    service.explain("Report text", {"parameters": parameters}, {})

    first, second, third = (
        sent_input(request) for request in service.client.requests
    )
    # First drop the report text, then send fewer results.
    assert len(names(first)) == 12
    assert "original_report_text" in first
    assert len(names(second)) == 12
    assert "original_report_text" not in second
    assert len(names(third)) == 8


def test_gives_up_when_every_try_is_too_large(monkeypatch):
    service = make_service(monkeypatch, [too_large_error()] * 4)

    with pytest.raises(APIStatusError):
        service.explain("text", {"parameters": [param("A")]}, {})


# ---------- chat ----------

def test_chat_with_many_results_fits(monkeypatch):
    service = make_service(monkeypatch, ["An answer."])
    parameters = [param(f"Test {i}") for i in range(107)]

    service.chat(
        extracted_text="line\n" * 20000,
        structured_data={"parameters": parameters},
        clinical_context={},
        explanation={},
        conversation_history=[],
        user_message="What is Test 5?",
    )

    request = service.client.requests[0]
    context = request["messages"][1]["content"]

    assert "Test 106: 1.0 g/dL | range: 1 - 2" in context
    assert (
        prompt_tokens(request) + request["max_completion_tokens"]
        < TOKEN_LIMIT
    )


def other_report(report_id, count):
    return {
        "report_id": report_id,
        "uploaded_at": "2026-11-01 10:00 IST",
        "timing": "earlier",
        "parameters": [param(f"Test {i}") for i in range(count)],
    }


def test_chat_leaves_out_oldest_reports_to_fit(monkeypatch):
    service = make_service(monkeypatch, ["An answer."])
    parameters = [param(f"Test {i}") for i in range(107)]

    service.chat(
        extracted_text="line\n" * 20000,
        structured_data={"parameters": parameters},
        clinical_context={},
        explanation={},
        conversation_history=[],
        user_message="Has Test 5 changed?",
        other_reports=[other_report(i, 107) for i in range(1, 6)],
    )

    request = service.client.requests[0]
    context = request["messages"][1]["content"]

    assert "left out to fit the AI limit" in context
    assert '"report_id": 5' in context  # newest report kept
    assert '"report_id": 1,' not in context  # oldest left out
    assert (
        prompt_tokens(request) + request["max_completion_tokens"]
        < TOKEN_LIMIT
    )


def test_chat_too_large_retries_with_less(monkeypatch):
    service = make_service(monkeypatch, [too_large_error(), "An answer."])

    answer, _ = service.chat(
        extracted_text="Report text",
        structured_data={"parameters": [param("A")]},
        clinical_context={},
        explanation={},
        conversation_history=[],
        user_message="What is A?",
        other_reports=[other_report(1, 3)],
    )

    second = service.client.requests[1]["messages"][1]["content"]

    assert "An answer." in answer
    assert '"other_reports": []' in second
    assert '"extracted_text": ""' in second


def bad_json_error(failed_generation=None):
    # Same shape as Groq's real error response.
    request = httpx.Request("POST", "https://api.groq.com/test")
    response = httpx.Response(400, request=request)
    details = {"code": "json_validate_failed"}

    if failed_generation is not None:
        details["failed_generation"] = failed_generation

    return BadRequestError(
        "Generated JSON does not match the expected schema",
        response=response,
        body={"error": details},
    )


def test_valid_parts_of_rejected_answer_are_kept(monkeypatch):
    rejected = {
        **EXPLANATION,
        "clinical_context_explanations": [
            # "explanation" is missing, as in the real error.
            {
                "category": "Clinical Findings",
                "item": "TSH 6.97",
                "source_text": "TSH 6.97",
                "confidence": "high",
            },
            {
                "category": "Symptoms",
                "item": "Fatigue",
                "explanation": "The report mentions tiredness.",
                "source_text": "c/o fatigue",
                "confidence": "high",
            },
        ],
    }
    service = make_service(
        monkeypatch, [bad_json_error(json.dumps(rejected))]
    )

    explanation = service.explain(
        "Report text", {"parameters": [param("A")]}, {}
    )

    assert len(service.client.requests) == 1
    assert [c.item for c in explanation.clinical_context_explanations] == [
        "Fatigue"
    ]


def test_bad_json_answer_is_asked_again(monkeypatch):
    service = make_service(
        monkeypatch, [bad_json_error(), json.dumps(EXPLANATION)]
    )

    explanation = service.explain(
        "Report text", {"parameters": [param("A")]}, {}
    )

    assert explanation.report_summary == "Summary."
    assert len(service.client.requests) == 2


def test_gives_up_after_two_bad_json_answers(monkeypatch):
    service = make_service(monkeypatch, [bad_json_error(), "not json"])

    with pytest.raises(ValueError):
        service.explain("Report text", {"parameters": [param("A")]}, {})


def test_other_bad_requests_are_not_retried(monkeypatch):
    request = httpx.Request("POST", "https://api.groq.com/test")
    other = BadRequestError(
        "bad model",
        response=httpx.Response(400, request=request),
        body={"code": "model_not_found"},
    )
    service = make_service(monkeypatch, [other])

    with pytest.raises(BadRequestError):
        service.explain("Report text", {"parameters": [param("A")]}, {})

    assert len(service.client.requests) == 1


def test_rejected_answer_without_observations_is_asked_again(monkeypatch):
    rejected = {
        key: value
        for key, value in EXPLANATION.items()
        if key != "important_observations"
    }
    service = make_service(
        monkeypatch,
        [bad_json_error(json.dumps(rejected)), json.dumps(EXPLANATION)],
    )

    service.explain("Report text", {"parameters": [param("A")]}, {})

    assert len(service.client.requests) == 2


def test_empty_observations_are_filled_from_report_flags(monkeypatch):
    service = make_service(monkeypatch, [json.dumps(EXPLANATION)])
    parameters = [param("A", flag="high"), param("B"), param("C", flag="low")]

    explanation = service.explain(
        "Report text", {"parameters": parameters}, {}
    )

    assert explanation.important_observations == [
        "The report flags 2 result(s) outside the reference range: "
        "A (high), C (low). Please discuss these with your doctor."
    ]


def test_no_flags_means_no_made_up_observations(monkeypatch):
    service = make_service(monkeypatch, [json.dumps(EXPLANATION)])

    explanation = service.explain(
        "Report text", {"parameters": [param("A")]}, {}
    )

    assert explanation.important_observations == []


def test_source_text_is_added_from_extracted_data(monkeypatch):
    answer = {
        **EXPLANATION,
        "parameter_explanations": [
            {
                "parameter_name": "Ferritin",
                "result_summary": "18 ng/mL",
                "what_it_measures": "Iron stores.",
                "what_your_result_means": "Within the range.",
                "why_it_matters": "Shows iron stores.",
                "limitations": [],
                "source_text": None,
                "confidence": "high",
            }
        ],
    }
    service = make_service(monkeypatch, [json.dumps(answer)])

    explanation = service.explain(
        "Report text", {"parameters": [param("Ferritin")]}, {}
    )

    sent = sent_input(service.client.requests[0])
    assert "source_text" not in sent["structured_data"]["parameters"][0]
    assert (
        explanation.parameter_explanations[0].source_text
        == "Ferritin 1.0 g/dL 1 - 2"
    )
