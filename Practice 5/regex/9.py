import re
txt = "HelloCapHowAreYou?"
x = re.sub("(?=[A-Z])", ' ', txt)
print(x)
# insert a space before capital latter