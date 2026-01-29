#is it pryme?
a=int(input())
test=0
if a<=1:
    print("NO")
else:
    for i in range(1,a+1):
        if a%i==0:
            test+=1
    if test==2:
        print("YES")
    else:
        print("NO")