"""
테스트용 데이터 시딩 스크립트
"""

import uuid
from datetime import datetime

from app.db.database import SessionLocal
from app.models.department import Department, DepartmentDisease
from app.models.equipment import (
    EquipmentDisease,
    MedicalEquipmentCategory,
    MedicalEquipmentSubcategory,
)
from app.models.hospital import Hospital, HospitalDepartment, HospitalEquipment
from app.models.medical import Disease
from app.models.user import User


def create_test_data():
    """테스트용 데이터 생성"""
    db = SessionLocal()

    try:
        print("🌱 테스트 데이터 생성 시작...")

        # 1. 진료과 데이터 생성
        departments_data = [
            {"name": "내과"},
            {"name": "신경과"},
            {"name": "신경외과"},
            {"name": "정형외과"},
            {"name": "안과"},
        ]

        departments = {}
        for dept_data in departments_data:
            dept = Department(name=dept_data["name"])
            db.add(dept)
            departments[dept_data["name"]] = dept

        db.commit()
        print(f"✅ {len(departments)} 진료과 생성 완료")

        # 2. 질환 데이터 생성
        diseases_data = [
            "간염",
            "골다공증",
            "치매",
            "퇴행성근골격계질환",
            "당뇨병",
            "동맥경화",
            "신장병",
            "요통",
            "류마티스관절염",
            "위장병",
            "노인성빈혈",
            "뇌동맥류",
            "변비",
            "고혈압",
            "뇌졸중",
            "파킨슨병",
            "오십견",
            "통풍",
            "녹내장",
            "갑상선기능항진증",
        ]

        diseases = {}
        for disease_name in diseases_data:
            disease = Disease(
                name=disease_name, description=f"{disease_name} 관련 질환"
            )
            db.add(disease)
            diseases[disease_name] = disease

        db.commit()
        print(f"✅ {len(diseases)} 질환 생성 완료")

        # 3. 질환-진료과 매핑
        disease_department_mapping = {
            "간염": "내과",
            "골다공증": "내과",
            "치매": "신경과",
            "퇴행성근골격계질환": "정형외과",
            "당뇨병": "내과",
            "동맥경화": "내과",
            "신장병": "내과",
            "요통": "정형외과",
            "류마티스관절염": "정형외과",
            "위장병": "내과",
            "노인성빈혈": "내과",
            "뇌동맥류": "신경외과",
            "변비": "내과",
            "고혈압": "내과",
            "뇌졸중": "신경과",
            "파킨슨병": "신경과",
            "오십견": "정형외과",
            "통풍": "내과",
            "녹내장": "안과",
            "갑상선기능항진증": "내과",
        }

        for disease_name, dept_name in disease_department_mapping.items():
            if disease_name in diseases and dept_name in departments:
                mapping = DepartmentDisease(
                    department_id=departments[dept_name].id,
                    disease_id=diseases[disease_name].id,
                )
                db.add(mapping)

        db.commit()
        print(f"✅ {len(disease_department_mapping)} 질환-진료과 매핑 완료")

        # 4. 의료장비 대분류 생성
        equipment_categories_data = [
            {"name": "영상진단장비", "code": "B100"},
            {"name": "검사장비", "code": "A200"},
            {"name": "치료장비", "code": "D200"},
            {"name": "수술장비", "code": "C300"},
        ]

        categories = {}
        for cat_data in equipment_categories_data:
            category = MedicalEquipmentCategory(
                name=cat_data["name"], code=cat_data["code"]
            )
            db.add(category)
            categories[cat_data["name"]] = category

        db.commit()
        print(f"✅ {len(categories)} 장비 대분류 생성 완료")

        # 5. 의료장비 세분류 생성
        equipment_subcategories_data = [
            {"name": "MRI", "code": "B10101", "category": "영상진단장비"},
            {"name": "CT", "code": "B10102", "category": "영상진단장비"},
            {"name": "X-ray", "code": "B10103", "category": "영상진단장비"},
            {"name": "초음파", "code": "B10104", "category": "영상진단장비"},
            {"name": "심전도기", "code": "A20101", "category": "검사장비"},
            {"name": "혈액검사기", "code": "A20102", "category": "검사장비"},
            {"name": "내시경", "code": "A20103", "category": "검사장비"},
            {"name": "제세동기", "code": "D20101", "category": "치료장비"},
        ]

        subcategories = {}
        for subcat_data in equipment_subcategories_data:
            if subcat_data["category"] in categories:
                subcategory = MedicalEquipmentSubcategory(
                    name=subcat_data["name"],
                    code=subcat_data["code"],
                    category_id=categories[subcat_data["category"]].id,
                )
                db.add(subcategory)
                subcategories[subcat_data["name"]] = subcategory

        db.commit()
        print(f"✅ {len(subcategories)} 장비 세분류 생성 완료")

        # 6. 질환-장비 매핑 (필수장비)
        disease_equipment_mapping = {
            "치매": ["MRI", "CT"],
            "뇌졸중": ["MRI", "CT"],
            "파킨슨병": ["MRI"],
            "뇌동맥류": ["MRI", "CT"],
            "퇴행성근골격계질환": ["X-ray", "MRI"],
            "요통": ["X-ray", "MRI"],
            "오십견": ["X-ray", "초음파"],
            "류마티스관절염": ["X-ray", "혈액검사기"],
            "골다공증": ["X-ray"],
            "위장병": ["내시경", "혈액검사기"],
            "간염": ["혈액검사기", "초음파"],
            "당뇨병": ["혈액검사기"],
            "고혈압": ["심전도기"],
            "신장병": ["혈액검사기", "초음파"],
            "갑상선기능항진증": ["혈액검사기", "초음파"],
        }

        equipment_mappings_count = 0
        for disease_name, equipment_list in disease_equipment_mapping.items():
            if disease_name in diseases:
                for equipment_name in equipment_list:
                    if equipment_name in subcategories:
                        mapping = EquipmentDisease(
                            equipment_subcategory_id=subcategories[equipment_name].id,
                            disease_id=diseases[disease_name].id,
                        )
                        db.add(mapping)
                        equipment_mappings_count += 1

        db.commit()
        print(f"✅ {equipment_mappings_count} 질환-장비 매핑 완료")

        # 7. 테스트용 병원 생성
        hospitals_data = [
            {
                "name": "서울대학교병원",
                "address": "서울특별시 종로구 대학로 101",
                "latitude": 37.5796,
                "longitude": 126.9999,
                "encrypted_code": "TEST001",
                "hospital_type_name": "종합병원",
                "phone": "02-2072-2114",
                "departments": ["내과", "신경과", "신경외과", "정형외과"],
                "equipment": [
                    "MRI",
                    "CT",
                    "X-ray",
                    "초음파",
                    "심전도기",
                    "혈액검사기",
                    "내시경",
                ],
            },
            {
                "name": "강남세브란스병원",
                "address": "서울특별시 강남구 언주로 211",
                "latitude": 37.5182,
                "longitude": 127.0364,
                "encrypted_code": "TEST002",
                "hospital_type_name": "종합병원",
                "phone": "02-2019-3114",
                "departments": ["내과", "신경과", "정형외과", "안과"],
                "equipment": ["MRI", "CT", "X-ray", "초음파", "혈액검사기"],
            },
            {
                "name": "삼성서울병원",
                "address": "서울특별시 강남구 일원로 81",
                "latitude": 37.4889,
                "longitude": 127.0857,
                "encrypted_code": "TEST003",
                "hospital_type_name": "종합병원",
                "phone": "02-3410-2114",
                "departments": ["내과", "신경외과", "정형외과"],
                "equipment": ["MRI", "CT", "X-ray", "심전도기", "혈액검사기", "내시경"],
            },
            {
                "name": "서초내과의원",
                "address": "서울특별시 서초구 서초대로 396",
                "latitude": 37.4943,
                "longitude": 127.0293,
                "encrypted_code": "TEST004",
                "hospital_type_name": "의원",
                "phone": "02-123-4567",
                "departments": ["내과"],
                "equipment": ["X-ray", "초음파", "심전도기", "혈액검사기"],
            },
            {
                "name": "강남정형외과",
                "address": "서울특별시 강남구 테헤란로 152",
                "latitude": 37.5006,
                "longitude": 127.0364,
                "encrypted_code": "TEST005",
                "hospital_type_name": "의원",
                "phone": "02-789-0123",
                "departments": ["정형외과"],
                "equipment": ["X-ray", "초음파", "MRI"],
            },
        ]

        hospitals = {}
        for hospital_data in hospitals_data:
            hospital = Hospital(
                name=hospital_data["name"],
                address=hospital_data["address"],
                latitude=hospital_data["latitude"],
                longitude=hospital_data["longitude"],
                encrypted_code=hospital_data["encrypted_code"],
                hospital_type_name=hospital_data["hospital_type_name"],
                phone=hospital_data["phone"],
            )
            db.add(hospital)
            hospitals[hospital_data["name"]] = hospital

        db.commit()
        print(f"✅ {len(hospitals)} 병원 생성 완료")

        # 8. 병원-진료과 매핑
        hospital_dept_count = 0
        for hospital_data in hospitals_data:
            hospital = hospitals[hospital_data["name"]]
            for dept_name in hospital_data["departments"]:
                if dept_name in departments:
                    mapping = HospitalDepartment(
                        hospital_id=hospital.id, department_id=departments[dept_name].id
                    )
                    db.add(mapping)
                    hospital_dept_count += 1

        db.commit()
        print(f"✅ {hospital_dept_count} 병원-진료과 매핑 완료")

        # 9. 병원-장비 매핑
        hospital_equip_count = 0
        for hospital_data in hospitals_data:
            hospital = hospitals[hospital_data["name"]]
            for equipment_name in hospital_data["equipment"]:
                if equipment_name in subcategories:
                    mapping = HospitalEquipment(
                        hospital_id=hospital.id,
                        equipment_subcategory_id=subcategories[equipment_name].id,
                        quantity=1,
                        is_operational=True,
                    )
                    db.add(mapping)
                    hospital_equip_count += 1

        db.commit()
        print(f"✅ {hospital_equip_count} 병원-장비 매핑 완료")

        # 10. 테스트용 사용자 생성
        test_user = User(
            email="test@example.com",
            nickname="테스트사용자",
            age=35,
            gender="M",
            road_address="서울특별시 강남구 테헤란로 123",
            latitude=37.5009,  # 강남역 근처
            longitude=127.0266,
            password_hash="$2b$12$dummy_hash_for_testing",
        )
        db.add(test_user)
        db.commit()
        print(f"✅ 테스트 사용자 생성 완료 (ID: {test_user.id})")

        print("\n🎉 모든 테스트 데이터 생성 완료!")
        print(f"📊 생성된 데이터:")
        print(f"   - 진료과: {len(departments)}개")
        print(f"   - 질환: {len(diseases)}개")
        print(f"   - 질환-진료과 매핑: {len(disease_department_mapping)}개")
        print(f"   - 장비 대분류: {len(categories)}개")
        print(f"   - 장비 세분류: {len(subcategories)}개")
        print(f"   - 질환-장비 매핑: {equipment_mappings_count}개")
        print(f"   - 병원: {len(hospitals)}개")
        print(f"   - 병원-진료과 매핑: {hospital_dept_count}개")
        print(f"   - 병원-장비 매핑: {hospital_equip_count}개")
        print(f"   - 테스트 사용자: 1명")

        return test_user.id

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    user_id = create_test_data()
    print(f"\n💡 테스트용 사용자 ID: {user_id}")
    print("💡 이 ID를 사용해서 병원 추천 API를 테스트할 수 있습니다.")
