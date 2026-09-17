from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    Text,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.medical_report import MedicalReport


class ReportAnalysis(Base):
    __tablename__ = "report_analyses"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    report_id: Mapped[int] = mapped_column(
        ForeignKey("medical_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    extracted_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    structured_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True
    )

    explanation: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    report: Mapped["MedicalReport"] = relationship(
        back_populates="analyses"
    )