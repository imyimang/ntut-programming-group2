a=int(input())
b=int(input())
c=int(input())
i=int(input())
j=int(input())
x=0.09*a+0.15*b+0.14*c+1.2*i+1.6*j
y=0.075*a+0.135*b+0.125*c+1.15*i+1.3*j
z=0.065*a+0.11*b+0.1*c+0.95*i+1.1*j
pay_199=x
pay_399=y
pay_799=z
if pay_199<199:
    pay_199=199
if pay_399<399:
    pay_399=399
if pay_799<799:
    pay_799=799
if pay_199<=pay_399 and pay_199<=pay_799:
    print(int(pay_199))
    print("199")
elif pay_399<=pay_799:
    print(int(pay_399))
    print("399")
else:
    print(int(pay_799))
    print("799")
