import sys

filepath = 'customer_mobile/www/js/app.js'

with open(filepath, 'r', encoding='latin-1') as f:
    content = f.read()

old = "    if (h === 'localhost' || h === '127.0.0.1') return 'http://localhost:5000/api';"
new = "    if ((h === 'localhost' || h === '127.0.0.1') && !(window.Capacitor && window.Capacitor.isNative)) return 'http://localhost:5000/api';"

if old in content:
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='latin-1') as f:
        f.write(content)
    print('SUCCESS: Fixed API_BASE localhost check to skip on native Capacitor')
else:
    print('ERROR: Target string not found - may already be fixed')
    sys.exit(1)
