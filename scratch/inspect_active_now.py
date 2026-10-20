with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(24653, 24750):
    if lines[i].strip():
        print(f'{i+1}: {lines[i]}', end='')
