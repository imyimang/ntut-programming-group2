# config.py
"""專案共用全域常數設定（供 F1–F6 與測試模組共用）。"""

# 星期與節次常數（星期 1–7、節次 1–9 及 a, b, c）
DAYS = [1, 2, 3, 4, 5, 6, 7]
PERIODS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c"]
DAY_NAMES = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "日"}
DAY_NAMES_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# F2 衝堂與選課檢查常數
STUDENT_OVERLAP = "STUDENT_OVERLAP"
CLASSROOM_OVERLAP = "CLASSROOM_OVERLAP"
ACTIVITY_OVERLAP = "ACTIVITY_OVERLAP"
CREDIT_LIMIT = "CREDIT_LIMIT"
COURSE_FULL = "COURSE_FULL"
TIME_TYPES = {STUDENT_OVERLAP, CLASSROOM_OVERLAP, ACTIVITY_OVERLAP}

RESULT_SUCCESS = "成功"
RESULT_FAIL = "失敗"

# F3 課表顯示格式常數
CONFLICT_SEPARATOR = " / "
CELL_WIDTH = 10

# F6 CSV 檔案欄位標頭常數
COURSE_HEADER = [
    "id", "name", "credit", "isRequired", "teacherName",
    "maxStudentCount", "classroom", "timeSlot",
]
STUDENT_HEADER = ["id", "name", "majorYear", "maxCredit"]
CLASSROOM_HEADER = ["name", "roomCapacity", "timeSlot", "type", "devices"]
ACTIVITY_HEADER = [
    "id", "name", "date", "timeSlot", "studentCount", "type",
    "requireList", "classroom", "participants",
]
ENROLLMENT_HEADER = ["studentId", "courseId", "status"]

FILE_HEADERS = {
    "courses.csv": COURSE_HEADER,
    "students.csv": STUDENT_HEADER,
    "classrooms.csv": CLASSROOM_HEADER,
    "activities.csv": ACTIVITY_HEADER,
    "enrollments.csv": ENROLLMENT_HEADER,
}
