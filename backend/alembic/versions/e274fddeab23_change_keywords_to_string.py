"""Change keywords to string

Revision ID: e274fddeab23
Revises: 3d0153c93b8e
Create Date: 2026-03-12 13:05:55.119681

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e274fddeab23'
down_revision: Union[str, Sequence[str], None] = '3d0153c93b8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Some environments previously created `keywords` as JSONB (array form).
    # Newer schema uses String. Convert only when the existing type is jsonb.
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'clinics'
              AND column_name = 'keywords'
              AND udt_name = 'jsonb'
          ) THEN
            ALTER TABLE clinics
              ALTER COLUMN keywords TYPE VARCHAR(255)
              USING (keywords::text);
            ALTER TABLE clinics
              ALTER COLUMN keywords DROP DEFAULT;
            ALTER TABLE clinics
              ALTER COLUMN keywords DROP NOT NULL;
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Best-effort downgrade: if column is VARCHAR, convert to JSONB array.
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'clinics'
              AND column_name = 'keywords'
              AND udt_name = 'varchar'
          ) THEN
            ALTER TABLE clinics
              ALTER COLUMN keywords TYPE JSONB
              USING (
                CASE
                  WHEN keywords IS NULL OR btrim(keywords) = '' THEN '[]'::jsonb
                  ELSE to_jsonb(ARRAY[keywords])
                END
              );
            ALTER TABLE clinics
              ALTER COLUMN keywords SET DEFAULT '[]'::jsonb;
            ALTER TABLE clinics
              ALTER COLUMN keywords SET NOT NULL;
          END IF;
        END $$;
        """
    )
