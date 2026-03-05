import re #It is needed for searching, checking and processing text according to a template.
txt = "Hello, Abbracham"
x = re.findall("ab*", txt, flags = re.IGNORECASE)
print(x)
# import module re(regular expression)
# create str variable, it contains text in which we look for something.
# re.findall--> searches all concidences according to the template and return list
# in first position we write template, in second any variable with a str, third flags
# "ab*"--> a means we search latter a, * means more reps previous latter (ab, abb, abbb, etc)
# "a" + any number of "b"
# re.IGNORECASE--> igore latter case A=a, b=B