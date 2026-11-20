# test_f6.py
import csv
import os

import pytest

from config import (
    ACTIVITY_HEADER,
    CLASSROOM_HEADER,
    COURSE_HEADER,
    ENROLLMENT_HEADER,
    STUDENT_HEADER,
)
from f6_storage import (
    load_all,
    parse_slot_text,
    save_all,
    slots_to_text,
    validate_references,
)


def sample_data():
    classrooms = {
        "R101": {
            "name": "R101", "roomCapacity": 40,
            "timeSlot": [(1, "1"), (1, "2")],
            "type": "lecture", "devices": ["projector", "pc"],
        },
    }
    courses = {
        "CS101": {
            "id": "CS101", "name": "計算機概論", "credit": 3,
            "isRequired": True, "teacherName": "王大明",
            "maxStudentCount": 50, "classroom": "R101",
            "timeSlot": [(1, "1")],
        },
    }
    students = {
        "S001": {
            "id": "S001", "name": "小明", "majorYear": "資工一",
            "maxCredit": 25, "courses": [], "activities": [],
        },
    }
    activities = {
        "ACT01": {
            "id": "ACT01", "name": "程式設計讀書會", "date": "2026-06-29",
            "timeSlot": [(1, "2")], "studentCount": 20, "type": "lecture",
            "requireList": ["projector"], "classroom": "R101",
            "participants": ["S001"],
        },
    }
    enrollments = [
        {"student_id": "S001", "course_id": "CS101", "status": "ENROLLED"},
    ]
    return classrooms, courses, students, activities, enrollments


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def write_only(tmp_path, name, header, rows):
    write_csv(os.path.join(tmp_path, name), header, rows)


# ==================== 正常案例 ====================

def test_f6_save_and_load_round_trip(tmp_path):
    data = sample_data()
    counts = save_all(tmp_path, *data)
    loaded = load_all(tmp_path)
    assert counts == {
        "courses": 1, "students": 1, "classrooms": 1,
        "activities": 1, "enrollments": 1,
    }
    assert loaded["errors"] == []
    assert loaded["issues"] == []


def test_f6_course_fields_round_trip(tmp_path):
    save_all(tmp_path, *sample_data())
    loaded = load_all(tmp_path)
    course = loaded["courses"]["CS101"]
    assert course["name"] == "計算機概論"
    assert course["credit"] == 3
    assert course["isRequired"] is True
    assert course["teacherName"] == "王大明"
    assert course["maxStudentCount"] == 50
    assert course["classroom"] == "R101"
    assert course["timeSlot"] == [(1, "1")]


def test_f6_student_courses_rebuilt_from_enrollments(tmp_path):
    save_all(tmp_path, *sample_data())
    loaded = load_all(tmp_path)
    assert loaded["students"]["S001"]["courses"] == ["CS101"]


def test_f6_student_activities_rebuilt_from_participants(tmp_path):
    save_all(tmp_path, *sample_data())
    loaded = load_all(tmp_path)
    assert loaded["students"]["S001"]["activities"] == ["ACT01"]


def test_f6_classroom_devices_round_trip(tmp_path):
    save_all(tmp_path, *sample_data())
    loaded = load_all(tmp_path)
    room = loaded["classrooms"]["R101"]
    assert room["devices"] == ["projector", "pc"]
    assert room["roomCapacity"] == 40
    assert room["type"] == "lecture"


def test_f6_activity_fields_round_trip(tmp_path):
    save_all(tmp_path, *sample_data())
    loaded = load_all(tmp_path)
    activity = loaded["activities"]["ACT01"]
    assert activity["date"] == "2026-06-29"
    assert activity["timeSlot"] == [(1, "2")]
    assert activity["requireList"] == ["projector"]
    assert activity["classroom"] == "R101"
    assert activity["participants"] == ["S001"]


def test_f6_enrollment_status_round_trip(tmp_path):
    save_all(tmp_path, *sample_data())
    loaded = load_all(tmp_path)
    assert loaded["enrollments"][0]["status"] == "ENROLLED"


def test_f6_compact_slot_text_round_trip():
    slots = [(1, "3"), (4, "1"), (4, "2"), (5, "a"), (5, "b")]
    text = slots_to_text(slots)
    assert text == "13,41,42,5A,5B"
    parsed, errors = parse_slot_text(text)
    assert errors == []
    assert parsed == slots


def test_f6_f2_range_slot_format_supported(tmp_path):
    write_only(tmp_path, "courses.csv", COURSE_HEADER, [
        ["CS101", "微積分", "3", "1", "老師", "40", "R101", "1:1-1:2;2:3-2:3"],
    ])
    loaded = load_all(tmp_path)
    assert loaded["courses"]["CS101"]["timeSlot"] == [(1, "1"), (1, "2"), (2, "3")]


def test_f6_missing_files_load_as_empty_with_warnings(tmp_path):
    loaded = load_all(tmp_path)
    assert loaded["courses"] == {}
    assert loaded["students"] == {}
    assert loaded["activities"] == {}
    assert len(loaded["warnings"]) == 5


def test_f6_save_creates_directory(tmp_path):
    target = tmp_path / "nested" / "data"
    save_all(str(target), *sample_data())
    assert target.exists()
    assert (target / "courses.csv").exists()


def test_f6_legacy_five_column_students_supported(tmp_path):
    write_only(tmp_path, "students.csv", STUDENT_HEADER, [
        ["S001", "小明", "資工一", "CS101", "25"],
    ])
    loaded = load_all(tmp_path)
    assert loaded["students"]["S001"]["maxCredit"] == 25


# ==================== 邊界案例 ====================

def test_f6_empty_file_is_empty_data(tmp_path):
    open(os.path.join(tmp_path, "courses.csv"), "w").close()
    loaded = load_all(tmp_path)
    assert loaded["courses"] == {}
    assert any(w["reason"].startswith("File is empty") for w in loaded["warnings"])


def test_f6_header_only_file_is_empty_data(tmp_path):
    write_only(tmp_path, "enrollments.csv", ENROLLMENT_HEADER, [])
    loaded = load_all(tmp_path)
    assert loaded["enrollments"] == []
    assert loaded["errors"] == []


def test_f6_first_and_last_period_slots(tmp_path):
    write_only(tmp_path, "courses.csv", COURSE_HEADER, [
        ["CS101", "A", "3", "1", "T", "40", "R101", "11,7C"],
    ])
    loaded = load_all(tmp_path)
    assert loaded["courses"]["CS101"]["timeSlot"] == [(1, "1"), (7, "c")]


def test_f6_utf8_bom_header_accepted(tmp_path):
    path = os.path.join(tmp_path, "enrollments.csv")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        handle.write("\ufeff" + ",".join(ENROLLMENT_HEADER) + "\nS001,CS101,ENROLLED\n")
    loaded = load_all(tmp_path)
    assert loaded["errors"] == []
    assert len(loaded["enrollments"]) == 1


def test_f6_whitespace_in_slot_text_ignored(tmp_path):
    write_only(tmp_path, "classrooms.csv", CLASSROOM_HEADER, [
        ["R101", "40", " 1 1 , 1 2 ", "lecture", "projector;pc"],
    ])
    loaded = load_all(tmp_path)
    assert loaded["classrooms"]["R101"]["timeSlot"] == [(1, "1"), (1, "2")]


def test_f6_dropped_enrollment_does_not_link_course(tmp_path):
    classrooms, courses, students, activities, enrollments = sample_data()
    enrollments[0]["status"] = "DROPPED"
    save_all(tmp_path, classrooms, courses, students, activities, enrollments)
    loaded = load_all(tmp_path)
    assert loaded["students"]["S001"]["courses"] == []


def test_f6_empty_classroom_time_slots_allowed(tmp_path):
    classrooms, courses, students, activities, enrollments = sample_data()
    classrooms["R101"]["timeSlot"] = []
    save_all(tmp_path, classrooms, courses, students, activities, enrollments)
    loaded = load_all(tmp_path)
    assert loaded["classrooms"]["R101"]["timeSlot"] == []


def test_f6_output_is_sorted_by_id(tmp_path):
    classrooms, courses, students, activities, enrollments = sample_data()
    courses["CS100"] = dict(courses["CS101"], id="CS100", timeSlot=[(1, "2")])
    save_all(tmp_path, classrooms, courses, students, activities, enrollments)
    with open(os.path.join(tmp_path, "courses.csv"), newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert [row[0] for row in rows[1:]] == ["CS100", "CS101"]


def test_f6_save_data_wrapper(tmp_path):
    from f6_storage import save_data
    classrooms, courses, students, activities, enrollments = sample_data()
    data = {
        "classrooms": classrooms, "courses": courses, "students": students,
        "activities": activities, "enrollments": enrollments,
    }
    save_data(str(tmp_path), data)
    assert load_all(str(tmp_path))["courses"]["CS101"]["id"] == "CS101"


# ==================== 錯誤與衝突案例 ====================

def test_f6_malformed_course_row_skipped(tmp_path):
    write_only(tmp_path, "courses.csv", COURSE_HEADER, [
        ["CS101", "微積分", "3"],
        ["CS102", "程式", "3", "1", "T", "40", "R101", "12"],
    ])
    loaded = load_all(tmp_path)
    assert "CS101" not in loaded["courses"]
    assert "CS102" in loaded["courses"]
    assert loaded["errors"][0]["line"] == 2


@pytest.mark.parametrize("row, reason", [
    (["CS101", "A", "0", "1", "T", "40", "R101", "11"], "Invalid credit"),
    (["CS101", "A", "3", "x", "T", "40", "R101", "11"], "Invalid isRequired"),
    (["CS101", "A", "3", "1", "T", "0", "R101", "11"], "Invalid maxStudentCount"),
    (["CS101", "A", "3", "1", "T", "40", "R101", "1Z"], "Invalid time slot"),
])
def test_f6_invalid_course_fields_skipped(tmp_path, row, reason):
    write_only(tmp_path, "courses.csv", COURSE_HEADER, [row])
    loaded = load_all(tmp_path)
    assert loaded["courses"] == {}
    assert any(reason in e["reason"] for e in loaded["errors"])


def test_f6_duplicate_course_id_skipped(tmp_path):
    write_only(tmp_path, "courses.csv", COURSE_HEADER, [
        ["CS101", "A", "3", "1", "T", "40", "R101", "11"],
        ["CS101", "B", "3", "1", "T", "40", "R101", "12"],
    ])
    loaded = load_all(tmp_path)
    assert loaded["courses"]["CS101"]["name"] == "A"
    assert any("Duplicate course id" in e["reason"] for e in loaded["errors"])


def test_f6_invalid_student_credit_skipped(tmp_path):
    write_only(tmp_path, "students.csv", STUDENT_HEADER, [
        ["S001", "小明", "資工一", "0"],
    ])
    loaded = load_all(tmp_path)
    assert loaded["students"] == {}
    assert any("Invalid maxCredit" in e["reason"] for e in loaded["errors"])


def test_f6_invalid_classroom_capacity_skipped(tmp_path):
    write_only(tmp_path, "classrooms.csv", CLASSROOM_HEADER, [
        ["R101", "abc", "11", "lecture", "projector"],
    ])
    loaded = load_all(tmp_path)
    assert loaded["classrooms"] == {}
    assert any("Invalid roomCapacity" in e["reason"] for e in loaded["errors"])


def test_f6_invalid_enrollment_status_skipped(tmp_path):
    write_only(tmp_path, "enrollments.csv", ENROLLMENT_HEADER, [
        ["S001", "CS101", "WAITING"],
    ])
    loaded = load_all(tmp_path)
    assert loaded["enrollments"] == []
    assert any("Invalid status" in e["reason"] for e in loaded["errors"])


def test_f6_invalid_activity_date_skipped(tmp_path):
    write_only(tmp_path, "activities.csv", ACTIVITY_HEADER, [
        ["ACT01", "A", "not-a-date", "12", "10", "lecture", "", "", ""],
    ])
    loaded = load_all(tmp_path)
    assert loaded["activities"] == {}
    assert any("Invalid date" in e["reason"] for e in loaded["errors"])


def test_f6_activity_weekday_mismatch_skipped(tmp_path):
    write_only(tmp_path, "activities.csv", ACTIVITY_HEADER, [
        ["ACT01", "A", "2026-06-29", "21", "10", "lecture", "", "", ""],
    ])
    loaded = load_all(tmp_path)
    assert loaded["activities"] == {}
    assert any("weekday does not match" in e["reason"] for e in loaded["errors"])


def test_f6_header_mismatch_reported(tmp_path):
    write_only(tmp_path, "courses.csv", ["wrong", "header"], [
        ["CS101", "A", "3", "1", "T", "40", "R101", "11"],
    ])
    loaded = load_all(tmp_path)
    assert any("Invalid header" in e["reason"] for e in loaded["errors"])
    assert "CS101" in loaded["courses"]


def test_f6_invalid_enrollment_references_marked(tmp_path):
    write_only(tmp_path, "enrollments.csv", ENROLLMENT_HEADER, [
        ["S999", "CS999", "ENROLLED"],
    ])
    loaded = load_all(tmp_path)
    types = [issue["type"] for issue in loaded["issues"]]
    assert "ENROLLMENT_STUDENT_NOT_FOUND" in types
    assert "ENROLLMENT_COURSE_NOT_FOUND" in types
    assert loaded["enrollments"][0]["invalid"] is True


def test_f6_course_unknown_classroom_marked_invalid(tmp_path):
    write_only(tmp_path, "courses.csv", COURSE_HEADER, [
        ["CS101", "A", "3", "1", "T", "40", "R999", "11"],
    ])
    loaded = load_all(tmp_path)
    assert loaded["courses"]["CS101"]["invalid"] is True
    assert loaded["issues"][0]["type"] == "COURSE_CLASSROOM_NOT_FOUND"


def test_f6_activity_unknown_classroom_and_student_marked(tmp_path):
    write_only(tmp_path, "activities.csv", ACTIVITY_HEADER, [
        ["ACT01", "A", "2026-06-29", "12", "10", "lecture", "", "R999", "S999"],
    ])
    loaded = load_all(tmp_path)
    types = [issue["type"] for issue in loaded["issues"]]
    assert "ACTIVITY_CLASSROOM_NOT_FOUND" in types
    assert "ACTIVITY_STUDENT_NOT_FOUND" in types
    assert loaded["activities"]["ACT01"]["invalid"] is True


def test_f6_validate_references_directly(tmp_path):
    classrooms, courses, students, activities, enrollments = sample_data()
    courses["CS101"]["classroom"] = "R999"
    issues = validate_references(classrooms, courses, students, activities, enrollments)
    assert issues[0]["type"] == "COURSE_CLASSROOM_NOT_FOUND"
    assert courses["CS101"]["invalid"] is True


# ==================== JSON 儲存 ====================

def test_f6_json_round_trip(tmp_path):
    from f6_storage import load_json, save_json
    save_json(str(tmp_path), *sample_data())
    loaded = load_json(str(tmp_path))
    assert loaded["errors"] == []
    assert loaded["courses"]["CS101"]["timeSlot"] == [(1, "1")]
    assert loaded["students"]["S001"]["courses"] == ["CS101"]
    assert loaded["students"]["S001"]["activities"] == ["ACT01"]
    assert loaded["activities"]["ACT01"]["participants"] == ["S001"]


def test_f6_json_missing_file(tmp_path):
    from f6_storage import load_json
    loaded = load_json(str(tmp_path))
    assert loaded["courses"] == {}
    assert any(w["reason"].startswith("File not found") for w in loaded["warnings"])


def test_f6_json_malformed_file(tmp_path):
    from f6_storage import load_json
    (tmp_path / "data.json").write_text("{not json", encoding="utf-8")
    loaded = load_json(str(tmp_path))
    assert loaded["courses"] == {}
    assert any("Cannot read JSON" in e["reason"] for e in loaded["errors"])


def test_f6_json_reference_validation(tmp_path):
    from f6_storage import load_json, save_json
    classrooms, courses, students, activities, enrollments = sample_data()
    courses["CS101"]["classroom"] = "R999"
    save_json(str(tmp_path), classrooms, courses, students, activities, enrollments)
    loaded = load_json(str(tmp_path))
    assert loaded["courses"]["CS101"]["invalid"] is True
    assert loaded["issues"][0]["type"] == "COURSE_CLASSROOM_NOT_FOUND"
