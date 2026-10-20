with open('c:/Dev/AutorideSystem2sides/AutorideSystem/admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

m = text.find('id="settings"')
if m != -1:
    print('Found settings tab at char', m)
    # Find line number
    line_no = text[:m].count('\n') + 1
    print('Line number:', line_no)
    print(text[m:m+2500])
