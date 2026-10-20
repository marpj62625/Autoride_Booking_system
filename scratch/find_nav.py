with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

m = text.find('drawer-item')
print('drawer-item at:', m)
print(text[m-50:m+1200])

m2 = text.find('nav-item')
print('nav-item at:', m2)
print(text[m2-50:m2+1200])
