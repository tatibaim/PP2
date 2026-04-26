# __init__ constructor

class Student:
    def __init__(self, name, grade):
        # __init__ — constructor
        # It is called automatically when an object is created
        
        self.name = name
        # Save the name to an object
        
        self.grade = grade
        # Save the rating to an object

    # Method for displaying information about a student
    def info(self):
        # Print the name and rating
        print(self.name, self.grade)

# Create an object of the Student class
# "Miras" - name, "A" - grade
s = Student("Miras", "A")

# Call the info method
s.info()
