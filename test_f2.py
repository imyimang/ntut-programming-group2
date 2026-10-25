# test_f2.py
import pytest
from f2_checker import check_course_enrollment


# ==================== 工具函式 (測試資料建立) ====================

def make_f2_world():
    """建立包含各種衝突情境的 Mock 資料庫環境"""
    classrooms_db = {
        "A101": {"capacity": 50},
        "A102": {"capacity": 50}
    }

    courses_db = {
        # 已修課程：星期二第 3 節
        "CS101": {
            "id": "CS101", "name": "微積分", "credit": 3,
            "maxStudentCount": 40, "classroom": "A101",
            "timeSlot": [(2, "3")]
        },
        # 衝突課程：星期二第 3 節（課程衝堂）+ 星期四第 5 節（活動衝堂）
        "CS102": {
            "id": "CS102", "name": "Python程式設計", "credit": 3,
            "maxStudentCount": 40, "classroom": "A102",
            "timeSlot": [(2, "3"), (4, "5")]
        },
        # 額滿課程
        "CS103": {
            "id": "CS103", "name": "資料結構", "credit": 3,
            "maxStudentCount": 1, "classroom": "A102",
            "timeSlot": [(1, "1")]
        },
        # 高學分課程（引發學分超標）
        "CS104": {
            "id": "CS104", "name": "專題研究", "credit": 10,
            "maxStudentCount": 40, "classroom": "A102",
            "timeSlot": [(5, "1")]
        },
        # 正常可加選課程
        "CS105": {
            "id": "CS105", "name": "離散數學", "credit": 3,
            "maxStudentCount": 40, "classroom": "A102",
            "timeSlot": [(3, "1"), (3, "2")]
        }
    }

    students_db = {
        "S001": {
            "id": "S001", "name": "小明", "department": "資工一",
            "maxCredit": 18, "activities": ["ACT01"]
        }
    }

    activities_db = {
        # 活動：星期四第 5 節
        "ACT01": {
            "id": "ACT01", "name": "程式設計讀書會",
            "timeSlot": [(4, "5")]
        }
    }

    # S001 已選 CS101 (3 學分)；S002 已選 CS103 (導致 CS103 額滿)
    enrollments = [
        {"student_id": "S001", "course_id": "CS101", "status": "ENROLLED"},
        {"student_id": "S002", "course_id": "CS103", "status": "ENROLLED"}
    ]

    return students_db, courses_db, activities_db, enrollments


# ==================== 單元測試案例 ====================

def test_f2_enrollment_success():
    """[TC01 正常測試]：完全無衝突時加選成功"""
    students, courses, activities, enrollments = make_f2_world()
    
    result = check_course_enrollment("S001", "CS105", students, courses, activities, enrollments)
    
    assert result["success"] is True
    assert len(result["conflicts"]) == 0
    assert result["after_credits"] == 6


def test_f2_course_and_activity_conflict():
    """[TC02 錯誤/衝突測試]：同時包含課程衝堂與活動衝突"""
    students, courses, activities, enrollments = make_f2_world()
    
    result = check_course_enrollment("S001", "CS102", students, courses, activities, enrollments)
    
    assert result["success"] is False
    assert len(result["conflicts"]) == 2
    assert result["conflicts"][0]["type"] == "COURSE_CONFLICT"
    assert result["conflicts"][1]["type"] == "ACTIVITY_CONFLICT"


def test_f2_capacity_full():
    """[TC03 邊界/錯誤測試]：人數額滿拒絕加選"""
    students, courses, activities, enrollments = make_f2_world()
    
    result = check_course_enrollment("S001", "CS103", students, courses, activities, enrollments)
    
    assert result["success"] is False
    types = [c["type"] for c in result["conflicts"]]
    assert "CAPACITY_FULL" in types


def test_f2_credit_exceeded():
    """[TC04 邊界/錯誤測試]：超過學分上限拒絕加選"""
    students, courses, activities, enrollments = make_f2_world()
    students["S001"]["maxCredit"] = 5  # 調低上限至 5
    
    result = check_course_enrollment("S001", "CS104", students, courses, activities, enrollments)
    
    assert result["success"] is False
    types = [c["type"] for c in result["conflicts"]]
    assert "CREDIT_EXCEEDED" in types


def test_f2_multiple_conflicts_accumulated_and_sorted():
    """[TC05 核心驗收驗證]：不提前中斷與時間排序"""
    students, courses, activities, enrollments = make_f2_world()
    
    # 故意打亂時段順序，並讓該門課同時額滿
    courses["CS102"]["timeSlot"] = [(4, "5"), (2, "3")]
    courses["CS102"]["maxStudentCount"] = 1
    enrollments.append({"student_id": "S003", "course_id": "CS102", "status": "ENROLLED"})
    
    result = check_course_enrollment("S001", "CS102", students, courses, activities, enrollments)
    
    assert result["success"] is False
    assert len(result["conflicts"]) == 3
    
    time_conflicts = [c for c in result["conflicts"] if c["type"] in ("COURSE_CONFLICT", "ACTIVITY_CONFLICT")]
    assert time_conflicts[0]["slot"] == (2, "3")
    assert time_conflicts[1]["slot"] == (4, "5")
