def validate_credits(credit):

    if type(credit) is int and credit >= 1:
        return True, "Valid credit."
    return False, "Credits must be a positive integer (credits >= 1)."


def validate_capacity(max_students):
    
    if type(max_students) is int and max_students >= 1:
        return True, "Valid capacity."
    return False, "Max students capacity must be at least 1 (max_students >= 1)."


def validate_time_slots(time_slots):
   
    valid_days = {1, 2, 3, 4, 5, 6, 7}
    valid_periods = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c"}

    if not isinstance(time_slots, list) or len(time_slots) == 0:
        return False, "Time slots must be a non-empty list."

    for slot in time_slots:
        if not isinstance(slot, tuple) or len(slot) != 2:
            return False, f"Invalid slot format: {slot}. Expected tuple (day, period)."
        day, period = slot[0], str(slot[1]).lower()
        if day not in valid_days:
            return False, f"Invalid day: {day}. Day must be an integer between 1 and 7."
        if period not in valid_periods:
            return False, f"Invalid period: {period}. Period must be 1-9 or a, b, c."

    return True, "Valid time slots."



def add_course(courses_db, course_id, name, credit, is_required, teacher_name, 
               max_student_count, classroom, time_slots):
    
    if course_id in courses_db:
        return courses_db, False, f"Add failed: Course ID '{course_id}' already exists."

   
    ok, msg = validate_credits(credit)
    if not ok:
        return courses_db, False, f"Add failed: {msg}"

    ok, msg = validate_capacity(max_student_count)
    if not ok:
        return courses_db, False, f"Add failed: {msg}"

    ok, msg = validate_time_slots(time_slots)
    if not ok:
        return courses_db, False, f"Add failed: {msg}"

    for existing_id, c in courses_db.items():
        if c["classroom"] == classroom:
            existing_slots = set(c["timeSlot"])
            for slot in time_slots:
                if slot in existing_slots:
                    return courses_db, False, (
                        f"Add failed: Classroom '{classroom}' at Day {slot[0]} Period {slot[1]} "
                        f"is already occupied by course '{existing_id}'."
                    )

    
    courses_db[course_id] = {
        "id": course_id,
        "name": name,
        "credit": credit,
        "isRequired": bool(is_required),
        "teacherName": teacher_name,
        "maxStudentCount": max_student_count,
        "classroom": classroom,
        "timeSlot": [(s[0], str(s[1]).lower()) for s in time_slots],
        "enrolled_students": []  
    }
    return courses_db, True, f"Course '{course_id}' added successfully."


def delete_course(courses_db, course_id):
    
    if course_id not in courses_db:
        return courses_db, False, f"Delete failed: Course ID '{course_id}' does not exist."

    target = courses_db[course_id]
    enrolled_count = len(target["enrolled_students"])

    if enrolled_count > 0:
        return courses_db, False, (
            f"Delete blocked: Course '{course_id}' currently has {enrolled_count} "
            f"student(s) enrolled. Drop enrollment before deleting."
        )

    del courses_db[course_id]
    return courses_db, True, f"Course '{course_id}' successfully removed."


def search_courses(courses_db, course_id=None, teacher_name=None, day=None, 
                   is_required=None, has_vacancy=None):
   
    results = []
    for cid, c in courses_db.items():
        if course_id and c["id"] != course_id:
            continue
        if teacher_name and c["teacherName"] != teacher_name:
            continue
        if is_required is not None and c["isRequired"] != is_required:
            continue
        if day is not None:
            if not any(slot[0] == day for slot in c["timeSlot"]):
                continue
        if has_vacancy is True:
            vacancies = c["maxStudentCount"] - len(c["enrolled_students"])
            if vacancies <= 0:
                continue
        results.append(c)
    return results


def add_student(students_db, student_id, name, major_year, max_credit=25):

    if student_id in students_db:
        return students_db, False, f"Add failed: Student ID '{student_id}' already exists."
    if type(max_credit) is not int or max_credit <= 0:
        return students_db, False, "Add failed: Max credit must be a positive integer."

    students_db[student_id] = {
        "id": student_id,
        "name": name,
        "majorYear": major_year,
        "courses": [],
        "maxCredit": max_credit
    }
    return students_db, True, f"Student '{name}' ({student_id}) added successfully."


def init_benchmark_test_data():

    courses = {}
    students = {}

    # 5 Classrooms: A101, A102, TR301, TR302, MB101
    sample_courses = [
        ("CS101", "Intro to CS", 3, True, "Prof. Wang", 50, "A101", [(1, "1"), (1, "2")]),
        ("CS102", "Python Programming", 3, True, "Prof. Wang", 50, "A102", [(1, "3"), (1, "4")]),
        ("CS103", "Object-Oriented Programming", 3, True, "Prof. Lee", 45, "TR301", [(2, "1"), (2, "2")]),
        ("CS104", "Data Structures", 3, True, "Prof. Chang", 40, "TR302", [(2, "3"), (2, "4")]),
        ("CS105", "Algorithms", 3, True, "Prof. Chang", 40, "MB101", [(3, "1"), (3, "2")]),
        ("CS106", "Discrete Mathematics", 3, True, "Prof. Chao", 60, "A101", [(3, "3"), (3, "4")]),
        ("CS107", "Linear Algebra", 3, True, "Prof. Chao", 60, "A102", [(4, "1"), (4, "2")]),
        ("CS108", "Operating Systems", 3, True, "Prof. Lin", 40, "TR301", [(4, "3"), (4, "4")]),
        ("CS109", "Computer Organization", 3, True, "Prof. Lin", 40, "TR302", [(5, "1"), (5, "2")]),
        ("CS110", "Database Systems", 3, False, "Prof. Huang", 35, "MB101", [(5, "3"), (5, "4")]),
        ("CS111", "Software Engineering", 3, False, "Prof. Huang", 35, "A101", [(1, "5"), (1, "6")]),
        ("CS112", "Intro to AI", 3, False, "Prof. Chen", 50, "A102", [(2, "5"), (2, "6")]),
        ("CS113", "Machine Learning", 3, False, "Prof. Chen", 30, "TR301", [(3, "5"), (3, "6")]),
        ("CS114", "Computer Networks", 3, False, "Prof. Wu", 45, "TR302", [(4, "5"), (4, "6")]),
        ("CS115", "Information Security", 3, False, "Prof. Wu", 40, "MB101", [(5, "5"), (5, "6")]),
        ("CS116", "Cloud Computing", 2, False, "Prof. Kuo", 30, "A101", [(1, "7"), (1, "8")]),
        ("CS117", "Web Frontend Design", 2, False, "Prof. Kuo", 30, "A102", [(2, "7"), (2, "8")]),
        ("CS118", "Mobile App Development", 2, False, "Prof. Sun", 30, "TR301", [(3, "7"), (3, "8")]),
        ("CS119", "Big Data Analytics", 2, False, "Prof. Sun", 30, "TR302", [(4, "7"), (4, "8")]),
        ("CS120", "Senior Project", 1, True, "Prof. Wang", 20, "MB101", [(5, "7")]),
    ]

    for c in sample_courses:
        courses, ok, msg = add_course(courses, c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7])

    sample_students = [
        (f"S{i:03d}", f"Student_{i}", "Computer Science Y2", 25) for i in range(1, 16)
    ]
    for s in sample_students:
        students, ok, msg = add_student(students, s[0], s[1], s[2], s[3])

    return courses, students


if __name__ == "__main__":
    print("=== Running F1 Automated Acceptance Tests ===")

    
    courses, students = init_benchmark_test_data()
    assert len(courses) == 20, f"Expected 20 courses, found {len(courses)}"
    assert len(students) == 15, f"Expected 15 students, found {len(students)}"
    print("[PASS] Test 1: Successfully initialized 20 courses and 15 students benchmark dataset.")

  
    courses, ok, msg = add_course(courses, "CS101", "Duplicate Test", 3, True, "Prof. Wang", 50, "A101", [(1, "1")])
    assert ok is False, "Failed to reject duplicate course ID"
    print("[PASS] Test 2: Successfully rejected duplicate course ID CS101.")

    
    courses, ok, msg = add_course(courses, "CS999", "Invalid Period Test", 3, True, "Prof. Wang", 50, "A101", [(1, "z")])
    assert ok is False, "Failed to reject invalid period"
    print("[PASS] Test 3: Successfully rejected invalid period (1, 'z').")

  
    courses, ok, msg = add_course(courses, "CS998", "Zero Credit Test", 0, True, "Prof. Wang", 50, "A101", [(1, "1")])
    assert ok is False, "Failed to reject zero credits"
    print("[PASS] Test 4: Successfully rejected non-positive credits (credit = 0).")


    courses, ok, msg = add_course(courses, "CS997", "Zero Capacity Test", 3, True, "Prof. Wang", 0, "A101", [(1, "1")])
    assert ok is False, "Failed to reject capacity < 1"
    print("[PASS] Test 5: Successfully rejected capacity < 1 (max_students = 0).")

    
    courses["CS102"]["enrolled_students"].append("S001")  
    courses, ok, msg = delete_course(courses, "CS102")
    assert ok is False, "Failed to block course deletion when students are enrolled"
    print("[PASS] Test 6: Successfully triggered UC-04 protection, blocking deletion of CS102.")

   
    courses["CS102"]["enrolled_students"].clear() 
    courses, ok, msg = delete_course(courses, "CS102")
    assert ok is True and "CS102" not in courses, "Failed to delete course after student dropped"
    print("[PASS] Test 7: Successfully deleted course CS102 after student dropped.")

    print("\nAll F1 acceptance criteria and Use Case unit tests passed 100%!")