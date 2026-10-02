import math
a=int(input())
b=int(input())
c=int(input())
D=b*b-4*a*c
if D>0:
    x1=((-b)+math.sqrt(D))/(2*a)
    x2=((-b)-math.sqrt(D))/(2*a)
    print(f"{x1:.1f}")
    print(f"{x2:.1f}")
elif D==0:
    x=-b/(2*a)
    print(f"{x:.1f}")
else:
    A=-b/(2*a)
    B=abs(math.sqrt(-D)/(2*a))
    print(f"{A:.1f}+{B:.1f}i")
    print(f"{A:.1f}-{B:.1f}i")