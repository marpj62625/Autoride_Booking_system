with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'showPage' in l and ('=' in l or 'function' in l):
        print(f'{i+1}: {l.strip()[:100]}')
        for j in range(i, min(len(lines), i+15)):
            print(f'  {j+1}: {lines[j].strip()[:100]}')
        break
