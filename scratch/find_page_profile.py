with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="page-profile"')
print('page-profile index:', idx)
print('Line:', text[:idx].count('\n') + 1)
print(text[idx:idx+300])
