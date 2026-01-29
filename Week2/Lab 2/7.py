#Position of maximum
a=int(input())
number=list(map(int, input().split()))
pos=number.index(max(number))
print(pos+1)