#Strings
n = int(input())
strings = [input() for _ in range(n)]

first_occurrence = {}  # словарь: ключ = строка, значение = индекс первой встречи (1-based)

for idx, s in enumerate(strings, start=1):  # нумеруем с 1
    if s not in first_occurrence:
        first_occurrence[s] = idx  # сохраняем первый индекс появления

# сортируем строки по алфавиту
for s in sorted(first_occurrence):
    print(s, first_occurrence[s])
