with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for j in range(13680, 13780):
    print(f'{j+1}: {lines[j]}', end='')
