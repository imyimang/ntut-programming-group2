a_x1=int(input())
a_x2=int(input())

b_x1=int(input())
b_x2=int(input())

c_x1=int(input())
c_x2=int(input())

def compare_x1(a,b):
    if a<b:
        x1=a
    elif a>b:
        x1=b
    else:
        x1=a=b
    return x1

def compare_x2(a,b):
    if a<b:
        x2=a
    elif a>b:
        x2=b
    else:
        x2=a=b
    return x2
x1=0
x2=0
compare_x1(a_x1,b_x1)
compare_x1(b_x1,c_x1)
compare_x1(a_x1,c_x1)
compare_x1(a_x1,b_x1)
compare_x2(a_x2,b_x2)
compare_x2(b_x2,c_x2)
compare_x2(a_x2,c_x2)
compare_x2(a_x2,b_x2)

print(x2-x1)
