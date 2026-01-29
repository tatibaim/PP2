#Power of two?
a=int(input())

pow=1
while pow<a:
    pow*=2
if pow==a:
    print('YES')
else:
    print("NO")
