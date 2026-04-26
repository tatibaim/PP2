names = ["Alice", "Bob", "Charlie"]
scores = [85, 90, 78]

# enumerate()
for i, name in enumerate(names):
    print(i, name)
# Adds indices to list elements while iterating.

# zip()
for name, score in zip(names, scores):
    print(name, score)
# Combines multiple lists by elements
# If the lists are of different lengths zip() takes the length of the shortest list

# type checking
x = "123"
print(type(x))

# conversion
num = int(x)
print(num + 10)