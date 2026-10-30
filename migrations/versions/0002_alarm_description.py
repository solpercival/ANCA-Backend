"""alarm description: a fixed description of each alarm, for retrieval

The alarm's title and runtime message make a weak search query: the message
carries values from one occurrence and few of the documentation's terms. The
description is written per alarm code in those terms (see
docs/alarm-description-guidelines.md). Empty for alarms that have none.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-14
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE alarm_code ADD COLUMN IF NOT EXISTS description TEXT NOT NULL DEFAULT ''"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE alarm_code DROP COLUMN IF EXISTS description")
