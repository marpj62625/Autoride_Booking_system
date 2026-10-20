import re

with open('AutorideSystem/frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'<div\s+[^>]*id=["\']([^"\']+)["\'][^>]*class=["\']([^"\']+)["\']', text)
for mid, mcls in matches:
    if any(k in mcls for k in ['overlay', 'modal', 'page']):
        print(f'{mid}: {mcls}')
