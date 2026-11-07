# test_f2.py
import pytest
from f2_checker import check_course_enrollment


# ==================== 工具函式 (測試資料建立) ====================

def make_f2_world():
    """建立包含各種衝突情境的 Mock 資料庫環境"""
    classrooms_db = {
        "A101": {"capacity": 50},
        "A102": {"capacity": 50}
    }

    courses_db = {
        # 已修課程：星期二第 3 節
        "CS101": {
            "id": "CS101", "name": "微積分", "credit": 3,
            "maxStudentCount": 40, "classroom": "A101",
            "timeSlot": [(2, "3")]
        },
        # 衝突課程：星期二第 3 節（課程衝堂）+ 星期四第 5 節（活動衝堂）
        "CS102": {
            "id": "CS102", "name": "Python程式設計", "credit": 3,
            "maxStudentCount": 40, "classroom": "A102",
            "timeSlot": [(2, "3"), (4, "5")]
        },
        # 額滿課程
        "CS103": {
            "id": "CS103", "name": "資料結構", "credit": 3,
            "maxStudentCount": 1, "classroom": "A102",
            "timeSlot": [(1, "1")]
        },
        # 高學分課程（引發學分超標）
        "CS104": {
            "id": "CS104", "name": "專題研究", "credit": 10,
            "maxStudentCount": 40, "classroom": "A102",
            "timeSlot": [(5, "1")]
        },
        # 正常可加選課程
        "CS105": {
            "id": "CS105", "name": "離散數學", "credit": 3,
            "maxStudentCount": 40, "classroom": "A102",
            "timeSlot": [(3, "1"), (3, "2")]
        }
    }

    students_db = {
        "S001": {
            "id": "S001", "name": "小明", "department": "資工一",
            "maxCredit": 18, "activities": ["ACT01"]
        }
    }

    activities_db = {
        # 活動：星期四第 5 節
        "ACT01": {
            "id": "ACT01", "name": "程式設計讀書會",
            "timeSlot": [(4, "5")]
        }
    }

    # S001 已選 CS101 (3 學分)；S002 已選 CS103 (導致 CS103 額滿)
    enrollments = [
        {"student_id": "S001", "course_id": "CS101", "status": "ENROLLED"},
        {"student_id": "S002", "course_id": "CS103", "status": "ENROLLED"}
    ]

    return students_db, courses_db, activities_db, enrollments


# ==================== 單元測試案例 ====================

def test_f2_enrollment_success():
    """[TC01 正常測試]：完全無衝突時加選成功"""
    students, courses, activities, enrollments = make_f2_world()
    
    result = check_course_enrollment("S001", "CS105", students, courses, activities, enrollments)
    
    assert result["success"] is True
    assert len(result["conflicts"]) == 0
    assert result["after_credits"] == 6


def test_f2_course_and_activity_conflict():
    """[TC02 錯誤/衝突測試]：同時包含課程衝堂與活動衝突"""
    students, courses, activities, enrollments = make_f2_world()
    
    result = check_course_enrollment("S001", "CS102", students, courses, activities, enrollments)
    
    assert result["success"] is False
    assert len(result["conflicts"]) == 2
    assert result["conflicts"][0]["type"] == "COURSE_CONFLICT"
    assert result["conflicts"][1]["type"] == "ACTIVITY_CONFLICT"


def test_f2_capacity_full():
    """[TC03 邊界/錯誤測試]：人數額滿拒絕加選"""
    students, courses, activities, enrollments = make_f2_world()
    
    result = check_course_enrollment("S001", "CS103", students, courses, activities, enrollments)
    
    assert result["success"] is False
    types = [c["type"] for c in result["conflicts"]]
    assert "CAPACITY_FULL" in types


def test_f2_credit_exceeded():
    """[TC04 邊界/錯誤測試]：超過學分上限拒絕加選"""
    students, courses, activities, enrollments = make_f2_world()
    students["S001"]["maxCredit"] = 5  # 調低上限至 5
    
    result = check_course_enrollment("S001", "CS104", students, courses, activities, enrollments)
    
    assert result["success"] is False
    types = [c["type"] for c in result["conflicts"]]
    assert "CREDIT_EXCEEDED" in types


def test_f2_multiple_conflicts_accumulated_and_sorted():
    """[TC05 核心驗收驗證]：不提前中斷與時間排序"""
    students, courses, activities, enrollments = make_f2_world()
    
    # 故意打亂時段順序，並讓該門課同時額滿
    courses["CS102"]["timeSlot"] = [(4, "5"), (2, "3")]
    courses["CS102"]["maxStudentCount"] = 1
    enrollments.append({"student_id": "S003", "course_id": "CS102", "status": "ENROLLED"})
    
    result = check_course_enrollment("S001", "CS102", students, courses, activities, enrollments)
    
    assert result["success"] is False
    assert len(result["conflicts"]) == 3
    
    time_conflicts = [c for c in result["conflicts"] if c["type"] in ("COURSE_CONFLICT", "ACTIVITY_CONFLICT")]
    assert time_conflicts[0]["slot"] == (2, "3")
    assert time_conflicts[1]["slot"] == (4, "5")

 
# ==================== 單一衝突：規格書要求五種分別測 ====================
 
def _student_conflict(s, c, a, e):
    c["CS201"] = make_course("CS201", slots=[(2, "3")])
 
def _classroom_conflict(s, c, a, e):   # S002 沒修 CS101，但同教室同時段
    s["S002"] = {"id": "S002", "maxCredit": 18, "activities": []}
    c["CS202"] = make_course("CS202", room="A101", slots=[(2, "3")])
 
def _activity_conflict(s, c, a, e):
    c["CS203"] = make_course("CS203", slots=[(4, "5")])
 
def _credit_exceeded(s, c, a, e):
    s["S001"]["maxCredit"] = 5
 
@pytest.mark.parametrize("expected, sid, cid, setup", [
    ("COURSE_CONFLICT",    "S001", "CS201", _student_conflict),
    ("CLASSROOM_CONFLICT", "S002", "CS202", _classroom_conflict),
    ("ACTIVITY_CONFLICT",  "S001", "CS203", _activity_conflict),
    ("CREDIT_EXCEEDED",    "S001", "CS104", _credit_exceeded),
    ("CAPACITY_FULL",      "S001", "CS103", None),
])
def test_f2_single_conflict_only(expected, sid, cid, setup):
    """[衝突] 只觸發一種限制時，不可誤報其他四種"""
    result = run(sid, cid, setup)
    assert result["success"] is False
    assert types_of(result) == [expected]
 
 
def test_f2_all_five_conflict_types_reported_together():
    """[衝突] 五種同時發生必須全部列出，不可發現第一項就停止"""
    result = run(cid="CS300", setup=five_conflicts_setup)
    assert sorted(types_of(result)) == sorted(
        ["COURSE_CONFLICT", "CLASSROOM_CONFLICT", "ACTIVITY_CONFLICT",
         "CAPACITY_FULL", "CREDIT_EXCEEDED"])
 
 
# ==================== 邊界 ====================
 
@pytest.mark.parametrize("max_credit, ok", [(6, True), (5, False)])
def test_f2_credit_limit_boundary(max_credit, ok):
    """[邊界] 加選後學分 6：上限 6 允許、上限 5 拒絕"""
    result = run(setup=lambda s, c, a, e: s["S001"].update(maxCredit=max_credit))
    assert result["success"] is ok
    assert result["after_credits"] == 6
 
 
@pytest.mark.parametrize("cap, ok", [(2, True), (1, False)])
def test_f2_seat_boundary(cap, ok):
    """[邊界] 已有 1 人：上限 2（剩最後一個名額）允許、上限 1 拒絕"""
    result = run(cid="CS103", setup=lambda s, c, a, e: c["CS103"].update(maxStudentCount=cap))
    assert result["success"] is ok
 
 
@pytest.mark.parametrize("enrolled_slots, target_slots, expected", [
    ([(1, "1"), (7, "c")], [(1, "1"), (7, "c")], [(1, "1"), (7, "c")]),   # 第 1 節與第 c 節
    ([(2, "A")], [(2, "a")], [(2, "a")]),                                  # 大小寫不分
    ([(2, "3")], [(2, "4")], []),                                          # 相鄰不重疊
    ([(2, "3")], [(3, "3")], []),                                          # 同節次不同星期
    ([(3, "1"), (1, "c"), (2, "a"), (2, "9")],
     [(3, "1"), (1, "c"), (2, "a"), (2, "9")],
     [(1, "c"), (2, "9"), (2, "a"), (3, "1")]),                            # 排序：先星期、9 在 a 前
])
def test_f2_time_overlap_boundary(enrolled_slots, target_slots, expected):
    """[邊界] 時段重疊判斷與排序"""
    def setup(s, c, a, e):
        c["CS101"]["timeSlot"] = enrolled_slots
        c["CS201"] = make_course("CS201", slots=target_slots)
    result = run(cid="CS201", setup=setup)
    assert [c["slot"] for c in result["conflicts"]] == expected
 
 
# ==================== 錯誤與資料異常 ====================
 
@pytest.mark.parametrize("sid, cid", [("S999", "CS105"), ("S001", "NOPE")])
def test_f2_student_or_course_not_found(sid, cid):
    """[錯誤] 學生或課程不存在：失敗並給錯誤訊息"""
    result = run(sid, cid)
    assert result["success"] is False
    assert result["errors"]
 
 
def test_f2_duplicate_enrollment_rejected():
    """[錯誤] 已選過的課程不可重複加選"""
    result = run(cid="CS101")
    assert result["success"] is False
    assert "DUPLICATE" in types_of(result)
 
 
def test_f2_dropped_enrollment_is_ignored():
    """[正常] 已退選(DROPPED)不算衝堂也不計學分"""
    result = run(cid="CS102", setup=lambda s, c, a, e: e[0].update(status="DROPPED"))
    assert "COURSE_CONFLICT" not in types_of(result)
    assert result["current_credits"] == 0
 
 
def _dangling_enrollment(s, c, a, e):
    e.append({"student_id": "S001", "course_id": "GHOST", "status": "ENROLLED"})
 
def _unknown_activity(s, c, a, e):
    s["S001"]["activities"].append("NO_SUCH_ACT")
 
def _no_timeslot(s, c, a, e):
    del c["CS105"]["timeSlot"]
 
@pytest.mark.parametrize("setup", [_dangling_enrollment, _unknown_activity, _no_timeslot])
def test_f2_dirty_data_does_not_crash(setup):
    """[錯誤] 指向不存在的課程/活動、缺少 timeSlot：不當機，仍可完成檢查"""
    result = run(setup=setup)
    assert result["success"] is True
 
 
def test_f2_does_not_modify_inputs():
    """[正常] F2 只檢查，不可修改傳入的資料"""
    world = make_f2_world()
    snapshot = copy.deepcopy(world)
    check_course_enrollment("S001", "CS105", *world)
    check_course_enrollment("S001", "CS102", *world)
    assert world == snapshot
 
 
def test_f2_result_contains_required_output_fields():
    """[正常] 輸出含規格要求的欄位與學分數字"""
    result = run()
    for key in ("success", "student_id", "target_course", "conflicts",
                "current_credits", "after_credits", "max_credits"):
        assert key in result
    assert result["target_course"] == "CS105 離散數學"
    assert (result["current_credits"], result["after_credits"], result["max_credits"]) == (3, 6, 18)
 
 
def test_f2_helper_functions():
    """[邊界] 輔助函式獨立測試：交集、正規化、排序鍵"""
    assert find_intersections([], [(1, "1")]) == []
    assert find_intersections([[2, "A"]], [(2, "a")]) == [(2, "a")]
    assert normalize_slots([(1, "1"), (1,), "x", None]) == {(1, "1")}
    assert get_slot_sort_key((2, "9")) < get_slot_sort_key((2, "a")) < get_slot_sort_key((3, "1"))
 
 
# ==================== 已知缺陷（依需求規格書應通過，目前程式失敗） ====================
 
@pytest.mark.xfail(strict=True, reason=(
    "BUG-F2-01: 額滿/重複加選以 slot=(0,'0') 佔位，排序後跑到時間衝突『之前』，"
    "規格要求無時間資訊的項目排在所有時間衝突之後"))
def test_bug_f2_01_non_time_conflicts_sorted_last():
    result = run(cid="CS300", setup=five_conflicts_setup)
    kinds = types_of(result)
    last_time = max(i for i, t in enumerate(kinds) if t in TIME_TYPES)
    first_other = min(i for i, t in enumerate(kinds) if t not in TIME_TYPES)
    assert last_time < first_other
 
 
@pytest.mark.xfail(strict=True, reason=(
    "BUG-F2-02: 同一天連續重疊的節次未合併，規格要顯示成『星期二第 3、4 節』一筆"))
def test_bug_f2_02_consecutive_periods_merged():
    def setup(s, c, a, e):
        c["CS101"]["timeSlot"] = [(2, "3"), (2, "4")]
        c["CS201"] = make_course("CS201", slots=[(2, "3"), (2, "4")])
    result = run(cid="CS201", setup=setup)
    assert types_of(result).count("COURSE_CONFLICT") == 1
 
 
@pytest.mark.xfail(strict=True, reason=(
    "BUG-F2-03: 重複加選時目標課程已在 enrolled_cids，學分被算兩次，"
    "多出虛假的 CREDIT_EXCEEDED；規格將『已選過』列為前置錯誤，只需回報這一項"))
def test_bug_f2_03_duplicate_enrollment_is_only_error():
    result = run(cid="CS101", setup=lambda s, c, a, e: s["S001"].update(maxCredit=5))
    assert types_of(result) == ["DUPLICATE"]
 
 
@pytest.mark.xfail(strict=True, reason=(
    "BUG-F2-04: 學生/課程不存在時回傳缺少 conflicts 欄位，呼叫端讀取會 KeyError"))
@pytest.mark.parametrize("sid, cid", [("S999", "CS105"), ("S001", "NOPE")])
def test_bug_f2_04_precondition_error_has_consistent_shape(sid, cid):
    result = run(sid, cid)
    assert result["success"] is False
    assert "conflicts" in result
 
