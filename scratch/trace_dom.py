with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

pos_body = text.find('<body')
pos_modal = text.find('id="desktopCameraModal"')

body_sub = text[pos_body:pos_modal]

# Parse tags
tokens = re.finditer(r'<(/?[a-zA-Z0-9]+)([^>]*)>', body_sub)
stack = []
for t in tokens:
    tag = t.group(1).lower()
    attrs = t.group(2)
    if tag in ['input', 'img', 'br', 'hr', 'meta', 'link']:
        continue
    if tag.startswith('/'):
        tag_name = tag[1:]
        if stack and stack[-1]['tag'] == tag_name:
            stack.pop()
    else:
        # Check self closing
        if attrs.endswith('/'):
            continue
        id_match = re.search(r'id=[\'"]([^\'"]+)[\'"]', attrs)
        class_match = re.search(r'class=[\'"]([^\'"]+)[\'"]', attrs)
        style_match = re.search(r'style=[\'"]([^\'"]+)[\'"]', attrs)
        stack.append({
            'tag': tag,
            'id': id_match.group(1) if id_match else '',
            'class': class_match.group(1) if class_match else '',
            'style': style_match.group(1) if style_match else ''
        })

print("Parent stack for desktopCameraModal:")
for item in stack:
    print(item)
