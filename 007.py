import math
x=int(input())
y=int(input())
z=int(input())
if 0<=x<=10:
    x=x*250
elif 11<=x<=20:
    x=x*0.9*250
elif 21<=x<=30:
    x=x*0.85*250
else:
    x=x*0.8*250

if 0<=y<=10:
    y=y*880
elif 11<=y<=20:
    y=y*0.95*880
elif 21<=y<=30:
    y=y*0.9*880
else:
    y=y*0.85*880

if 0<=z<=10:
    z=z*150
elif 11<=z<=20:
    z=z*0.85*150
elif 21<=z<=30:
    z=z*0.75*150
else:
    z=z*0.65*150
Total=x+y+z
print(math.ceil(round(Total,5)))


