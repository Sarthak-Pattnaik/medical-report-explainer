
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.medical_report import MedicalReport
from app.models.user import User

from fastapi.responses import FileResponse
from mimetypes import guess_type

from app.models.report_analysis import ReportAnalysis
from app.services.ocr_service import extract_text

from app.services.structured_extraction_service import (
    extract_structured_data,
)

from app.services.extraction_service import (
    extract_medical_data,
)

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", status_code=status.HTTP_201_CREATED)
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

    unique_filename = f"{uuid4()}{extension}"
    file_path = UPLOAD_DIR / unique_filename

    file_path.write_bytes(file_content)

    report = MedicalReport(
    user_id=current_user.id,
    file_name=unique_filename,
    file_path=str(file_path),
    status="processing"
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    try:
        extracted_text = extract_text(str(file_path))
        
        structured_data, extraction_method = (
        extract_medical_data(extracted_text)
        )

        print(
            "SELECTED EXTRACTION METHOD:",
            extraction_method,
        )

        if isinstance(structured_data, dict):
            structured_data["extraction_method"] = (
            extraction_method
        )

        analysis = ReportAnalysis(
        report_id=report.id,
        extracted_text=extracted_text,
        structured_data=structured_data,
        explanation=None
        )

        db.add(analysis)

        report.status = "text_extracted"

        db.commit()
        db.refresh(report)

    except Exception as error:
        db.rollback()

        report.status = "extraction_failed"

        db.add(report)
        db.commit()

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


from sqlalchemy import select


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

    file_path = Path(report.file_path)

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found"
        )

    media_type, _ = guess_type(report.file_name)
    media_type = media_type or "application/octet-stream"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=report.file_name
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