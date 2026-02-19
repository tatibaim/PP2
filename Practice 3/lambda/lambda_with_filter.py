# filter with lambda

numbers = [1, 2, 3, 4, 5, 6]
#Create a list of numbers

# filter takes each element of the list
# lambda x: x % 2 == 0 checks if the number is divisible by 2
# If True, the number remains
# If False, the number is removed
evens = list(filter(lambda x: x % 2 == 0, numbers))

# print result
print(evens)
