# sorted with lambda

students = [
    ("Ali", 85),
    ("Dana", 92),
    ("Max", 78)
]

sorted_students = sorted(students, key=lambda x: x[1])

print(sorted_students)
