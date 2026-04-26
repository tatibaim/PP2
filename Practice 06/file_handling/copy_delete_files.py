import shutil
# shutil — file manipulation (advanced)
# Main functions: Copy file, Move file, Delete folder
import os 
# working with the operation system
# This is a built-in Python module that allows you to: work with files,
# work with folders, get system, Copy a file

shutil.copy("example.txt", "backup.txt") 
# example.txt is what we copy into backup.txt and a new file backup.txt appears (copy)
print("File copied!")

# Deleting a file
if os.path.exists("backup.txt"): # Checks if file.txt exists.
    os.remove("backup.txt")  #if yes, Deleting a file
    print("File deleted safely!") 