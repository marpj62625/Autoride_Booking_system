with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '.page {' in l or '.page{' in l or '.bottom-nav {' in l or '.bottom-nav{' in l:
        print(f'{i+1}: {l.strip()[:100]}')
        for j in range(i, min(len(lines), i+10)):
            print(f'  {j+1}: {lines[j].strip()[:100]}')
