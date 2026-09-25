
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from fastapi.responses import Response

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.medical_report import MedicalReport
from app.models.user import User

from fastapi.responses import FileResponse
from mimetypes import guess_type
from sqlalchemy import select
from app.models.report_analysis import ReportAnalysis
from app.services.ocr_service import extract_text

import os
from app.services.storage_service import StorageService

from app.services.extraction_service import (
    extract_medical_data,
)

from app.services.clinical_context_service import (
    GroqClinicalContextService
)

from app.services.explanation_service import (
    GroqExplanationService
)

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)




ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED
)
async def upload_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing"
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, JPG, JPEG, and PNG files are allowed"
        )

    file_content = await file.read()

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size must not exceed 10 MB"
        )

    # --------------------------------------------------
    # Create unique storage path
    # --------------------------------------------------

    unique_filename = f"{uuid4()}{extension}"

    storage_path = (
        f"{current_user.id}/{unique_filename}"
    )

    content_types = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }

    content_type = content_types.get(
        extension,
        "application/octet-stream"
    )

    storage_service = StorageService()
    report = None

    try:

        # --------------------------------------------------
        # Upload to Supabase Storage
        # --------------------------------------------------

        storage_service.upload_bytes(
            file_data=file_content,
            storage_path=storage_path,
            content_type=content_type,
        )

        # --------------------------------------------------
        # Create database record
        # --------------------------------------------------

        report = MedicalReport(
            user_id=current_user.id,
            file_name=unique_filename,
            file_path=storage_path,
            status="processing"
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        # --------------------------------------------------
        # Download from Supabase temporarily for OCR
        # --------------------------------------------------

        ocr_file_path = storage_service.download_to_temp(
            storage_path=storage_path,
            suffix=extension,
        )

        try:
            extracted_text = extract_text(
                ocr_file_path
            )

        finally:
            try:
                os.unlink(ocr_file_path)
            except OSError:
                pass

        # --------------------------------------------------
        # Structured extraction
        # Groq → Gemini → Rule-based
        # --------------------------------------------------

        structured_data, extraction_method = (
            extract_medical_data(
                extracted_text
            )
        )

        print(
            "SELECTED EXTRACTION METHOD:",
            extraction_method,
        )

        if isinstance(structured_data, dict):
            structured_data[
                "extraction_method"
            ] = extraction_method

        # --------------------------------------------------
        # Clinical context extraction
        # --------------------------------------------------

        try:
            clinical_context_service = GroqClinicalContextService()

            clinical_context = clinical_context_service.extract(
                extracted_text
            )

            clinical_context_data = clinical_context.model_dump()

        except Exception as error:
            print(
                "CLINICAL CONTEXT EXTRACTION FAILED:",
            error
            )

            clinical_context_data = {
                "medical_history": [],
                "symptoms": [],
                "medications": [],
                "clinical_findings": [],
                "recommendations": [],
                "relevant_context": [],
                "context_notes": [
                "Clinical context extraction was unavailable."
                ]
            }

        
        # --------------------------------------------------
        # Medical explanation generation
        # --------------------------------------------------

        try:
            explanation_service = GroqExplanationService()

            explanation = explanation_service.explain(
                extracted_text=extracted_text,
                structured_data=structured_data,
                clinical_context=clinical_context_data
            )

            explanation_data = explanation.model_dump()

            print(
                "MEDICAL EXPLANATION GENERATED SUCCESSFULLY"
            )

        except Exception as error:
            print(
                "MEDICAL EXPLANATION GENERATION FAILED:",
                error
            )

            explanation_data = None


        # --------------------------------------------------
        # Save analysis
        # --------------------------------------------------

        analysis = ReportAnalysis(
            report_id=report.id,
            extracted_text=extracted_text,
            structured_data=structured_data,
            clinical_context=clinical_context_data,
            explanation=explanation_data
        )

        db.add(analysis)

        report.status = "completed"

        db.commit()
        db.refresh(report)

    except Exception as error:
        db.rollback()

        # Report was already committed before processing.
        # Keep the Storage file so the report remains accessible.
        if report is not None:
            try:
                report.status = "extraction_failed"
                db.add(report)
                db.commit()
            except Exception:
                db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Text extraction failed: {str(error)}"
        )

    return {
        "message": "Report uploaded successfully",
        "report_id": report.id,
        "file_name": report.file_name,
        "status": report.status
    }



@router.get("/")
def get_user_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reports = db.scalars(
        select(MedicalReport)
        .where(MedicalReport.user_id == current_user.id)
        .order_by(MedicalReport.created_at.desc())
    ).all()

    return [
        {
            "id": report.id,
            "file_name": report.file_name,
            "status": report.status,
            "created_at": report.created_at
        }
        for report in reports
    ]


from fastapi import Path as FastAPIPath


@router.get("/{report_id}")
def get_report_details(
    report_id: int = FastAPIPath(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = db.scalar(
        select(MedicalReport).where(
            MedicalReport.id == report_id,
            MedicalReport.user_id == current_user.id
        )
    )

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    return {
        "id": report.id,
        "file_name": report.file_name,
        "file_path": report.file_path,
        "status": report.status,
        "created_at": report.created_at
    }


@router.get("/{report_id}/file")
def get_report_file(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = (
        db.query(MedicalReport)
        .filter(MedicalReport.id == report_id)
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Ensure the logged-in user owns this report
    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this report"
        )

    try:
        storage_service = StorageService()

        file_data = storage_service.download_file(
            report.file_path
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File could not be retrieved: {str(error)}"
        )

    extension = Path(report.file_name).suffix.lower()

    content_types = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }

    media_type = content_types.get(
        extension,
        "application/octet-stream"
    )

    return Response(
        content=file_data,
        media_type=media_type,
        headers={
            "Content-Disposition": (
                f'inline; filename="{report.file_name}"'
            )
        }
    )

@router.get("/{report_id}/analysis")
def get_report_analysis(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = db.scalar(
        select(ReportAnalysis)
        .join(MedicalReport)
        .where(
            ReportAnalysis.report_id == report_id,
            MedicalReport.user_id == current_user.id
        )
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    return {
        "report_id": analysis.report_id,
        "extracted_text": analysis.extracted_text,
        "structured_data": analysis.structured_data,
        "explanation": analysis.explanation,
        "created_at": analysis.created_at
    }


@router.get("/{report_id}/explanation")
def get_report_explanation(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --------------------------------------------------
    # Fetch explanation with ownership verification
    # --------------------------------------------------

    analysis = db.scalar(
        select(ReportAnalysis)
        .join(MedicalReport)
        .where(
            ReportAnalysis.report_id == report_id,
            MedicalReport.user_id == current_user.id
        )
    )

    # --------------------------------------------------
    # Handle missing analysis
    # --------------------------------------------------

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # --------------------------------------------------
    # Handle unavailable explanation
    # --------------------------------------------------

    if analysis.explanation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical explanation is not available for this report"
        )

    # --------------------------------------------------
    # Return explanation
    # --------------------------------------------------

    return {
        "report_id": analysis.report_id,
        "explanation": analysis.explanation,
        "created_at": analysis.created_at
    }
