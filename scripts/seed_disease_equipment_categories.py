#!/usr/bin/env python
"""
Seed disease_equipment_categories from seed_data/질병_기기_매핑_fin.csv
 - 공란 장비는 '필수 없음' 처리로 건너뜀
 - 이름 정규화로 장비 대분류 매칭
 - 실패는 seed_data/seed_failures_disease_equipment_categories.csv 저장
"""
import os
import sys
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BASE_DIR.parents[1]
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import and_
from app.db.database import SessionLocal
from app.models.medical import Disease
from app.models.equipment import MedicalEquipmentCategory
from app.models.disease_equipment import DiseaseEquipmentCategory


def main():
    seed_path = ROOT_DIR / "seed_data" / "질병_기기_매핑_fin.csv"
    df = pd.read_csv(seed_path)

    db = SessionLocal()
    failures = []
    try:
        # Load maps
        disease_map = {d.name: d.id for d in db.query(Disease).all()}
        cats = db.query(MedicalEquipmentCategory).all()
        cat_by_name = {c.name: (c.id, c.code) for c in cats}
        alt_map = {
            k.replace(" ", "").replace("·", "").replace("-", ""): (v[0], v[1], k)
            for k, v in cat_by_name.items()
        }

        created = 0
        for _, row in df.iterrows():
            disease_name = str(row.get("disease", "")).strip()
            equip_name = str(row.get("장비", "")).strip()
            if not disease_name:
                continue
            disease_id = disease_map.get(disease_name)
            if not disease_id:
                failures.append({"disease": disease_name, "장비": equip_name, "reason": "disease_not_found"})
                continue
            if not equip_name:
                # 필수 없음 처리: skip row
                continue
            if equip_name in cat_by_name:
                cid, ccode = cat_by_name[equip_name]
                matched_cat_name = equip_name
            else:
                norm = equip_name.replace(" ", "").replace("·", "").replace("-", "")
                if norm in alt_map:
                    cid, ccode, matched_cat_name = alt_map[norm]
                else:
                    failures.append({"disease": disease_name, "장비": equip_name, "reason": "equipment_not_found"})
                    continue

            # upsert unique(disease_id, equipment_category_id)
            exists = (
                db.query(DiseaseEquipmentCategory)
                .filter(
                    and_(
                        DiseaseEquipmentCategory.disease_id == disease_id,
                        DiseaseEquipmentCategory.equipment_category_id == int(cid),
                    )
                )
                .first()
            )
            if not exists:
                db.add(
                    DiseaseEquipmentCategory(
                        disease_id=disease_id,
                        equipment_category_id=int(cid),
                        disease_name=disease_name,
                        equipment_category_name=matched_cat_name,
                        equipment_category_code=str(ccode),
                        source="seed_fin_v1",
                    )
                )
                created += 1
        if created:
            db.commit()
        print(f"disease_equipment_categories created: {created}")
    finally:
        db.close()
        # write failures
        fail_path = ROOT_DIR / "seed_data" / "seed_failures_disease_equipment_categories.csv"
        pd.DataFrame(failures).to_csv(fail_path, index=False)
        print(f"Failures written to {fail_path} ({len(failures)} rows)")


if __name__ == "__main__":
    main()

