# BMI = w(kg ) / (h*h)(m^2)
# 1 m = 100 cm, 1 pound = 0.454 kg
"""
Underweight BMI<18
Normal 18<=BMI<24
Overweight 24<=BMI<27
Mild obesity 27<=BMI<30
Moderate obesity 30<=BMI<35
Severe obesity BMI>=35
"""
h=float(input())
w=int(input())
BMI = w*0.454 / (0.01*0.01*h*h)
if BMI<18:
    print("Underweight")
elif 18<=BMI<24:
    print("Normal")
elif 24<=BMI<27:
    print("Overweight")
elif 27<=BMI<30:
    print("Mild obesity")
elif 30<=BMI<35:
    print("Moderate obesity")
else:
    print("Severe obesity")
