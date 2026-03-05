import re
import json

with open("raw.txt", "r", encoding="utf-8") as file:
    text = file.read()
prices = re.findall(r"(\d+ ?\d*,\d{2})\s*Стоимость", text)

product_names = re.findall(r"\d+\.\n(.+)", text)

total = re.search(r'ИТОГО:\s*\n?([\d\s]+,\d{2})', text)
last_total = total.group(1) if total else None

date = re.search(r'\d{2}\.\d{2}\.\d{4}\s\d{2}:\d{2}:\d{2}', text)
datetime = date.group(0) if date else None

if "Банковская карта" in text:
    payment_method = "Банковская карта"
elif "Наличные" in text:
    payment_method = "Наличные"
else:
    payment_method = "Не найдено"

result = {
    "products": product_names,
    "prices": prices,
    "reported_total": last_total,
    "datetime": datetime,
    "payment_method": payment_method
}

print(json.dumps(result, ensure_ascii=False, indent=4))