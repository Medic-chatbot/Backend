"""create disease_equipment_categories

Revision ID: 004_create_disease_equipment_categories
Revises: 003_create_hospital_types
Create Date: 2025-09-13 03:05:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_create_disease_equipment_categories"
down_revision: Union[str, None] = "003_create_hospital_types"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "disease_equipment_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("disease_id", sa.Integer(), sa.ForeignKey("diseases.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "equipment_category_id",
            sa.Integer(),
            sa.ForeignKey("medical_equipment_categories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("disease_name", sa.String(), nullable=False),
        sa.Column("equipment_category_name", sa.String(), nullable=False),
        sa.Column("equipment_category_code", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_disease_equipment_category",
        "disease_equipment_categories",
        ["disease_id", "equipment_category_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_disease_equipment_category", "disease_equipment_categories", type_="unique")
    op.drop_table("disease_equipment_categories")
