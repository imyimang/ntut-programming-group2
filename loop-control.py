# # break 的簡易範例
# n=0
# while n<5:
#     if n==3:
#         break
#     print(n)
#     n+=1
# print(n)

# # continue 的簡易範例
# n=0
# for x in [0,1,2,3]:
#     if x%2==0:
#         continue
#     print(x)
#     n+=1
# print(n)

# # else 的簡易範例
# sum=0
# for n in range(11): #rang(11)==0~10
#     sum+=n
# else:
#     print(sum) #1+2+3.....+9+10

#綜合範例：找出整數平方根
#輸入9得到3
n=input("請輸入正整數：")
n=int(n)
for i in range(n): # i從0~ n-1
    if i*i==n:
        print("整數平方根", i)
        break
else:
    print(n,"沒有整數平方根")
    