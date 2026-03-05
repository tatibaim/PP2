import re
txt = "abbb abb ab"
x = re.findall("ab{2,3}", txt)
print(x)
# number of repetitions
# {2,3} → 2 to 3 times (abb or abbb)