# Different types of arguments

# positional
def introduce(name, age):
    print("Name:", name, "Age:", age)

introduce("Miras", 18)


# default argument
def power(number, exp=2):
    return number ** exp

print(power(5))
print(power(5, 3))
