#Reverse elements from exttt{l} to exttt{r}
a, b, c=map(int, input().split())
b-=1
c-=1
list=list(map(int, input().split()))
list[b:c+1]=list[b:c+1][::-1] #я тут хз как вообще работает фигня с индексами

print(*list)