# Shared constants for Week & Periods across F1–F6
DAYS = [1, 2, 3, 4, 5, 6, 7]
PERIODS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c"]


def validate_credits(credit):
    if type(credit) is int and credit >= 1:
        return True, None
    return False, {"field": "credit", "input_value": credit, "reason": "Credits must be an integer >= 1"}


def validate_capacity(max_students):
    if type(max_students) is int and max_students >= 1:
        return True, None
    return False, {"field": "max_student_count", "input_value": max_students, "reason": "Max student capacity must be an integer >= 1"}


def validate_max_credits(max_credit):
    if type(max_credit) is int and max_credit >= 1:
        return True, None
    return False, {"field": "max_credit", "input_value": max_credit, "reason": "Max credit limit must be an integer >= 1"}


def validate_time_slots(time_slots):
    errors = []
    valid_days, valid_periods = set(DAYS), set(PERIODS)
    if not isinstance(time_slots, list) or not time_slots:
        return False, [{"field": "time_slots", "input_value": time_slots, "reason": "Time slots must be a non-empty list"}]

    norm = []
    has_format_error = False
    for s in time_slots:
        if isinstance(s, (tuple, list)) and len(s) == 2:
            norm.append((s[0], str(s[1]).lower()))
        else:
            has_format_error = True

    if has_format_error or len(norm) != len(set(norm)):
        errors.append({"field": "time_slots", "input_value": time_slots, "reason": "Invalid time slot format or duplicate periods inside course"})

    for slot in norm:
        day, period = slot[0], slot[1]
        if type(day) is not int or day not in valid_days:
            errors.append({"field": "time_slots.day", "input_value": day, "reason": f"Invalid day: {day}"})
        if period not in valid_periods:
            errors.append({"field": "time_slots.period", "input_value": period, "reason": f"Invalid period: {period}"})

    return (False, errors) if errors else (True, [])


def get_active_count(enrollments, course_id):
    return sum(1 for e in enrollments if e.get("course_id") == course_id and e.get("status") == "ENROLLED")


def get_remaining_seats(courses_db, enrollments, course_id):
    if course_id not in courses_db:
        return 0
    return max(0, courses_db[course_id]["maxStudentCount"] - get_active_count(enrollments, course_id))


def add_course(courses_db, classrooms_db, course_id, name, credit, is_req, teacher, max_students, room, slots):
    errors = []
    if course_id in courses_db:
        errors.append({"field": "course_id", "input_value": course_id, "reason": "Course ID already exists"})

    ok_cr, err_cr = validate_credits(credit)
    if not ok_cr:
        errors.append(err_cr)

    ok_cap, err_cap = validate_capacity(max_students)
    if not ok_cap:
        errors.append(err_cap)

    ok_ts, err_ts = validate_time_slots(slots)
    if not ok_ts:
        errors.extend(err_ts)

    if room not in classrooms_db:
        errors.append({"field": "classroom", "input_value": room, "reason": f"Classroom {room} does not exist"})
    elif ok_ts:
        norm_new = set((s[0], str(s[1]).lower()) for s in slots)
        for exist_id, exist_c in courses_db.items():
            if exist_c.get("classroom") == room:
                exist_norm = set((s[0], str(s[1]).lower()) for s in exist_c.get("timeSlot", []))
                conflict = norm_new & exist_norm
                if conflict:
                    errors.append({
                        "field": "classroom",
                        "input_value": room,
                        "reason": f"Classroom conflict with course {exist_id} at slots {list(conflict)}"
                    })
                    break

    if errors:
        return courses_db, False, errors

    courses_db[course_id] = {
        "id": course_id,
        "name": name,
        "credit": credit,
        "isRequired": bool(is_req),
        "teacherName": teacher,
        "maxStudentCount": max_students,
        "classroom": room,
        "timeSlot": [(s[0], str(s[1]).lower()) for s in slots]
    }
    return courses_db, True, "Course added successfully"


def update_course(courses_db, enrollments, classrooms_db, course_id, **kwargs):
    if course_id not in courses_db:
        return courses_db, False, [{"field": "course_id", "input_value": course_id, "reason": "Course not found"}]

    c = courses_db[course_id]
    errors = []

    if "credit" in kwargs:
        ok_cr, err_cr = validate_credits(kwargs["credit"])
        if not ok_cr:
            errors.append(err_cr)

    if "max_student_count" in kwargs:
        new_max = kwargs["max_student_count"]
        ok_cap, err_cap = validate_capacity(new_max)
        if not ok_cap:
            errors.append(err_cap)
        elif new_max < get_active_count(enrollments, course_id):
            errors.append({"field": "max_student_count", "input_value": new_max, "reason": "Capacity cannot be lower than current enrollment"})

    if "classroom" in kwargs and kwargs["classroom"] not in classrooms_db:
        errors.append({"field": "classroom", "input_value": kwargs["classroom"], "reason": "Classroom does not exist"})

    if "time_slots" in kwargs:
        ok_ts, err_ts = validate_time_slots(kwargs["time_slots"])
        if not ok_ts:
            errors.extend(err_ts)

    if errors:
        return courses_db, False, errors

    if "name" in kwargs:
        c["name"] = kwargs["name"]
    if "credit" in kwargs:
        c["credit"] = kwargs["credit"]
    if "max_student_count" in kwargs:
        c["maxStudentCount"] = kwargs["max_student_count"]
    if "classroom" in kwargs:
        c["classroom"] = kwargs["classroom"]
    if "time_slots" in kwargs:
        c["timeSlot"] = [(s[0], str(s[1]).lower()) for s in kwargs["time_slots"]]

    return courses_db, True, "Course updated successfully"


def delete_course(courses_db, enrollments, course_id):
    if course_id not in courses_db:
        return courses_db, False, [{"field": "course_id", "input_value": course_id, "reason": "Course not found"}]
    if get_active_count(enrollments, course_id) > 0:
        return courses_db, False, [{"field": "course_id", "input_value": course_id, "reason": "Cannot delete: course has active enrolled students (UC-04)"}]
    del courses_db[course_id]
    return courses_db, True, "Course deleted successfully"


def add_student(students_db, s_id, name, major_year, max_credit=25):
    errors = []
    if s_id in students_db:
        errors.append({"field": "student_id", "input_value": s_id, "reason": "Duplicate student ID"})

    ok_mc, err_mc = validate_max_credits(max_credit)
    if not ok_mc:
        errors.append(err_mc)

    if errors:
        return students_db, False, errors

    students_db[s_id] = {
        "id": s_id,
        "name": name,
        "majorYear": major_year,
        "maxCredit": max_credit,
        "courses": [],
        "activities": []
    }
    return students_db, True, "Student added successfully"


def update_student(students_db, s_id, **kwargs):
    if s_id not in students_db:
        return students_db, False, [{"field": "student_id", "input_value": s_id, "reason": "Student not found"}]
    if "max_credit" in kwargs:
        ok_mc, err_mc = validate_max_credits(kwargs["max_credit"])
        if not ok_mc:
            return students_db, False, [err_mc]
    students_db[s_id].update(kwargs)
    return students_db, True, "Student updated successfully"


def delete_student(students_db, enrollments, s_id):
    if s_id not in students_db:
        return students_db, enrollments, False, [{"field": "student_id", "input_value": s_id, "reason": "Student not found"}]
    del students_db[s_id]
    for e in enrollments:
        if e.get("student_id") == s_id and e.get("status") == "ENROLLED":
            e["status"] = "DROPPED"
    return students_db, enrollments, True, "Student deleted and active enrollments dropped"


def enroll_course(enrollments, courses_db, students_db, s_id, c_id):
    if s_id not in students_db or c_id not in courses_db:
        return enrollments, False, [{"field": "id", "input_value": (s_id, c_id), "reason": "Student or Course not found"}]
    if any(e["student_id"] == s_id and e["course_id"] == c_id and e["status"] == "ENROLLED" for e in enrollments):
        return enrollments, False, [{"field": "enrollment", "input_value": (s_id, c_id), "reason": "Already actively enrolled"}]
    if get_remaining_seats(courses_db, enrollments, c_id) <= 0:
        return enrollments, False, [{"field": "capacity", "input_value": c_id, "reason": "Course is at full capacity"}]

    enrollments.append({"student_id": s_id, "course_id": c_id, "status": "ENROLLED"})

    # Sync with students_db["courses"] for F2/F3 compatibility
    student_courses = students_db[s_id].setdefault("courses", [])
    if c_id not in student_courses:
        student_courses.append(c_id)

    return enrollments, True, "Enrolled successfully"


def drop_course(enrollments, s_id, c_id, students_db=None):
    for e in enrollments:
        if e["student_id"] == s_id and e["course_id"] == c_id and e["status"] == "ENROLLED":
            e["status"] = "DROPPED"
            # Sync removal if students_db is passed
            if students_db is not None and s_id in students_db:
                student_courses = students_db[s_id].get("courses", [])
                if c_id in student_courses:
                    student_courses.remove(c_id)
            return enrollments, True, "Dropped successfully"
    return enrollments, False, [{"field": "enrollment", "input_value": (s_id, c_id), "reason": "No active enrollment record found"}]


def generate_sample_data():
    """產生符合驗收標準之測試資料：至少 5 間教室、20 門課程、15 名學生"""
    classrooms_db = {
        "R101": {"id": "R101", "capacity": 60, "equipment": ["Projector", "PC"]},
        "R102": {"id": "R102", "capacity": 50, "equipment": ["Projector"]},
        "R201": {"id": "R201", "capacity": 40, "equipment": ["Whiteboard"]},
        "R202": {"id": "R202", "capacity": 45, "equipment": ["Projector", "Lab"]},
        "R301": {"id": "R301", "capacity": 80, "equipment": ["Projector", "Mic"]},
    }

    courses_db = {}
    sample_courses = [
        ("CS101", "計算機概論", 3, True, "王大明", 50, "R101", [(1, "1"), (1, "2"), (3, "1")]),
        ("CS102", "Python程式設計", 3, True, "陳建宏", 45, "R102", [(2, "3"), (2, "4"), (4, "3")]),
        ("CS103", "資料結構", 3, True, "林志玲", 40, "R201", [(1, "3"), (1, "4"), (3, "3")]),
        ("CS104", "演算法設計", 3, True, "張無忌", 40, "R202", [(2, "6"), (2, "7"), (4, "6")]),
        ("CS105", "作業系統", 3, True, "李逍遙", 50, "R301", [(3, "6"), (3, "7"), (5, "6")]),
        ("CS106", "資料庫系統", 3, True, "趙靈兒", 45, "R101", [(2, "1"), (2, "2"), (4, "1")]),
        ("CS107", "電腦網路", 3, False, "周芷若", 40, "R102", [(1, "6"), (1, "7"), (3, "6")]),
        ("CS108", "人工智慧導論", 3, False, "黃蓉", 50, "R301", [(4, "7"), (4, "8"), (5, "7")]),
        ("CS109", "機器學習", 3, False, "郭靖", 35, "R202", [(5, "1"), (5, "2"), (5, "3")]),
        ("CS110", "軟體工程", 3, True, "楊過", 45, "R101", [(3, "8"), (3, "9"), (5, "8")]),
        ("MA101", "微積分(一)", 4, True, "歐陽鋒", 60, "R301", [(1, "3"), (1, "4"), (3, "3"), (3, "4")]),
        ("MA102", "線性代數", 3, True, "洪七公", 50, "R102", [(2, "8"), (2, "9"), (4, "8")]),
        ("MA103", "離散數學", 3, True, "黃藥師", 45, "R201", [(4, "1"), (4, "2"), (5, "4")]),
        ("MA104", "機率與統計", 3, False, "段譽", 40, "R202", [(1, "8"), (1, "9"), (3, "8")]),
        ("GE201", "英文聽講", 2, True, "Smith", 35, "R201", [(2, "5"), (4, "5")]),
        ("GE202", "科技英文寫作", 2, False, "Johnson", 30, "R201", [(5, "a"), (5, "b")]),
        ("GE203", "經濟學原理", 2, False, "孫悟空", 60, "R301", [(2, "a"), (2, "b")]),
        ("GE204", "心理學導論", 2, False, "豬八戒", 55, "R101", [(4, "a"), (4, "b")]),
        ("GE205", "音樂欣賞", 2, False, "沙悟淨", 50, "R102", [(3, "a"), (3, "b")]),
        ("PE101", "體育(羽球)", 1, True, "唐三藏", 30, "R301", [(4, "5"), (4, "6")]),
    ]
    for c in sample_courses:
        add_course(courses_db, classrooms_db, *c)

    students_db = {}
    for i in range(1, 16):
        s_id = f"S{i:03d}"
        add_student(students_db, s_id, f"學生{i:02d}", f"資工{(i % 4) + 1}年級", max_credit=25)

    enrollments = []
    return classrooms_db, courses_db, students_db, enrollments
