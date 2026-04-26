#1
from datetime import datetime, timedelta

today = datetime.now()
five_days_ago = today - timedelta(days=5)

print(five_days_ago)

#2
from datetime import datetime, timedelta

today = datetime.now()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)

print(today)
print(yesterday)
print(tomorrow)

#3
from datetime import datetime

now = datetime.now()
no_micro = now.replace(microsecond=0)

print(no_micro)

#4
from datetime import datetime

d1 = datetime(2026, 2, 26, 10, 30, 0)
d2 = datetime(2026, 2, 26, 10, 45, 20)

d = d2 - d1

seconds = d.total_seconds()

print(seconds)
