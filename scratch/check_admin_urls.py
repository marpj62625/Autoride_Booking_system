with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# Check for /api/admin references that should not have /api prefix
# The admin app uses API_BASE which already has /api
import re
matches = re.findall(r'(?:fetch|apiCall|apiFetch)\([^)]*(/api/admin/[^)]*)\)', content)
for m in matches:
    print(f"Found: {m}")

# Also check for ${API_BASE}/api pattern
api_base_matches = re.findall(r'\$\{API_BASE\}/api/', content)
print(f"\nFound {len(api_base_matches)} occurrences of ${{API_BASE}}/api/")

# Check what API_BASE is in admin
api_base_match = re.search(r"API_BASE\s*=\s*['\"]([^'\"]+)['\"]", content)
if api_base_match:
    print(f"Admin API_BASE: {api_base_match.group(1)}")

# Find the license-details fetch calls
lines = content.splitlines()
for i, line in enumerate(lines, 1):
    if 'license-details' in line and ('fetch' in line or 'api' in line.lower()):
        print(f"Line {i}: {line.strip()[:200]}")
