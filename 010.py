card_values = {
    'A': 1.0, '2': 2.0, '3': 3.0, '4': 4.0, '5': 5.0,
    '6': 6.0, '7': 7.0, '8': 8.0, '9': 9.0, '10': 10.0,
    'J': 0.5, 'Q': 0.5, 'K': 0.5
}
x1=input().strip()
x2=input().strip()
x3=input().strip()
y1=input().strip()
y2=input().strip()
y3=input().strip()
x=card_values[x1]+card_values[x2]+card_values[x3]
y=card_values[y1]+card_values[y2]+card_values[y3]
if x>10.5:
    x=0
print(f"{x:g}")


if y>10.5:
    y=0
print(f"{y:g}")


def compare(x,y):
    if x==y:
        print("Tie")
    elif x>y:
        print("X Win")
    else:
        print("Y Win")

compare(x,y)