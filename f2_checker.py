# f2_checker.py
from f1_manager import get_remaining_seats
from f3_schedule import PERIODS

DAY_NAMES = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "日"}


def get_slot_sort_key(slot: tuple) -> tuple:
   
    if slot is None:
        return (999, 999)
    day, period = slot[0], str(slot[1]).lower()
    p_idx = PERIODS.index(period) if period in PERIODS else 998
    return (day, p_idx)


def normalize_slots(slots: list) -> set:
   
    return {(s[0], str(s[1]).lower()) for s in slots if isinstance(s, (tuple, list)) and len(s) == 2}


def find_intersections(slots_a: list, slots_b: list) -> list:
   
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


def check_course_enrollment(student_id: str,
                            target_course_id: str,
                            students_db: dict,
                            courses_db: dict,
                            activities_db: dict,
                            enrollments: list) -> dict:
    """F2 核心選課與衝堂檢查"""

    # 4. 學生或課程不存在時，補齊完整欄位
    if student_id not in students_db or target_course_id not in courses_db:
        return {
            "success": False,
            "student_id": student_id,
            "target_course": target_course_id,
            "conflicts": [{
                "slot": None,
                "type": "NOT_FOUND",
                "description": "學生或課程不存在"
            }],
            "current_credits": 0,
            "after_credits": 0,
            "max_credits": 0
        }

    student = students_db[student_id]
    target_course = courses_db[target_course_id]
    target_slots = target_course.get("timeSlot", [])
    target_room = target_course.get("classroom", "")

   
    enrolled_cids = [
        e.get("course_id")
        for e in enrollments
        if e.get("student_id") == student_id and e.get("status") == "ENROLLED"
    ]
    activity_ids = student.get("activities", [])
    curr_credits = sum(courses_db[cid].get("credit", 0) for cid in enrolled_cids if cid in courses_db)

    # 3. 重複加選檢查
    if target_course_id in enrolled_cids:
        return {
            "success": False,
            "student_id": student_id,
            "target_course": f"{target_course_id} {target_course.get('name', '')}",
            "conflicts": [{
                "slot": None,
                "type": "DUPLICATE",
                "description": "重複加選相同課程"
            }],
            "current_credits": curr_credits,
            "after_credits": curr_credits,
            "max_credits": student.get("maxCredit", 25)
        }

    conflicts = []

    # 2. 學生課程衝堂檢查
    for cid in enrolled_cids:
        if cid in courses_db and cid != target_course_id:
            c = courses_db[cid]
            overlap = find_intersections(target_slots, c.get("timeSlot", []))
            for group in group_continuous_slots(overlap):
                first_slot = group[0]
                day_str = DAY_NAMES.get(first_slot[0], str(first_slot[0]))
                periods_str = "、".join([p for _, p in group])
                conflicts.append({
                    "slot": first_slot,
                    "type": "COURSE_CONFLICT",
                    "description": f"已選課程衝堂: {cid} {c.get('name', '')} (星期{day_str}第 {periods_str} 節)"
                })

    # 3. 活動衝突檢查
    for act_id in activity_ids:
        if act_id in activities_db:
            act = activities_db[act_id]
            overlap = find_intersections(target_slots, act.get("timeSlot", []))
            for group in group_continuous_slots(overlap):
                first_slot = group[0]
                day_str = DAY_NAMES.get(first_slot[0], str(first_slot[0]))
                periods_str = "、".join([p for _, p in group])
                conflicts.append({
                    "slot": first_slot,
                    "type": "ACTIVITY_CONFLICT",
                    "description": f"已參加活動衝突: {act.get('name', '')} (星期{day_str}第 {periods_str} 節)"
                })

    # 4. 教室衝堂檢查
    if target_room:
        for cid, c in courses_db.items():
            if cid != target_course_id and c.get("classroom") == target_room:
                overlap = find_intersections(target_slots, c.get("timeSlot", []))
                for group in group_continuous_slots(overlap):
                    first_slot = group[0]
                    day_str = DAY_NAMES.get(first_slot[0], str(first_slot[0]))
                    periods_str = "、".join([p for _, p in group])
                    conflicts.append({
                        "slot": first_slot,
                        "type": "CLASSROOM_CONFLICT",
                        "description": f"教室衝突: {target_room} 已被課程 {cid} 佔用 (星期{day_str}第 {periods_str} 節)"
                    })

    # 5. 人數限制檢查
    rem_seats = get_remaining_seats(courses_db, enrollments, target_course_id)
    if rem_seats <= 0:
        conflicts.append({
            "slot": None,
            "type": "CAPACITY_FULL",
            "description": "課程人數已額滿"
        })

    # 6. 學分限制檢查 
    target_credit = target_course.get("credit", 0)
    after_credits = curr_credits + target_credit
    max_credit = student.get("maxCredit", 25)

    if after_credits > max_credit:
        conflicts.append({
            "slot": None,
            "type": "CREDIT_EXCEEDED",
            "description": f"加選後學分 ({after_credits}) 超過學分上限 ({max_credit})"
        })

    
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
