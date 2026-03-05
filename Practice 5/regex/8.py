import re
txt = "HelloBro"
x = re.split("(?=[A-Z])", txt)
print(x)