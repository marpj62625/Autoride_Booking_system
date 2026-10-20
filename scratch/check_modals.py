import re

with open("frontend/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Find all overlay pages
overlays = re.findall(r'id=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*overlay-page[^"\']*["\']', content)
print("Overlay pages:", len(overlays))
for o in overlays:
    print("  overlay:", o)

# Find all elements with modal in id
modals = re.findall(r'id=["\']([^"\']*[Mm]odal[^"\']*)["\']', content)
print("Modals:", len(modals))
for m in modals:
    print("  modal:", m)
