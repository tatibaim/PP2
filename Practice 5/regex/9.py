import re
txt = "HelloCapHowAreYou?"
x = re.sub("(?=[A-Z])", ' ', txt)
print(x)