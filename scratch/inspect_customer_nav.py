import re

with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text_idx = f.read()

with open('customer_mobile/www/dashboard.html', 'r', encoding='utf-8') as f:
    text_dash = f.read()

print('index.html nav elements:')
for m in re.finditer(r'<nav[^>]*>.*?</nav>', text_idx, re.DOTALL):
    print(m.group(0)[:200])

print('dashboard.html nav elements:')
for m in re.finditer(r'<nav[^>]*>.*?</nav>', text_dash, re.DOTALL):
    print(m.group(0)[:200])

for m in re.finditer(r'class="[^"]*nav[^"]*"', text_dash):
    print('class with nav:', m.group(0))
