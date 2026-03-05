import re
txt = "CamelToSnake"
x = re.sub("([A-Z])", r"_\1", txt).lower()
print(x)
# capture group
# r"" raw string, so that \ works correctly