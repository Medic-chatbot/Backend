#!/usr/bin/env python
"""
Seed/update departments, department_diseases, hospital_departments (with specialist_count)
from seed_data files, limited to hospitals present in DB (서초구 병합 기준).

Inputs:
- seed_data/department_label_map.json                 (existing departments in DB for reference)
- seed_data/disease_department_map.json               (21 disease → departments mapping)
- seed_data/hospital_서초구_병합.csv                      (scope hospitals; encrypted code is the key)
- seed_data/hospital_department_treatment_v2.csv      (nationwide department data with specialist counts)

DB connection via Backend/.env

Outputs (for audit/failures):
- seed_data/seed_failures_departments.csv
- seed_data/seed_failures_department_diseases.csv
- seed_data/seed_failures_hospital_departments.csv
"""

import os
import sys
import json
import logging
from pathlib import Path
from collections import defaultdict

import pandas as pd
from sqlalchemy.orm import Session

# Make Backend importable and ensure .env is discovered
BASE_DIR = Path(__file__).resolve().parents[1]  # Backend/
ROOT_DIR = BASE_DIR.parents[1]                  # project root
os.chdir(BASE_DIR)  # ensure Config.env_file ('.env') is found
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings
from app.db.database import SessionLocal, engine
from app.models.department import Department, DepartmentDisease, HospitalDepartment
from app.models.hospital import Hospital
from app.models.medical import Disease


logger = logging.getLogger("seed-departments")
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")

SEED_DIR = ROOT_DIR / "seed_data"


def load_seed_files():
    dept_label_map_path = SEED_DIR / "department_label_map.json"
    disease_dept_map_path = SEED_DIR / "disease_department_map.json"
    hospitals_scope_path = SEED_DIR / "hospital_서초구_병합.csv"
    v2_path = SEED_DIR / "hospital_department_treatment_v2.csv"

    with open(dept_label_map_path, "r", encoding="utf-8") as f:
        dept_label_map = json.load(f)

    with open(disease_dept_map_path, "r", encoding="utf-8") as f:
        disease_dept_map = json.load(f)

    hospitals_scope = pd.read_csv(hospitals_scope_path)
    v2 = pd.read_csv(v2_path)

    return dept_label_map, disease_dept_map, hospitals_scope, v2


def ensure_departments(db: Session, candidate_names: set) -> dict:
    """Ensure all department names exist; return {name: id}."""
    existing = {d.name: d.id for d in db.query(Department).all()}
    to_create = [name for name in sorted(candidate_names) if name not in existing]
    for name in to_create:
        d = Department(name=name)
        db.add(d)
    if to_create:
        db.commit()
        # refresh mapping
        existing = {d.name: d.id for d in db.query(Department).all()}
        logger.info(f"Created departments: {to_create}")
    return existing


def ensure_department_diseases(db: Session, disease_dept_map: dict) -> list:
    """Ensure department_diseases rows per mapping. Return failures list of dicts."""
    # Map disease names to ids (by name)
    disease_by_name = {d.name: d.id for d in db.query(Disease).all()}
    dept_by_name = {d.name: d.id for d in db.query(Department).all()}

    failures = []
    created = 0
    for disease_name, dept_names in disease_dept_map.items():
        disease_id = disease_by_name.get(disease_name)
        if not disease_id:
            failures.append({
                "disease_name": disease_name,
                "reason": "disease_not_found",
            })
            continue
        for dept_name in dept_names:
            dept_id = dept_by_name.get(dept_name)
            if not dept_id:
                failures.append({
                    "disease_name": disease_name,
                    "department_name": dept_name,
                    "reason": "department_not_found",
                })
                continue
            # Check existence
            exists = (
                db.query(DepartmentDisease)
                .filter(
                    DepartmentDisease.disease_id == disease_id,
                    DepartmentDisease.department_id == dept_id,
                )
                .first()
            )
            if not exists:
                db.add(DepartmentDisease(disease_id=disease_id, department_id=dept_id))
                created += 1
    if created:
        db.commit()
        logger.info(f"Created department_diseases rows: {created}")
    return failures


def seed_hospital_departments(db: Session, hospitals_scope: pd.DataFrame, v2: pd.DataFrame) -> list:
    """Seed hospital_departments from v2, limited to hospitals existing in DB. Returns failures list."""
    # Normalize keys
    scope_codes = set(hospitals_scope["암호화요양기호"].astype(str).unique())
    # Map encrypted_code -> hospital_id (DB is already 서초구 scoped)
    hospital_map = {h.encrypted_code: h.id for h in db.query(Hospital).all()}

    dept_by_name = {d.name: d.id for d in db.query(Department).all()}

    # Filter v2 by scope and by hospitals present in DB
    v2 = v2.copy()
    v2["암호화요양기호"] = v2["암호화요양기호"].astype(str)
    v2_scoped = v2[v2["암호화요양기호"].isin(scope_codes)]

    # Aggregate to one row per hospital+dept with summed specialist_count
    agg = (
        v2_scoped.groupby(["암호화요양기호", "진료과목코드명"], as_index=False)["과목별 전문의수"].sum()
    )

    failures = []
    created = 0
    updated = 0
    for _, row in agg.iterrows():
        enc = row["암호화요양기호"]
        dept_name = row["진료과목코드명"]
        count = int(row["과목별 전문의수"]) if pd.notna(row["과목별 전문의수"]) else None

        hospital_id = hospital_map.get(enc)
        dept_id = dept_by_name.get(dept_name)
        if not hospital_id:
            failures.append({
                "암호화요양기호": enc,
                "진료과목": dept_name,
                "reason": "hospital_not_in_db",
            })
            continue
        if not dept_id:
            failures.append({
                "암호화요양기호": enc,
                "진료과목": dept_name,
                "reason": "department_not_in_db",
            })
            continue

        existing = (
            db.query(HospitalDepartment)
            .filter(
                HospitalDepartment.hospital_id == hospital_id,
                HospitalDepartment.department_id == dept_id,
            )
            .first()
        )
        if existing:
            # Update specialist_count if different and value provided
            if count is not None and existing.specialist_count != count:
                existing.specialist_count = count
                db.add(existing)
                updated += 1
        else:
            db.add(
                HospitalDepartment(
                    hospital_id=hospital_id,
                    department_id=dept_id,
                    specialist_count=count,
                )
            )
            created += 1

    if created or updated:
        db.commit()
        logger.info(f"HospitalDepartment upserted - created: {created}, updated: {updated}")
    return failures


def main():
    logger.info("Loading seed files...")
    dept_label_map, disease_dept_map, hospitals_scope, v2 = load_seed_files()

    # Candidate departments = union of existing label map + all names in v2 + all names from disease_dept_map
    candidate_departments = set(dept_label_map.values())
    candidate_departments.update(set(v2["진료과목코드명"].astype(str).unique()))
    for names in disease_dept_map.values():
        candidate_departments.update(names)

    db = SessionLocal()
    try:
        logger.info("Ensuring departments...")
        ensure_departments(db, candidate_departments)

        logger.info("Ensuring department_diseases mapping...")
        dd_failures = ensure_department_diseases(db, disease_dept_map)

        logger.info("Seeding hospital_departments (서초구 한정 병원만)...")
        hd_failures = seed_hospital_departments(db, hospitals_scope, v2)

        # Write failures for later patching
        fail_dept = SEED_DIR / "seed_failures_departments.csv"
        fail_dd = SEED_DIR / "seed_failures_department_diseases.csv"
        fail_hd = SEED_DIR / "seed_failures_hospital_departments.csv"

        # Departments step has no direct failure file (we create missing directly), so just write empty if none
        pd.DataFrame([], columns=["note"]).to_csv(fail_dept, index=False)
        pd.DataFrame(dd_failures).to_csv(fail_dd, index=False)
        pd.DataFrame(hd_failures).to_csv(fail_hd, index=False)

        logger.info("Done. Failure files written.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
