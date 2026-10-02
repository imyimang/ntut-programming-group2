x=input()
y=int(input())
a=int(input())
b=int(input())
c=int(input())
score=[a,b,c]
total=sum(score)
average=total//len(score)
print("Name:"+x, "Id:"+str(y), "Total:"+str(total), "Average:"+str(average), sep='\n')

