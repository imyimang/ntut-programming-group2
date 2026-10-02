"""
def strike_if(a,b,c):
    if c=="x3_2_1":
        if x3_1==10:
            x3_2_1=int(input())
            x3_2_2=int(input())
        elif x3_1+x3_2==10:
            x3_2_1=int(input())
    elif a==10:
        c=int(input())
    else:
        b=int(input())
        c=int(input())
    return a,b,c

x1_1=int(input())
x1_2=0
x2_1=0
x2_2=0
x3_1=0
x3_2=0
x3_2_1=0
x3_2_2=0
strike_if(x1_1,x1_2,x2_1)
strike_if(x2_1,x2_2,x3_1)
strike_if(x3_1,x3_2,x3_2_1)
print (x1_1+x1_2+x2_1+x2_2+x3_1+x3_2+x3_2_1+x3_2_2)
"""



g1_1=int(input())
if g1_1==10:
    g1_2=0
else:
    g1_2=int(input())

g2_1=int(input())
if g2_1==10:
    g2_2=0
else:
    g2_2=int(input())


g3_1=int(input())
if g3_1==10:
    g3_2=0

elif g3_1!=10:
    g3_2=int(input())

ex1=0
ex2=0
if g3_1==10:
    ex1=int(input())
    ex2=int(input())
elif g3_1+g3_2==10:
    ex1=int(input())



#分數
if g1_1==10:
    if g2_1!=10:
        score1=10+g2_1+g2_2
    else:
        score1=10+g2_1+g3_1
elif g1_1+g1_2==10:
    score1=10+g2_1
else:
    score1=g1_1+g1_2

if g2_1==10:
    if g3_1!=10:
        score2=10+g3_1+g3_2
    else:
        score2=10+g3_1+ex1
elif g2_1+g2_2==10:
    score2=10+g3_1
else:
    score2=g2_1+g2_2

if g3_1==10:
    score3=g3_1+ex1+ex2
elif g3_1+g3_2==10:
    score3=10+ex1
else:
    score3=g3_1+g3_2

print(score1+score2+score3)


