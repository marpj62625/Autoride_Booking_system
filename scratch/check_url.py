import re

with open('customer_mobile/www/js/app.js', 'r', encoding='latin-1') as f:
    content = f.read()

# Find API_BASE
m = re.search(r"API_BASE\s*=\s*['\"]([^'\"]+)['\"]", content)
if m:
    api_base = m.group(1)
    print(f"API_BASE = {api_base}")
else:
    print("Could not find API_BASE")
    api_base = "???"

# Find the uploadFile call for license
idx = content.find("uploadFile('/api/user/license-details'")
if idx >= 0:
    print(f"PROBLEM FOUND: uploadFile('/api/user/license-details', fd)")
    print(f"  Resulting URL: {api_base}/api/user/license-details")
    print(f"  This has DOUBLE /api !")
else:
    idx2 = content.find("uploadFile('/user/license-details'")
    if idx2 >= 0:
        print(f"OK: uploadFile('/user/license-details', fd)")
        print(f"  Resulting URL: {api_base}/user/license-details")
    else:
        # Search more broadly
        for line_num, line in enumerate(content.splitlines(), 1):
            if 'uploadFile' in line and 'license' in line:
                print(f"Line {line_num}: {line.strip()}")
