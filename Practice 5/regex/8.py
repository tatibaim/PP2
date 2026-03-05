import re
txt = "HelloBro"
x = re.split("(?=[A-Z])", txt)
print(x)
# split BEFORE each capital letter
# splits a string based on a pattern