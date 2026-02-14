# __init__ constructor

class Student:
    def __init__(self, name, grade):
        self.name = name
        self.grade = grade

    def info(self):
        print(self.name, self.grade)

s = Student("Miras", "A")
s.info()
