# test_f3.py
import pytest
from f3_schedule import (build_schedule_matrix, query_schedule_slot,
                         find_course_slots, find_idle_runs,
                         find_continuous_idle_slots,
                         find_idle_runs_across_days,
                         get_schedule_statistics, render_cli_schedule)


def make_dbs():
    courses = {
        "CS101": {"id": "CS101", "name": "Python Programming", "credit": 3,
                  "timeSlot": [(1, "3"), (1, "4"), (3, "1")]},
        "MA101": {"id": "MA101", "name": "Calculus", "credit": 2,
                  "timeSlot": [(1, "1"), (2, "3"), (2, "4")]},
        "EN101": {"id": "EN101", "name": "English", "credit": 2,
                  "timeSlot": [(5, "c")]},
        # "SC101": {"id": "SC101", "name": "Science", "credit": 3,
        #         "timeSlot": [(4, "3"),(4, "4"),(4, "5")]},
    }
    activities = {
        "ACT01": {"id": "ACT01", "name": "Study Group",
                  "timeSlot": [(2, "5")]},
    }
    students = {
        "S001": {"id": "S001", "name": "Alice",
                 "courses": ["CS101", "MA101"], "activities": ["ACT01"]},
        "S002": {"id": "S002", "name": "Bob",
                 "courses": [], "activities": []},
    }
    return students, courses, activities


def make_matrix(student_id="S001"): #EDIT THIS TO CHANGE THE STUDENT SCHEDULE WHEN PRINTING THE MATRIX YEAAAAA
    students, courses, activities = make_dbs()
    return build_schedule_matrix(student_id, students, courses, activities)


def test_matrix_shape():
    m = make_matrix()
    assert len(m) == 7
    assert all(len(row) == 12 for row in m)


def test_course_placed_with_label():
    m = make_matrix()
    assert m[0][2] == "CS101 (Python Programming)"   # Mon period 3


def test_multi_slot_course_in_all_slots():
    m = make_matrix()
    assert m[0][2] == m[0][3] == m[2][0] == "CS101 (Python Programming)"


def test_activity_placed():
    assert make_matrix()[1][4] == "ACT01 (Study Group)"   # Tue period 5

def test_period_letters_map_to_last_columns():
    students, courses, activities = make_dbs()
    students["S001"]["courses"].append("EN101")
    m = build_schedule_matrix("S001", students, courses, activities)
    assert m[4][11] == "EN101 (English)"


def test_student_without_items_is_all_free():
    m = make_matrix("S002")
    assert all(cell is None for row in m for cell in row)


def test_multiple_courses_same_day():
    m = make_matrix()
    assert m[0][0] == "MA101 (Calculus)"
    assert m[0][2] == "CS101 (Python Programming)"


def test_uppercase_period_accepted():
    students, courses, activities = make_dbs()
    courses["EN101"]["timeSlot"] = [(5, "C")]
    students["S001"]["courses"].append("EN101")
    m = build_schedule_matrix("S001", students, courses, activities)
    assert m[4][11] == "EN101 (English)"


def test_overlap_is_shown_not_hidden():
    students, courses, activities = make_dbs()
    activities["ACT01"]["timeSlot"] = [(1, "3")]   # clashes with CS101
    m = build_schedule_matrix("S001", students, courses, activities)
    assert "CS101" in m[0][2] and "ACT01" in m[0][2]


def test_build_does_not_modify_inputs():
    students, courses, activities = make_dbs()
    build_schedule_matrix("S001", students, courses, activities)
    assert (students, courses, activities) == make_dbs()


def test_build_unknown_student():
    students, courses, activities = make_dbs()
    with pytest.raises(ValueError):
        build_schedule_matrix("S999", students, courses, activities)


def test_build_unknown_course():
    students, courses, activities = make_dbs()
    students["S001"]["courses"].append("XX999")
    with pytest.raises(ValueError):
        build_schedule_matrix("S001", students, courses, activities)

def test_build_unknown_activity():
    students, courses, activities = make_dbs()
    students["S001"]["activities"].append("ACT99")
    with pytest.raises(ValueError):
        build_schedule_matrix("S001", students, courses, activities)

@pytest.mark.parametrize("slot", [(8, "1"), (0, "1"), (1, "d"), (1, "0"),
                                  (1,), "x"])
def test_build_invalid_time_slot(slot):
    students, courses, activities = make_dbs()
    courses["CS101"]["timeSlot"] = [slot]
    with pytest.raises(ValueError):
        build_schedule_matrix("S001", students, courses, activities)


def test_query_occupied_slot():
    assert query_schedule_slot(make_matrix(), 1, "3") == \
        "CS101 (Python Programming)"

def test_query_free_slot_returns_none():
    assert query_schedule_slot(make_matrix(), 7, "c") is None

def test_query_letter_period():
    students, courses, activities = make_dbs()
    students["S001"]["courses"].append("EN101")
    m = build_schedule_matrix("S001", students, courses, activities)
    assert query_schedule_slot(m, 5, "c") == "EN101 (English)"

@pytest.mark.parametrize("day", [0, 8, -1, "1", None, 1.0, True])
def test_query_invalid_day(day):
    with pytest.raises(ValueError):
        query_schedule_slot(make_matrix(), day, "1")

@pytest.mark.parametrize("period", ["0", "d", "10", "", None, 0, 10])
def test_query_invalid_period(period):
    with pytest.raises(ValueError):
        query_schedule_slot(make_matrix(), 1, period)

def test_query_integer_period_is_normalised():
    assert query_schedule_slot(make_matrix(), 1, 3) == \
        "CS101 (Python Programming)"
    assert query_schedule_slot(make_matrix(), 1, "A") is None

def test_query_malformed_matrix():
    with pytest.raises(ValueError):
        query_schedule_slot([[None] * 12] * 6, 1, "1")

def test_find_course_slots_multi():
    assert find_course_slots(make_matrix(), "CS101") == \
        [(1, "3"), (1, "4"), (3, "1")]

def test_find_activity_slots():
    assert find_course_slots(make_matrix(), "ACT01") == [(2, "5")]

def test_find_course_slots_not_present():
    assert find_course_slots(make_matrix(), "ZZ999") == []

def test_find_course_slots_prefix_id_not_confused():
    students, courses, activities = make_dbs()
    courses["CS10"] = {"id": "CS10", "name": "Intro", "credit": 1,
                       "timeSlot": [(4, "1")]}
    students["S001"]["courses"].append("CS10")
    m = build_schedule_matrix("S001", students, courses, activities)
    assert find_course_slots(m, "CS10") == [(4, "1")]

def test_find_course_slots_invalid_id():
    with pytest.raises(ValueError):
        find_course_slots(make_matrix(), "")


def test_idle_full_free_day():
    # Sunday is empty
    slots = find_continuous_idle_slots(make_matrix(), 7, "1", "c")
    assert len(slots) == 12
    assert slots[0] == (7, "1") and slots[-1] == (7, "c")


def test_idle_excludes_occupied():
    slots = find_continuous_idle_slots(make_matrix(), 1, "1", "5")
    assert slots == [(1, "2"), (1, "5")]


def test_idle_three_consecutive():
    slots = find_continuous_idle_slots(make_matrix(), 1, "1", "9",
                                       min_length=3)
    assert slots == [(1, p) for p in "56789"]

def test_idle_three_consecutive_none_available():
    assert find_continuous_idle_slots(make_matrix(), 1, "1", "5",
                                      min_length=3) == []


def test_idle_range_clips_run():
    slots = find_continuous_idle_slots(make_matrix(), 1, "6", "8",
                                       min_length=3)
    assert slots == [(1, "6"), (1, "7"), (1, "8")]


def test_idle_single_period_range():
    assert find_continuous_idle_slots(make_matrix(), 1, "2", "2") == \
        [(1, "2")]
    assert find_continuous_idle_slots(make_matrix(), 1, "3", "3") == []


def test_idle_range_with_letters():
    slots = find_continuous_idle_slots(make_matrix(), 1, "9", "c")
    assert slots == [(1, "9"), (1, "a"), (1, "b"), (1, "c")]


def test_idle_fully_occupied_day_returns_empty():
    m = make_matrix()
    m[0] = ["X (x)"] * 12
    assert find_continuous_idle_slots(m, 1, "1", "c") == []


def test_idle_runs_split_by_class():
    runs = find_idle_runs(make_matrix(), 1, "1", "6")
    assert runs == [[(1, "2")], [(1, "5"), (1, "6")]]


def test_idle_start_after_end():
    with pytest.raises(ValueError):
        find_continuous_idle_slots(make_matrix(), 1, "5", "2")


def test_idle_invalid_day_and_period():
    m = make_matrix()
    with pytest.raises(ValueError):
        find_continuous_idle_slots(m, 9, "1", "5")
    with pytest.raises(ValueError):
        find_continuous_idle_slots(m, 1, "z", "5")
    with pytest.raises(ValueError):
        find_continuous_idle_slots(m, 1, "1", "z")


@pytest.mark.parametrize("n", [0, -1, "3", 2.5, True])
def test_idle_invalid_min_length(n):
    with pytest.raises(ValueError):
        find_continuous_idle_slots(make_matrix(), 1, "1", "c", min_length=n)


def test_cross_day_query():
    result = find_idle_runs_across_days(make_matrix(), [1, 2, 7], "5", "9",
                                        min_length=3)
    assert result[1] == [[(1, p) for p in "56789"]]
    assert result[2] == [[(2, p) for p in "6789"]]
    assert result[7] == [[(7, p) for p in "56789"]]


def test_cross_day_skips_days_without_runs():
    result = find_idle_runs_across_days(make_matrix(), [1, 7], "1", "4",
                                        min_length=3)
    assert 1 not in result     
    assert result[7] == [[(7, p) for p in "1234"]]


def test_cross_day_invalid_days():
    with pytest.raises(ValueError):
        find_idle_runs_across_days(make_matrix(), [], "1", "c")
    with pytest.raises(ValueError):
        find_idle_runs_across_days(make_matrix(), [1, 9], "1", "c")


def test_statistics_normal():
    students, courses, activities = make_dbs()
    m = build_schedule_matrix("S001", students, courses, activities)
    stats = get_schedule_statistics("S001", m, students, courses)
    assert stats["daily_class_counts"] == [3, 3, 1, 0, 0, 0, 0]
    assert stats["total_credits"] == 5
    assert stats["total_idle_slots"] == 84 - 7


def test_statistics_empty_student():
    students, courses, activities = make_dbs()
    m = build_schedule_matrix("S002", students, courses, activities)
    stats = get_schedule_statistics("S002", m, students, courses)
    assert stats["daily_class_counts"] == [0] * 7
    assert stats["total_credits"] == 0
    assert stats["total_idle_slots"] == 84


def test_statistics_counts_add_up():
    students, courses, activities = make_dbs()
    m = build_schedule_matrix("S001", students, courses, activities)
    stats = get_schedule_statistics("S001", m, students, courses)
    assert sum(stats["daily_class_counts"]) + stats["total_idle_slots"] == 84

def test_statistics_unknown_student():
    students, courses, activities = make_dbs()
    m = build_schedule_matrix("S001", students, courses, activities)
    with pytest.raises(ValueError):
        get_schedule_statistics("S999", m, students, courses)

def test_statistics_unknown_course():
    students, courses, activities = make_dbs()
    m = build_schedule_matrix("S001", students, courses, activities)
    students["S001"]["courses"].append("XX999")
    with pytest.raises(ValueError):
        get_schedule_statistics("S001", m, students, courses)

def test_statistics_malformed_matrix():
    students, courses, _ = make_dbs()
    with pytest.raises(ValueError):
        get_schedule_statistics("S001", [], students, courses)

def test_render_contains_headers_and_ids():
    text = render_cli_schedule(make_matrix())
    for day in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
        assert day in text
    assert "CS101" in text and "MA101" in text and "ACT01" in text

def test_render_legend_has_full_names():
    text = render_cli_schedule(make_matrix())
    assert "CS101 (Python Programming)" in text

def test_render_table_lines_equal_width():
    text = render_cli_schedule(make_matrix())
    table = [ln for ln in text.splitlines() if ln.startswith(("+", "|"))]
    assert len({len(ln) for ln in table}) == 1
    assert len(table) == 3 + 2 * 12      # header block + 12 rows

def test_render_empty_matrix_has_no_legend():
    text = render_cli_schedule(make_matrix("S002"))
    assert "Legend" not in text

def test_render_long_id_truncated_keeps_alignment():
    m = make_matrix("S002")
    m[0][0] = "VERYLONGCOURSEID (Name)"
    table = [ln for ln in render_cli_schedule(m).splitlines()
             if ln.startswith(("+", "|"))]
    assert len({len(ln) for ln in table}) == 1

def test_render_malformed_matrix():
    with pytest.raises(ValueError):
        render_cli_schedule([[None] * 12])
