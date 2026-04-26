# *args and **kwargs examples

# *args
def sum_all(*numbers):
    total = 0
    for n in numbers:
        total += n
    return total

print(sum_all(1, 2, 3, 4))


# **kwargs
def print_info(**info):
    for key, value in info.items():
        print(key, ":", value)

print_info(name="Miras", age=18, city="Almaty")
