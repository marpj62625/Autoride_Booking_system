import re

with open('backend/app.py', encoding='utf-8') as f:
    text = f.read()

routes = re.findall(r"@app\.route\('([^']*)'", text)
user_routes = [r for r in routes if 'user' in r]
print("User routes:")
for r in sorted(set(user_routes)):
    print(" ", r)

# Also find where customer tab is populated in admin_app
with open('admin_app/index.html', encoding='utf-8') as f:
    admin_text = f.read()

admin_routes = re.findall(r"fetch\([`'\"]([^`'\"]*users[^`'\"]*)[`'\"]", admin_text)
print("\nAdmin fetches:")
for r in sorted(set(admin_routes)):
    print(" ", r)
