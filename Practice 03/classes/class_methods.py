# Instance methods

class Calculator: # we create class Calculator
    def add(self, a, b):
        # method for adding two numbers
        # self - link for the object
        # a and b the numbers we pass to the method
        return a + b # return sum of numbers

    def multiply(self, a, b):
        # method for multiplying two numbers
        return a * b # Return the product of a and b

c = Calculator()
# create an object for the class Calculator

print(c.add(3, 4))
print(c.multiply(3, 4))
# we call the add method and print result