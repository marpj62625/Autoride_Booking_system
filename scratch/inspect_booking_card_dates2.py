with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(18880, 18940):
    if lines[i].strip():
        print(f'{i+1}: {lines[i]}', end='')
