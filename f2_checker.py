# f2_checker.py
from f1_manager import get_remaining_seats
from f3_schedule import PERIODS

DAYS = [1, 2, 3, 4, 5, 6, 7]
DAY_NAMES = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "日"}

STUDENT_OVERLAP = "STUDENT_OVERLAP"
CLASSROOM_OVERLAP = "CLASSROOM_OVERLAP"
ACTIVITY_OVERLAP = "ACTIVITY_OVERLAP"
CREDIT_LIMIT = "CREDIT_LIMIT"
COURSE_FULL = "COURSE_FULL"

RESULT_SUCCESS = "成功"
RESULT_FAIL = "失敗"


def get_slot_sort_key(slot: tuple) -> tuple:
    if not isinstance(slot, (tuple, list)) or len(slot) != 2:
        return (999, 999)
    day, period = slot[0], str(slot[1]).lower()
    day_key = day if type(day) is int and day in DAYS else 999
    p_idx = PERIODS.index(period) if period in PERIODS else 998
    return (day_key, p_idx)


def _parse_slot_token(token: str):
    parts = token.split(":")
    if len(parts) != 2:
        return None
    day_text, period_text = parts[0].strip(), parts[1].strip().lower()
    try:
        day = int(day_text)
    except (TypeError, ValueError):
        return None
    if day not in DAYS or period_text not in PERIODS:
        return None
    return (day, period_text)


def _report_invalid_slot(errors: list, owner_id, description: str) -> None:
    if errors is not None:
        errors.append({
            "errorType": "INVALID_TIME_SLOT",
            "target": owner_id,
            "description": description,
        })


def _parse_slot_string(raw: str, errors: list, owner_id) -> list:
    slots = []
    cleaned = "".join(str(raw).split())
    if not cleaned:
        return slots

    for segment in cleaned.split(";"):
        if not segment:
            continue

        if "-" in segment:
            left, right = segment.split("-", 1)
        else:
            left = right = segment

        start = _parse_slot_token(left)
        end = _parse_slot_token(right)
        if start is None or end is None:
            _report_invalid_slot(errors, owner_id, "Invalid time slot segment: " + segment)
            continue

        if start[0] != end[0]:
            _report_invalid_slot(errors, owner_id, "Start and end day must be the same: " + segment)
            continue

        start_idx = PERIODS.index(start[1])
        end_idx = PERIODS.index(end[1])
        if start_idx > end_idx:
            _report_invalid_slot(errors, owner_id, "Start period is after end period: " + segment)
            continue

        for period in PERIODS[start_idx:end_idx + 1]:
            slots.append((start[0], period))

    return slots


def _looks_like_slot_pair(raw) -> bool:
    return (
        isinstance(raw, (tuple, list))
        and len(raw) == 2
        and type(raw[0]) is int
        and not isinstance(raw[1], (tuple, list, dict))
    )


def _parse_slot_list(items, errors: list, owner_id) -> list:
    slots = []
    for item in items:
        if isinstance(item, str):
            slots.extend(_parse_slot_string(item, errors, owner_id))
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            day, period = item[0], str(item[1]).lower()
            if type(day) is int and day in DAYS and period in PERIODS:
                slots.append((day, period))
            else:
                _report_invalid_slot(errors, owner_id, "Invalid time slot: " + repr(item))
        else:
            _report_invalid_slot(errors, owner_id, "Invalid time slot: " + repr(item))
    return slots


def parse_time_slots(raw, errors: list = None, owner_id=None) -> list:
    """Parse tuple lists or the spec string format '1:5-1:6; 2:7-2:7'."""
    if raw is None:
        return []
    if isinstance(raw, str):
        return _parse_slot_string(raw, errors, owner_id)
    if isinstance(raw, (tuple, list)):
        if _looks_like_slot_pair(raw):
            return _parse_slot_list([raw], errors, owner_id)
        return _parse_slot_list(raw, errors, owner_id)
    _report_invalid_slot(errors, owner_id, "Unsupported time slot format: " + repr(raw))
    return []


def normalize_slots(slots, errors: list = None, owner_id=None) -> set:
    return set(parse_time_slots(slots, errors, owner_id))


def find_intersections(slots_a, slots_b) -> list:
    set_a = normalize_slots(slots_a)
    set_b = normalize_slots(slots_b)
    overlap = list(set_a & set_b)
    overlap.sort(key=get_slot_sort_key)
    return overlap


def group_continuous_slots(slots: list) -> list:
    if not slots:
        return []

    sorted_slots = sorted(slots, key=get_slot_sort_key)
    groups = []
    current_group = [sorted_slots[0]]

    for slot in sorted_slots[1:]:
        prev_day, prev_p = current_group[-1]
        curr_day, curr_p = slot

        prev_idx = PERIODS.index(prev_p) if prev_p in PERIODS else -1
        curr_idx = PERIODS.index(curr_p) if curr_p in PERIODS else -1

        if curr_day == prev_day and curr_idx == prev_idx + 1 and curr_idx != -1:
            current_group.append(slot)
        else:
            groups.append(current_group)
            current_group = [slot]

    groups.append(current_group)
    return groups


def _build_time_conflicts(conflict_type: str, target_ids: list, overlap: list,
                          label: str) -> list:
    conflicts = []
    for group in group_continuous_slots(overlap):
        first_slot = group[0]
        day_str = DAY_NAMES.get(first_slot[0], str(first_slot[0]))
        periods_str = "、".join(period for _, period in group)
        conflicts.append({
            "conflictType": conflict_type,
            "timeSlot": first_slot,
            "conflictedTargets": list(target_ids),
            "description": label + " (星期" + day_str + "第 " + periods_str + " 節)",
        })
    return conflicts


def _build_result(student_id, student_name, course_id, course_name, result,
                  conflicts, errors, current_credit, after_credit, max_credit) -> dict:
    return {
        "studentId": student_id,
        "studentName": student_name,
        "courseId": course_id,
        "courseName": course_name,
        "result": result,
        "conflicts": conflicts,
        "currentCredit": current_credit,
        "creditAfterJoinCourse": after_credit,
        "maxCredit": max_credit,
        "errors": errors,
    }


def check_course_enrollment(student_id: str,
                            target_course_id: str,
                            students_db: dict,
                            courses_db: dict,
                            activities_db: dict,
                            enrollments: list) -> dict:
    """F2 多層次衝堂與選課檢查。"""

    errors = []
    student = students_db.get(student_id) if isinstance(students_db, dict) else None
    target_course = courses_db.get(target_course_id) if isinstance(courses_db, dict) else None

    student_name = student.get("name", "") if isinstance(student, dict) else ""
    course_name = target_course.get("name", "") if isinstance(target_course, dict) else ""
    max_credit = student.get("maxCredit", 0) if isinstance(student, dict) else 0

    enrolled_cids = []
    if isinstance(enrollments, list):
        enrolled_cids = [
            e.get("course_id")
            for e in enrollments
            if isinstance(e, dict)
            and e.get("student_id") == student_id
            and e.get("status") == "ENROLLED"
        ]

    current_credit = 0
    if isinstance(courses_db, dict):
        for cid in enrolled_cids:
            course = courses_db.get(cid)
            if isinstance(course, dict):
                current_credit += course.get("credit", 0)

    if student is None:
        errors.append({
            "errorType": "STUDENT_NOT_FOUND",
            "target": student_id,
            "description": "學生不存在",
        })
    if target_course is None:
        errors.append({
            "errorType": "COURSE_NOT_FOUND",
            "target": target_course_id,
            "description": "課程不存在",
        })

    if errors:
        return _build_result(
            student_id, student_name, target_course_id, course_name, RESULT_FAIL,
            [], errors, current_credit, current_credit, max_credit)

    if target_course_id in enrolled_cids:
        errors.append({
            "errorType": "ALREADY_ENROLLED",
            "target": target_course_id,
            "description": "學生已經選過該課程",
        })
        return _build_result(
            student_id, student_name, target_course_id, course_name, RESULT_FAIL,
            [], errors, current_credit, current_credit, max_credit)

    slot_cache = {}

    def slots_for(kind: str, owner_id, raw) -> list:
        key = (kind, owner_id)
        if key not in slot_cache:
            slot_cache[key] = parse_time_slots(raw, errors, owner_id)
        return slot_cache[key]

    target_slot_count_before = len(errors)
    target_slots = slots_for("course", target_course_id, target_course.get("timeSlot", []))
    target_slot_invalid = len(errors) > target_slot_count_before
    target_slot_set = set(target_slots)
    target_room = target_course.get("classroom", "") or ""
    conflicts = []

    # 1. 學生衝堂
    for cid in enrolled_cids:
        if cid == target_course_id:
            continue
        course = courses_db.get(cid)
        if not isinstance(course, dict):
            errors.append({
                "errorType": "ENROLLED_COURSE_NOT_FOUND",
                "target": cid,
                "description": "已選課程不存在，已跳過該筆",
            })
            continue
        overlap = sorted(target_slot_set & set(slots_for("course", cid, course.get("timeSlot", []))),
                         key=get_slot_sort_key)
        conflicts.extend(_build_time_conflicts(
            STUDENT_OVERLAP, [cid], overlap,
            "已選課程：" + cid + " " + course.get("name", "")))

    # 2. 活動衝突
    activity_ids = student.get("activities", [])
    if not isinstance(activity_ids, (list, tuple)):
        activity_ids = []
    for act_id in activity_ids:
        activity = activities_db.get(act_id) if isinstance(activities_db, dict) else None
        if not isinstance(activity, dict):
            errors.append({
                "errorType": "ACTIVITY_NOT_FOUND",
                "target": act_id,
                "description": "已報名活動不存在，已跳過該筆",
            })
            continue
        overlap = sorted(target_slot_set & set(slots_for("activity", act_id, activity.get("timeSlot", []))),
                         key=get_slot_sort_key)
        conflicts.extend(_build_time_conflicts(
            ACTIVITY_OVERLAP, [act_id], overlap,
            "已參加活動：" + act_id + " " + activity.get("name", "")))

    # 3. 教室衝堂（課程與活動共用同一間教室）
    if target_room:
        for cid, course in courses_db.items():
            if cid == target_course_id or not isinstance(course, dict):
                continue
            if course.get("classroom") != target_room:
                continue
            overlap = sorted(target_slot_set & set(slots_for("course", cid, course.get("timeSlot", []))),
                             key=get_slot_sort_key)
            conflicts.extend(_build_time_conflicts(
                CLASSROOM_OVERLAP, [cid], overlap,
                "教室 " + str(target_room) + " 已被課程 " + cid + " " + course.get("name", "") + " 使用"))

        if isinstance(activities_db, dict):
            for act_id, activity in activities_db.items():
                if not isinstance(activity, dict):
                    continue
                if activity.get("classroom") != target_room:
                    continue
                overlap = sorted(target_slot_set & set(slots_for("activity", act_id, activity.get("timeSlot", []))),
                                 key=get_slot_sort_key)
                conflicts.extend(_build_time_conflicts(
                    CLASSROOM_OVERLAP, [act_id], overlap,
                    "教室 " + str(target_room) + " 已被活動 " + act_id + " " + activity.get("name", "") + " 使用"))

    # 4. 學分限制
    target_credit = target_course.get("credit", 0)
    credit_after = current_credit + target_credit
    if credit_after > max_credit:
        conflicts.append({
            "conflictType": CREDIT_LIMIT,
            "timeSlot": None,
            "conflictedTargets": [],
            "description": "加選後學分 (" + str(credit_after) + ") 超過學分上限 (" + str(max_credit) + ")",
        })

    # 5. 人數限制
    remaining = get_remaining_seats(courses_db, enrollments, target_course_id)
    if remaining <= 0:
        conflicts.append({
            "conflictType": COURSE_FULL,
            "timeSlot": None,
            "conflictedTargets": [],
            "description": "課程人數已額滿",
        })

    conflicts.sort(key=lambda c: get_slot_sort_key(c.get("timeSlot")))
    result = RESULT_FAIL if conflicts or target_slot_invalid else RESULT_SUCCESS

    return _build_result(
        student_id, student_name, target_course_id, course_name, result,
        conflicts, errors, current_credit, credit_after, max_credit)
