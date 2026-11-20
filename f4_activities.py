# f4_activities.py
import copy
from datetime import date as _date

from config import ACTIVITY_OVERLAP, DAYS, DAY_NAMES, PERIODS, STUDENT_OVERLAP
from f2_checker import (
    get_slot_sort_key,
    group_continuous_slots,
    parse_time_slots,
)


def _as_list(value) -> list:
    if isinstance(value, str):
        return [item.strip() for item in value.split(";") if item.strip()]
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return []


def _parse_slots_field(raw, owner_id=None) -> tuple[list, list]:
    errors = []
    slots = parse_time_slots(raw, errors, owner_id)
    return slots, [
        {"field": "timeSlot", "input_value": raw, "reason": e["description"]}
        for e in errors
    ]


def _normalize_slots(slots: list) -> list:
    return sorted(set(slots), key=get_slot_sort_key)


def _weekday_from_date(date_text) -> int | None:
    if not isinstance(date_text, str):
        return None
    try:
        return _date.fromisoformat(date_text.strip()).weekday() + 1
    except ValueError:
        return None


def _classroom_capacity(room: dict) -> int:
    return room.get("roomCapacity", 0) or 0


def _classroom_devices(room: dict) -> set:
    return set(_as_list(room.get("devices", [])))


def _classroom_type(room: dict) -> str:
    return room.get("type", "")


def _classroom_available_slots(room: dict) -> set:
    slots = set(parse_time_slots(room.get("timeSlot", [])))
    if not slots:
        return {(day, period) for day in DAYS for period in PERIODS}
    return slots


def get_room_occupied_slots(room_name: str, courses_db: dict = None,
                            activities_db: dict = None,
                            exclude_course_id: str = None,
                            exclude_activity_id: str = None) -> set:
    occupied = set()
    for cid, course in (courses_db or {}).items():
        if cid == exclude_course_id or not isinstance(course, dict):
            continue
        if course.get("classroom") == room_name:
            occupied.update(parse_time_slots(course.get("timeSlot", [])))
    for aid, activity in (activities_db or {}).items():
        if aid == exclude_activity_id or not isinstance(activity, dict):
            continue
        if activity.get("classroom") == room_name:
            occupied.update(parse_time_slots(activity.get("timeSlot", [])))
    return occupied


def get_classroom_unmet_reasons(room_name: str, activity: dict,
                                classrooms_db: dict,
                                courses_db: dict = None,
                                activities_db: dict = None,
                                exclude_activity_id: str = None) -> list:
    room = classrooms_db.get(room_name)
    if not isinstance(room, dict):
        return ["教室不存在"]

    reasons = []
    capacity = _classroom_capacity(room)
    if capacity < activity.get("studentCount", 0):
        reasons.append("容量不足")

    required_devices = set(_as_list(activity.get("requireList", [])))
    if not required_devices.issubset(_classroom_devices(room)):
        reasons.append("缺少指定設備")

    room_type = _classroom_type(room)
    if room_type and room_type != activity.get("type", ""):
        reasons.append("活動類型不符合")

    required_slots = set(parse_time_slots(activity.get("timeSlot", [])))
    if not required_slots.issubset(_classroom_available_slots(room)):
        reasons.append("不在教室可用時段內")

    occupied = get_room_occupied_slots(
        room_name, courses_db, activities_db,
        exclude_activity_id=exclude_activity_id)
    if required_slots & occupied:
        reasons.append("時段已被占用")

    return reasons


def _validate_activity_input(activity: dict, activities_db: dict,
                             classrooms_db: dict, courses_db: dict) -> tuple[dict, list]:
    errors = []
    if not isinstance(activity, dict):
        return {}, [{"field": "activity", "input_value": activity, "reason": "活動資料必須是物件"}]

    activity_id = activity.get("id")
    if not isinstance(activity_id, str) or not activity_id.strip():
        errors.append({"field": "id", "input_value": activity_id, "reason": "活動代號不可為空"})
    elif activity_id in activities_db:
        errors.append({"field": "id", "input_value": activity_id, "reason": "活動代號重複"})

    name = activity.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append({"field": "name", "input_value": name, "reason": "活動名稱不可為空"})

    date_text = activity.get("date")
    weekday = _weekday_from_date(date_text)
    if weekday is None:
        errors.append({"field": "date", "input_value": date_text, "reason": "日期格式必須為 YYYY-MM-DD"})

    slots, slot_errors = _parse_slots_field(activity.get("timeSlot"), activity_id)
    errors.extend(slot_errors)
    slots = _normalize_slots(slots)
    if not slots and not slot_errors:
        errors.append({"field": "timeSlot", "input_value": activity.get("timeSlot"), "reason": "活動時段不可為空"})

    if weekday is not None:
        wrong_days = sorted({day for day, _ in slots if day != weekday})
        if wrong_days:
            errors.append({
                "field": "timeSlot",
                "input_value": activity.get("timeSlot"),
                "reason": "活動時段星期與日期推算結果不一致",
            })

    student_count = activity.get("studentCount")
    if type(student_count) is not int or student_count < 1:
        errors.append({"field": "studentCount", "input_value": student_count, "reason": "預計人數必須為 >= 1 的整數"})

    activity_type = activity.get("type")
    if not isinstance(activity_type, str) or not activity_type.strip():
        errors.append({"field": "type", "input_value": activity_type, "reason": "活動類型不可為空"})

    require_list = _as_list(activity.get("requireList", []))

    classroom = activity.get("classroom", "") or ""
    if classroom:
        if classroom not in classrooms_db:
            errors.append({"field": "classroom", "input_value": classroom, "reason": "教室不存在"})
        elif not errors:
            reasons = get_classroom_unmet_reasons(
                classroom, {
                    "studentCount": student_count,
                    "requireList": require_list,
                    "type": activity_type,
                    "timeSlot": slots,
                }, classrooms_db, courses_db, activities_db)
            if reasons:
                errors.append({
                    "field": "classroom",
                    "input_value": classroom,
                    "reason": "教室不合適: " + "、".join(reasons),
                })

    record = {
        "id": activity_id,
        "name": name,
        "date": date_text,
        "timeSlot": slots,
        "studentCount": student_count,
        "type": activity_type,
        "requireList": require_list,
        "classroom": classroom,
        "participants": [],
    }
    return record, errors


def add_activity(activities_db: dict, activity: dict,
                 classrooms_db: dict = None, courses_db: dict = None):
    record, errors = _validate_activity_input(
        activity, activities_db, classrooms_db or {}, courses_db or {})
    if errors:
        return activities_db, False, errors
    activities_db[record["id"]] = record
    return activities_db, True, "Activity added successfully"


def _map_modified_type(modified_type) -> str | None:
    mapping = {
        "name": "name", "名稱": "name",
        "date": "date", "日期": "date",
        "timeSlot": "timeSlot", "時段": "timeSlot",
        "studentCount": "studentCount", "預計人數": "studentCount",
        "type": "type", "活動類型": "type",
        "requireList": "requireList", "場地需求": "requireList",
        "classroom": "classroom", "教室": "classroom",
    }
    return mapping.get(modified_type)


def update_activity(activities_db: dict, activity_id: str,
                    modified_type, modified_content,
                    classrooms_db: dict = None, courses_db: dict = None):
    if activity_id not in activities_db:
        return activities_db, False, [{"field": "id", "input_value": activity_id, "reason": "活動不存在"}]

    activity = activities_db[activity_id]

    field = _map_modified_type(modified_type)
    if field is None:
        return activities_db, False, [{"field": "modifiedType", "input_value": modified_type, "reason": "不支援的修改項目"}]

    candidate = copy.deepcopy(activity)
    if field == "studentCount":
        try:
            candidate["studentCount"] = int(modified_content)
        except (TypeError, ValueError):
            candidate["studentCount"] = modified_content
    elif field == "requireList":
        candidate["requireList"] = _as_list(modified_content)
    elif field == "classroom":
        candidate["classroom"] = modified_content or ""
    else:
        candidate[field] = modified_content

    if type(candidate.get("studentCount")) is int and candidate["studentCount"] < len(activity.get("participants", [])):
        return activities_db, False, [{
            "field": "studentCount",
            "input_value": candidate.get("studentCount"),
            "reason": "預計人數不可小於目前已報名人數",
        }]

    refreshed, errors = _validate_activity_input(
        candidate, {k: v for k, v in activities_db.items() if k != activity_id},
        classrooms_db or {}, courses_db or {})
    if errors:
        return activities_db, False, errors
    refreshed["participants"] = activity.get("participants", [])

    activities_db[activity_id].clear()
    activities_db[activity_id].update(refreshed)
    return activities_db, True, "Activity updated successfully"


def cancel_activity(activities_db: dict, students_db: dict, activity_id: str):
    if activity_id not in activities_db:
        return activities_db, False, [{"field": "id", "input_value": activity_id, "reason": "活動不存在"}]

    del activities_db[activity_id]
    for student in (students_db or {}).values():
        activities = student.get("activities", [])
        if activity_id in activities:
            activities.remove(activity_id)
    return activities_db, True, "Activity cancelled successfully"


def get_activity(activities_db: dict, activity_id: str):
    return activities_db.get(activity_id)


def query_activities(activities_db: dict, activity_type: str = None,
                     date_text: str = None) -> list:
    result = []
    for activity in activities_db.values():
        if not isinstance(activity, dict):
            continue
        if activity_type is not None and activity.get("type") != activity_type:
            continue
        if date_text is not None and activity.get("date") != date_text:
            continue
        result.append(activity)
    return sorted(result, key=lambda a: str(a.get("id", "")))


def find_suitable_classrooms(room_capacity: int, time_slot_range: list,
                             activity_type: str, require_list: list,
                             classrooms_db: dict,
                             courses_db: dict = None,
                             activities_db: dict = None) -> dict:
    required_slots, slot_errors = _parse_slots_field(time_slot_range)
    required_devices = set(_as_list(require_list))

    details = {}
    suitable = []

    for room_name, room in sorted(classrooms_db.items()):
        if not isinstance(room, dict):
            continue
        reasons = []
        if _classroom_capacity(room) < room_capacity:
            reasons.append("容量不足")
        if not required_devices.issubset(_classroom_devices(room)):
            reasons.append("缺少指定設備")
        room_type = _classroom_type(room)
        if room_type and room_type != activity_type:
            reasons.append("活動類型不符合")
        if slot_errors or not set(required_slots).issubset(_classroom_available_slots(room)):
            reasons.append("不在教室可用時段內")
        if not slot_errors:
            occupied = get_room_occupied_slots(room_name, courses_db, activities_db)
            if set(required_slots) & occupied:
                reasons.append("時段已被占用")

        details[room_name] = reasons
        if not reasons:
            suitable.append(room_name)

    unmet = []
    for room_name, reasons in details.items():
        for reason in reasons:
            unmet.append(room_name + ": " + reason)
    if slot_errors:
        unmet.extend(err["reason"] for err in slot_errors)

    return {
        "isSucceed": len(suitable) > 0,
        "unmetReasons": unmet if unmet else None,
        "suitableClassrooms": suitable,
        "details": details,
    }


def _overlap_conflicts(conflict_type: str, target_id: str, overlap: list,
                       label: str) -> list:
    conflicts = []
    for group in group_continuous_slots(sorted(overlap, key=get_slot_sort_key)):
        first_slot = group[0]
        day_str = DAY_NAMES.get(first_slot[0], str(first_slot[0]))
        periods_str = "、".join(str(period) for _, period in group)
        conflicts.append({
            "conflictType": conflict_type,
            "timeSlot": first_slot,
            "conflictedTargets": [target_id],
            "description": label + " (星期" + day_str + "第 " + periods_str + " 節)",
        })
    return conflicts


def enroll_activity(activity_id: str, student_id: str, activities_db: dict,
                    students_db: dict, courses_db: dict = None,
                    enrollments: list = None,
                    classrooms_db: dict = None) -> dict:
    errors = []
    conflicts = []

    activity = activities_db.get(activity_id)
    student = students_db.get(student_id)

    if not isinstance(activity, dict):
        errors.append({"errorType": "ACTIVITY_NOT_FOUND", "target": activity_id, "description": "活動不存在"})
    if not isinstance(student, dict):
        errors.append({"errorType": "STUDENT_NOT_FOUND", "target": student_id, "description": "學生不存在"})

    if errors:
        return {"success": False, "activityId": activity_id, "studentId": student_id,
                "conflicts": [], "errors": errors, "remainingSeats": 0}

    participants = activity.get("participants")
    if not isinstance(participants, list):
        participants = []
        activity["participants"] = participants

    if student_id in participants:
        errors.append({"errorType": "ALREADY_ENROLLED", "target": activity_id, "description": "學生已報名此活動"})

    limit = activity.get("studentCount", 0)
    classroom = activity.get("classroom", "")
    room = (classrooms_db or {}).get(classroom) if classroom else None
    if isinstance(room, dict):
        limit = min(limit, _classroom_capacity(room))

    remaining = limit - len(participants)
    if remaining <= 0:
        errors.append({"errorType": "ACTIVITY_FULL", "target": activity_id, "description": "活動報名人數已達上限"})

    activity_slots = set(parse_time_slots(activity.get("timeSlot", [])))

    student_courses = []
    if isinstance(enrollments, list):
        student_courses = [
            e.get("course_id") for e in enrollments
            if isinstance(e, dict) and e.get("student_id") == student_id
            and e.get("status") == "ENROLLED"
        ]
    else:
        student_courses = list(student.get("courses", []))

    for cid in student_courses:
        course = (courses_db or {}).get(cid)
        if not isinstance(course, dict):
            continue
        overlap = activity_slots & set(parse_time_slots(course.get("timeSlot", [])))
        conflicts.extend(_overlap_conflicts(
            STUDENT_OVERLAP, cid, list(overlap),
            "已選課程：" + cid + " " + str(course.get("name", ""))))

    for aid in student.get("activities", []):
        if aid == activity_id:
            continue
        other = activities_db.get(aid)
        if not isinstance(other, dict):
            continue
        overlap = activity_slots & set(parse_time_slots(other.get("timeSlot", [])))
        conflicts.extend(_overlap_conflicts(
            ACTIVITY_OVERLAP, aid, list(overlap),
            "已報名活動：" + aid + " " + str(other.get("name", ""))))

    success = not errors and not conflicts
    if success:
        participants.append(student_id)
        student.setdefault("activities", [])
        if activity_id not in student["activities"]:
            student["activities"].append(activity_id)

    return {
        "success": success,
        "activityId": activity_id,
        "studentId": student_id,
        "conflicts": conflicts,
        "errors": errors,
        "remainingSeats": max(0, remaining),
    }
