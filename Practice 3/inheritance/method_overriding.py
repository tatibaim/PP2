# Method overriding

class Animal:
    def speak(self):
        print("Animal sound")

class Cat(Animal):
    def speak(self):
        print("Meow")

c = Cat()
c.speak()
