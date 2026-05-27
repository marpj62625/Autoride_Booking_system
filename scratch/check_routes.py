import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

routes = re.findall(r"@app\.route\('(/[^']+)'", content)
api_routes = [r for r in routes if r.startswith('/api/')]
no_api_routes = [r for r in routes if not r.startswith('/api/')]

print(f"Routes with /api prefix: {len(api_routes)}")
print(f"Routes without /api prefix: {len(no_api_routes)}")
print()
print("Sample routes WITHOUT /api:")
for r in no_api_routes[:10]:
    print(f"  {r}")
print()
print("ALL routes WITH /api:")
for r in api_routes:
    print(f"  {r}")
