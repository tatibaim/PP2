#1
import math

deg = float(input())
rad = math.radians(deg)

print(rad)

#2
h = float(input())
b1 = float(input())
b2 = float(input())

area = (b1 + b2) * h / 2

print(area)

#3
import math

n = int(input())
s = float(input())

area = (n * s * s) / (4 * math.tan(math.pi / n))

print(area)

#4
base = float(input())
height = float(input())

area = base * height

print(area)