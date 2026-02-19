# Class vs instance variables

class Car:
    wheels = 4  
    # class variable, it is common to all objects of this class.

    def __init__(self, brand): 
        # __init__ is a special method that is automatically called when an object is created.
        self.brand = brand  
        # instance variable, each object has its own

# crate two object of the class Car
car1 = Car("Toyota")
car2 = Car("BMW")

print(car1.wheels)
# We display the number of wheels on car1
# wheels are taken from the Car class

print(car2.brand)
# Displaying the car brand car2
# brand is a private variable of the car2 object