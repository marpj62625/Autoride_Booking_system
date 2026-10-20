with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

for m in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.DOTALL):
    s = m.group(1)
    if 'fleet-calendar' in s or '.fc-' in s:
        print(f"Style block at char {m.start()} of len {len(s)} has fleet-calendar rules:")
        for line in s.splitlines():
            if 'fleet-calendar' in line or '.fc-' in line or 'overflow' in line:
                print("  ", line.strip()[:100])
