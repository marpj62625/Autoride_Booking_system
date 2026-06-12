
SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5ZGZzZ2pybG93cnJ0bG1lZndxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTAyOTA1NywiZXhwIjoyMDkwNjA1MDU3fQ.mMZth_DpbilzCsDJhriyP6ZKb8pM5PSyhgLfgGA-5Ww'

# 1. Update config.py to add SUPABASE_SERVICE_KEY
with open('backend/config.py', 'r', encoding='utf-8', errors='ignore') as f:
    config = f.read()

old_key_line = "SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5ZGZzZ2pybG93cnJ0bG1lZndxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUwMjkwNTcsImV4cCI6MjA5MDYwNTA1N30.m94HHMC7852zw9xfkkOYTPY1IzoH_kNPLYpTe0myGB4')"
new_key_lines = old_key_line + f"\nSUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '{SERVICE_ROLE_KEY}')"

if old_key_line in config:
    config = config.replace(old_key_line, new_key_lines)
    with open('backend/config.py', 'w', encoding='utf-8') as f:
        f.write(config)
    print('config.py updated!')
else:
    print('config.py: target not found')

# 2. Update app.py to use SUPABASE_SERVICE_KEY for storage uploads
with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    app_content = f.read()

old_auth = """            from config import SUPABASE_URL, SUPABASE_KEY
            _auth_headers = {
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'apikey': SUPABASE_KEY
            }"""

new_auth = """            from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
            _auth_headers = {
                'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
                'apikey': SUPABASE_SERVICE_KEY
            }"""

if old_auth in app_content:
    app_content = app_content.replace(old_auth, new_auth)
    with open('backend/app.py', 'w', encoding='utf-8') as f:
        f.write(app_content)
    print('app.py updated!')
else:
    print('app.py: target not found')
    # Count occurrences
    count = app_content.count('from config import SUPABASE_URL, SUPABASE_KEY')
    print(f'Found {count} occurrences of old import')
