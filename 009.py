y1=int(input())
m1=int(input())
d1=int(input())

y2=int(input())
m2=int(input())
d2=int(input())

if m1>13 or m2>13:
    print("Invalid Date")
elif d1==31:
    if m1==1 or 3 or 5 or 7 or 8 or 1 or 12:
        print("Invalid Date")
    elif d1==29:
        
        print("")
if y1//4==0:
    if y1//100==0:
        if y1//400==0:
            print("Leap Year")
        else:
            print("Common Year")
    print("Common Year")
else:
    print("Common Year")


if y2//4==0:
    if y2//100==0:
        if y2//400==0:
            print("Leap Year")
        else:
            print("Common Year")
    print("Common Year")
else:
    print("Common Year")



