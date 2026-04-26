import os

# Creating nested folders
os.makedirs("folder11/folder22/folder33", exist_ok=True)
# Creates nested folders immediately
# exist_ok Doesn't throw an error if they already exist

# List of files and folders
files = os.listdir(".") 
# "." = current folder
# Returns a list
print("Files and folders:")
print(files)