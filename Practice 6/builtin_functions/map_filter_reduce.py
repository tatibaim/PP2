from functools import reduce

numbers = [1, 2, 3, 4, 5]

# map()
squares = list(map(lambda x: x**2, numbers))
print("Squares:", squares)
#applies a function to all elements

# filter()
even = list(filter(lambda x: x % 2 == 0, numbers))
print("Even:", even)
# leaves only elements where the condition is True

# reduce()
sum_all = reduce(lambda a, b: a + b, numbers)
print("Sum:", sum_all)
# reduce takes a list and “compresses” it into a single value