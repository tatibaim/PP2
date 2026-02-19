# Simple class

class Person: # create class with name person
    def speak(self):
        # create metod (metod - function inside a class)
        # self - the object that will call the metod 
        
        print("Hello!")
        # print text 

p = Person()
# this we create an object of the class Person

p.speak()
# object p execute metod speak