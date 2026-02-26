#1
n = int(input())

def squares(n):
    for i in range(1, n + 1): 
        yield i * i

for x in squares(n):
    print(x)

#2
n = int(input())

def evens(n):
    for i in range(0, n + 1, 2):
        yield i

first = True
for x in evens(n):
    if not first:
        print(",", end="")
    print(x, end="")
    first = False

#3
n = int(input())

def evens(n):
    for i in range(0, n + 1, 2):
        yield i

first = True
for x in evens(n):
    if not first:
        print(",", end="")
    print(x, end="")
    first = False

#4
a, b = map(int, input().split())

def squares(a, b):
    for i in range(a, b + 1):
        yield i * i

for x in squares(a, b):
    print(x)