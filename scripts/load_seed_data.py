#!/usr/bin/env python3
"""
시드 데이터 로더 스크립트

사용법:
    python scripts/load_seed_data.py --all
    python scripts/load_seed_data.py --diseases
    python scripts/load_seed_data.py --hospitals
    python scripts/load_seed_data.py --equipment
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 프로젝트 루트 디렉토리를 Python path에 추가
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.database import get_db
from app.models.department import Department, DepartmentDisease, HospitalDepartment
from app.models.equipment import MedicalEquipmentCategory, MedicalEquipmentSubcategory
from app.models.hospital import Hospital, HospitalEquipment
from app.models.medical import Disease

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEED_DATA_DIR = Path("/Users/song-yoonju/medic/seed_data")


class SeedDataLoader:
    """시드 데이터 로더"""

    def __init__(self, db_session):
        self.db = db_session

    def load_diseases(self):
        """질병 데이터 로드"""
        logger.info("🏥 질병 데이터 로드 시작...")

        disease_file = SEED_DATA_DIR / "disease_label_map.json"
        if not disease_file.exists():
            logger.error(f"파일을 찾을 수 없습니다: {disease_file}")
            return

        with open(disease_file, "r", encoding="utf-8") as f:
            disease_map = json.load(f)

        for disease_name, disease_id in disease_map.items():
            # 이미 존재하는지 확인
            existing = (
                self.db.query(Disease).filter(Disease.name == disease_name).first()
            )
            if existing:
                logger.info(f"질병 '{disease_name}' 이미 존재함 - 건너뛰기")
                continue

            disease = Disease(
                name=disease_name,
                description=f"{disease_name} 관련 질환",
            )
            self.db.add(disease)
            logger.info(f"질병 추가: {disease_name}")

        self.db.commit()
        logger.info("✅ 질병 데이터 로드 완료!")

    def load_equipment_categories(self):
        """의료장비 대분류/세분류 데이터 로드"""
        logger.info("🔧 의료장비 데이터 로드 시작...")

        equipment_file = SEED_DATA_DIR / "장비_info.csv"
        if not equipment_file.exists():
            logger.error(f"파일을 찾을 수 없습니다: {equipment_file}")
            return

        df = pd.read_csv(equipment_file)
        logger.info(f"장비 데이터 {len(df)}개 로드됨")

        # 대분류 처리
        categories = df[["장비대분류명_정규화", "장비대분류코드"]].drop_duplicates()
        for _, row in categories.iterrows():
            category_name = row["장비대분류명_정규화"]
            category_code = row["장비대분류코드"]

            existing = (
                self.db.query(MedicalEquipmentCategory)
                .filter(MedicalEquipmentCategory.name == category_name)
                .first()
            )
            if existing:
                continue

            category = MedicalEquipmentCategory(name=category_name, code=category_code)
            self.db.add(category)

        self.db.commit()
        logger.info("대분류 데이터 로드 완료")

        # 세분류 처리
        for _, row in df.iterrows():
            category_name = row["장비대분류명_정규화"]
            subcategory_name = row["장비세분류명"]
            subcategory_code = row["장비세분류코드"]

            # 대분류 찾기
            category = (
                self.db.query(MedicalEquipmentCategory)
                .filter(MedicalEquipmentCategory.name == category_name)
                .first()
            )
            if not category:
                logger.warning(f"대분류를 찾을 수 없음: {category_name}")
                continue

            existing = (
                self.db.query(MedicalEquipmentSubcategory)
                .filter(MedicalEquipmentSubcategory.name == subcategory_name)
                .first()
            )
            if existing:
                continue

            subcategory = MedicalEquipmentSubcategory(
                category_id=category.id,
                name=subcategory_name,
                code=subcategory_code,
            )
            self.db.add(subcategory)

        self.db.commit()
        logger.info("✅ 의료장비 데이터 로드 완료!")

    def load_hospitals_sample(self, limit=50):
        """병원 데이터 샘플 로드 (전체는 너무 많아서 샘플만)"""
        logger.info(f"🏥 병원 데이터 샘플 로드 시작 (최대 {limit}개)...")

        hospital_file = SEED_DATA_DIR / "hospital_서초구_병합.csv"
        if not hospital_file.exists():
            logger.error(f"파일을 찾을 수 없습니다: {hospital_file}")
            return

        df = pd.read_csv(hospital_file)
        if limit <= 0:
            data_to_process = df
            logger.info(f"병원 데이터 {len(df)}개 로드됨 (전체 처리)")
        else:
            data_to_process = df.head(limit)
            logger.info(f"병원 데이터 {len(df)}개 로드됨 (샘플 {limit}개만 처리)")

        for i, (_, row) in enumerate(data_to_process.iterrows()):
            if pd.isna(row["암호화요양기호"]) or pd.isna(row["요양기관명"]):
                continue

            encrypted_code = str(row["암호화요양기호"])
            name = str(row["요양기관명"])

            # 이미 존재하는지 확인
            existing = (
                self.db.query(Hospital)
                .filter(Hospital.encrypted_code == encrypted_code)
                .first()
            )
            if existing:
                continue

            # 좌표 정보 처리
            try:
                latitude = float(row["좌표(Y)"]) if pd.notna(row["좌표(Y)"]) else 37.5
                longitude = float(row["좌표(X)"]) if pd.notna(row["좌표(X)"]) else 127.0
            except (ValueError, TypeError):
                latitude, longitude = 37.5, 127.0

            # 개설일자 처리
            opening_date = None
            if pd.notna(row["개설일자"]):
                try:
                    opening_date = pd.to_datetime(row["개설일자"]).date()
                except:
                    opening_date = None

            # 총의사수 처리
            total_doctors = None
            if pd.notna(row["총의사수"]):
                try:
                    total_doctors = int(row["총의사수"])
                except:
                    total_doctors = None

            # 주차_가능대수 처리
            parking_slots = None
            if pd.notna(row["주차_가능대수"]):
                try:
                    parking_slots = int(float(row["주차_가능대수"]))
                except:
                    parking_slots = None

            # 진료시간 JSON 구성
            treatment_hours = {}
            days = [
                "일요일",
                "월요일",
                "화요일",
                "수요일",
                "목요일",
                "금요일",
                "토요일",
            ]
            for day in days:
                start_col = f"진료시작시간_{day}"
                end_col = f"진료종료시간_{day}"
                if start_col in row and end_col in row:
                    start_time = (
                        str(row[start_col]) if pd.notna(row[start_col]) else None
                    )
                    end_time = str(row[end_col]) if pd.notna(row[end_col]) else None
                    if start_time and end_time:
                        treatment_hours[day] = {"start": start_time, "end": end_time}

            hospital = Hospital(
                encrypted_code=encrypted_code,
                name=name,
                address=str(row["주소"]) if pd.notna(row["주소"]) else "",
                latitude=latitude,
                longitude=longitude,
                hospital_type_code=(
                    str(row["종별코드"]) if pd.notna(row["종별코드"]) else None
                ),
                hospital_type_name=(
                    str(row["종별코드명"]) if pd.notna(row["종별코드명"]) else None
                ),
                region_code=str(row["시도코드"]) if pd.notna(row["시도코드"]) else None,
                region_name=(
                    str(row["시도코드명"]) if pd.notna(row["시도코드명"]) else None
                ),
                district_code=(
                    str(row["시군구코드"]) if pd.notna(row["시군구코드"]) else None
                ),
                district_name=(
                    str(row["시군구코드명"]) if pd.notna(row["시군구코드명"]) else None
                ),
                dong_name=str(row["읍면동"]) if pd.notna(row["읍면동"]) else None,
                postal_code=str(row["우편번호"]) if pd.notna(row["우편번호"]) else None,
                phone=str(row["전화번호"]) if pd.notna(row["전화번호"]) else None,
                website=(
                    str(row["병원홈페이지"]) if pd.notna(row["병원홈페이지"]) else None
                ),
                opening_date=opening_date,
                total_doctors=total_doctors,
                parking_slots=parking_slots,
                parking_fee_required=(
                    str(row["주차_비용 부담여부"])
                    if pd.notna(row["주차_비용 부담여부"])
                    else None
                ),
                parking_notes=(
                    str(row["주차_기타 안내사항"])
                    if pd.notna(row["주차_기타 안내사항"])
                    else None
                ),
                closed_sunday=(
                    str(row["휴진안내_일요일"])
                    if pd.notna(row["휴진안내_일요일"])
                    else None
                ),
                closed_holiday=(
                    str(row["휴진안내_공휴일"])
                    if pd.notna(row["휴진안내_공휴일"])
                    else None
                ),
                emergency_day_available=(
                    str(row["응급실_주간_운영여부"])
                    if pd.notna(row["응급실_주간_운영여부"])
                    else None
                ),
                emergency_day_phone1=(
                    str(row["응급실_주간_전화번호1"])
                    if pd.notna(row["응급실_주간_전화번호1"])
                    else None
                ),
                emergency_day_phone2=(
                    str(row["응급실_주간_전화번호2"])
                    if pd.notna(row["응급실_주간_전화번호2"])
                    else None
                ),
                emergency_night_available=(
                    str(row["응급실_야간_운영여부"])
                    if pd.notna(row["응급실_야간_운영여부"])
                    else None
                ),
                emergency_night_phone1=(
                    str(row["응급실_야간_전화번호1"])
                    if pd.notna(row["응급실_야간_전화번호1"])
                    else None
                ),
                emergency_night_phone2=(
                    str(row["응급실_야간_전화번호2"])
                    if pd.notna(row["응급실_야간_전화번호2"])
                    else None
                ),
                lunch_time_weekday=(
                    str(row["점심시간_평일"])
                    if pd.notna(row["점심시간_평일"])
                    else None
                ),
                lunch_time_saturday=(
                    str(row["점심시간_토요일"])
                    if pd.notna(row["점심시간_토요일"])
                    else None
                ),
                reception_time_weekday=(
                    str(row["접수시간_평일"])
                    if pd.notna(row["접수시간_평일"])
                    else None
                ),
                reception_time_saturday=(
                    str(row["접수시간_토요일"])
                    if pd.notna(row["접수시간_토요일"])
                    else None
                ),
                treatment_hours=treatment_hours if treatment_hours else None,
            )
            self.db.add(hospital)
            logger.info(f"병원 추가: {name}")

        self.db.commit()
        logger.info("✅ 병원 데이터 샘플 로드 완료!")

    def load_departments(self):
        """진료과 데이터 로드"""
        logger.info("🏥 진료과 데이터 로드 시작...")

        # 하드코딩된 진료과 목록 (파일명 기반)
        departments = [
            "내과",
            "신경과",
            "신경외과",
            "안과",
            "재활의학과",
            "정신건강의학과",
            "정형외과",
        ]

        for dept_name in departments:
            existing = (
                self.db.query(Department).filter(Department.name == dept_name).first()
            )
            if existing:
                logger.info(f"진료과 이미 존재: {dept_name}")
                continue

            department = Department(name=dept_name)
            self.db.add(department)
            logger.info(f"진료과 추가: {dept_name}")

        self.db.commit()
        logger.info("✅ 진료과 데이터 로드 완료!")

    def load_hospital_department_mappings(self):
        """진료과-병원 매핑 데이터 로드"""
        logger.info("🏥 진료과-병원 매핑 데이터 로드 시작...")

        # 진료과별 파일 처리
        departments = [
            "내과",
            "신경과",
            "신경외과",
            "안과",
            "재활의학과",
            "정신건강의학과",
            "정형외과",
        ]

        total_mappings = 0

        for dept_name in departments:
            file_name = f"진료과_병원_매핑_{dept_name}.csv"
            file_path = SEED_DATA_DIR / file_name

            if not file_path.exists():
                logger.warning(f"파일을 찾을 수 없습니다: {file_path}")
                continue

            # 진료과 ID 조회
            department = (
                self.db.query(Department).filter(Department.name == dept_name).first()
            )
            if not department:
                logger.error(f"진료과를 찾을 수 없습니다: {dept_name}")
                continue

            logger.info(f"📋 {dept_name} 매핑 파일 처리 중...")

            try:
                # CSV 파일 읽기 (헤더 없음)
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                dept_mappings = 0
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split(",")
                    if len(parts) < 2:
                        continue

                    encrypted_code = parts[0].strip()
                    hospital_name = parts[1].strip()

                    # 병원 조회
                    hospital = (
                        self.db.query(Hospital)
                        .filter(Hospital.encrypted_code == encrypted_code)
                        .first()
                    )

                    if not hospital:
                        logger.debug(
                            f"병원을 찾을 수 없습니다: {encrypted_code} ({hospital_name})"
                        )
                        continue

                    # 이미 존재하는 매핑인지 확인
                    existing = (
                        self.db.query(HospitalDepartment)
                        .filter(
                            HospitalDepartment.hospital_id == hospital.id,
                            HospitalDepartment.department_id == department.id,
                        )
                        .first()
                    )

                    if existing:
                        continue

                    # 새 매핑 생성
                    mapping = HospitalDepartment(
                        hospital_id=hospital.id, department_id=department.id
                    )
                    self.db.add(mapping)
                    dept_mappings += 1

                self.db.commit()
                logger.info(f"✅ {dept_name}: {dept_mappings}개 병원 매핑 완료")
                total_mappings += dept_mappings

            except Exception as e:
                logger.error(f"❌ {dept_name} 매핑 처리 중 오류: {e}")
                self.db.rollback()

        logger.info(f"🎉 진료과-병원 매핑 완료! 총 {total_mappings}개 매핑 생성")

    def load_hospital_equipment_mappings(self):
        """병원-장비 대분류 매핑 데이터 로드 (올바른 구조)"""
        logger.info("🔧 병원-장비 대분류 매핑 데이터 로드 시작...")

        # 병원별 장비대분류 통계 파일 사용
        equipment_file = SEED_DATA_DIR / "병원별_장비대분류_통계.csv"
        if not equipment_file.exists():
            logger.error(f"파일을 찾을 수 없습니다: {equipment_file}")
            return

        df = pd.read_csv(equipment_file)
        logger.info(f"장비 대분류 매핑 데이터 {len(df)}개 로드됨")

        total_mappings = 0
        missing_hospitals = set()
        missing_categories = set()
        skipped_records = []  # 실패/제외된 레코드들

        logger.info("병원-장비 대분류 매핑 처리 중...")

        for idx, row in df.iterrows():
            if pd.isna(row["암호화된 요양기호"]) or pd.isna(row["보유장비대분류_목록"]):
                skipped_records.append(
                    {
                        "reason": "필수 데이터 누락",
                        "row": idx + 1,
                        "encrypted_code": row.get("암호화된 요양기호", ""),
                        "data": str(row.to_dict()),
                    }
                )
                continue

            encrypted_code = str(row["암호화된 요양기호"])

            # 특수 케이스 제외 (폐업된 요양기관 등)
            if "폐업" in encrypted_code or "이후" in encrypted_code:
                skipped_records.append(
                    {
                        "reason": "폐업된 요양기관",
                        "encrypted_code": encrypted_code,
                        "data": str(row.to_dict()),
                    }
                )
                continue

            # 병원 조회
            hospital = (
                self.db.query(Hospital)
                .filter(Hospital.encrypted_code == encrypted_code)
                .first()
            )

            if not hospital:
                missing_hospitals.add(encrypted_code)
                skipped_records.append(
                    {
                        "reason": "병원 매칭 실패",
                        "encrypted_code": encrypted_code,
                        "data": str(row.to_dict()),
                    }
                )
                continue

            # 보유장비대분류_목록 파싱
            equipment_list_str = str(row["보유장비대분류_목록"])

            # 문자열에서 장비 목록 추출 ([] 제거하고 ' 기준으로 분할)
            import re

            equipment_names = re.findall(r"'([^']*)'", equipment_list_str)

            if not equipment_names:
                skipped_records.append(
                    {
                        "reason": "장비 목록 파싱 실패",
                        "encrypted_code": encrypted_code,
                        "equipment_list": equipment_list_str,
                        "data": str(row.to_dict()),
                    }
                )
                continue

            # 각 장비 대분류별로 매핑 생성
            for equipment_name in equipment_names:
                equipment_name = equipment_name.strip()
                if not equipment_name:
                    continue

                # 장비 대분류 조회
                equipment_category = (
                    self.db.query(MedicalEquipmentCategory)
                    .filter(MedicalEquipmentCategory.name == equipment_name)
                    .first()
                )

                if not equipment_category:
                    missing_categories.add(equipment_name)
                    continue

                # 이미 존재하는 매핑인지 확인 (새 컬럼 기준)
                existing = (
                    self.db.query(HospitalEquipment)
                    .filter(
                        HospitalEquipment.hospital_id == hospital.id,
                        HospitalEquipment.equipment_category_id
                        == equipment_category.id,
                    )
                    .first()
                )

                if existing:
                    # 기존 레코드 업데이트
                    existing.hospital_name = hospital.name
                    existing.equipment_category_name = equipment_category.name
                    existing.equipment_category_code = equipment_category.code
                    existing.quantity = 1
                    continue

                # 새 매핑 생성 (올바른 대분류 기준)
                mapping = HospitalEquipment(
                    hospital_id=hospital.id,
                    hospital_name=hospital.name,
                    equipment_category_id=equipment_category.id,
                    equipment_category_name=equipment_category.name,
                    equipment_category_code=equipment_category.code,
                    equipment_subcategory_id=equipment_category.id,  # 기존 필드 호환성
                    quantity=1,  # 대분류별 보유 여부
                )
                self.db.add(mapping)
                total_mappings += 1

                # 1000개씩 배치 커밋
                if total_mappings % 1000 == 0:
                    self.db.commit()
                    logger.info(f"진행 중... {total_mappings}개 매핑 생성")

        self.db.commit()

        # 결과 리포트
        logger.info(f"🎉 병원-장비 대분류 매핑 완료! 총 {total_mappings}개 매핑 생성")

        if missing_hospitals:
            logger.warning(f"매칭 실패 병원: {len(missing_hospitals)}개")

        if missing_categories:
            logger.warning(f"매칭 실패 장비 대분류: {len(missing_categories)}개")
            for category in sorted(list(missing_categories)[:10]):
                logger.warning(f"  - {category}")

        if skipped_records:
            logger.warning(f"건너뛴 레코드: {len(skipped_records)}개")

        # 실패 데이터를 파일로 저장
        if skipped_records or missing_hospitals or missing_categories:
            self._save_failed_mappings(
                skipped_records, missing_hospitals, missing_categories
            )

    def _save_failed_mappings(
        self, skipped_records, missing_hospitals, missing_categories
    ):
        """매핑 실패 데이터를 파일로 저장"""
        import json
        from datetime import datetime

        failure_data = {
            "timestamp": datetime.now().isoformat(),
            "skipped_records": skipped_records,
            "missing_hospitals": list(missing_hospitals),
            "missing_categories": list(missing_categories),
            "summary": {
                "skipped_count": len(skipped_records),
                "missing_hospitals_count": len(missing_hospitals),
                "missing_categories_count": len(missing_categories),
            },
        }

        failure_file = SEED_DATA_DIR / "hospital_equipment_mapping_failures.json"
        with open(failure_file, "w", encoding="utf-8") as f:
            json.dump(failure_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📁 매핑 실패 데이터 저장: {failure_file}")

    def load_hospital_equipment_mappings_v2(self):
        """병원-장비 대분류 매핑 데이터 로드 (최종 올바른 구조 + 실제 수량)"""
        logger.info("🔧 병원-장비 대분류 실제 수량 매핑 데이터 로드 시작...")

        # 새로운 병원별 장비수 매핑 파일 사용
        equipment_file = SEED_DATA_DIR / "병원_대분류_장비수_매핑.csv"
        if not equipment_file.exists():
            logger.error(f"파일을 찾을 수 없습니다: {equipment_file}")
            return

        df = pd.read_csv(equipment_file)
        logger.info(f"장비 수량 매핑 데이터 {len(df)}개 로드됨")

        total_mappings = 0
        missing_hospitals = set()
        missing_categories = set()
        skipped_records = []
        failure_details = []

        logger.info("병원-장비 대분류 실제 수량 매핑 처리 중...")

        for idx, row in df.iterrows():
            # 필수 필드 검증
            required_fields = [
                "암호화 요양기호",
                "병원명",
                "장비대분류명",
                "장비대분류코드",
                "같은대분류인장비수",
            ]
            if any(pd.isna(row[field]) for field in required_fields):
                skipped_records.append(
                    {
                        "reason": "필수 데이터 누락",
                        "row": idx + 1,
                        "data": str(row.to_dict()),
                    }
                )
                continue

            encrypted_code = str(row["암호화 요양기호"]).strip()
            hospital_name = str(row["병원명"]).strip()
            equipment_name = str(row["장비대분류명"]).strip()
            equipment_code = str(row["장비대분류코드"]).strip()

            # 수량 파싱
            try:
                quantity = int(row["같은대분류인장비수"])
            except (ValueError, TypeError):
                quantity = 1
                logger.warning(
                    f"수량 파싱 실패 (기본값 1 사용): {row['같은대분류인장비수']}"
                )

            # 특수 케이스 제외 (폐업된 요양기관 등)
            if "폐업" in encrypted_code or "이후" in encrypted_code:
                skipped_records.append(
                    {
                        "reason": "폐업된 요양기관",
                        "encrypted_code": encrypted_code,
                        "hospital_name": hospital_name,
                    }
                )
                continue

            # 병원 조회 (암호화 코드 기준)
            hospital = (
                self.db.query(Hospital)
                .filter(Hospital.encrypted_code == encrypted_code)
                .first()
            )

            if not hospital:
                missing_hospitals.add(f"{encrypted_code} ({hospital_name})")
                failure_details.append(
                    {
                        "type": "hospital_not_found",
                        "encrypted_code": encrypted_code,
                        "hospital_name": hospital_name,
                        "equipment_name": equipment_name,
                        "equipment_code": equipment_code,
                        "quantity": quantity,
                    }
                )
                continue

            # 장비 대분류 조회 (코드 기준)
            equipment_category = (
                self.db.query(MedicalEquipmentCategory)
                .filter(MedicalEquipmentCategory.code == equipment_code)
                .first()
            )

            if not equipment_category:
                # 이름으로도 시도
                equipment_category = (
                    self.db.query(MedicalEquipmentCategory)
                    .filter(MedicalEquipmentCategory.name == equipment_name)
                    .first()
                )

            if not equipment_category:
                missing_categories.add(f"{equipment_name} ({equipment_code})")
                failure_details.append(
                    {
                        "type": "equipment_not_found",
                        "hospital_name": hospital.name,
                        "equipment_name": equipment_name,
                        "equipment_code": equipment_code,
                        "quantity": quantity,
                    }
                )
                continue

            # 이미 존재하는 매핑인지 확인
            existing = (
                self.db.query(HospitalEquipment)
                .filter(
                    HospitalEquipment.hospital_id == hospital.id,
                    HospitalEquipment.equipment_category_id == equipment_category.id,
                )
                .first()
            )

            if existing:
                # 기존 레코드 업데이트 (수량 누적)
                existing.hospital_name = hospital.name
                existing.equipment_category_name = equipment_category.name
                existing.equipment_category_code = equipment_category.code
                existing.quantity += quantity
                logger.debug(
                    f"기존 매핑 업데이트: {hospital.name} - {equipment_category.name} (수량: {existing.quantity})"
                )
                continue

            # 새 매핑 생성
            mapping = HospitalEquipment(
                hospital_id=hospital.id,
                hospital_name=hospital.name,
                equipment_category_id=equipment_category.id,
                equipment_category_name=equipment_category.name,
                equipment_category_code=equipment_category.code,
                quantity=quantity,
            )
            self.db.add(mapping)
            total_mappings += 1

            # 1000개씩 배치 커밋
            if total_mappings % 1000 == 0:
                self.db.commit()
                logger.info(f"진행 중... {total_mappings}개 매핑 생성")

        self.db.commit()

        # 결과 리포트
        logger.info(f"🎉 병원-장비 대분류 매핑 완료! 총 {total_mappings}개 매핑 생성")

        if missing_hospitals:
            logger.warning(f"매칭 실패 병원: {len(missing_hospitals)}개")

        if missing_categories:
            logger.warning(f"매칭 실패 장비 대분류: {len(missing_categories)}개")

        if skipped_records:
            logger.warning(f"건너뛴 레코드: {len(skipped_records)}개")

        # 실패 데이터를 CSV로 저장
        if failure_details:
            self._save_failure_details_csv(failure_details)

    def _save_failure_details_csv(self, failure_details):
        """매핑 실패 데이터를 CSV로 저장"""
        import pandas as pd

        if not failure_details:
            return

        df_failures = pd.DataFrame(failure_details)
        failure_file = SEED_DATA_DIR / "병원_대분류_장비수_매핑_failures.csv"
        df_failures.to_csv(failure_file, index=False, encoding="utf-8-sig")

        logger.info(f"📁 매핑 실패 데이터 CSV 저장: {failure_file}")
        logger.info(
            f"   - 병원 미발견: {len([x for x in failure_details if x['type'] == 'hospital_not_found'])}개"
        )
        logger.info(
            f"   - 장비 미발견: {len([x for x in failure_details if x['type'] == 'equipment_not_found'])}개"
        )


def main():
    parser = argparse.ArgumentParser(description="시드 데이터 로더")
    parser.add_argument("--all", action="store_true", help="모든 데이터 로드")
    parser.add_argument("--diseases", action="store_true", help="질병 데이터만 로드")
    parser.add_argument("--hospitals", action="store_true", help="병원 데이터만 로드")
    parser.add_argument("--equipment", action="store_true", help="장비 데이터만 로드")
    parser.add_argument(
        "--departments", action="store_true", help="진료과 데이터만 로드"
    )
    parser.add_argument(
        "--hospital-departments",
        action="store_true",
        help="진료과-병원 매핑 데이터 로드",
    )
    parser.add_argument(
        "--hospital-equipment",
        action="store_true",
        help="병원-장비 매핑 데이터 로드",
    )
    parser.add_argument(
        "--hospital-equipment-v2",
        action="store_true",
        help="병원-장비 실제 수량 매핑 로드",
    )
    parser.add_argument(
        "--hospital-limit",
        type=int,
        default=50,
        help="병원 데이터 로드 제한 (기본: 50)",
    )

    args = parser.parse_args()

    if not any(
        [
            args.all,
            args.diseases,
            args.hospitals,
            args.equipment,
            args.departments,
            args.hospital_departments,
            args.hospital_equipment,
            args.hospital_equipment_v2,
        ]
    ):
        parser.print_help()
        return

    # 데이터베이스 연결
    try:
        from app.db.database import engine

        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        loader = SeedDataLoader(db)

        if args.all or args.diseases:
            loader.load_diseases()

        if args.all or args.equipment:
            loader.load_equipment_categories()

        if args.all or args.departments:
            loader.load_departments()

        if args.all or args.hospitals:
            loader.load_hospitals_sample(limit=args.hospital_limit)

        if args.hospital_departments:
            loader.load_hospital_department_mappings()

        if args.hospital_equipment:
            loader.load_hospital_equipment_mappings()

        if args.hospital_equipment_v2:
            loader.load_hospital_equipment_mappings_v2()

        logger.info("🎉 시드 데이터 로드 완료!")

    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
