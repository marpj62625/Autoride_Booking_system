with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for j in range(10619, 10650):
    print(f'{j+1}: {lines[j]}', end='')
