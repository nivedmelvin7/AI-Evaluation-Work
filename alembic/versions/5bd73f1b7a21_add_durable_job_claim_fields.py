"""add durable job claim fields

Revision ID: 5bd73f1b7a21
Revises: 8e8da02c7b81
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5bd73f1b7a21"
down_revision: Union[str, Sequence[str], None] = "8e8da02c7b81"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evaluation_versions",
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "evaluation_versions",
        sa.Column("worker_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "evaluation_versions",
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "evaluation_versions",
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_evaluation_versions_queue",
        "evaluation_versions",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_evaluation_versions_heartbeat",
        "evaluation_versions",
        ["status", "heartbeat_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_evaluation_versions_heartbeat", table_name="evaluation_versions")
    op.drop_index("ix_evaluation_versions_queue", table_name="evaluation_versions")
    op.drop_column("evaluation_versions", "heartbeat_at")
    op.drop_column("evaluation_versions", "claimed_at")
    op.drop_column("evaluation_versions", "worker_id")
    op.drop_column("evaluation_versions", "attempt_count")
