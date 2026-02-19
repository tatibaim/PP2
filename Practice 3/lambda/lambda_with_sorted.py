# sorted with lambda

# Create a list of students as tuples (name, grade)
students = [
    ("Ali", 85),
    ("Dana", 92),
    ("Max", 78)
]

# sorted — sorts the list
# key=lambda x: x[1] — says: sort by the SECOND element (score)
sorted_students = sorted(students, key=lambda x: x[1])

# Output a sorted list
print(sorted_students)
