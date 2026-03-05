import re
txt = "Snake_to_Camel"
x = re.sub(r"_([a-zA-Z])", lambda x: x.group(1).upper(), txt)
print(x)
# [a-zA-Z] means any latter
# x is a match object
# () means capture group