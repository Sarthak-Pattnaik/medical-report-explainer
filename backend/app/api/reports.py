
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

from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatRequest

from app.services.report_history_service import (
    get_other_reports_context
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

@router.post("/{report_id}/chat")
def chat_with_report(
    report_id: int,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --------------------------------------------------
    # 1. Verify report ownership
    # --------------------------------------------------

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

    # --------------------------------------------------
    # 2. Retrieve latest report analysis
    # --------------------------------------------------

    analysis = db.scalar(
        select(ReportAnalysis)
        .where(
            ReportAnalysis.report_id == report_id
        )
        .order_by(
            ReportAnalysis.created_at.desc(),
            ReportAnalysis.id.desc()
        )
        .limit(1)
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found for this report"
        )

    if analysis.explanation is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chat is unavailable because the report explanation has not been generated"
        )

    # --------------------------------------------------
    # 3. Retrieve previous conversation messages
    # --------------------------------------------------

    previous_messages = db.scalars(
        select(ChatMessage)
        .where(
            ChatMessage.report_id == report_id
        )
        .order_by(
            ChatMessage.created_at.desc(),
            ChatMessage.id.desc()
        )
        .limit(12)
    ).all()

# Reverse to restore chronological order.
    conversation_history = [
        {
            "role": message.role,
            "content": message.content
        }
        for message in reversed(previous_messages)
    ]

    # Retrieve the user's other reports for comparison.
    other_reports = get_other_reports_context(
        db=db,
        user_id=current_user.id,
        current_report=report,
    )

    # --------------------------------------------------
    # 4. Generate AI response
    # --------------------------------------------------

    try:
        explanation_service = GroqExplanationService()

        answer, sources = explanation_service.chat(
            extracted_text=analysis.extracted_text or "",
            structured_data=analysis.structured_data or {},
            clinical_context=analysis.clinical_context or {},
            explanation=analysis.explanation or {},
            conversation_history=conversation_history,
            user_message=request.message,
            other_reports=other_reports,
            current_report_uploaded_at=report.created_at.strftime(
                "%Y-%m-%d %H:%M"
            )
        )

    except Exception:
        db.rollback()

        print("REPORT CHAT GENERATION FAILED:", error)

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate a response. Please try again."
        )

    # --------------------------------------------------
    # 5. Save user message and AI response
    # --------------------------------------------------

    user_message = ChatMessage(
        report_id=report_id,
        role="user",
        content=request.message
    )

    assistant_message = ChatMessage(
        report_id=report_id,
        role="assistant",
        content=answer
    )

    try:
        db.add_all([
            user_message,
            assistant_message
        ])

        db.commit()

        db.refresh(user_message)
        db.refresh(assistant_message)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save chat messages"
        )

    # --------------------------------------------------
    # 6. Return response
    # --------------------------------------------------

    return {
        "report_id": report_id,
        "user_message": {
            "id": user_message.id,
            "role": user_message.role,
            "content": user_message.content,
            "created_at": user_message.created_at
        },
        "assistant_message": {
            "id": assistant_message.id,
            "role": assistant_message.role,
            "content": assistant_message.content,
            "created_at": assistant_message.created_at
        },
        "sources": sources
    }

@router.get("/{report_id}/chat")
def get_report_chat(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify report ownership.
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

    # Retrieve chat messages in chronological order.
    messages = db.scalars(
        select(ChatMessage)
        .where(
            ChatMessage.report_id == report_id
        )
        .order_by(
            ChatMessage.created_at.asc(),
            ChatMessage.id.asc()
        )
    ).all()

    return {
        "report_id": report_id,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at
            }
            for message in messages
        ]
    }

@router.delete("/{report_id}/chat")
def delete_report_chat(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --------------------------------------------------
    # 1. Verify report ownership
    # --------------------------------------------------

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

    # --------------------------------------------------
    # 2. Retrieve existing chat messages
    # --------------------------------------------------

    messages = db.scalars(
        select(ChatMessage).where(
            ChatMessage.report_id == report_id
        )
    ).all()

    if not messages:
        return {
            "report_id": report_id,
            "message": "No chat history exists for this report",
            "deleted_count": 0
        }

    # --------------------------------------------------
    # 3. Delete chat messages
    # --------------------------------------------------

    deleted_count = len(messages)

    try:
        for message in messages:
            db.delete(message)

        db.commit()

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete chat history"
        )

    # --------------------------------------------------
    # 4. Return confirmation
    # --------------------------------------------------

    return {
        "report_id": report_id,
        "message": "Chat history deleted successfully",
        "deleted_count": deleted_count
    }