# test_f5.py
import copy
import pytest

from f5_filter import filter_courses


def make_courses():
    return {
        "C001": {
            "id": "C001", "name": "微積分", "credit": 3,
            "maxStudentCount": 40, "classroom": "R101", "timeSlot": [(1, "1")],
        },
        "C002": {
            "id": "C002", "name": "程式設計", "credit": 3,
            "maxStudentCount": 40, "classroom": "R101", "timeSlot": [(1, "1")],
        },
        "C003": {
            "id": "C003", "name": "英文", "credit": 2,
            "maxStudentCount": 40, "classroom": "R102", "timeSlot": [(2, "2")],
        },
        "C004": {
            "id": "C004", "name": "專題", "credit": 10,
            "maxStudentCount": 40, "classroom": "R103", "timeSlot": [(3, "3")],
        },
        "C005": {
            "id": "C005", "name": "熱門課", "credit": 3,
            "maxStudentCount": 1, "classroom": "R104", "timeSlot": [(4, "4")],
        },
    }


def make_enrollments():
    return [{"student_id": "S900", "course_id": "C005", "status": "ENROLLED"}]


def run(**kwargs):
    courses = kwargs.pop("courses", make_courses())
    enrollments = kwargs.pop("enrollments", make_enrollments())
    return filter_courses(courses, enrollments, **kwargs)


# ==================== 正常案例 ====================

def test_f5_returns_all_eligible_courses():
    result = run(min_credit=6, max_credit=20)
    assert result["isFeasible"] is True
    assert [c["id"] for c in result["candidateCourses"]] == ["C001", "C002", "C003", "C004"]


def test_f5_preferred_days_sort_candidates_first():
    result = run(min_credit=0, max_credit=20, preferred_days=[2])
    assert [c["id"] for c in result["candidateCourses"]] == ["C003", "C001", "C002", "C004"]


def test_f5_preferred_days_are_not_hard_filter():
    result = run(min_credit=0, max_credit=20, preferred_days=[2])
    assert len(result["candidateCourses"]) == 4


def test_f5_forbidden_times_exclude_courses():
    result = run(min_credit=0, max_credit=20, forbidden_times=[(1, "1")])
    assert [c["id"] for c in result["candidateCourses"]] == ["C003", "C004"]


def test_f5_full_course_is_excluded():
    result = run(min_credit=0, max_credit=20)
    assert "C005" not in [c["id"] for c in result["candidateCourses"]]


def test_f5_wished_missing_course_reports_reason():
    result = run(min_credit=0, max_credit=20, wished_courses=["C999"])
    excluded = {c["courseId"]: c for c in result["excludedCourses"]}
    assert excluded["C999"]["reasons"] == ["課程不存在"]


def test_f5_wished_full_course_reports_reason():
    result = run(min_credit=0, max_credit=20, wished_courses=["C005"])
    excluded = {c["courseId"]: c for c in result["excludedCourses"]}
    assert "課程已額滿" in excluded["C005"]["reasons"]


def test_f5_required_courses_included_when_valid():
    result = run(min_credit=0, max_credit=20, required_courses=["C001"])
    assert result["isFeasible"] is True
    assert "C001" in [c["id"] for c in result["candidateCourses"]]


# ==================== 邊界案例 ====================

def test_f5_min_credit_exactly_met():
    total = 3 + 3 + 2 + 10
    result = run(min_credit=total, max_credit=20)
    assert result["isFeasible"] is True
    assert result["unmetReasons"] == []


def test_f5_required_credit_equals_max_credit():
    result = run(min_credit=0, max_credit=3, required_courses=["C001"])
    assert result["isFeasible"] is True


def test_f5_no_courses_available_below_minimum():
    result = run(min_credit=1, max_credit=20,
                 forbidden_times=[(1, "1"), (2, "2"), (3, "3"), (4, "4")])
    assert result["isFeasible"] is False
    assert any("仍低於最低學分" in r for r in result["unmetReasons"])


def test_f5_empty_course_db():
    result = run(courses={}, min_credit=0, max_credit=10)
    assert result["candidateCourses"] == []
    assert result["isFeasible"] is True


# ==================== 錯誤與衝突案例 ====================

def test_f5_min_credit_greater_than_max_credit():
    result = run(min_credit=10, max_credit=5)
    assert result["isFeasible"] is False
    assert "最低學分不可大於最高學分" in result["unmetReasons"]


@pytest.mark.parametrize("min_credit, max_credit", [("-1", 10), (0, "x"), (-1, 10)])
def test_f5_invalid_credit_input(min_credit, max_credit):
    result = run(min_credit=min_credit, max_credit=max_credit)
    assert result["isFeasible"] is False
    assert result["unmetReasons"]


def test_f5_required_course_in_forbidden_time():
    result = run(min_credit=0, max_credit=20,
                 required_courses=["C001"], forbidden_times=[(1, "1")])
    assert result["isFeasible"] is False
    assert any("落在不可上課時段" in r for r in result["unmetReasons"])


def test_f5_required_courses_conflict():
    result = run(min_credit=0, max_credit=20, required_courses=["C001", "C002"])
    assert result["isFeasible"] is False
    assert any("衝堂" in r for r in result["unmetReasons"])


def test_f5_required_course_full():
    result = run(min_credit=0, max_credit=20, required_courses=["C005"])
    assert result["isFeasible"] is False
    assert any("已額滿" in r for r in result["unmetReasons"])


def test_f5_required_credits_exceed_max():
    result = run(min_credit=0, max_credit=6, required_courses=["C004"])
    assert result["isFeasible"] is False
    assert any("超過最高學分" in r for r in result["unmetReasons"])


def test_f5_cannot_reach_min_credit():
    result = run(min_credit=100, max_credit=200)
    assert result["isFeasible"] is False
    assert any("仍低於最低學分" in r for r in result["unmetReasons"])


def test_f5_multiple_problems_all_reported():
    result = run(
        min_credit=50, max_credit=2,
        required_courses=["C001", "C002", "C005", "C999"],
        forbidden_times=[(1, "1")],
    )
    reasons = " | ".join(result["unmetReasons"])
    assert result["isFeasible"] is False
    assert "最低學分不可大於最高學分" in reasons
    assert "不存在" in reasons
    assert "落在不可上課時段" in reasons
    assert "衝堂" in reasons
    assert "已額滿" in reasons
    assert "超過最高學分" in reasons


def test_f5_required_course_excluded_listed():
    result = run(min_credit=0, max_credit=20,
                 required_courses=["C001"], forbidden_times=[(1, "1")])
    excluded = {c["courseId"]: c for c in result["excludedCourses"]}
    assert "C001" in excluded
    assert any("不可上課時段" in r for r in excluded["C001"]["reasons"])


def test_f5_does_not_modify_inputs():
    courses = make_courses()
    enrollments = make_enrollments()
    snapshot = copy.deepcopy((courses, enrollments))
    filter_courses(courses, enrollments, wished_courses=["C001"],
                   required_courses=["C002"], min_credit=0, max_credit=20,
                   forbidden_times=[(1, "1")], preferred_days=[1])
    assert (courses, enrollments) == snapshot
