# 定義函式
# 函式內部的程式碼，沒有呼叫，不執行
def multiply(n1,n2):
    print(n1*n2)
    return n1*n2
# 呼叫函式
value=multiply(3, 4)
print(value)
# multiply(3, 4)
# multiply(10, 8)

#程式的包裝: 同樣的程式邏輯可以重複利用
def calculate(max):
    sum=0
    for n in range(1,max+1):
        sum=sum+n
    print (sum)

calculate(10) #呼叫第一次 
calculate(20) #呼叫第二次