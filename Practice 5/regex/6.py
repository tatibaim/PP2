import re
txt = "Hello, Jon. How are you?"
x = re.sub("[\s.,]", ":", txt)
print(x)    
# coincidences
# (template, coincidences, str)
# space or point or comma