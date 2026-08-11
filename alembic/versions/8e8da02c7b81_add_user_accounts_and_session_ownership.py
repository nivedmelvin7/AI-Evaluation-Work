"""add user accounts and session ownership

Revision ID: 8e8da02c7b81
Revises: 6c9e7b8d1a24
Create Date: 2026-08-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8e8da02c7b81"
down_revision: Union[str, Sequence[str], None] = "6c9e7b8d1a24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=True),
        sa.Column("google_subject", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("google_subject"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.add_column("sessions", sa.Column("owner_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_sessions_owner_id_users", "sessions", "users", ["owner_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index(op.f("ix_sessions_owner_id"), "sessions", ["owner_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sessions_owner_id"), table_name="sessions")
    op.drop_constraint("fk_sessions_owner_id_users", "sessions", type_="foreignkey")
    op.drop_column("sessions", "owner_id")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
