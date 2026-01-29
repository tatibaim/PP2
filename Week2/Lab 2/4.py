#Positive number
a=int(input())
number=list(map(int, input().split()))

total=0
for i in number:
    if i>0:
        total+=1
    else:
        continue
        
print(total)
