import re #It is needed for searching, checking and processing text according to a template.
txt = "Hello, Abbracham"
x = re.findall("ab*", txt, flags = re.IGNORECASE)
print(x)
