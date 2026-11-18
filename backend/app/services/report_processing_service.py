"""
Processes an uploaded report in the background: OCR, structured
extraction, clinical context and explanation. A long report can
take a few minutes, so the upload request returns right away and
the frontend checks the report's status until it is done.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.models.medical_report import MedicalReport
from app.models.report_analysis import ReportAnalysis
from app.services.clinical_context_service import (
    GroqClinicalContextService,
)
from app.services.explanation_service import GroqExplanationService
from app.services.extraction_service import extract_medical_data
from app.services.ocr_service import extract_pages
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

PROCESSING = "processing"
COMPLETED = "completed"
FAILED = "extraction_failed"

# A report still "processing" after this long was interrupted,
# for example by a server restart, and is shown as failed.
PROCESSING_TIMEOUT = timedelta(minutes=20)

EMPTY_CLINICAL_CONTEXT = {
    "medical_history": [],
    "symptoms": [],
    "medications": [],
    "clinical_findings": [],
    "recommendations": [],
    "relevant_context": [],
    "context_notes": [
        "Clinical context extraction was unavailable."
    ],
}


def visible_status(report: MedicalReport) -> str:
    """
    The status to show the user. Does not change the database.
    """

    if report.status != PROCESSING or report.created_at is None:
        return report.status

    created_at = report.created_at

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) - created_at > PROCESSING_TIMEOUT:
        return FAILED

    return report.status


def analyse_report(storage_path: str, extension: str) -> dict:
    """
    Run every processing step and return the analysis fields.
    Only structured extraction may fail the report; clinical
    context and explanation have fallbacks.
    """

    # OCR on a temporary copy of the stored file.
    ocr_file_path = StorageService().download_to_temp(
        storage_path=storage_path,
        suffix=extension,
    )

    try:
        pages = extract_pages(ocr_file_path)
        extracted_text = "\n".join(pages).strip()
    finally:
        try:
            os.unlink(ocr_file_path)
        except OSError:
            pass

    # Structured extraction: Groq → Gemini → rule-based.
    structured_data, extraction_method = extract_medical_data(
        extracted_text,
        pages=pages,
    )

    logger.info("Extraction method: %s", extraction_method)

    if isinstance(structured_data, dict):
        structured_data["extraction_method"] = extraction_method

    try:
        clinical_context_data = (
            GroqClinicalContextService()
            .extract(extracted_text)
            .model_dump()
        )
    except Exception:
        logger.exception("Clinical context extraction failed")
        clinical_context_data = {
            key: list(value)
            for key, value in EMPTY_CLINICAL_CONTEXT.items()
        }

    try:
        explanation_data = (
            GroqExplanationService()
            .explain(
                extracted_text=extracted_text,
                structured_data=structured_data,
                clinical_context=clinical_context_data,
            )
            .model_dump()
        )
        logger.info("Medical explanation generated")
    except Exception:
        # The user can generate it later with the retry button.
        logger.exception("Medical explanation generation failed")
        explanation_data = None

    return {
        "extracted_text": extracted_text,
        "structured_data": structured_data,
        "clinical_context": clinical_context_data,
        "explanation": explanation_data,
    }


def process_report(report_id: int, storage_path: str, extension: str) -> None:
    """
    Background task. Uses its own database session, because the
    upload request's session is closed once the response is sent.
    """

    db = SessionLocal()

    try:
        report = db.get(MedicalReport, report_id)

        if report is None:
            logger.warning("Report %s no longer exists", report_id)
            return

        try:
            analysis_data = analyse_report(storage_path, extension)

            db.add(ReportAnalysis(report_id=report_id, **analysis_data))
            report.status = COMPLETED
            db.commit()

            logger.info("Report %s processed", report_id)

        except Exception:
            db.rollback()
            logger.exception("Report %s processing failed", report_id)

            # Keep the stored file so the report stays viewable.
            report = db.get(MedicalReport, report_id)

            if report is not None:
                report.status = FAILED
                db.commit()

    except Exception:
        db.rollback()
        logger.exception("Could not update report %s", report_id)

    finally:
        db.close()
