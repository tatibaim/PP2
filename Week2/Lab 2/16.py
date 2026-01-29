#Newbie
a=int(input())
list=(list(map(int, input().split())))
s=set() # опять же будем юзать сет 

for i in list:
    if i not in s: # тут уже прикол самого сета, можно так чекать есть ли этот элемент в массиве сет, в случае если нет 
        # сначал принтим ответ а потом добовляем его в массив сет
        print("YES")
        s.add(i)
    else:
        print("NO")