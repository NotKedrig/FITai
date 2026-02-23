"""Add confidence column to recommendations.

Revision ID: 0002
Revises: 0001
Create Date: Add confidence to recommendations table

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "recommendations",
        sa.Column("confidence", sa.String(length=10), nullable=False, server_default="medium"),
    )


def downgrade() -> None:
    op.drop_column("recommendations", "confidence")
