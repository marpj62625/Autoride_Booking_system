with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

old_marker = '${isApprovable ?'
idx = content.find(old_marker)
if idx == -1:
    print('ERROR: marker not found')
else:
    line_start = content.rfind('\n', 0, idx)
    indent = content[line_start+1:idx]
    print(f'Found marker at char {idx}, indent: [{indent[:20]}...]')
    print(f'Line number: {content[:idx].count(chr(10))+1}')

