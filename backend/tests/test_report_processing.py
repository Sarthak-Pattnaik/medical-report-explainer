from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.api.reports as reports_module
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.main import app
from app.services import report_processing_service as processing
from app.services.ocr_service import ExtractedReport
from app.services.report_processing_service import (
    COMPLETED,
    FAILED,
    PROCESSING,
    analyse_report,
    mark_vision_pages,
    process_report,
    visible_status,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def fake_logged_in_user():
    return SimpleNamespace(id=1, email="test@example.com")


class FakeStorage:
    uploads = []

    def upload_bytes(self, **kwargs):
        FakeStorage.uploads.append(kwargs)

    def download_to_temp(self, **kwargs):
        return "missing-temp-file.pdf"


class BrokenStorage:
    def upload_bytes(self, **kwargs):
        raise RuntimeError("storage is down")


class UploadSession:
    def __init__(self):
        self.added = []
        self.committed = False

    def add(self, item):
        self.added.append(item)

    def commit(self):
        self.committed = True

    def refresh(self, item):
        item.id = 42

    def rollback(self):
        pass


def use_upload_session(session):
    def override():
        yield session

    app.dependency_overrides[get_current_user] = fake_logged_in_user
    app.dependency_overrides[get_db] = override


# ---------- Upload ----------

def test_upload_returns_at_once_and_starts_processing(monkeypatch):
    scheduled = []
    monkeypatch.setattr(reports_module, "StorageService", FakeStorage)
    monkeypatch.setattr(
        reports_module,
        "process_report",
        lambda *args: scheduled.append(args),
    )
    session = UploadSession()
    use_upload_session(session)

    response = client.post(
        "/reports/upload",
        files={"file": ("report.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert response.status_code == 202
    assert response.json()["status"] == PROCESSING
    assert response.json()["report_id"] == 42
    assert session.committed is True

    report_id, storage_path, extension = scheduled[0]
    assert report_id == 42
    assert storage_path.startswith("1/") and storage_path.endswith(".pdf")
    assert extension == ".pdf"


def test_upload_storage_failure_returns_500(monkeypatch):
    scheduled = []
    monkeypatch.setattr(reports_module, "StorageService", BrokenStorage)
    monkeypatch.setattr(
        reports_module,
        "process_report",
        lambda *args: scheduled.append(args),
    )
    use_upload_session(UploadSession())

    response = client.post(
        "/reports/upload",
        files={"file": ("report.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert response.status_code == 500
    assert scheduled == []


# ---------- Background processing ----------

class ProcessingSession:
    def __init__(self, report):
        self.report = report
        self.added = []
        self.commits = 0
        self.closed = False

    def get(self, model, report_id):
        return self.report

    def add(self, item):
        self.added.append(item)

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass

    def close(self):
        self.closed = True


ANALYSIS = {
    "extracted_text": "Ferritin 18 ng/mL",
    "structured_data": {"parameters": []},
    "clinical_context": {},
    "explanation": None,
}


def run_processing(monkeypatch, analyse):
    report = SimpleNamespace(id=7, status=PROCESSING)
    session = ProcessingSession(report)
    monkeypatch.setattr(processing, "SessionLocal", lambda: session)
    monkeypatch.setattr(processing, "analyse_report", analyse)

    process_report(7, "1/report.pdf", ".pdf")

    return report, session


def test_processing_saves_analysis_and_completes(monkeypatch):
    report, session = run_processing(monkeypatch, lambda *args: ANALYSIS)

    assert report.status == COMPLETED
    assert session.added[0].extracted_text == "Ferritin 18 ng/mL"
    assert session.commits == 1
    assert session.closed is True


def test_processing_failure_marks_report_failed(monkeypatch):
    def broken(*args):
        raise RuntimeError("OCR failed")

    report, session = run_processing(monkeypatch, broken)

    assert report.status == FAILED
    assert session.added == []
    assert session.closed is True


def test_explanation_failure_still_completes(monkeypatch):
    class BrokenExplanation:
        def explain(self, **kwargs):
            raise RuntimeError("Groq is down")

    class BrokenClinicalContext:
        def extract(self, text):
            raise RuntimeError("Groq is down")

    monkeypatch.setattr(processing, "StorageService", FakeStorage)
    monkeypatch.setattr(
        processing,
        "extract_report",
        lambda path: ExtractedReport(pages=["Ferritin 18"]),
    )
    monkeypatch.setattr(
        processing,
        "extract_medical_data",
        lambda text, pages=None: ({"parameters": []}, "groq"),
    )
    monkeypatch.setattr(processing, "GroqExplanationService", BrokenExplanation)
    monkeypatch.setattr(
        processing, "GroqClinicalContextService", BrokenClinicalContext
    )

    result = analyse_report("1/report.pdf", ".pdf")

    assert result["extracted_text"] == "Ferritin 18"
    assert result["structured_data"]["extraction_method"] == "groq"
    assert result["explanation"] is None
    assert result["clinical_context"]["context_notes"] == [
        "Clinical context extraction was unavailable."
    ]


# ---------- Status shown to the user ----------

def report_created(status, minutes_ago, aware=True):
    created_at = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)

    if not aware:
        created_at = created_at.replace(tzinfo=None)

    return SimpleNamespace(status=status, created_at=created_at)


def test_recent_processing_report_stays_processing():
    assert visible_status(report_created(PROCESSING, 2)) == PROCESSING


def test_stuck_processing_report_shows_as_failed():
    assert visible_status(report_created(PROCESSING, 30)) == FAILED
    assert visible_status(report_created(PROCESSING, 30, aware=False)) == FAILED


def test_other_statuses_are_unchanged():
    assert visible_status(report_created(COMPLETED, 300)) == COMPLETED


def test_handwritten_pages_lower_confidence_and_add_note():
    structured_data = {
        "parameters": [
            {"name": "Hb", "value": 11.8, "confidence": "high"},
            {"name": "FBS", "value": 104, "confidence": "medium"},
        ],
        "extraction_notes": ["Earlier note."],
    }

    mark_vision_pages(structured_data, [1, 3])

    assert structured_data["vision_pages"] == [1, 3]
    assert {p["confidence"] for p in structured_data["parameters"]} == {"low"}
    assert structured_data["extraction_notes"][0].startswith(
        "Page(s) 1, 3 looked handwritten"
    )
    assert structured_data["extraction_notes"][1] == "Earlier note."
