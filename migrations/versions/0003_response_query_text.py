"""response.query as TEXT: a resolve turn's query no longer fits in 255 characters

/resolve stores its turn with the retrieval query, which is the alarm title plus its
description (migration 0002). Several descriptions make that longer than 255
characters, so the insert failed with StringDataRightTruncation: the turn was not
stored, the response had no response_id, and a /chat follow-up in the same
conversation had no history to rewrite against, so it retrieved unrelated sections
and answered "not covered".

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-22
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE response ALTER COLUMN query TYPE TEXT")


def downgrade() -> None:
    # shorten longer queries rather than fail the downgrade
    op.execute("ALTER TABLE response ALTER COLUMN query TYPE VARCHAR(255) USING left(query, 255)")
