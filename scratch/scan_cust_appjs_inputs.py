import re

with open("customer_mobile/www/js/app.js", "r", encoding="utf-8") as f:
    cust_js = f.read()

# Find any <input in customer app.js
inputs = re.findall(r'<input\s+([^>]+)>', cust_js)
print(f"Total <input> elements in customer_mobile/www/js/app.js: {len(inputs)}")
for idx, inp in enumerate(inputs):
    if any(t in inp for t in ['type="hidden"', 'type="checkbox"', 'type="radio"', 'type="file"', 'type="submit"', 'type="button"']):
        continue
    if 'maxlength' not in inp and 'max=' not in inp:
        print(f"Cust JS Input {idx}: {inp[:80]}")
