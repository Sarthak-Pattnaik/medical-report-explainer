import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import ReportAnalysis
from app.services.explanation_service import GroqExplanationService


def main(report_id: int) -> None:
    db = SessionLocal()

    try:
        analysis = db.scalar(
            select(ReportAnalysis)
            .where(ReportAnalysis.report_id == report_id)
            .order_by(
                ReportAnalysis.created_at.desc(),
                ReportAnalysis.id.desc(),
            )
            .limit(1)
        )

        if analysis is None:
            print(f"No analysis found for report {report_id}")
            return

        explanation = GroqExplanationService().explain(
            extracted_text=analysis.extracted_text or "",
            structured_data=analysis.structured_data or {},
            clinical_context=analysis.clinical_context or {},
        )

        analysis.explanation = explanation.model_dump()
        db.commit()

        print(f"Explanation regenerated for report {report_id}")

    finally:
        db.close()


if __name__ == "__main__":
    main(int(sys.argv[1]))