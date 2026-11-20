# f6_storage.py
import csv
import os
from datetime import date as _date

from config import (
    ACTIVITY_HEADER,
    CLASSROOM_HEADER,
    COURSE_HEADER,
    DAYS,
    ENROLLMENT_HEADER,
    FILE_HEADERS,
    PERIODS,
    STUDENT_HEADER,
)
from f2_checker import get_slot_sort_key, parse_time_slots


def _error(filename: str, line: int, reason: str) -> dict:
    return {"file": filename, "line": line, "reason": reason}


def slots_to_text(slots) -> str:
    ordered = sorted(set(parse_time_slots(slots)), key=get_slot_sort_key)
    return ",".join(str(day) + str(period).upper() for day, period in ordered)


def parse_slot_text(text) -> tuple[list, list]:
    if text is None:
        return [], []
    cleaned = "".join(str(text).split())
    if not cleaned:
        return [], []

    if ":" in cleaned or "-" in cleaned:
        errors = []
        slots = parse_time_slots(cleaned, errors)
        return slots, [e["description"] for e in errors]

    slots = []
    reasons = []
    for token in cleaned.replace(";", ",").split(","):
        if not token:
            continue
        if len(token) < 2:
            reasons.append("Invalid time slot: " + token)
            continue
        day_text, period_text = token[0], token[1:].lower()
        try:
            day = int(day_text)
        except ValueError:
            reasons.append("Invalid time slot: " + token)
            continue
        if day not in DAYS or period_text not in PERIODS:
            reasons.append("Invalid time slot: " + token)
            continue
        slots.append((day, period_text))

    unique = sorted(set(slots), key=get_slot_sort_key)
    return unique, reasons


def _to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _split_list(value) -> list:
    if value is None:
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def _to_bool_int(value):
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "y", "是"):
        return True
    if text in ("0", "false", "no", "n", "否", ""):
        return False
    return None


def _read_rows(data_dir: str, filename: str, errors: list, warnings: list) -> list:
    path = os.path.join(data_dir, filename)
    if not os.path.exists(path):
        warnings.append(_error(filename, 0, "File not found; treated as empty data"))
        return []
    try:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))
    except OSError as exc:
        errors.append(_error(filename, 0, "Cannot read file: " + str(exc)))
        return []

    if not rows:
        warnings.append(_error(filename, 0, "File is empty; treated as empty data"))
        return []

    header = [cell.strip() for cell in rows[0]]
    if header != FILE_HEADERS[filename]:
        errors.append(_error(filename, 1, "Invalid header: " + ",".join(header)))
    return [(line, row) for line, row in enumerate(rows[1:], start=2)]


def _load_courses(data_dir, errors, warnings):
    db = {}
    for line, row in _read_rows(data_dir, "courses.csv", errors, warnings):
        if len(row) < 8:
            errors.append(_error("courses.csv", line, "Expected 8 columns, got " + str(len(row))))
            continue
        cid = row[0].strip()
        if not cid:
            errors.append(_error("courses.csv", line, "Course id is empty"))
            continue
        if cid in db:
            errors.append(_error("courses.csv", line, "Duplicate course id: " + cid))
            continue
        credit = _to_int(row[2])
        if credit is None or credit < 1:
            errors.append(_error("courses.csv", line, "Invalid credit: " + row[2]))
            continue
        is_required = _to_bool_int(row[3])
        if is_required is None:
            errors.append(_error("courses.csv", line, "Invalid isRequired: " + row[3]))
            continue
        max_students = _to_int(row[5])
        if max_students is None or max_students < 1:
            errors.append(_error("courses.csv", line, "Invalid maxStudentCount: " + row[5]))
            continue
        slots, slot_errors = parse_slot_text(row[7])
        if slot_errors:
            errors.append(_error("courses.csv", line, "; ".join(slot_errors)))
            continue
        db[cid] = {
            "id": cid,
            "name": row[1].strip(),
            "credit": credit,
            "isRequired": is_required,
            "teacherName": row[4].strip(),
            "maxStudentCount": max_students,
            "classroom": row[6].strip(),
            "timeSlot": slots,
            "_line": line,
        }
    return db


def _load_students(data_dir, errors, warnings):
    db = {}
    for line, row in _read_rows(data_dir, "students.csv", errors, warnings):
        if len(row) < 4:
            errors.append(_error("students.csv", line, "Expected at least 4 columns, got " + str(len(row))))
            continue
        sid = row[0].strip()
        if not sid:
            errors.append(_error("students.csv", line, "Student id is empty"))
            continue
        if sid in db:
            errors.append(_error("students.csv", line, "Duplicate student id: " + sid))
            continue
        max_credit = _to_int(row[4] if len(row) >= 5 else row[3])
        if max_credit is None or max_credit < 1:
            errors.append(_error("students.csv", line, "Invalid maxCredit"))
            continue
        db[sid] = {
            "id": sid,
            "name": row[1].strip(),
            "majorYear": row[2].strip(),
            "maxCredit": max_credit,
            "courses": [],
            "activities": [],
            "_line": line,
        }
    return db


def _load_classrooms(data_dir, errors, warnings):
    db = {}
    for line, row in _read_rows(data_dir, "classrooms.csv", errors, warnings):
        if len(row) < 5:
            errors.append(_error("classrooms.csv", line, "Expected 5 columns, got " + str(len(row))))
            continue
        name = row[0].strip()
        if not name:
            errors.append(_error("classrooms.csv", line, "Classroom name is empty"))
            continue
        if name in db:
            errors.append(_error("classrooms.csv", line, "Duplicate classroom name: " + name))
            continue
        capacity = _to_int(row[1])
        if capacity is None or capacity < 1:
            errors.append(_error("classrooms.csv", line, "Invalid roomCapacity: " + row[1]))
            continue
        slots, slot_errors = parse_slot_text(row[2])
        if slot_errors:
            errors.append(_error("classrooms.csv", line, "; ".join(slot_errors)))
            continue
        db[name] = {
            "name": name,
            "roomCapacity": capacity,
            "timeSlot": slots,
            "type": row[3].strip(),
            "devices": _split_list(row[4]),
            "_line": line,
        }
    return db


def _load_activities(data_dir, errors, warnings):
    db = {}
    for line, row in _read_rows(data_dir, "activities.csv", errors, warnings):
        if len(row) < 7:
            errors.append(_error("activities.csv", line, "Expected at least 7 columns, got " + str(len(row))))
            continue
        aid = row[0].strip()
        if not aid:
            errors.append(_error("activities.csv", line, "Activity id is empty"))
            continue
        if aid in db:
            errors.append(_error("activities.csv", line, "Duplicate activity id: " + aid))
            continue
        try:
            activity_date = _date.fromisoformat(row[2].strip())
        except ValueError:
            errors.append(_error("activities.csv", line, "Invalid date: " + row[2]))
            continue
        slots, slot_errors = parse_slot_text(row[3])
        if slot_errors or not slots:
            reason = "; ".join(slot_errors) if slot_errors else "Activity timeSlot is empty"
            errors.append(_error("activities.csv", line, reason))
            continue
        weekday = activity_date.weekday() + 1
        if any(day != weekday for day, _ in slots):
            errors.append(_error("activities.csv", line, "Activity weekday does not match date"))
            continue
        student_count = _to_int(row[4])
        if student_count is None or student_count < 1:
            errors.append(_error("activities.csv", line, "Invalid studentCount: " + row[4]))
            continue

        classroom = row[7].strip() if len(row) >= 8 else ""
        participants = _split_list(row[8]) if len(row) >= 9 else []
        is_cancelled = _to_bool_int(row[9] if len(row) >= 10 else "0")
        if is_cancelled is None:
            errors.append(_error("activities.csv", line, "Invalid isCancelled: " + row[9]))
            continue

        db[aid] = {
            "id": aid,
            "name": row[1].strip(),
            "date": row[2].strip(),
            "timeSlot": slots,
            "studentCount": student_count,
            "type": row[5].strip(),
            "requireList": _split_list(row[6]),
            "classroom": classroom,
            "participants": participants,
            "isCancelled": is_cancelled,
            "_line": line,
        }
    return db


def _load_enrollments(data_dir, errors, warnings):
    rows = []
    for line, row in _read_rows(data_dir, "enrollments.csv", errors, warnings):
        if len(row) < 3:
            errors.append(_error("enrollments.csv", line, "Expected 3 columns, got " + str(len(row))))
            continue
        student_id = row[0].strip()
        course_id = row[1].strip()
        status = row[2].strip().upper()
        if not student_id or not course_id:
            errors.append(_error("enrollments.csv", line, "studentId and courseId are required"))
            continue
        if status not in ("ENROLLED", "DROPPED"):
            errors.append(_error("enrollments.csv", line, "Invalid status: " + row[2]))
            continue
        rows.append({
            "student_id": student_id,
            "course_id": course_id,
            "status": status,
            "_line": line,
        })
    return rows


def _mark_invalid(record: dict, reason: str) -> None:
    record["invalid"] = True
    record.setdefault("invalidReasons", []).append(reason)


def validate_references(classrooms_db: dict, courses_db: dict,
                        students_db: dict, activities_db: dict,
                        enrollments: list) -> list:
    issues = []

    for cid, course in courses_db.items():
        room = course.get("classroom")
        if room and room not in classrooms_db:
            reason = "Course " + cid + " references unknown classroom " + str(room)
            issues.append({"type": "COURSE_CLASSROOM_NOT_FOUND", "target": cid, "reason": reason})
            _mark_invalid(course, reason)

    for aid, activity in activities_db.items():
        room = activity.get("classroom")
        if room and room not in classrooms_db:
            reason = "Activity " + aid + " references unknown classroom " + str(room)
            issues.append({"type": "ACTIVITY_CLASSROOM_NOT_FOUND", "target": aid, "reason": reason})
            _mark_invalid(activity, reason)
        for sid in activity.get("participants", []):
            if sid not in students_db:
                reason = "Activity " + aid + " references unknown student " + sid
                issues.append({"type": "ACTIVITY_STUDENT_NOT_FOUND", "target": aid, "reason": reason})
                _mark_invalid(activity, reason)

    for enrollment in enrollments:
        sid = enrollment.get("student_id")
        cid = enrollment.get("course_id")
        if sid not in students_db:
            reason = "Enrollment references unknown student " + str(sid)
            issues.append({"type": "ENROLLMENT_STUDENT_NOT_FOUND", "target": sid, "reason": reason})
            _mark_invalid(enrollment, reason)
        if cid not in courses_db:
            reason = "Enrollment references unknown course " + str(cid)
            issues.append({"type": "ENROLLMENT_COURSE_NOT_FOUND", "target": cid, "reason": reason})
            _mark_invalid(enrollment, reason)

    return issues


def _rebuild_student_links(students_db, activities_db, enrollments) -> None:
    for student in students_db.values():
        student["courses"] = []
        student["activities"] = []

    for enrollment in enrollments:
        if enrollment.get("invalid") or enrollment.get("status") != "ENROLLED":
            continue
        student = students_db.get(enrollment.get("student_id"))
        if student is not None and enrollment["course_id"] not in student["courses"]:
            student["courses"].append(enrollment["course_id"])

    for activity in activities_db.values():
        if activity.get("isCancelled"):
            continue
        for sid in activity.get("participants", []):
            student = students_db.get(sid)
            if student is not None and activity["id"] not in student["activities"]:
                student["activities"].append(activity["id"])


def load_all(data_dir: str) -> dict:
    errors = []
    warnings = []

    classrooms = _load_classrooms(data_dir, errors, warnings)
    courses = _load_courses(data_dir, errors, warnings)
    students = _load_students(data_dir, errors, warnings)
    activities = _load_activities(data_dir, errors, warnings)
    enrollments = _load_enrollments(data_dir, errors, warnings)

    issues = validate_references(classrooms, courses, students, activities, enrollments)
    _rebuild_student_links(students, activities, enrollments)

    return {
        "classrooms": classrooms,
        "courses": courses,
        "students": students,
        "activities": activities,
        "enrollments": enrollments,
        "errors": errors,
        "warnings": warnings,
        "issues": issues,
    }


load_data = load_all


def _write_rows(path: str, header: list, rows: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def save_all(data_dir: str, classrooms_db: dict, courses_db: dict,
             students_db: dict, activities_db: dict, enrollments: list) -> dict:
    os.makedirs(data_dir, exist_ok=True)

    course_rows = []
    for cid in sorted(courses_db):
        course = courses_db[cid]
        course_rows.append([
            course.get("id", cid),
            course.get("name", ""),
            course.get("credit", 0),
            1 if course.get("isRequired") else 0,
            course.get("teacherName", ""),
            course.get("maxStudentCount", 0),
            course.get("classroom", ""),
            slots_to_text(course.get("timeSlot", [])),
        ])

    student_rows = []
    for sid in sorted(students_db):
        student = students_db[sid]
        student_rows.append([
            student.get("id", sid),
            student.get("name", ""),
            student.get("majorYear", ""),
            student.get("maxCredit", 0),
        ])

    classroom_rows = []
    for name in sorted(classrooms_db):
        room = classrooms_db[name]
        classroom_rows.append([
            room.get("name", name),
            room.get("roomCapacity", room.get("capacity", 0)),
            slots_to_text(room.get("timeSlot", [])),
            room.get("type", ""),
            ";".join(room.get("devices", room.get("equipment", []))),
        ])

    activity_rows = []
    for aid in sorted(activities_db):
        activity = activities_db[aid]
        activity_rows.append([
            activity.get("id", aid),
            activity.get("name", ""),
            activity.get("date", ""),
            slots_to_text(activity.get("timeSlot", [])),
            activity.get("studentCount", 0),
            activity.get("type", ""),
            ";".join(activity.get("requireList", [])),
            activity.get("classroom", ""),
            ";".join(activity.get("participants", [])),
            1 if activity.get("isCancelled") else 0,
        ])

    enrollment_rows = []
    for enrollment in enrollments:
        enrollment_rows.append([
            enrollment.get("student_id", ""),
            enrollment.get("course_id", ""),
            enrollment.get("status", ""),
        ])

    _write_rows(os.path.join(data_dir, "courses.csv"), COURSE_HEADER, course_rows)
    _write_rows(os.path.join(data_dir, "students.csv"), STUDENT_HEADER, student_rows)
    _write_rows(os.path.join(data_dir, "classrooms.csv"), CLASSROOM_HEADER, classroom_rows)
    _write_rows(os.path.join(data_dir, "activities.csv"), ACTIVITY_HEADER, activity_rows)
    _write_rows(os.path.join(data_dir, "enrollments.csv"), ENROLLMENT_HEADER, enrollment_rows)

    return {
        "courses": len(course_rows),
        "students": len(student_rows),
        "classrooms": len(classroom_rows),
        "activities": len(activity_rows),
        "enrollments": len(enrollment_rows),
    }


def save_data(data_dir: str, data: dict) -> dict:
    return save_all(
        data_dir,
        data.get("classrooms", {}),
        data.get("courses", {}),
        data.get("students", {}),
        data.get("activities", {}),
        data.get("enrollments", []),
    )


def _json_ready(record: dict) -> dict:
    return {
        key: value for key, value in record.items()
        if key not in ("_line", "invalid", "invalidReasons")
    }


def save_json(data_dir: str, classrooms_db: dict, courses_db: dict,
              students_db: dict, activities_db: dict, enrollments: list,
              filename: str = "data.json") -> str:
    import json

    os.makedirs(data_dir, exist_ok=True)
    payload = {
        "classrooms": {k: _json_ready(v) for k, v in classrooms_db.items()},
        "courses": {k: _json_ready(v) for k, v in courses_db.items()},
        "students": {k: _json_ready(v) for k, v in students_db.items()},
        "activities": {k: _json_ready(v) for k, v in activities_db.items()},
        "enrollments": [
            {key: value for key, value in row.items()
             if key not in ("_line", "invalid", "invalidReasons")}
            for row in enrollments
        ],
    }
    path = os.path.join(data_dir, filename)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return path


def _normalize_json_slots(db: dict) -> None:
    for record in db.values():
        if isinstance(record, dict) and isinstance(record.get("timeSlot"), list):
            record["timeSlot"] = [
                (int(slot[0]), str(slot[1]).lower())
                for slot in record["timeSlot"]
                if isinstance(slot, (list, tuple)) and len(slot) == 2
            ]


def load_json(data_dir: str, filename: str = "data.json") -> dict:
    import json

    errors = []
    warnings = []
    payload = {}
    path = os.path.join(data_dir, filename)

    if not os.path.exists(path):
        warnings.append(_error(filename, 0, "File not found; treated as empty data"))
    else:
        try:
            with open(path, encoding="utf-8") as handle:
                payload = json.load(handle)
            if not isinstance(payload, dict):
                raise ValueError("JSON root must be an object")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(_error(filename, 0, "Cannot read JSON: " + str(exc)))
            payload = {}

    classrooms = payload.get("classrooms", {}) if isinstance(payload, dict) else {}
    courses = payload.get("courses", {}) if isinstance(payload, dict) else {}
    students = payload.get("students", {}) if isinstance(payload, dict) else {}
    activities = payload.get("activities", {}) if isinstance(payload, dict) else {}
    enrollments = payload.get("enrollments", []) if isinstance(payload, dict) else []

    for name, value in (("classrooms", classrooms), ("courses", courses),
                        ("students", students), ("activities", activities)):
        if not isinstance(value, dict):
            errors.append(_error(filename, 0, name + " must be an object"))
    if not isinstance(enrollments, list):
        errors.append(_error(filename, 0, "enrollments must be a list"))
        enrollments = []

    for db in (classrooms, courses, activities):
        if isinstance(db, dict):
            _normalize_json_slots(db)

    if isinstance(students, dict):
        for student in students.values():
            if isinstance(student, dict):
                student.setdefault("courses", [])
                student.setdefault("activities", [])

    issues = validate_references(classrooms, courses, students, activities, enrollments)
    _rebuild_student_links(students, activities, enrollments)

    return {
        "classrooms": classrooms,
        "courses": courses,
        "students": students,
        "activities": activities,
        "enrollments": enrollments,
        "errors": errors,
        "warnings": warnings,
        "issues": issues,
    }
