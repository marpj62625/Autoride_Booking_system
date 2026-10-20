import re

with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

for m in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.DOTALL):
    s = m.group(1)
    print(f'Inline style block of length {len(s)}')
    for term in ['.bottom-nav', '.page', '.header', 'fixed', 'padding-bottom']:
        if term in s:
            print(f'  contains {term}')
