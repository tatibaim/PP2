# Basic inheritance

# Create a base class Animal
class Animal:
    def speak(self):
        print("Some sound") # General behavior for all animals

# Create a Dog class that inherites from Animal
class Dog(Animal):
    pass # pass means: we won't add anything new for now

# Create an object of the Dog class
d = Dog()

# Call the speaking method
# Although the Dog class doesn't have a speak method,
# it's taken from the Animal class (the parent) 
d.speak() # print Some sound
