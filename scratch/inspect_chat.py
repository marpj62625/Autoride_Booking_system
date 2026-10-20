with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'id="chat"' in line or 'ac-input-bar' in line or 'acInputBar' in line or 'id="adminChatContent"' in line or 'adminChatContent' in line:
            print(f'{i+1}: {line.strip()[:100]}')
