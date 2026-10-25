# f2_checker.py
from f1_manager import get_remaining_seats
from f3_schedule import PERIODS, DAYS  

DAY_NAMES = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "日"}

def get_slot_sort_key(slot: tuple) -> tuple:
    day, period = slot[0], str(slot[1]).lower()
    p_idx = PERIODS.index(period) if period in PERIODS else 999
    return (day, p_idx)

def normalize_slots(slots: list) -> set:
    return {(s[0], str(s[1]).lower()) for s in slots if isinstance(s, (tuple, list)) and len(s) == 2}

def find_intersections(slots_a: list, slots_b: list) -> list:
    """計算兩組時段交集（衝堂），並依 F3 的星期與節次排序"""
    set_a = normalize_slots(slots_a)
    set_b = normalize_slots(slots_b)
    overlap = list(set_a & set_b)
    overlap.sort(key=get_slot_sort_key)
    return overlap

def check_course_enrollment(student_id: str,
                            target_course_id: str,
                            students_db: dict,
                            courses_db: dict,
                            activities_db: dict,
                            enrollments: list) -> dict:
    """F2 核心選課與衝堂檢查："""
    if student_id not in students_db or target_course_id not in courses_db:
        return {"success": False, "errors": ["學生或課程不存在"]}

    student = students_db[student_id]
    target_course = courses_db[target_course_id]
    target_slots = target_course.get("timeSlot", [])
    target_room = target_course.get("classroom", "")

    conflicts = []

    #1. 取得學生目前已加選的課程 
    enrolled_cids = [
        e.get("course_id") or e.get("studentId")
        for e in enrollments
        if (e.get("student_id") == student_id or e.get("studentId") == student_id)
        and e.get("status") == "ENROLLED"
    ]
    activity_ids = student.get("activities", [])

    # 重複選課檢查
    if target_course_id in enrolled_cids:
        conflicts.append({
            "slot": (0, "0"),
            "type": "DUPLICATE",
            "description": "重複加選相同課程"
        })

    # 2. 學生課程衝堂檢查
    for cid in enrolled_cids:
        if cid in courses_db and cid != target_course_id:
            c = courses_db[cid]
            overlap = find_intersections(target_slots, c.get("timeSlot", []))
            for slot in overlap:
                conflicts.append({
                    "slot": slot,
                    "type": "COURSE_CONFLICT",
                    "description": f"已選課程: {cid} {c.get('name', '')}"
                })

    # 3. 活動衝突檢查
    for act_id in activity_ids:
        if act_id in activities_db:
            act = activities_db[act_id]
            overlap = find_intersections(target_slots, act.get("timeSlot", []))
            for slot in overlap:
                conflicts.append({
                    "slot": slot,
                    "type": "ACTIVITY_CONFLICT",
                    "description": f"已參加活動: {act.get('name', '')}"
                })

    # 4. 教室衝堂檢查
    for cid, c in courses_db.items():
        if cid != target_course_id and c.get("classroom") == target_room:
            overlap = find_intersections(target_slots, c.get("timeSlot", []))
            for slot in overlap:
                conflicts.append({
                    "slot": slot,
                    "type": "CLASSROOM_CONFLICT",
                    "description": f"教室衝突: {target_room} 已被課程 {cid} 佔用"
                })

    # 5. 人數限制檢查 (呼叫 f1_manager 函式)
    rem_seats = get_remaining_seats(courses_db, enrollments, target_course_id)
    if rem_seats <= 0:
        conflicts.append({
            "slot": (0, "0"),
            "type": "CAPACITY_FULL",
            "description": "課程人數已額滿"
        })

    # 6. 學分限制檢查
    curr_credits = sum(courses_db[cid].get("credit", 0) for cid in enrolled_cids if cid in courses_db)
    target_credit = target_course.get("credit", 0)
    after_credits = curr_credits + target_credit
    max_credit = student.get("maxCredit", 25)

    if after_credits > max_credit:
        conflicts.append({
            "slot": (99, "99"),
            "type": "CREDIT_EXCEEDED",
            "description": f"加選後學分 ({after_credits}) 超過學分上限 ({max_credit})"
        })

    # 依 (星期, 節次) 統一排序所有衝突
    conflicts.sort(key=lambda x: get_slot_sort_key(x["slot"]))

    return {
        "success": len(conflicts) == 0,
        "student_id": student_id,
        "target_course": f"{target_course_id} {target_course.get('name', '')}",
        "conflicts": conflicts,
        "current_credits": curr_credits,
        "after_credits": after_credits,
        "max_credits": max_credit
    }
