"""Add hospital fields from seed data

Revision ID: 001_add_hospital_seed_fields
Revises:
Create Date: 2025-09-12 12:55:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_add_hospital_seed_fields"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 기존 hospitals 테이블에 시드 데이터 필드들만 추가

    # 시드 데이터 추가 필드들
    op.add_column("hospitals", sa.Column("opening_date", sa.Date(), nullable=True))
    op.add_column("hospitals", sa.Column("total_doctors", sa.Integer(), nullable=True))
    op.add_column("hospitals", sa.Column("dong_name", sa.String(), nullable=True))

    # 주차 정보
    op.add_column("hospitals", sa.Column("parking_slots", sa.Integer(), nullable=True))
    op.add_column(
        "hospitals", sa.Column("parking_fee_required", sa.String(), nullable=True)
    )
    op.add_column("hospitals", sa.Column("parking_notes", sa.Text(), nullable=True))

    # 휴진 안내
    op.add_column("hospitals", sa.Column("closed_sunday", sa.String(), nullable=True))
    op.add_column("hospitals", sa.Column("closed_holiday", sa.String(), nullable=True))

    # 응급실 운영
    op.add_column(
        "hospitals", sa.Column("emergency_day_available", sa.String(), nullable=True)
    )
    op.add_column(
        "hospitals", sa.Column("emergency_day_phone1", sa.String(), nullable=True)
    )
    op.add_column(
        "hospitals", sa.Column("emergency_day_phone2", sa.String(), nullable=True)
    )
    op.add_column(
        "hospitals", sa.Column("emergency_night_available", sa.String(), nullable=True)
    )
    op.add_column(
        "hospitals", sa.Column("emergency_night_phone1", sa.String(), nullable=True)
    )
    op.add_column(
        "hospitals", sa.Column("emergency_night_phone2", sa.String(), nullable=True)
    )

    # 점심시간 및 접수시간
    op.add_column(
        "hospitals", sa.Column("lunch_time_weekday", sa.String(), nullable=True)
    )
    op.add_column(
        "hospitals", sa.Column("lunch_time_saturday", sa.String(), nullable=True)
    )
    op.add_column(
        "hospitals", sa.Column("reception_time_weekday", sa.String(), nullable=True)
    )
    op.add_column(
        "hospitals", sa.Column("reception_time_saturday", sa.String(), nullable=True)
    )

    # 진료시간 (요일별) - JSON 타입
    op.add_column(
        "hospitals",
        sa.Column(
            "treatment_hours", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
    )


def downgrade() -> None:
    # hospitals 테이블에서 추가한 시드 데이터 필드들 제거
    op.drop_column("hospitals", "treatment_hours")
    op.drop_column("hospitals", "reception_time_saturday")
    op.drop_column("hospitals", "reception_time_weekday")
    op.drop_column("hospitals", "lunch_time_saturday")
    op.drop_column("hospitals", "lunch_time_weekday")
    op.drop_column("hospitals", "emergency_night_phone2")
    op.drop_column("hospitals", "emergency_night_phone1")
    op.drop_column("hospitals", "emergency_night_available")
    op.drop_column("hospitals", "emergency_day_phone2")
    op.drop_column("hospitals", "emergency_day_phone1")
    op.drop_column("hospitals", "emergency_day_available")
    op.drop_column("hospitals", "closed_holiday")
    op.drop_column("hospitals", "closed_sunday")
    op.drop_column("hospitals", "parking_notes")
    op.drop_column("hospitals", "parking_fee_required")
    op.drop_column("hospitals", "parking_slots")
    op.drop_column("hospitals", "dong_name")
    op.drop_column("hospitals", "total_doctors")
    op.drop_column("hospitals", "opening_date")
