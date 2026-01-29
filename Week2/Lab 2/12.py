#Square
a=int(input())

list=list(map(int, input().split()))

for i in range(a):
    list[i]=list[i]**2
print(*list)