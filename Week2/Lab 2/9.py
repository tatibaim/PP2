#MaxToMin
a=int(input())
number=list(map(int, input().split()))

max=max(number)
min=min(number)
for i in range(a):
    if number[i]==max:
        number[i]=min
for i in range(a):
    print(number[i], end=" ")