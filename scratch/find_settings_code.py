import os

search_terms = ['Tap to send a test push', 'Manage system settings', 'superadmin', 'Push Notifications', 'Dark Mode']

for root, dirs, files in os.walk('admin_app'):
    for f in files:
        if f.endswith(('.html', '.js', '.css')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                for i, l in enumerate(lines):
                    for term in search_terms:
                        if term.lower() in l.lower():
                            print(f"{path}:{i+1} [{term}]: {l.strip()[:100]}")
