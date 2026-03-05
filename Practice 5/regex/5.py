import re
txt = "aaeeerrb aaaasudeei"
x = re.findall("a.*?b", txt)
print(x)
#question mark, nearest