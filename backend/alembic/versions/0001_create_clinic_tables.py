from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0001_create_clinic_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    status_enum = sa.Enum(
        "new",
        "invited",
        "registered",
        "ignored",
        name="clinic_lead_status",
    )
    bind = op.get_bind()
    status_enum.create(bind, checkfirst=True)

    op.create_table(
        "registered_clinics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("place_id", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_registered_clinics_place_id",
        "registered_clinics",
        ["place_id"],
        unique=False,
    )
    op.create_index(
        "ix_registered_clinics_name",
        "registered_clinics",
        ["name"],
        unique=False,
    )

    op.create_table(
        "clinic_leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("place_id", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("website", sa.String(length=2048), nullable=True),
        sa.Column(
            "emails",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "invite_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("last_invited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_invite_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            status_enum,
            nullable=False,
            server_default=sa.text("'new'"),
        ),
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
    op.create_index(
        "ix_clinic_leads_place_id",
        "clinic_leads",
        ["place_id"],
        unique=False,
    )
    op.create_index(
        "ix_clinic_leads_name",
        "clinic_leads",
        ["name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_clinic_leads_name", table_name="clinic_leads")
    op.drop_index("ix_clinic_leads_place_id", table_name="clinic_leads")
    op.drop_table("clinic_leads")

    op.drop_index("ix_registered_clinics_name", table_name="registered_clinics")
    op.drop_index("ix_registered_clinics_place_id", table_name="registered_clinics")
    op.drop_table("registered_clinics")

    status_enum = sa.Enum(
        "new",
        "invited",
        "registered",
        "ignored",
        name="clinic_lead_status",
    )
    bind = op.get_bind()
    status_enum.drop(bind, checkfirst=True)

