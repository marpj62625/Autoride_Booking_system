with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

target = "tabId === 'activity'"
m = text.find(target)
print('tabId === activity at:', m)
if m != -1:
    line_no = text[:m].count('\n') + 1
    print('Line:', line_no)
    print(text[m-20:m+200])
