with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(32700, 32770):
    print(f'{i+1}: {lines[i]}', end='')
