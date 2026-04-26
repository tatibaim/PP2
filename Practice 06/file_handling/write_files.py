# Creating and writing to a file
with open("example.txt", "w") as f:
    f.write("Hello, this is line 1\n")
    f.write("This is line 2\n")

print("File created and written!")

# The open() function takes two parameters; filename, and mode.

# "w" - Write - Opens a file for writing, creates the file if it does not exist

# If we use the open() function, we will have to close the file ourselves at 
# the end of working with it, but with the with() function, we don't have 
# to worry about closing the file every time.