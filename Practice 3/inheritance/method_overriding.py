# Method overriding

# Create a base class Animal
class Animal:
    # The speak method is "to make a sound"
    def speak(self):
        print("Animal sound")

# Create a Cat class that inherits from Animal
class Cat(Animal):
    # Override the speak method
    # Now Cat has its own version of this method
    def speak(self):
        print("Meow")

# Create an object of the Cat class
c = Cat()

# Call the speak method
# The version from the Cat class is used, not the Animal version.
c.speak() # print: Meow
