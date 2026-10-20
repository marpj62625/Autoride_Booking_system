with open('customer_mobile/www/style.css', 'r', encoding='utf-8') as f:
    text_cm = f.read()

with open('frontend/style.css', 'r', encoding='utf-8') as f:
    text_fe = f.read()

print('customer_mobile/www/style.css length:', len(text_cm))
print('frontend/style.css length:', len(text_fe))

for name, t in [('customer_mobile', text_cm), ('frontend', text_fe)]:
    print(f'=== {name} ===')
    for term in ['bottom-nav', 'header', 'safe-area', 'padding-bottom', '@media']:
        count = t.count(term)
        print(f'  {term}: {count}')
