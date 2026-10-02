"""
def getData():
    course = [input(), input(), input()]
    return course

def compute():
    course1 = getData()
    course2 = getData()
    course3 = getData()
    courses = [course1, course2, course3]
"""
course1=int(input())
t1_1=int(input())
t1_2=int(input())

course2=int(input())
t2_1=int(input())
t2_2=int(input())

course3=int(input())
t3_1=int(input())
t3_2=int(input())

if course1 > course2:
    course1, course2 = course2, course1 
    t1_1, t2_1 = t2_1, t1_1
    t1_2, t2_2 = t2_2, t1_2

if course2 > course3:
    course2, course3 = course3, course2
    t2_1, t3_1 = t3_1, t2_1
    t2_2, t3_2 = t3_2, t2_2

if course1 > course2:
    course1 , course2 = course2, course1
    t1_1, t2_1 = t2_1, t1_1
    t1_2, t2_2 = t2_2, t1_2

has_conflict = False

#先比課一課二
timea1=min(t1_1,t1_2)
timea2=max(t1_1,t1_2)
timeb1=min(t2_1,t2_2)
timeb2=max(t2_1,t2_2)

if timea1==timeb1:
    print(f"{course1} and {course2} conflict on {timea1}")
    has_conflict = True
if timea1==timeb2:
    print(f"{course1} and {course2} conflict on {timea1}")
    has_conflict = True
if timea2==timeb1:
    print(f"{course1} and {course2} conflict on {timea2}")
    has_conflict = True
if timea2==timeb2:
    print(f"{course1} and {course2} conflict on {timea2}")
    has_conflict = True

#課一課三
timec1=min(t3_1,t3_2)
timec2=max(t3_1,t3_2)

if timea1==timec1:
    print(f"{course1} and {course3} conflict on {timea1}")
    has_conflict = True
if timea1==timec2:
    print(f"{course1} and {course3} conflict on {timea1}")
    has_conflict = True
if timea2==timec1:
    print(f"{course1} and {course3} conflict on {timea2}")
    has_conflict = True
if timea2==timec2:
    print(f"{course1} and {course3} conflict on {timea2}")
    has_conflict = True

#課二課三

if timeb1==timec1:
    print(f"{course2} and {course3} conflict on {timeb1}")
    has_conflict = True
if timeb1==timec2:
    print(f"{course2} and {course3} conflict on {timeb1}")
    has_conflict = True
if timeb2==timec1:
    print(f"{course2} and {course3} conflict on {timeb2}")
    has_conflict = True
if timeb2==timec2:
    print(f"{course2} and {course3} conflict on {timeb2}")
    has_conflict = True


if not has_conflict:
    print("correct")