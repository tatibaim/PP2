#Aida and korean serials
n = int(input())
episodes = {}  # словарь: ключ = название дорамы, значение = количество эпизодов

for _ in range(n):
    s, k = input().split()
    k = int(k)
    if s in episodes:
        episodes[s] += k  # прибавляем эпизоды, если дорама уже была
    else:
        episodes[s] = k   # создаём новую запись

# выводим по лексикографическому порядку названий
for dorama in sorted(episodes):
    print(dorama, episodes[dorama])
