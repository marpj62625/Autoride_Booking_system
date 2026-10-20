import re

for path in ['admin_app/index.html', 'customer_mobile/www/index.html']:
    try:
        with open(path, encoding='utf-8') as f:
            text = f.read()
        links = re.findall(r'href=[\'"][^\'"]*\.apk[\'"]', text)
        print(f"{path}: {set(links)}")
    except Exception as e:
        print(f"{path}: {e}")
