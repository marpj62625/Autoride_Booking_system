with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'id="activity"'
m = text.find(target)
print('id="activity" at:', m)
if m != -1:
    line_no = text[:m].count('\n') + 1
    print('Line:', line_no)
    print(text[m:m+600])
