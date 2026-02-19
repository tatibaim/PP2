# map with lambda

# Create a list of numbers
numbers = [1, 2, 3, 4]

# map takes each element of the list
# lambda x: x * x — squares a number
# This function is applied to each number
squares = list(map(lambda x: x * x, numbers))

# print result
print(squares)
