from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.medical_report import MedicalReport
from app.models.report_analysis import ReportAnalysis


# Maximum number of other reports included in chat context.
MAX_OTHER_REPORTS = 5

PARAMETER_FIELDS = ("name", "value", "unit", "flag", "reference_range")


def get_other_reports_context(
    db: Session,
    user_id: int,
    current_report: MedicalReport,
) -> list[dict]:
    """
    Return extracted values from the user's other completed
    reports, oldest first, for comparison in chat.
    """

    rows = db.execute(
        select(MedicalReport, ReportAnalysis)
        .join(
            ReportAnalysis,
            ReportAnalysis.report_id == MedicalReport.id,
        )
        .where(
            MedicalReport.user_id == user_id,
            MedicalReport.id != current_report.id,
            MedicalReport.status == "completed",
        )
        .order_by(MedicalReport.created_at.desc())
        .limit(MAX_OTHER_REPORTS)
    ).all()

    other_reports = []
    seen_report_ids = set()

    for report, analysis in rows:
        if report.id in seen_report_ids:
            continue

        seen_report_ids.add(report.id)

        parameters = (analysis.structured_data or {}).get(
            "parameters", []
        )

        other_reports.append({
            "report_id": report.id,
            "uploaded_at": report.created_at.strftime("%Y-%m-%d %H:%M"),
            "timing": (
                "earlier"
                if report.created_at < current_report.created_at
                else "later"
            ),
            "parameters": [
                {field: parameter.get(field) for field in PARAMETER_FIELDS}
                for parameter in parameters
                if isinstance(parameter, dict)
            ],
        })

    # Oldest first, so the timeline reads naturally.
    other_reports.reverse()

    return other_reports