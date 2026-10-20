with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('id="desktopCameraModal"')
print('Position of desktopCameraModal:', pos)

# Find what parent pages or overlays surround this position
# Check for occurrences of class="page" or class="overlay" or id="page-
import re
pages = list(re.finditer(r'<div[^>]+id=[\'"]([^\'"]+)[\'"][^>]*class=[\'"]([^\'"]+)[\'"]', text[:pos]))
for p in pages[-15:]:
    print(p.group(0)[:120])
