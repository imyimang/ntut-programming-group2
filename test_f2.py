# test_f2.py
import copy
import pytest
from config import TIME_TYPES
from f2_checker import (
    check_course_enrollment,
    find_intersections,
    get_slot_sort_key,
    normalize_slots,
    parse_time_slots,
)


def make_course(cid, name="測試課程", credit=3, cap=40, room="B201", slots=None):
    return {
        "id": cid, "name": name, "credit": credit,
        "maxStudentCount": cap, "classroom": room,
        "timeSlot": slots if slots is not None else []
    }


def make_f2_world():
    classrooms_db = {
        "A101": {"capacity": 50},
        "A102": {"capacity": 50},
    }

    courses_db = {
        "CS101": {
            "id": "CS101", "name": "微積分", "credit": 3,
            "maxStudentCount": 40, "classroom": "A101",
            "timeSlot": "2:3-2:3",
        },
        "CS102": {
            "id": "CS102", "name": "Python程式設計", "credit": 3,
            "maxStudentCount": 40, "classroom": "A102",
            "timeSlot": [(2, "3"), (4, "5")],
        },
        "CS103": {
            "id": "CS103", "name": "資料結構", "credit": 3,
            "maxStudentCount": 1, "classroom": "A102",
            "timeSlot": [(1, "1")],
        },
        "CS104": {
            "id": "CS104", "name": "專題研究", "credit": 10,
            "maxStudentCount": 40, "classroom": "A102",
            "timeSlot": [(5, "1")],
        },
        "CS105": {
            "id": "CS105", "name": "離散數學", "credit": 3,
            "maxStudentCount": 40, "classroom": "A102",
            "timeSlot": [(3, "1"), (3, "2")],
        },
    }

    students_db = {
        "S001": {
            "id": "S001", "name": "小明", "department": "資工一",
            "maxCredit": 18, "activities": ["ACT01"],
        },
        "S002": {
            "id": "S002", "name": "小華", "department": "資工二",
            "maxCredit": 18, "activities": [],
        },
    }

    activities_db = {
        "ACT01": {
            "id": "ACT01", "name": "程式設計讀書會",
            "classroom": "B999",
            "timeSlot": [(4, "5")],
        },
    }

    enrollments = [
        {"student_id": "S001", "course_id": "CS101", "status": "ENROLLED"},
        {"student_id": "S002", "course_id": "CS103", "status": "ENROLLED"},
    ]

    return students_db, courses_db, activities_db, enrollments


def run(sid="S001", cid="CS105", setup=None):
    s, c, a, e = make_f2_world()
    if setup:
        setup(s, c, a, e)
    return check_course_enrollment(sid, cid, s, c, a, e)


def types_of(res):
    return [c["conflictType"] for c in res.get("conflicts", [])]


def five_conflicts_setup(s, c, a, e):
    c["CS300"] = {
        "id": "CS300", "name": "綜合衝突課", "credit": 20,
        "maxStudentCount": 1, "classroom": "A101",
        "timeSlot": [(2, "3"), (4, "5")],
    }
    e.append({"student_id": "S002", "course_id": "CS300", "status": "ENROLLED"})


# ==================== 正常 / 衝突案例 ====================

def test_f2_enrollment_success():
    students, courses, activities, enrollments = make_f2_world()
    result = check_course_enrollment("S001", "CS105", students, courses, activities, enrollments)
    assert result["result"] == "成功"
    assert result["conflicts"] == []
    assert result["creditAfterJoinCourse"] == 6


def test_f2_course_and_activity_conflict():
    students, courses, activities, enrollments = make_f2_world()
    result = check_course_enrollment("S001", "CS102", students, courses, activities, enrollments)
    assert result["result"] == "失敗"
    assert types_of(result) == ["STUDENT_OVERLAP", "ACTIVITY_OVERLAP"]


def test_f2_capacity_full():
    students, courses, activities, enrollments = make_f2_world()
    result = check_course_enrollment("S001", "CS103", students, courses, activities, enrollments)
    assert result["result"] == "失敗"
    assert "COURSE_FULL" in types_of(result)


def test_f2_credit_exceeded():
    students, courses, activities, enrollments = make_f2_world()
    students["S001"]["maxCredit"] = 5
    result = check_course_enrollment("S001", "CS104", students, courses, activities, enrollments)
    assert result["result"] == "失敗"
    assert "CREDIT_LIMIT" in types_of(result)


def test_f2_multiple_conflicts_accumulated_and_sorted():
    students, courses, activities, enrollments = make_f2_world()
    courses["CS102"]["timeSlot"] = [(4, "5"), (2, "3")]
    courses["CS102"]["maxStudentCount"] = 1
    enrollments.append({"student_id": "S003", "course_id": "CS102", "status": "ENROLLED"})
    result = check_course_enrollment("S001", "CS102", students, courses, activities, enrollments)

    assert result["result"] == "失敗"
    assert len(result["conflicts"]) == 3
    time_conflicts = [c for c in result["conflicts"] if c["conflictType"] in TIME_TYPES]
    assert time_conflicts[0]["timeSlot"] == (2, "3")
    assert time_conflicts[1]["timeSlot"] == (4, "5")


# ==================== 單一衝突類型 ====================

def _student_conflict(s, c, a, e):
    c["CS201"] = make_course("CS201", room="A999", slots=[(2, "3")])


def _classroom_conflict(s, c, a, e):
    c["CS202"] = make_course("CS202", room="A101", slots=[(2, "3")])


def _activity_conflict(s, c, a, e):
    c["CS203"] = make_course("CS203", room="A999", slots=[(4, "5")])


def _credit_exceeded(s, c, a, e):
    s["S001"]["maxCredit"] = 5


@pytest.mark.parametrize("expected, sid, cid, setup", [
    ("STUDENT_OVERLAP", "S001", "CS201", _student_conflict),
    ("CLASSROOM_OVERLAP", "S002", "CS202", _classroom_conflict),
    ("ACTIVITY_OVERLAP", "S001", "CS203", _activity_conflict),
    ("CREDIT_LIMIT", "S001", "CS104", _credit_exceeded),
    ("COURSE_FULL", "S001", "CS103", None),
])
def test_f2_single_conflict_only(expected, sid, cid, setup):
    result = run(sid, cid, setup)
    assert result["result"] == "失敗"
    assert types_of(result) == [expected]


def test_f2_all_five_conflict_types_reported_together():
    result = run(cid="CS300", setup=five_conflicts_setup)
    assert sorted(types_of(result)) == sorted([
        "STUDENT_OVERLAP", "CLASSROOM_OVERLAP", "ACTIVITY_OVERLAP",
        "COURSE_FULL", "CREDIT_LIMIT",
    ])


def test_f2_does_not_stop_after_first_conflict():
    result = run(cid="CS300", setup=five_conflicts_setup)
    assert len(types_of(result)) == 5


# ==================== 邊界 ====================

@pytest.mark.parametrize("max_credit, ok", [(6, True), (5, False)])
def test_f2_credit_limit_boundary(max_credit, ok):
    result = run(setup=lambda s, c, a, e: s["S001"].update(maxCredit=max_credit))
    assert (result["result"] == "成功") is ok
    assert result["creditAfterJoinCourse"] == 6


@pytest.mark.parametrize("cap, ok", [(2, True), (1, False)])
def test_f2_seat_boundary(cap, ok):
    result = run(cid="CS103", setup=lambda s, c, a, e: c["CS103"].update(maxStudentCount=cap))
    assert (result["result"] == "成功") is ok


@pytest.mark.parametrize("enrolled_slots, target_slots, expected", [
    ([(1, "1"), (7, "c")], [(1, "1"), (7, "c")], [(1, "1"), (7, "c")]),
    ([(2, "A")], [(2, "a")], [(2, "a")]),
    ([(2, "3")], [(2, "4")], []),
    ([(2, "3")], [(3, "3")], []),
    ([(3, "1"), (1, "c"), (2, "a"), (2, "9")],
     [(3, "1"), (1, "c"), (2, "a"), (2, "9")],
     [(1, "c"), (2, "9"), (3, "1")]),
])
def test_f2_time_overlap_boundary(enrolled_slots, target_slots, expected):
    def setup(s, c, a, e):
        c["CS101"]["timeSlot"] = enrolled_slots
        c["CS201"] = make_course("CS201", slots=target_slots, room="A999")
    result = run(cid="CS201", setup=setup)
    assert [c["timeSlot"] for c in result["conflicts"]] == expected


# ==================== 前置錯誤 ====================

@pytest.mark.parametrize("sid, cid, error_type", [
    ("S999", "CS105", "STUDENT_NOT_FOUND"),
    ("S001", "NOPE", "COURSE_NOT_FOUND"),
])
def test_f2_student_or_course_not_found(sid, cid, error_type):
    result = run(sid, cid)
    assert result["result"] == "失敗"
    assert result["conflicts"] == []
    assert error_type in [e["errorType"] for e in result["errors"]]


def test_f2_duplicate_enrollment_rejected():
    result = run(cid="CS101")
    assert result["result"] == "失敗"
    assert result["conflicts"] == []
    assert [e["errorType"] for e in result["errors"]] == ["ALREADY_ENROLLED"]


def test_f2_dropped_enrollment_is_ignored():
    result = run(cid="CS102", setup=lambda s, c, a, e: e[0].update(status="DROPPED"))
    assert "STUDENT_OVERLAP" not in types_of(result)
    assert result["currentCredit"] == 0


# ==================== 時段格式 ====================

def test_f2_accepts_spec_string_slots_and_merges():
    def setup(s, c, a, e):
        c["CS101"]["timeSlot"] = [(1, "5"), (1, "6")]
        c["CS210"] = make_course("CS210", room="A999", slots=" 1 : 5 - 1 : 6 ; 2:7-2:7 ")
    result = run(cid="CS210", setup=setup)
    assert types_of(result) == ["STUDENT_OVERLAP"]
    assert result["conflicts"][0]["timeSlot"] == (1, "5")
    assert "星期一第 5、6 節" in result["conflicts"][0]["description"]
    assert result["conflicts"][0]["conflictedTargets"] == ["CS101"]


def test_f2_accepts_single_period_string():
    assert parse_time_slots("2:3") == [(2, "3")]


@pytest.mark.parametrize("bad", ["1:6-1:5", "1:5-2:6", "1:x-1:6", "9:1-9:2"])
def test_f2_invalid_time_slot_reports_error(bad):
    result = run(cid="CS210", setup=lambda s, c, a, e: c.update({
        "CS210": make_course("CS210", room="A999", slots=bad)
    }))
    assert result["result"] == "失敗"
    assert "INVALID_TIME_SLOT" in [x["errorType"] for x in result["errors"]]


# ==================== 教室與活動 ====================

def test_f2_classroom_conflict_with_activity():
    def setup(s, c, a, e):
        a["ACT_RM"] = {
            "id": "ACT_RM", "name": "教室活動", "classroom": "A101",
            "timeSlot": [(6, "1")],
        }
        c["CS202"] = make_course("CS202", room="A101", slots=[(6, "1")])
    result = run(sid="S002", cid="CS202", setup=setup)
    assert types_of(result) == ["CLASSROOM_OVERLAP"]
    assert result["conflicts"][0]["conflictedTargets"] == ["ACT_RM"]


# ==================== 髒資料：跳過並回報 ====================

def _dangling_enrollment(s, c, a, e):
    e.append({"student_id": "S001", "course_id": "GHOST", "status": "ENROLLED"})


def _unknown_activity(s, c, a, e):
    s["S001"]["activities"].append("NO_SUCH_ACT")


def _invalid_other_course(s, c, a, e):
    c["CS199"] = make_course("CS199", room="A102", slots="bad-format")


@pytest.mark.parametrize("setup, error_type", [
    (_dangling_enrollment, "ENROLLED_COURSE_NOT_FOUND"),
    (_unknown_activity, "ACTIVITY_NOT_FOUND"),
    (_invalid_other_course, "INVALID_TIME_SLOT"),
])
def test_f2_dirty_data_skipped_and_reported(setup, error_type):
    result = run(setup=setup)
    assert result["result"] == "成功"
    assert error_type in [e["errorType"] for e in result["errors"]]


# ==================== 輸出契約 ====================

def test_f2_does_not_modify_inputs():
    world = make_f2_world()
    snapshot = copy.deepcopy(world)
    check_course_enrollment("S001", "CS105", *world)
    check_course_enrollment("S001", "CS102", *world)
    assert world == snapshot


def test_f2_result_contains_required_output_fields():
    result = run()
    for key in ("studentId", "studentName", "courseId", "courseName", "result",
                "conflicts", "currentCredit", "creditAfterJoinCourse", "maxCredit"):
        assert key in result
    assert result["studentId"] == "S001"
    assert result["studentName"] == "小明"
    assert result["courseId"] == "CS105"
    assert result["courseName"] == "離散數學"
    assert (result["currentCredit"], result["creditAfterJoinCourse"], result["maxCredit"]) == (3, 6, 18)


def test_f2_conflict_detail_fields():
    result = run(cid="CS201", setup=_student_conflict)
    conflict = result["conflicts"][0]
    for key in ("conflictType", "timeSlot", "conflictedTargets"):
        assert key in conflict
    assert conflict["conflictedTargets"] == ["CS101"]


# ==================== Helper 函式 ====================

def test_f2_helper_functions():
    assert find_intersections([], [(1, "1")]) == []
    assert find_intersections([[2, "A"]], [(2, "a")]) == [(2, "a")]
    assert normalize_slots([(1, "1"), (1,), "x", None]) == {(1, "1")}
    assert get_slot_sort_key((2, "9")) < get_slot_sort_key((2, "a")) < get_slot_sort_key((3, "1"))


def test_bug_f2_01_non_time_conflicts_sorted_last():
    result = run(cid="CS300", setup=five_conflicts_setup)
    kinds = types_of(result)
    last_time = max(i for i, t in enumerate(kinds) if t in TIME_TYPES)
    first_other = min(i for i, t in enumerate(kinds) if t not in TIME_TYPES)
    assert last_time < first_other


def test_bug_f2_02_consecutive_periods_merged():
    def setup(s, c, a, e):
        c["CS101"]["timeSlot"] = [(2, "3"), (2, "4")]
        c["CS201"] = make_course("CS201", slots=[(2, "3"), (2, "4")], room="A999")
    result = run(cid="CS201", setup=setup)
    assert types_of(result).count("STUDENT_OVERLAP") == 1
    assert "星期二第 3、4 節" in result["conflicts"][0]["description"]


def test_bug_f2_03_duplicate_enrollment_is_only_error():
    result = run(cid="CS101", setup=lambda s, c, a, e: s["S001"].update(maxCredit=5))
    assert [e["errorType"] for e in result["errors"]] == ["ALREADY_ENROLLED"]
