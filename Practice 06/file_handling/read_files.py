# Reading a file
with open("example.txt", "r") as f:
    content = f.read()

print("File content:")
print(content)

# "r" - Read - Default value. Opens a file for reading, error if the file does not exist

with open("example.txt", "a") as f:
    f.write("New line\n")
# "a" adds to the end