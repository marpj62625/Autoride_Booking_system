import re

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update .mobile-header
# Let's find .mobile-header block
m = re.search(r'\.mobile-header\s*\{([^}]+)\}', content)
if m:
    print("Found .mobile-header:", m.group(0)[:120])
else:
    print("WARNING: .mobile-header not found")

# 2. Update .main-content
m = re.search(r'\.main-content\s*\{([^}]+)\}', content)
if m:
    print("Found .main-content:", m.group(0)[:120])

# 3. Update .bottom-nav
m = re.search(r'\.bottom-nav\s*\{([^}]+)\}', content)
if m:
    print("Found .bottom-nav:", m.group(0)[:120])

# 4. Check switchTab fleet-calendar
m = re.search(r"if\s*\(tabId\s*===\s*'fleet-calendar'\s*&&\s*window\.innerWidth\s*>=\s*769\)", content)
if m:
    print("Found switchTab fleet-calendar check")
