"""Create unified clinics table.

Revision ID: 0001_unified_clinics
Revises: None
Create Date: 2026-03-04

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_unified_clinics"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create unified clinics table."""
    
    op.create_table(
        "clinics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("place_id", sa.String(length=255), nullable=True, unique=True),
        sa.Column("website", sa.String(length=2048), nullable=True),
        sa.Column(
            "emails",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "clinic_location",
            postgresql.JSONB(),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "registered",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "invited_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("last_invited", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    
    # Create indices
    op.create_index("ix_clinics_name", "clinics", ["name"])
    op.create_index("ix_clinics_place_id", "clinics", ["place_id"])


def downgrade() -> None:
    """Drop unified clinics table."""
    op.drop_index("ix_clinics_place_id", table_name="clinics")
    op.drop_index("ix_clinics_name", table_name="clinics")
    op.drop_table("clinics")
