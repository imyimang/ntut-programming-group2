# test_integration.py
from f1_manager import enroll_course, generate_sample_data
from f2_checker import check_course_enrollment
from f3_schedule import build_schedule_matrix, find_course_slots
from f4_activities import add_activity, enroll_activity
from f5_filter import filter_courses
from f6_storage import load_all, save_all


def test_f1_to_f6_round_trip_keeps_schedule(tmp_path):
    classrooms, courses, students, enrollments = generate_sample_data()
    enroll_course(enrollments, courses, students, "S001", "CS101")
    save_all(str(tmp_path), classrooms, courses, students, {}, enrollments)

    loaded = load_all(str(tmp_path))
    assert loaded["errors"] == []
    assert loaded["students"]["S001"]["courses"] == ["CS101"]

    matrix = build_schedule_matrix(
        "S001", loaded["students"], loaded["courses"], loaded["activities"])
    assert find_course_slots(matrix, "CS101") == courses["CS101"]["timeSlot"]


def test_f2_works_with_f6_loaded_data(tmp_path):
    classrooms, courses, students, enrollments = generate_sample_data()
    enroll_course(enrollments, courses, students, "S001", "CS101")
    save_all(str(tmp_path), classrooms, courses, students, {}, enrollments)
    loaded = load_all(str(tmp_path))

    result = check_course_enrollment(
        "S001", "CS102", loaded["students"], loaded["courses"],
        loaded["activities"], loaded["enrollments"])
    assert result["result"] == "成功"
    assert result["courseId"] == "CS102"
    assert result["currentCredit"] == 3


def test_f4_activity_appears_in_f3_schedule():
    classrooms = {
        "R101": {
            "name": "R101", "roomCapacity": 40, "timeSlot": [],
            "type": "lecture", "devices": ["projector"],
        },
    }
    activities = {}
    students = {"S001": {"id": "S001", "name": "小明", "courses": [], "activities": []}}
    add_activity(activities, {
        "id": "ACT01", "name": "讀書會", "date": "2026-06-29",
        "timeSlot": [(1, "2")], "studentCount": 20, "type": "lecture",
        "requireList": ["projector"], "classroom": "R101",
    }, classrooms, {})
    result = enroll_activity("ACT01", "S001", activities, students, {}, classrooms_db=classrooms)
    assert result["success"] is True

    matrix = build_schedule_matrix("S001", students, {}, activities)
    assert matrix[0][1] is not None
    assert "ACT01" in matrix[0][1]


def test_f4_rejects_activity_room_already_used_by_f1_course():
    classrooms = {
        "R101": {
            "name": "R101", "roomCapacity": 40,
            "timeSlot": [(1, "1")], "type": "lecture", "devices": ["projector"],
        },
    }
    courses = {
        "CS101": {
            "id": "CS101", "name": "微積分", "credit": 3,
            "maxStudentCount": 40, "classroom": "R101", "timeSlot": [(1, "1")],
        },
    }
    _, ok, errors = add_activity({}, {
        "id": "ACT01", "name": "讀書會", "date": "2026-06-29",
        "timeSlot": [(1, "1")], "studentCount": 20, "type": "lecture",
        "requireList": ["projector"], "classroom": "R101",
    }, classrooms, courses)
    assert ok is False
    assert any("時段已被占用" in e["reason"] for e in errors)


def test_f5_uses_f6_loaded_data(tmp_path):
    classrooms, courses, students, enrollments = generate_sample_data()
    enroll_course(enrollments, courses, students, "S001", "CS101")
    save_all(str(tmp_path), classrooms, courses, students, {}, enrollments)
    loaded = load_all(str(tmp_path))

    result = filter_courses(
        loaded["courses"], loaded["enrollments"],
        wished_courses=["CS102"], required_courses=["MA101"],
        min_credit=10, max_credit=25,
        forbidden_times=[(1, "1")],
        preferred_days=[2],
    )
    assert result["isFeasible"] is True
    assert "MA101" in [c["id"] for c in result["candidateCourses"]]
    assert "CS102" in [c["id"] for c in result["candidateCourses"]]


def test_f4_and_f6_activity_round_trip(tmp_path):
    classrooms = {
        "R101": {
            "name": "R101", "roomCapacity": 40, "timeSlot": [(1, "2")],
            "type": "lecture", "devices": ["projector"],
        },
    }
    activities = {}
    students = {"S001": {"id": "S001", "name": "小明", "majorYear": "資工一", "maxCredit": 25, "courses": [], "activities": []}}
    add_activity(activities, {
        "id": "ACT01", "name": "讀書會", "date": "2026-06-29",
        "timeSlot": [(1, "2")], "studentCount": 20, "type": "lecture",
        "requireList": ["projector"], "classroom": "R101",
    }, classrooms, {})
    enroll_activity("ACT01", "S001", activities, students, {}, classrooms_db=classrooms)
    save_all(str(tmp_path), classrooms, {}, students, activities, [])

    loaded = load_all(str(tmp_path))
    assert loaded["activities"]["ACT01"]["participants"] == ["S001"]
    assert loaded["students"]["S001"]["activities"] == ["ACT01"]
    assert loaded["activities"]["ACT01"]["classroom"] == "R101"
