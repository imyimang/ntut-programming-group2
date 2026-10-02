# 1. 讀取 3 門課程資料
courses = []
for _ in range(3):
    c_id = int(input().strip())      # 課程編號轉成整數
    t1 = int(input().strip())        # 第一節時間轉成整數
    t2 = int(input().strip())        # 第二節時間轉成整數
    courses.append((c_id, [t1, t2]))

# 為了方便後續比較，我們先將 3 門課程依據編號由小到大排序
courses.sort(key=lambda c: c[0])

conflicts = [] # 用來存放所有衝堂紀錄

# 2. 兩兩比對課程 (course[0]與course[1]、course[0]與course[2]、course[1]與course[2])
for i in range(len(courses)):
    for j in range(i + 1, len(courses)):
        c1_id, c1_times = courses[i]
        c2_id, c2_times = courses[j]
        
        # 找出兩門課相同的上課時間
        common_times = []
        for t1 in c1_times:
            if t1 in c2_times and t1 not in common_times:
                common_times.append(t1)
        
        # 時間從小到大排序（確保同兩門課衝堂時，時間小者先輸出）
        common_times.sort()
        
        # 記錄衝堂資訊
        for t in common_times:
            conflicts.append((c1_id, c2_id, t))

# 3. 輸出結果
if not conflicts:
    print("correct")
else:
    for c1_id, c2_id, time_slot in conflicts:
        print(f"{c1_id} and {c2_id} conflict on {time_slot}")