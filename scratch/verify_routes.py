# Verify frontend URL matches backend route
api_base = "https://autoride-booking-system.vercel.app/api"

# Frontend calls (after fix):
frontend_get = api_base + "/user/license-details?user_id=123"
frontend_post = api_base + "/user/license-details"

print("Frontend GET URL:", frontend_get)
print("Frontend POST URL:", frontend_post)

# Backend routes:
with open('backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
routes = re.findall(r"@app\.route\('([^']*license[^']*)'", content)
for r in routes:
    print("Backend route:", r)
    
# Check if they match
print()
# The Vercel serverless function strips the /api prefix and maps to Flask routes
# So frontend /api/user/license-details -> Flask /api/user/license-details
print("Frontend expects Flask route: /api/user/license-details")
if "/api/user/license-details" in [r.split(',')[0] for r in routes]:
    print("MATCH - Backend has this route")
else:
    print("MISMATCH - Check routes!")
    for r in routes:
        print(f"  Available: {r}")
