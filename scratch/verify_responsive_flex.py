with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open('admin_app/desktop.css', 'r', encoding='utf-8') as f:
    css = f.read()

# 1. Verify navTo('activity') and showTab
assert "onclick=\"navTo('activity')\"" in html, "ERROR: Security card onclick navTo('activity') missing!"
assert "window.showTab = navTo;" in html, "ERROR: window.showTab alias missing!"
print("[PASS] Security & Audit card navigation is connected to navTo('activity') and window.showTab alias is present.")

# 2. Verify no hardcoded 340px inline style on settings-layout-container
assert 'class="settings-layout-container" style="display: grid; grid-template-columns: 340px' not in html, "ERROR: Hardcoded inline grid still on container!"
assert 'class="settings-layout-container"' in html, "ERROR: settings-layout-container class missing!"
print("[PASS] Hardcoded inline grid styles removed from HTML markup.")

# 3. Verify responsive fluid CSS in index.html
assert "/* Mobile-First: 1-Column stacked by default */" in html, "ERROR: Mobile-first stacked comment missing"
assert "@media (min-width: 920px)" in html, "ERROR: min-width: 920px missing in index.html"
assert "@media (max-width: 500px)" in html, "ERROR: max-width: 500px missing in index.html"
print("[PASS] index.html has complete mobile-first responsive layout.")

# 4. Verify desktop.css responsive rules
assert "@media (min-width: 920px)" in css, "ERROR: min-width: 920px missing in desktop.css"
assert "@media (max-width: 919px)" in css, "ERROR: max-width: 919px missing in desktop.css"
print("[PASS] desktop.css has responsive 2-col/1-col media query separation.")

print("\nALL RESPONSIVE FLEXIBILITY VERIFICATIONS PASSED!")
