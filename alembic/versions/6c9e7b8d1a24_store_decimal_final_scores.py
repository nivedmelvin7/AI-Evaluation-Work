"""store decimal final scores

Revision ID: 6c9e7b8d1a24
Revises: 7acbc4d78749
Create Date: 2026-08-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6c9e7b8d1a24"
down_revision: Union[str, Sequence[str], None] = "7acbc4d78749"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "evaluation_versions",
        "final_score",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=True,
        postgresql_using="final_score::double precision",
    )


def downgrade() -> None:
    op.alter_column(
        "evaluation_versions",
        "final_score",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="round(final_score)::integer",
    )
