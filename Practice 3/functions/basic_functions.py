# Basic function examples

# 1. simple function
def greet():
    print("Hello, student!")

greet()


# 2. function with parameters
def add(a, b):
    print(a + b)

add(3, 5)


# 3. function with return value
def square(x):
    return x * x

print(square(4))


# 4. function with list argument
def print_list(items):
    for item in items:
        print(item)

print_list([1, 2, 3])
