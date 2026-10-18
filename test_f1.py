# test_f1.py
import pytest
from f1_manager import (add_course, update_course, delete_course,
                        add_student, delete_student,
                        enroll_course, drop_course, get_remaining_seats)


# ==================== 工具函式 ====================

def make_rooms():
    return {"A101": {"capacity": 50}, "A102": {"capacity": 50}}


def make_args(**changes):
    """add_course 的合法參數，只改想測的欄位"""
    args = {"course_id": "CS101", "name": "程式設計", "credit": 3,
            "is_req": True, "teacher": "王老師", "max_students": 40,
            "room": "A101", "slots": [(2, "3")]}
    args.update(changes)
    return args


def try_add(courses, rooms=None, **changes):
    """呼叫 add_course，只回傳 (ok, result)"""
    rooms = make_rooms() if rooms is None else rooms
    _, ok, result = add_course(courses, rooms, **make_args(**changes))
    return ok, result


def make_world(max_students=1):
    """小世界：2 間教室、1 門課、2 位學生、空的選課表"""
    rooms = make_rooms()
    courses, students, enrollments = {}, {}, []
    try_add(courses, rooms, max_students=max_students)
    add_student(students, "S001", "甲", "資工一")
    add_student(students, "S002", "乙", "資工一")
    return rooms, courses, students, enrollments


# ==================== 新增課程：正常 ====================

def test_add_course_success():
    courses = {}
    ok, result = try_add(courses)
    assert ok is True
    assert "CS101" in courses
    assert courses["CS101"]["credit"] == 3


def test_add_course_multiple_slots_accepted():
    courses = {}
    ok, result = try_add(courses, slots=[(2, "3"), (2, "4"), (4, "5")])
    assert ok is True
    assert len(courses["CS101"]["timeSlot"]) == 3


def test_add_two_different_courses_accepted():
    courses = {}
    rooms = make_rooms()
    try_add(courses, rooms, course_id="CS101")
    ok, result = try_add(courses, rooms, course_id="CS102", room="A102")
    assert ok is True
    assert len(courses) == 2


# ==================== 新增課程：邊界 ====================

@pytest.mark.parametrize("slot", [(1, "1"), (7, "9"), (3, "a"), (3, "c")])
def test_add_course_boundary_slot_accepted(slot):
    courses = {}
    ok, result = try_add(courses, slots=[slot])
    assert ok is True


def test_add_course_capacity_1_accepted():
    courses = {}
    ok, result = try_add(courses, max_students=1)
    assert ok is True


# ==================== 新增課程：錯誤 ====================

def test_add_duplicate_course_rejected():
    courses = {}
    rooms = make_rooms()
    try_add(courses, rooms)
    ok, result = try_add(courses, rooms)
    assert ok is False
    assert len(courses) == 1


@pytest.mark.parametrize("bad_slot", [(2, "d"), (8, "3"), (0, "3"), (2, "10")])
def test_add_course_invalid_slot_rejected(bad_slot):
    courses = {}
    ok, result = try_add(courses, slots=[bad_slot])
    assert ok is False
    assert "CS101" not in courses


@pytest.mark.parametrize("field, value", [
    ("credit", 0), ("credit", 2.5), ("credit", True),
    ("max_students", 0), ("max_students", -5),
])
def test_add_course_invalid_number_rejected(field, value):
    courses = {}
    ok, result = try_add(courses, **{field: value})
    assert ok is False
    assert "CS101" not in courses


def test_add_course_empty_slots_rejected():
    courses = {}
    ok, result = try_add(courses, slots=[])
    assert ok is False


def test_add_course_duplicate_slots_rejected():
    """D001：同課重複時段（含大小寫）"""
    courses = {}
    ok, result = try_add(courses, slots=[(1, "A"), (1, "a")])
    assert ok is False


def test_add_course_nonexistent_room_rejected():
    courses = {}
    ok, result = try_add(courses, room="NO_ROOM")
    assert ok is False
    assert "CS101" not in courses


def test_add_course_multiple_errors_reported_together():
    """規格：一次列出所有錯誤"""
    courses = {}
    ok, errors = try_add(courses, credit=0, max_students=0)
    assert ok is False
    fields = {e["field"] for e in errors}
    assert {"credit", "max_student_count"} <= fields


def test_add_course_same_room_same_slot_rejected():
    """D009：同教室同時段不可排兩門課（預期失敗，新版少了這個檢查）"""
    courses = {}
    rooms = make_rooms()
    try_add(courses, rooms, course_id="CS101")
    ok, result = try_add(courses, rooms, course_id="CS102")
    assert ok is False
    assert "CS102" not in courses


# ==================== 修改課程 ====================

def test_update_course_capacity_success():
    courses = {}
    rooms = make_rooms()
    try_add(courses, rooms)
    _, ok, result = update_course(courses, [], rooms, "CS101", max_student_count=50)
    assert ok is True
    assert courses["CS101"]["maxStudentCount"] == 50


def test_update_nonexistent_course_rejected():
    _, ok, result = update_course({}, [], make_rooms(), "XX999", max_student_count=50)
    assert ok is False


def test_update_capacity_below_enrolled_rejected():
    """規格：人數上限不可低於目前已選人數"""
    rooms, courses, students, enrollments = make_world(max_students=2)
    enroll_course(enrollments, courses, students, "S001", "CS101")
    enroll_course(enrollments, courses, students, "S002", "CS101")
    _, ok, result = update_course(courses, enrollments, rooms, "CS101", max_student_count=1)
    assert ok is False
    assert courses["CS101"]["maxStudentCount"] == 2


def test_update_nonexistent_room_rejected():
    courses = {}
    rooms = make_rooms()
    try_add(courses, rooms)
    _, ok, result = update_course(courses, [], rooms, "CS101", classroom="NO_ROOM")
    assert ok is False
    assert courses["CS101"]["classroom"] == "A101"


@pytest.mark.parametrize("change, key, original", [
    ({"credit": 0}, "credit", 3),
    ({"max_student_count": 0}, "maxStudentCount", 40),
])
def test_update_course_invalid_value_rejected(change, key, original):
    """D010：修改也要套用新增的驗證規則（預期失敗）"""
    courses = {}
    rooms = make_rooms()
    try_add(courses, rooms)
    _, ok, result = update_course(courses, [], rooms, "CS101", **change)
    assert ok is False
    assert courses["CS101"][key] == original


# ==================== 刪除課程 ====================

def test_delete_course_success():
    courses = {}
    try_add(courses)
    _, ok, result = delete_course(courses, [], "CS101")
    assert ok is True
    assert "CS101" not in courses


def test_delete_nonexistent_course_rejected():
    _, ok, result = delete_course({}, [], "XX999")
    assert ok is False


def test_delete_course_with_enrolled_student_rejected():
    rooms, courses, students, enrollments = make_world()
    enroll_course(enrollments, courses, students, "S001", "CS101")
    _, ok, result = delete_course(courses, enrollments, "CS101")
    assert ok is False
    assert "CS101" in courses


def test_delete_course_after_drop_success():
    rooms, courses, students, enrollments = make_world()
    enroll_course(enrollments, courses, students, "S001", "CS101")
    drop_course(enrollments, "S001", "CS101")
    _, ok, result = delete_course(courses, enrollments, "CS101")
    assert ok is True
    assert "CS101" not in courses


# ==================== 學生與選課 ====================

def test_add_student_success():
    students = {}
    _, ok, result = add_student(students, "S001", "甲", "資工一")
    assert ok is True
    assert "S001" in students


def test_add_duplicate_student_rejected():
    students = {}
    add_student(students, "S001", "甲", "資工一")
    _, ok, result = add_student(students, "S001", "乙", "資工一")
    assert ok is False
    assert len(students) == 1


@pytest.mark.parametrize("bad_limit", [0, -1])
def test_add_student_invalid_credit_limit_rejected(bad_limit):
    """D011：學分上限必須是正整數（預期失敗）"""
    students = {}
    _, ok, result = add_student(students, "S001", "甲", "資工一", bad_limit)
    assert ok is False
    assert "S001" not in students


def test_enroll_success():
    rooms, courses, students, enrollments = make_world()
    _, ok, result = enroll_course(enrollments, courses, students, "S001", "CS101")
    assert ok is True
    assert get_remaining_seats(courses, enrollments, "CS101") == 0


def test_enroll_full_course_rejected():
    rooms, courses, students, enrollments = make_world(max_students=1)
    enroll_course(enrollments, courses, students, "S001", "CS101")
    _, ok, result = enroll_course(enrollments, courses, students, "S002", "CS101")
    assert ok is False
    assert len(enrollments) == 1


def test_drop_course_frees_seat():
    rooms, courses, students, enrollments = make_world(max_students=1)
    enroll_course(enrollments, courses, students, "S001", "CS101")
    _, ok, result = drop_course(enrollments, "S001", "CS101")
    assert ok is True
    assert get_remaining_seats(courses, enrollments, "CS101") == 1


def test_delete_student_drops_enrollments():
    rooms, courses, students, enrollments = make_world()
    enroll_course(enrollments, courses, students, "S001", "CS101")
    _, _, ok, result = delete_student(students, enrollments, "S001")   # 注意：回傳 4 個值
    assert ok is True
    assert "S001" not in students
    assert enrollments[0]["status"] == "DROPPED"


# ==================== 驗收資料：20 課、15 生、5 教室 ====================

def test_acceptance_20_courses_15_students_5_rooms():
    rooms = {f"R{i}": {"capacity": 50} for i in range(1, 6)}
    courses, students = {}, {}
    for i in range(1, 21):
        ok, result = try_add(courses, rooms, course_id=f"CS{100 + i}",
                             room=f"R{(i % 5) + 1}",
                             slots=[((i % 7) + 1, str((i % 9) + 1))])
        assert ok is True
    for i in range(1, 16):
        _, ok, result = add_student(students, f"S{i:03d}", f"學生{i}", "資工一")
        assert ok is True
    assert len(courses) == 20
    assert len(students) == 15
    assert len(rooms) == 5