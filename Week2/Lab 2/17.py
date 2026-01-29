# Contacts
import sys
input = sys.stdin.readline  # для очень больших данных

n = int(input())
doc = {}

for _ in range(n):
    command = input().split()
    if command[0] == "set":
        doc[command[1]] = command[2]
    else:  # get
        key = command[1]
        if key in doc:
            print(doc[key])
        else:
            print(f"KE: no key {key} found in the document")