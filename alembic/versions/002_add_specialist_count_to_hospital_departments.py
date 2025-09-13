"""Add specialist_count to hospital_departments

Revision ID: 002_add_specialist_count
Revises: 001_add_hospital_seed_fields
Create Date: 2025-09-13 02:05:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_add_specialist_count"
down_revision: Union[str, None] = "001_add_hospital_seed_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "hospital_departments",
        sa.Column("specialist_count", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("hospital_departments", "specialist_count")

