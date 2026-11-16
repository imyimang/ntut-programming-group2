# test_f4.py
import copy
import pytest

from f4_activities import (
    add_activity,
    cancel_activity,
    enroll_activity,
    find_suitable_classrooms,
    get_activity,
    get_classroom_unmet_reasons,
    query_activities,
    update_activity,
)


def make_world():
    classrooms = {
        "R101": {
            "name": "R101", "roomCapacity": 30,
            "timeSlot": [(1, "5"), (2, "3"), (2, "4")],
            "type": "lecture", "devices": ["projector", "pc"],
        },
        "R102": {
            "name": "R102", "roomCapacity": 10,
            "timeSlot": [(1, "1"), (1, "2")],
            "type": "sports", "devices": ["speaker"],
        },
        "R103": {
            "name": "R103", "roomCapacity": 60,
            "timeSlot": [],
            "type": "lecture", "devices": ["projector"],
        },
    }
    courses = {
        "CS101": {
            "id": "CS101", "name": "微積分", "credit": 3,
            "maxStudentCount": 40, "classroom": "R101",
            "timeSlot": [(2, "3")],
        },
    }
    activities = {}
    students = {
        "S001": {"id": "S001", "name": "小明", "courses": ["CS101"], "activities": []},
        "S002": {"id": "S002", "name": "小華", "courses": [], "activities": []},
        "S003": {"id": "S003", "name": "小美", "courses": [], "activities": []},
    }
    return classrooms, courses, activities, students


def activity_data(**overrides):
    data = {
        "id": "ACT01",
        "name": "程式設計讀書會",
        "date": "2026-06-30",
        "timeSlot": [(2, "3")],
        "studentCount": 20,
        "type": "lecture",
        "requireList": ["projector"],
    }
    data.update(overrides)
    return data


# ==================== 正常案例 ====================

def test_f4_add_activity_success():
    classrooms, courses, activities, _ = make_world()
    activities, ok, msg = add_activity(activities, activity_data(), classrooms, courses)
    assert ok is True
    assert activities["ACT01"]["name"] == "程式設計讀書會"
    assert activities["ACT01"]["timeSlot"] == [(2, "3")]


def test_f4_update_activity_name():
    classrooms, courses, activities, _ = make_world()
    add_activity(activities, activity_data(), classrooms, courses)
    activities, ok, _ = update_activity(activities, "ACT01", "name", "新名稱", classrooms, courses)
    assert ok is True
    assert activities["ACT01"]["name"] == "新名稱"


def test_f4_update_activity_assigns_suitable_classroom():
    classrooms, courses, activities, _ = make_world()
    add_activity(activities, activity_data(), classrooms, courses)
    activities, ok, errors = update_activity(
        activities, "ACT01", "classroom", "R103", classrooms, courses)
    assert ok is True, errors
    assert activities["ACT01"]["classroom"] == "R103"


def test_f4_cancel_activity_releases_room_and_participants():
    classrooms, courses, activities, students = make_world()
    add_activity(activities, activity_data(), classrooms, courses)
    activities, ok, _ = update_activity(activities, "ACT01", "classroom", "R103", classrooms, courses)
    assert ok
    result = enroll_activity("ACT01", "S002", activities, students, courses, classrooms_db=classrooms)
    assert result["success"] is True

    activities, ok, _ = cancel_activity(activities, students, "ACT01")
    assert ok is True
    assert activities["ACT01"]["isCancelled"] is True
    assert activities["ACT01"]["classroom"] == ""
    assert activities["ACT01"]["participants"] == []
    assert students["S002"]["activities"] == []


def test_f4_query_activities_filter():
    classrooms, courses, activities, _ = make_world()
    add_activity(activities, activity_data(), classrooms, courses)
    add_activity(activities, activity_data(id="ACT02", type="sports", date="2026-07-01", timeSlot=[(3, "3")]), classrooms, courses)
    assert [a["id"] for a in query_activities(activities)] == ["ACT01", "ACT02"]
    assert [a["id"] for a in query_activities(activities, activity_type="sports")] == ["ACT02"]
    assert [a["id"] for a in query_activities(activities, date_text="2026-06-30")] == ["ACT01"]


def test_f4_find_suitable_classroom_success():
    classrooms, courses, activities, _ = make_world()
    result = find_suitable_classrooms(
        20, [(2, "3")], "lecture", ["projector"], classrooms, courses, activities)
    assert result["isSucceed"] is True
    assert "R103" in result["suitableClassrooms"]


def test_f4_enroll_activity_success():
    classrooms, courses, activities, students = make_world()
    add_activity(activities, activity_data(), classrooms, courses)
    result = enroll_activity("ACT01", "S002", activities, students, courses, classrooms_db=classrooms)
    assert result["success"] is True
    assert "S002" in activities["ACT01"]["participants"]
    assert "ACT01" in students["S002"]["activities"]


def test_f4_multiple_students_can_enroll():
    classrooms, courses, activities, students = make_world()
    add_activity(activities, activity_data(), classrooms, courses)
    for sid in ("S001", "S002", "S003"):
        result = enroll_activity("ACT01", sid, activities, students, courses,
                                 classrooms_db=classrooms)
        if sid == "S001":
            assert result["success"] is False
            assert result["conflicts"]
        else:
            assert result["success"] is True


# ==================== 邊界案例 ====================

def test_f4_capacity_exactly_matches_student_count():
    classrooms, courses, activities, _ = make_world()
    activities, ok, errors = add_activity(
        activities, activity_data(studentCount=30, requireList=["projector"]), classrooms, courses)
    assert ok is True, errors


def test_f4_room_without_time_limit_accepts_any_slot():
    classrooms, courses, activities, _ = make_world()
    activities, ok, errors = add_activity(
        activities, activity_data(id="ACT03", date="2026-07-05", timeSlot=[(7, "c")]), classrooms, courses)
    assert ok is True, errors
    result = find_suitable_classrooms(
        20, [(7, "c")], "lecture", ["projector"], classrooms, courses, activities)
    assert "R103" in result["suitableClassrooms"]


def test_f4_first_and_last_period_supported():
    classrooms, courses, activities, _ = make_world()
    activities, ok, _ = add_activity(
        activities, activity_data(id="ACT04", timeSlot=[(2, "3"), (2, "4")]), classrooms, courses)
    assert ok is True
    assert activities["ACT04"]["timeSlot"] == [(2, "3"), (2, "4")]


def test_f4_update_student_count_equal_to_participants():
    classrooms, courses, activities, students = make_world()
    add_activity(activities, activity_data(), classrooms, courses)
    enroll_activity("ACT01", "S002", activities, students, courses, classrooms_db=classrooms)
    activities, ok, _ = update_activity(activities, "ACT01", "studentCount", 1, classrooms, courses)
    assert ok is True
    assert activities["ACT01"]["studentCount"] == 1


def test_f4_enroll_until_full_then_reject():
    classrooms, courses, activities, students = make_world()
    add_activity(activities, activity_data(studentCount=2, timeSlot=[(2, "4")]), classrooms, courses)
    assert enroll_activity("ACT01", "S001", activities, students, courses)["success"] is True
    assert enroll_activity("ACT01", "S002", activities, students, courses)["success"] is True
    third = enroll_activity("ACT01", "S003", activities, students, courses)
    assert third["success"] is False
    assert "ACTIVITY_FULL" in [e["errorType"] for e in third["errors"]]


# ==================== 錯誤案例 ====================

def test_f4_duplicate_activity_rejected():
    classrooms, courses, activities, _ = make_world()
    add_activity(activities, activity_data(), classrooms, courses)
    _, ok, errors = add_activity(activities, activity_data(), classrooms, courses)
    assert ok is False
    assert errors[0]["field"] == "id"


@pytest.mark.parametrize("field, value", [
    ("date", "2026-07-01"),
    ("timeSlot", [(3, "1")]),
    ("timeSlot", [(2, "z")]),
    ("date", "not-a-date"),
])
def test_f4_invalid_date_or_slot_rejected(field, value):
    classrooms, courses, activities, _ = make_world()
    _, ok, errors = add_activity(activities, activity_data(**{field: value}), classrooms, courses)
    assert ok is False
    assert errors


def test_f4_room_capacity_too_small_rejected():
    classrooms, courses, activities, _ = make_world()
    data = activity_data(studentCount=31, classroom="R101")
    _, ok, errors = add_activity(activities, data, classrooms, courses)
    assert ok is False
    assert any("容量不足" in e["reason"] for e in errors)


def test_f4_room_missing_device_rejected():
    classrooms, courses, activities, _ = make_world()
    data = activity_data(requireList=["mic"], classroom="R101")
    _, ok, errors = add_activity(activities, data, classrooms, courses)
    assert ok is False
    assert any("缺少指定設備" in e["reason"] for e in errors)


def test_f4_room_wrong_type_rejected():
    classrooms, courses, activities, _ = make_world()
    data = activity_data(type="sports", classroom="R101")
    _, ok, errors = add_activity(activities, data, classrooms, courses)
    assert ok is False
    assert any("活動類型不符合" in e["reason"] for e in errors)


def test_f4_room_time_not_available_rejected():
    classrooms, courses, activities, _ = make_world()
    data = activity_data(timeSlot=[(2, "2")], classroom="R101")
    _, ok, errors = add_activity(activities, data, classrooms, courses)
    assert ok is False
    assert any("不在教室可用時段內" in e["reason"] for e in errors)


def test_f4_room_occupied_by_course_rejected():
    classrooms, courses, activities, _ = make_world()
    data = activity_data(timeSlot=[(2, "3")], classroom="R101")
    _, ok, errors = add_activity(activities, data, classrooms, courses)
    assert ok is False
    assert any("時段已被占用" in e["reason"] for e in errors)


def test_f4_room_occupied_by_activity_rejected():
    classrooms, courses, activities, _ = make_world()
    add_activity(activities, activity_data(id="ACT01", timeSlot=[(2, "4")], classroom="R101"), classrooms, courses)
    _, ok, errors = add_activity(
        activities, activity_data(id="ACT02", timeSlot=[(2, "4")], classroom="R101"), classrooms, courses)
    assert ok is False
    assert any("時段已被占用" in e["reason"] for e in errors)


def test_f4_enroll_conflicts_with_course():
    classrooms, courses, activities, students = make_world()
    add_activity(activities, activity_data(), classrooms, courses)
    result = enroll_activity("ACT01", "S001", activities, students, courses)
    assert result["success"] is False
    assert result["conflicts"][0]["conflictType"] == "STUDENT_OVERLAP"


def test_f4_enroll_conflicts_with_other_activity():
    classrooms, courses, activities, students = make_world()
    add_activity(activities, activity_data(id="ACT01"), classrooms, courses)
    add_activity(activities, activity_data(id="ACT02"), classrooms, courses)
    students["S002"]["activities"] = ["ACT02"]
    activities["ACT02"]["participants"] = ["S002"]
    result = enroll_activity("ACT01", "S002", activities, students, courses)
    assert result["success"] is False
    assert result["conflicts"][0]["conflictType"] == "ACTIVITY_OVERLAP"


def test_f4_enroll_cancelled_activity_rejected():
    classrooms, courses, activities, students = make_world()
    add_activity(activities, activity_data(), classrooms, courses)
    cancel_activity(activities, students, "ACT01")
    result = enroll_activity("ACT01", "S002", activities, students, courses)
    assert result["success"] is False
    assert result["errors"][0]["errorType"] == "ACTIVITY_CANCELLED"


def test_f4_update_cancelled_activity_rejected():
    classrooms, courses, activities, students = make_world()
    add_activity(activities, activity_data(), classrooms, courses)
    cancel_activity(activities, students, "ACT01")
    _, ok, errors = update_activity(activities, "ACT01", "name", "x", classrooms, courses)
    assert ok is False
    assert "已取消" in errors[0]["reason"]


def test_f4_no_suitable_classroom_lists_all_reasons():
    classrooms, courses, activities, _ = make_world()
    result = find_suitable_classrooms(
        100, [(2, "3")], "workshop", ["mic"], classrooms, courses, activities)
    assert result["isSucceed"] is False
    assert result["suitableClassrooms"] == []
    assert result["unmetReasons"]
    assert any("容量不足" in r for r in result["unmetReasons"])
    assert any("缺少指定設備" in r for r in result["unmetReasons"])
    assert any("活動類型不符合" in r for r in result["unmetReasons"])


def test_f4_classroom_unmet_reasons_helper():
    classrooms, courses, activities, _ = make_world()
    reasons = get_classroom_unmet_reasons(
        "R102", activity_data(studentCount=5, requireList=["projector"], classroom="R102"),
        classrooms, courses, activities)
    assert "容量不足" not in reasons
    assert "缺少指定設備" in reasons
    assert "活動類型不符合" in reasons
    assert "不在教室可用時段內" in reasons


def test_f4_get_activity():
    classrooms, courses, activities, _ = make_world()
    add_activity(activities, activity_data(), classrooms, courses)
    assert get_activity(activities, "ACT01")["id"] == "ACT01"
    assert get_activity(activities, "NOPE") is None
