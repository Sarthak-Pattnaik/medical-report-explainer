from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.api.reports import MAX_FILE_SIZE
from app.core.database import get_db
from app.main import app
import app.api.reports as reports_module

client = TestClient(app)


class WorkingSession:
    def execute(self, statement):
        return None


class BrokenSession:
    def execute(self, statement):
        raise RuntimeError("database is down")


def use_session(session):
    def override():
        yield session

    return override


def fake_logged_in_user():
    return SimpleNamespace(id=1, email="test@example.com")


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ---------- Health checks ----------

def test_health_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_database_health_ok():
    app.dependency_overrides[get_db] = use_session(WorkingSession())

    response = client.get("/health/database")

    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_database_health_returns_503_when_database_is_down():
    app.dependency_overrides[get_db] = use_session(BrokenSession())

    response = client.get("/health/database")

    assert response.status_code == 503
    assert response.json()["status"] == "error"


# ---------- Authentication ----------

def test_reports_require_login():
    response = client.get("/reports/")

    assert response.status_code == 401


def test_invalid_token_is_rejected():
    response = client.get(
        "/reports/",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


# ---------- Upload validation ----------

def test_upload_rejects_unsupported_file_type():
    app.dependency_overrides[get_current_user] = fake_logged_in_user

    response = client.post(
        "/reports/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400


def test_upload_rejects_file_over_size_limit():
    app.dependency_overrides[get_current_user] = fake_logged_in_user

    too_big = b"0" * (MAX_FILE_SIZE + 1)

    response = client.post(
        "/reports/upload",
        files={"file": ("big.pdf", too_big, "application/pdf")},
    )

    assert response.status_code == 413

# ---------- CORS ----------

def test_cors_allows_known_frontend():
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )

    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:3000"
    )


def test_cors_rejects_unknown_site():
    response = client.get(
        "/health",
        headers={"Origin": "https://unknown-site.example.com"},
    )

    assert "access-control-allow-origin" not in response.headers


# ---------- Retry explanation ----------

class FakeAnalysisSession:
    def __init__(self, analysis):
        self.analysis = analysis
        self.committed = False

    def scalar(self, statement):
        return self.analysis

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def make_analysis(explanation=None):
    return SimpleNamespace(
        report_id=7,
        explanation=explanation,
        extracted_text="Hemoglobin 11.8 g/dL",
        structured_data={},
        clinical_context={},
        created_at=datetime(2026, 11, 8, tzinfo=timezone.utc),
    )


class FakeExplanationService:
    def explain(self, **kwargs):
        return SimpleNamespace(
            model_dump=lambda: {"report_summary": "Test summary"}
        )


class FailingExplanationService:
    def explain(self, **kwargs):
        raise RuntimeError("Groq is down")


def use_retry_session(session):
    app.dependency_overrides[get_current_user] = fake_logged_in_user
    app.dependency_overrides[get_db] = use_session(session)


def test_retry_explanation_not_found():
    use_retry_session(FakeAnalysisSession(None))

    response = client.post("/reports/7/explanation/retry")

    assert response.status_code == 404


def test_retry_explanation_refuses_when_one_exists():
    session = FakeAnalysisSession(
        make_analysis(explanation={"report_summary": "Existing"})
    )
    use_retry_session(session)

    response = client.post("/reports/7/explanation/retry")

    assert response.status_code == 409
    assert session.committed is False


def test_retry_explanation_saves_new_explanation(monkeypatch):
    monkeypatch.setattr(
        reports_module, "GroqExplanationService", FakeExplanationService
    )
    session = FakeAnalysisSession(make_analysis())
    use_retry_session(session)

    response = client.post("/reports/7/explanation/retry")

    assert response.status_code == 200
    assert response.json()["explanation"] == {
        "report_summary": "Test summary"
    }
    assert session.committed is True


def test_retry_explanation_reports_ai_failure(monkeypatch):
    monkeypatch.setattr(
        reports_module, "GroqExplanationService", FailingExplanationService
    )
    session = FakeAnalysisSession(make_analysis())
    use_retry_session(session)

    response = client.post("/reports/7/explanation/retry")

    assert response.status_code == 502
    assert session.committed is False