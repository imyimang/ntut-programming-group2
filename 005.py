a=int(input())
b=int(input())
c=int(input())
x=max(a,b,c) #第三邊
m=(a+b+c)-x  #任兩邊
n=(a**2+b**2+c**2)-x**2
if a<=0 or b<=0 or c<=0 or m<=x:
   print("Not Triangle")
else:
    if a==b==c:
        print("Equilateral Triangle")
    if a==b or b==c or a==c:
        print("Isosceles Triangle")
    if x**2>n:
        print("Obtuse Triangle")
    if x**2<n:
        print("Acute Triangle")
    if x**2==n:
        print("Right Triangle")
    print(a+b+c)