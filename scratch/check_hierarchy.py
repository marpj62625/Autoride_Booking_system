with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Check all parent elements of #fleet-calendar
# From body -> main -> #fleet-calendar -> .stat-card -> #fleetCalendarScrollContainer
print("=== CHECKING CSS HIERARCHY ===")
for sel in ['body', '.main-content', '.tab-content', '#fleet-calendar', '.stat-card', '#fleetCalendarScrollContainer']:
    m = re.search(re.escape(sel) + r'\s*\{([^}]+)\}', text)
    if m:
        print(f"{sel}:")
        for line in m.group(1).splitlines():
            line = line.strip()
            if any(k in line for k in ['height', 'overflow', 'position', 'touch', 'flex', 'padding']):
                print(f"  {line}")
    else:
        print(f"{sel}: not found in stylesheet")
