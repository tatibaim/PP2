import re
txt = "Hello, beko"
x = re.findall("[A-Z][a-z]+", txt)
print(x)
