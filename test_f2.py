# test_f2.py
import copy
import pytest
from f2_checker import check_course_enrollment


# ==================== 工具與 Helper 函式 ====================

TIME_TYPES = {"COURSE_CONFLICT", "CLASSROOM_CONFLICT", "ACTIVITY_CONFLICT"}


def make_course(cid, name="測試課程", credit=3, cap=40, room="B201", slots=None):
    return {
        "id": cid, "name": name, "credit": credit,
        "maxStudentCount": cap, "classroom": room,
        "timeSlot": slots if slots is not None else []
    }


def make_f2_world():

    classrooms_db = {
        "A101": {"capacity": 50},
        "A102": {"capacity": 50}
    }

    courses_db = {

        "CS101": {
            "id": "CS101", "name": "微積分", "credit": 3,
            "maxStudentCount": 40, "classroom": "A101",
            "timeSlot": [(2, "3")]
        },

        "CS102": {
            "id": "CS102", "name": "Python程式設計", "credit": 3,
            "maxStudentCount": 40, "classroom": "A102",
            "timeSlot": [(2, "3"), (4, "5")]
        },
 
        "CS103": {
            "id": "CS103", "name": "資料結構", "credit": 3,
            "maxStudentCount": 1, "classroom": "A102",
            "timeSlot": [(1, "1")]
        },
 
        "CS104": {
            "id": "CS104", "name": "專題研究", "credit": 10,
            "maxStudentCount": 40, "classroom": "A102",
            "timeSlot": [(5, "1")]
        },
   
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
  
        "ACT01": {
            "id": "ACT01", "name": "程式設計讀書會",
            "timeSlot": [(4, "5")]
        }
    }

  
    enrollments = [
        {"student_id": "S001", "course_id": "CS101", "status": "ENROLLED"},
        {"student_id": "S002", "course_id": "CS103", "status": "ENROLLED"}
    ]

    return students_db, courses_db, activities_db, enrollments


def run(sid="S001", cid="CS105", setup=None):
    s, c, a, e = make_f2_world()
    if setup:
        setup(s, c, a, e)
    return check_course_enrollment(sid, cid, s, c, a, e)


def types_of(res):
    return [c["type"] for c in res.get("conflicts", [])]


def five_conflicts_setup(s, c, a, e):
  
    c["CS300"] = {
        "id": "CS300", "name": "綜合衝突課", "credit": 20,
        "maxStudentCount": 1, "classroom": "A101",
        "timeSlot": [(2, "3"), (4, "5")]
    }
    e.append({"student_id": "S002", "course_id": "CS300", "status": "ENROLLED"})


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
    
    students, courses, activities, enrollments = make_f2_world()
    students["S001"]["maxCredit"] = 5 
    result = check_course_enrollment("S001", "CS104", students, courses, activities, enrollments)
    assert result["success"] is False
    types = [c["type"] for c in result["conflicts"]]
    assert "CREDIT_EXCEEDED" in types


def test_f2_multiple_conflicts_accumulated_and_sorted():

    students, courses, activities, enrollments = make_f2_world()
    courses["CS102"]["timeSlot"] = [(4, "5"), (2, "3")]
    courses["CS102"]["maxStudentCount"] = 1
    enrollments.append({"student_id": "S003", "course_id": "CS102", "status": "ENROLLED"})
    result = check_course_enrollment("S001", "CS102", students, courses, activities, enrollments)

    assert result["success"] is False
    assert len(result["conflicts"]) == 3

    time_conflicts = [c for c in result["conflicts"] if c["type"] in ("COURSE_CONFLICT", "ACTIVITY_CONFLICT")]
    assert time_conflicts[0]["slot"] == (2, "3")
    assert time_conflicts[1]["slot"] == (4, "5")




def _student_conflict(s, c, a, e):
    c["CS201"] = make_course("CS201", room="A999", slots=[(2, "3")])


def _classroom_conflict(s, c, a, e):
    s["S002"] = {"id": "S002", "maxCredit": 18, "activities": []}
    c["CS202"] = make_course("CS202", room="A101", slots=[(2, "3")])


def _activity_conflict(s, c, a, e):
    c["CS203"] = make_course("CS203", slots=[(4, "5")])


def _credit_exceeded(s, c, a, e):
    s["S001"]["maxCredit"] = 5


@pytest.mark.parametrize("expected, sid, cid, setup", [
    ("COURSE_CONFLICT",    "S001", "CS201", _student_conflict),
    ("CLASSROOM_CONFLICT", "S002", "CS202", _classroom_conflict),
    ("ACTIVITY_CONFLICT",  "S001", "CS203", _activity_conflict),
    ("CREDIT_EXCEEDED",    "S001", "CS104", _credit_exceeded),
    ("CAPACITY_FULL",      "S001", "CS103", None),
])
def test_f2_single_conflict_only(expected, sid, cid, setup):

    result = run(sid, cid, setup)
    assert result["success"] is False
    assert types_of(result) == [expected]


def test_f2_all_five_conflict_types_reported_together():

    result = run(cid="CS300", setup=five_conflicts_setup)
    assert sorted(types_of(result)) == sorted(
        ["COURSE_CONFLICT", "CLASSROOM_CONFLICT", "ACTIVITY_CONFLICT",
         "CAPACITY_FULL", "CREDIT_EXCEEDED"])




@pytest.mark.parametrize("max_credit, ok", [(6, True), (5, False)])
def test_f2_credit_limit_boundary(max_credit, ok):

    result = run(setup=lambda s, c, a, e: s["S001"].update(maxCredit=max_credit))
    assert result["success"] is ok
    assert result["after_credits"] == 6


@pytest.mark.parametrize("cap, ok", [(2, True), (1, False)])
def test_f2_seat_boundary(cap, ok):
 
    result = run(cid="CS103", setup=lambda s, c, a, e: c["CS103"].update(maxStudentCount=cap))
    assert result["success"] is ok


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
        c["CS201"] = make_course("CS201", slots=target_slots)
    result = run(cid="CS201", setup=setup)
    assert [c["slot"] for c in result["conflicts"]] == expected



@pytest.mark.parametrize("sid, cid", [("S999", "CS105"), ("S001", "NOPE")])
def test_f2_student_or_course_not_found(sid, cid):

    result = run(sid, cid)
    assert result["success"] is False
    assert result.get("errors") or result.get("conflicts")


def test_f2_duplicate_enrollment_rejected():

    result = run(cid="CS101")
    assert result["success"] is False
    assert "DUPLICATE" in types_of(result)


def test_f2_dropped_enrollment_is_ignored():
 
    result = run(cid="CS102", setup=lambda s, c, a, e: e[0].update(status="DROPPED"))
    assert "COURSE_CONFLICT" not in types_of(result)
    assert result["current_credits"] == 0


def _dangling_enrollment(s, c, a, e):
    e.append({"student_id": "S001", "course_id": "GHOST", "status": "ENROLLED"})


def _unknown_activity(s, c, a, e):
    s["S001"]["activities"].append("NO_SUCH_ACT")


def _no_timeslot(s, c, a, e):
    del c["CS105"]["timeSlot"]


@pytest.mark.parametrize("setup", [_dangling_enrollment, _unknown_activity, _no_timeslot])
def test_f2_dirty_data_does_not_crash(setup):

    result = run(setup=setup)
    assert result["success"] is True


def test_f2_does_not_modify_inputs():

    world = make_f2_world()
    snapshot = copy.deepcopy(world)
    check_course_enrollment("S001", "CS105", *world)
    check_course_enrollment("S001", "CS102", *world)
    assert world == snapshot


def test_f2_result_contains_required_output_fields():

    result = run()
    for key in ("success", "student_id", "target_course", "conflicts",
                "current_credits", "after_credits", "max_credits"):
        assert key in result
    assert result["target_course"] == "CS105 離散數學"
    assert (result["current_credits"], result["after_credits"], result["max_credits"]) == (3, 6, 18)


def test_f2_helper_functions():

    from f2_checker import find_intersections, normalize_slots, get_slot_sort_key
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
        c["CS201"] = make_course("CS201", slots=[(2, "3"), (2, "4")])
    result = run(cid="CS201", setup=setup)
    assert types_of(result).count("COURSE_CONFLICT") == 1
    assert "星期二第 3、4 節" in result["conflicts"][0]["description"]


def test_bug_f2_03_duplicate_enrollment_is_only_error():

    result = run(cid="CS101", setup=lambda s, c, a, e: s["S001"].update(maxCredit=5))
    assert types_of(result) == ["DUPLICATE"]


@pytest.mark.parametrize("sid, cid", [("S999", "CS105"), ("S001", "NOPE")])
def test_bug_f2_04_precondition_error_has_consistent_shape(sid, cid):

    result = run(sid, cid)
    assert result["success"] is False
    assert "conflicts" in result
