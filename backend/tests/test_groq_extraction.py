import httpx
import pytest
from groq import InternalServerError, RateLimitError

from app.schemas.structured_data import StructuredMedicalData
from app.services import groq_extraction_service as service_module
from app.services.groq_extraction_service import GroqExtractionService


def make_service(monkeypatch, chunk_results):
    """
    Build the service with a fake _extract_chunk that returns
    (or raises) the given results in order.
    """

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    service = GroqExtractionService()
    calls = []
    results = iter(chunk_results)

    def fake_extract_chunk(chunk):
        calls.append(chunk)
        result = next(results)
        if isinstance(result, Exception):
            raise result
        return result

    service._extract_chunk = fake_extract_chunk
    return service, calls


def data(*parameters, notes=()):
    return StructuredMedicalData.model_validate(
        {
            "parameters": [
                {"name": n, "value": v, "unit": u, "flag": None}
                for n, v, u in parameters
            ],
            "extraction_notes": list(notes),
        }
    )


def rate_limit_error(seconds="2"):
    request = httpx.Request("POST", "https://api.groq.com/test")
    response = httpx.Response(
        429, headers={"retry-after": seconds}, request=request
    )
    return RateLimitError("rate limited", response=response, body=None)


def two_chunk_pages():
    # Each page is close to the chunk size, so they become two chunks.
    return ["Haemoglobin 11.8 g/dL\n" + "x" * 5000, "Ferritin 18 ng/mL\n" + "y" * 5000]


def test_empty_text_returns_note(monkeypatch):
    service, calls = make_service(monkeypatch, [])

    result = service.extract("   ")

    assert result.parameters == []
    assert calls == []


def test_chunks_are_merged_and_duplicates_removed(monkeypatch):
    service, calls = make_service(
        monkeypatch,
        [
            data(("Haemoglobin", 11.8, "g/dL")),
            data(("haemoglobin ", 11.8, "g/dL"), ("Ferritin", 18, "ng/mL")),
        ],
    )

    result = service.extract("text", pages=two_chunk_pages())

    assert len(calls) == 2
    assert [p.name for p in result.parameters] == ["Haemoglobin", "Ferritin"]


def test_waits_and_retries_on_rate_limit(monkeypatch):
    waits = []
    monkeypatch.setattr(service_module.time, "sleep", waits.append)
    service, calls = make_service(
        monkeypatch,
        [rate_limit_error("2"), data(("Ferritin", 18, "ng/mL"))],
    )

    result = service.extract("Ferritin 18 ng/mL")

    assert waits == [2.0]
    assert len(calls) == 2
    assert result.parameters[0].name == "Ferritin"


def test_failed_part_adds_note(monkeypatch):
    service, _ = make_service(
        monkeypatch,
        [data(("Haemoglobin", 11.8, "g/dL")), ValueError("bad JSON")],
    )

    result = service.extract("text", pages=two_chunk_pages())

    assert [p.name for p in result.parameters] == ["Haemoglobin"]
    assert "Part 2 of 2 of the report could not be processed." in result.extraction_notes


def test_raises_when_every_part_fails(monkeypatch):
    service, _ = make_service(monkeypatch, [ValueError("bad JSON")])

    with pytest.raises(RuntimeError):
        service.extract("Ferritin 18 ng/mL")


def test_wait_is_capped(monkeypatch):
    assert service_module._retry_after_seconds(rate_limit_error("999")) == 60
    assert service_module._retry_after_seconds(rate_limit_error("abc")) == 20

def server_error():
    request = httpx.Request("POST", "https://api.groq.com/test")
    response = httpx.Response(500, request=request)
    return InternalServerError("server error", response=response, body=None)


def test_retries_on_server_error(monkeypatch):
    waits = []
    monkeypatch.setattr(service_module.time, "sleep", waits.append)
    service, calls = make_service(
        monkeypatch,
        [server_error(), data(("Ferritin", 18, "ng/mL"))],
    )

    result = service.extract("Ferritin 18 ng/mL")

    assert waits == [2]
    assert result.parameters[0].name == "Ferritin"


def test_client_does_not_retry_by_itself(monkeypatch):
    service, _ = make_service(monkeypatch, [])

    assert service.client.max_retries == 0