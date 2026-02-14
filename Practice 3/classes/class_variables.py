# Class vs instance variables

class Car:
    wheels = 4  # class variable

    def __init__(self, brand):
        self.brand = brand  # instance variable

car1 = Car("Toyota")
car2 = Car("BMW")

print(car1.wheels)
print(car2.brand)
