x=int(input())
y=int(input())
z=int(input())
n=x+y+z
m=440*x+1200*y+130*z
if n>=5:
    m=int(m*0.9)
if m>=3000:
    print(m-300)
else:
    print(m)
