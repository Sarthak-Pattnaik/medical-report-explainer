"""remove on update cascade from chat_messages fk

Revision ID: 7f5d4cafa1cf
Revises: ca05cb9c354a
Create Date: 2026-11-08 15:00:30.471998

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f5d4cafa1cf'
down_revision: Union[str, Sequence[str], None] = 'ca05cb9c354a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FK_NAME = "chat_messages_report_id_fkey"


def upgrade() -> None:
    """
    Recreate the chat_messages -> medical_reports foreign key with
    ON DELETE CASCADE only, matching the ChatMessage model.

    The Supabase database had ON UPDATE CASCADE added by hand in the
    dashboard, outside migrations. On a fresh database this simply
    recreates the same key.
    """
    op.drop_constraint(FK_NAME, "chat_messages", type_="foreignkey")

    op.create_foreign_key(
        FK_NAME,
        "chat_messages",
        "medical_reports",
        ["report_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Intentionally empty: before this migration the key differed
    # between databases (Supabase had ON UPDATE CASCADE, fresh
    # databases did not), so there is no single state to restore.
    pass
