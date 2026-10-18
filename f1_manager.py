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
    valid_days, valid_periods = {1, 2, 3, 4, 5, 6, 7}, set("123456789abc")
    if not isinstance(time_slots, list) or not time_slots:
        return False, [{"field": "time_slots", "input_value": time_slots, "reason": "Time slots must be a non-empty list"}]

    norm = []
    has_format_error = False
    for s in time_slots:
        if isinstance(s, tuple) and len(s) == 2:
            norm.append((s[0], str(s[1]).lower()))
        else:
            has_format_error = True

    if has_format_error or len(norm) != len(set(norm)):
        errors.append({"field": "time_slots", "input_value": time_slots, "reason": "Invalid time slot format or duplicate periods inside course"})

    for slot in norm:
        day, period = slot[0], slot[1]
        if day not in valid_days:
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

    # Classroom verification and collision detection (matches test_add_course_same_room_same_slot_rejected)
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

    # Apply changes only if all validations pass
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

    students_db[s_id] = {"id": s_id, "name": name, "majorYear": major_year, "maxCredit": max_credit}
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
    return enrollments, True, "Enrolled successfully"


def drop_course(enrollments, s_id, c_id):
    for e in enrollments:
        if e["student_id"] == s_id and e["course_id"] == c_id and e["status"] == "ENROLLED":
            e["status"] = "DROPPED"
            return enrollments, True, "Dropped successfully"
    return enrollments, False, [{"field": "enrollment", "input_value": (s_id, c_id), "reason": "No active enrollment record found"}]