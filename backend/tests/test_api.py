from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.api.reports import MAX_FILE_SIZE
from app.core.database import get_db
from app.main import app


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