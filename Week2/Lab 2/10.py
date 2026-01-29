#ReverseSorting
a=int(input())

list=list(map(int, input().split()))
list.sort(reverse=True)
for i in range(a):
    print(list[i], end=" ")