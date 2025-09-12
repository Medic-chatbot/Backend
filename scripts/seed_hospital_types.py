#!/usr/bin/env python
"""
병원 종별 코드/명(hospital_type_code/name)을 hospital_types 테이블로 적재.
소스: hospitals 테이블의 distinct(code,name)
"""
import os
import sys
from pathlib import Path
from sqlalchemy import distinct

BASE_DIR = Path(__file__).resolve().parents[1]
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))

from app.db.database import SessionLocal
from app.models.hospital import Hospital, HospitalType


def main():
    db = SessionLocal()
    try:
        pairs = (
            db.query(Hospital.hospital_type_code, Hospital.hospital_type_name)
            .filter(Hospital.hospital_type_code.isnot(None))
            .filter(Hospital.hospital_type_name.isnot(None))
            .distinct()
            .all()
        )
        created = 0
        for code, name in pairs:
            exists = db.query(HospitalType).filter(HospitalType.code == str(code)).first()
            if not exists:
                db.add(HospitalType(code=str(code), name=str(name)))
                created += 1
        if created:
            db.commit()
        print(f"hospital_types upserted: created={created}, total={db.query(HospitalType).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

