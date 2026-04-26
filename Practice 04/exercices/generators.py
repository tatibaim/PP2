#1
n = int(input())

def squares(n):
    for i in range(1, n + 1): 
        yield i * i

for x in squares(n):
    print(x)

#2
def even_numbers(n):
    for i in range(0, n + 1):
        if i % 2 == 0:
            yield i

n = int(input())

print(",".join(str(x) for x in even_numbers(n)))

#3
def divisible(n):
    for i in range(0, n + 1):
        if i % 3 == 0 and i % 4 == 0:
            yield i

n = int(input())

for num in divisible(n):
    print(num)

#4
def squares(a, b):
    for i in range(a, b + 1):
        yield i * i

a = int(input("Enter a: "))
b = int(input("Enter b: "))

for value in squares(a, b):
    print(value)
    
#5
def countdown(n):
    for i in range(n, -1, -1):
        yield i

n = int(input())

for num in countdown(n):
    print(num)