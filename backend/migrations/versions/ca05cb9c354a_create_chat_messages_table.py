"""create chat_messages table

Revision ID: ca05cb9c354a
Revises: 5c6c59c8e508
Create Date: 2026-11-08 14:37:03.069408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca05cb9c354a'
down_revision: Union[str, Sequence[str], None] = '5c6c59c8e508'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create chat_messages if it does not exist.

    Existing databases already have this table: it was created by
    Base.metadata.create_all() before this migration existed. So
    this migration only creates it on fresh databases.
    """
    inspector = sa.inspect(op.get_bind())

    if inspector.has_table("chat_messages"):
        return

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("report_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["report_id"],
            ["medical_reports.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_chat_messages_report_id"),
        "chat_messages",
        ["report_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_chat_messages_report_id"),
        table_name="chat_messages",
    )
    op.drop_table("chat_messages")
