DAYS = [1, 2, 3, 4, 5, 6, 7]
PERIODS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c"]
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

CONFLICT_SEPARATOR = " / "
CELL_WIDTH = 10


def day_to_row(day: int) -> int:
 
    if type(day) is not int or day < 1 or day > 7:
        raise ValueError("Invalid day: " + repr(day) + " (use 1 to 7)")
    return day - 1


def period_to_column(period: str) -> int:
    period_text = str(period).lower()
    if period_text not in PERIODS:
        raise ValueError(
            "Invalid period: " + repr(period) + " (use '1'-'9', 'a', 'b', 'c')"
        )
    return PERIODS.index(period_text)


def check_matrix(matrix: list) -> None:
    if type(matrix) is not list or len(matrix) != 7:
        raise ValueError("Matrix must be a 7 x 12 list of lists")
    for row in matrix:
        if type(row) is not list or len(row) != 12:
            raise ValueError("Matrix must be a 7 x 12 list of lists")


def check_min_length(min_length: int) -> None:
    if type(min_length) is not int or min_length < 1:
        raise ValueError(
            "min_length must be a whole number >= 1, got " + repr(min_length)
        )


def place_item(matrix: list, item_id: str, item: dict,
               time_slots: list) -> None:
    label = item_id + " (" + str(item.get("name", "")) + ")"

    if type(time_slots) is not list:
        raise ValueError(item_id + ": timeSlot must be a list")

    already_done = []
    for slot in time_slots:
        if type(slot) not in (tuple, list) or len(slot) != 2:
            raise ValueError(item_id + ": invalid time slot " + repr(slot))
        row = day_to_row(slot[0])
        column = period_to_column(slot[1])

        if (row, column) in already_done:
            continue  
        already_done.append((row, column))

        if matrix[row][column] is None:
            matrix[row][column] = label
        else:
            matrix[row][column] = (matrix[row][column]
                                   + CONFLICT_SEPARATOR + label)



def build_schedule_matrix(student_id: str, students_db: dict,
                          courses_db: dict,
                          activities_db: dict) -> list[list[str | None]]:
    if student_id not in students_db:
        raise ValueError("Student not found: " + repr(student_id))
    student = students_db[student_id]

    matrix = []
    for _ in range(7):
        matrix.append([None] * 12)

    for course_id in student.get("courses", []):
        if course_id not in courses_db:
            raise ValueError("Course not found: " + repr(course_id))
        course = courses_db[course_id]
        place_item(matrix, course_id, course, course.get("timeSlot", []))

    for activity_id in student.get("activities", []):
        if activity_id not in activities_db:
            raise ValueError("Activity not found: " + repr(activity_id))
        activity = activities_db[activity_id]
        place_item(matrix, activity_id, activity,
                   activity.get("timeSlot", []))

    return matrix


def query_schedule_slot(matrix: list[list[str | None]], day: int,
                        period: str) -> str | None:
    check_matrix(matrix)
    row = day_to_row(day)
    column = period_to_column(period)
    return matrix[row][column]


def find_course_slots(matrix: list[list[str | None]],
                      course_id: str) -> list[tuple[int, str]]:
    check_matrix(matrix)
    if type(course_id) is not str or course_id == "":
        raise ValueError("Invalid course ID: " + repr(course_id))

    start_text = course_id + " ("  # a cell for this course starts with this
    result = []
    for row in range(7):
        for column in range(12):
            cell = matrix[row][column]
            if cell is None:
                continue
            # A cell may hold several items joined by " / ".
            for part in cell.split(CONFLICT_SEPARATOR):
                if part.startswith(start_text):
                    result.append((DAYS[row], PERIODS[column]))
                    break
    return result


def find_idle_runs(matrix: list[list[str | None]], day: int,
                   start_period: str,
                   end_period: str) -> list[list[tuple[int, str]]]:
    check_matrix(matrix)
    row = day_to_row(day)
    start = period_to_column(start_period)
    end = period_to_column(end_period)
    if start > end:
        raise ValueError("start_period must not be after end_period")

    runs = []      # all finished groups
    current = []   # the group we are building right now
    for column in range(start, end + 1):
        if matrix[row][column] is None:
            current.append((day, PERIODS[column]))
        else:
            if len(current) > 0:
                runs.append(current)
            current = []
    if len(current) > 0:
        runs.append(current)
    return runs


def find_continuous_idle_slots(matrix: list[list[str | None]], day: int,
                               start_period: str, end_period: str,
                               min_length: int = 1
                               ) -> list[tuple[int, str]]:
    check_min_length(min_length)
    runs = find_idle_runs(matrix, day, start_period, end_period)

    result = []
    for run in runs:
        if len(run) >= min_length:
            result.extend(run)
    return result


def find_idle_runs_across_days(matrix: list[list[str | None]], days: list,
                               start_period: str, end_period: str,
                               min_length: int = 1) -> dict:
    if type(days) not in (list, tuple) or len(days) == 0:
        raise ValueError("days must be a non-empty list of days (1-7)")
    check_min_length(min_length)

    result = {}
    for day in sorted(days):
        good_runs = []
        for run in find_idle_runs(matrix, day, start_period, end_period):
            if len(run) >= min_length:
                good_runs.append(run)
        if len(good_runs) > 0:
            result[day] = good_runs
    return result


def get_schedule_statistics(student_id: str,
                            matrix: list[list[str | None]],
                            students_db: dict, courses_db: dict) -> dict:

    check_matrix(matrix)
    if student_id not in students_db:
        raise ValueError("Student not found: " + repr(student_id))

    daily_counts = []
    for row in matrix:
        count = 0
        for cell in row:
            if cell is not None:
                count += 1
        daily_counts.append(count)

    total_credits = 0
    for course_id in students_db[student_id].get("courses", []):
        if course_id not in courses_db:
            raise ValueError("Course not found: " + repr(course_id))
        total_credits += courses_db[course_id].get("credit", 0)

    idle_slots = 7 * 12 - sum(daily_counts)

    return {
        "daily_class_counts": daily_counts,
        "total_credits": total_credits,
        "total_idle_slots": idle_slots,
    }


def short_label(cell: str | None) -> str:
    if cell is None:
        return ""
    ids = []
    for part in cell.split(CONFLICT_SEPARATOR):
        ids.append(part.split(" (")[0])
    text = "/".join(ids)
    if len(text) > CELL_WIDTH:
        text = text[:CELL_WIDTH - 1] + "~"
    return text


def make_table_line(cells: list) -> str:
    line = "|"
    for text in cells:
        line += " " + text.ljust(CELL_WIDTH) + " |"
    return line


def render_cli_schedule(matrix: list[list[str | None]]) -> str:
    check_matrix(matrix)

    border = "+" + "+".join(["-" * (CELL_WIDTH + 2)] * 8) + "+"

    lines = [border, make_table_line(["Period"] + DAY_NAMES), border]
    for column in range(12):
        cells = [PERIODS[column]]
        for row in range(7):
            cells.append(short_label(matrix[row][column]))
        lines.append(make_table_line(cells))
        lines.append(border)

    # Collect each different item once for the legend.
    legend = []
    for row in matrix:
        for cell in row:
            if cell is None:
                continue
            for part in cell.split(CONFLICT_SEPARATOR):
                if part not in legend:
                    legend.append(part)

    if len(legend) > 0:
        lines.append("Legend:")
        for entry in sorted(legend):
            lines.append("  " + entry)

    return "\n".join(lines)
