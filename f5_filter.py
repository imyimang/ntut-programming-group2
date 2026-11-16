# f5_filter.py
from f1_manager import get_remaining_seats
from f2_checker import DAY_NAMES, get_slot_sort_key, parse_time_slots


def _slots(raw) -> set:
    return set(parse_time_slots(raw))


def _format_slots(slots: set) -> str:
    return ", ".join(
        "星期" + DAY_NAMES.get(day, str(day)) + "第" + str(period) + "節"
        for day, period in sorted(slots, key=get_slot_sort_key)
    )


def filter_courses(courses_db: dict, enrollments: list,
                   wished_courses: list = None,
                   required_courses: list = None,
                   min_credit: int = 0,
                   max_credit: int = 0,
                   forbidden_times: list = None,
                   preferred_days: list = None) -> dict:
    wished = list(dict.fromkeys(wished_courses or []))
    required = list(dict.fromkeys(required_courses or []))
    forbidden = _slots(forbidden_times or [])
    preferred = set(preferred_days or [])

    unmet = []
    excluded = []
    excluded_ids = set()

    if type(min_credit) is not int or type(max_credit) is not int:
        unmet.append("學分上下限必須為整數")
    elif min_credit < 0 or max_credit < 0:
        unmet.append("學分上下限不可為負數")
    elif min_credit > max_credit:
        unmet.append("最低學分不可大於最高學分")

    all_ids = list(dict.fromkeys(list(courses_db.keys()) + wished + required))
    candidates = []

    for cid in sorted(all_ids):
        course = courses_db.get(cid)
        if not isinstance(course, dict):
            reasons = ["課程不存在"]
            excluded_ids.add(cid)
            excluded.append({"courseId": cid, "courseName": "", "reasons": reasons})
            if cid in required:
                unmet.append("必修課程 " + cid + " 不存在")
            continue

        reasons = []
        course_slots = _slots(course.get("timeSlot", []))
        forbidden_overlap = course_slots & forbidden
        if forbidden_overlap:
            reasons.append("課程時段落在不可上課時段：" + _format_slots(forbidden_overlap))
        if get_remaining_seats(courses_db, enrollments, cid) <= 0:
            reasons.append("課程已額滿")

        if reasons:
            if cid in wished or cid in required:
                excluded_ids.add(cid)
                excluded.append({
                    "courseId": cid,
                    "courseName": course.get("name", ""),
                    "reasons": reasons,
                })
        else:
            candidates.append(course)

    existing_required = [
        cid for cid in required
        if isinstance(courses_db.get(cid), dict)
    ]

    for cid in existing_required:
        course = courses_db[cid]
        course_slots = _slots(course.get("timeSlot", []))
        forbidden_overlap = course_slots & forbidden
        if forbidden_overlap:
            unmet.append(
                "必修課程 " + cid + " 落在不可上課時段：" +
                _format_slots(forbidden_overlap))
        if get_remaining_seats(courses_db, enrollments, cid) <= 0:
            unmet.append("必修課程 " + cid + " 已額滿")

    for index, cid_a in enumerate(existing_required):
        for cid_b in existing_required[index + 1:]:
            overlap = _slots(courses_db[cid_a].get("timeSlot", [])) & \
                _slots(courses_db[cid_b].get("timeSlot", []))
            if overlap:
                unmet.append(
                    "必修課程 " + cid_a + " 與 " + cid_b + " 衝堂：" +
                    _format_slots(overlap))

    required_credit = sum(
        courses_db[cid].get("credit", 0) for cid in existing_required)
    if type(max_credit) is int and required_credit > max_credit:
        unmet.append(
            "必修課程總學分 " + str(required_credit) +
            " 超過最高學分 " + str(max_credit))

    candidate_credit = sum(course.get("credit", 0) for course in candidates)
    if type(min_credit) is int and candidate_credit < min_credit:
        unmet.append(
            "所有候選課程總學分 " + str(candidate_credit) +
            " 仍低於最低學分 " + str(min_credit))

    def preference_key(course):
        slots = _slots(course.get("timeSlot", []))
        on_preferred = any(day in preferred for day, _ in slots)
        return (0 if on_preferred else 1, str(course.get("id", "")))

    candidates.sort(key=preference_key)

    return {
        "candidateCourses": candidates,
        "excludedCourses": excluded,
        "isFeasible": len(unmet) == 0,
        "unmetReasons": unmet,
    }
