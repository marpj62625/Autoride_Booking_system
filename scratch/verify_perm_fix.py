import re

with open('admin_app/desktop.css', 'r', encoding='utf-8') as f:
    desktop_css = f.read()

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    index_html = f.read()

# 1. Verify desktop.css has no display: flex !important on .settings-action-card
m = re.search(r'\.settings-action-card\s*\{([^}]+)\}', desktop_css)
assert m, "Could not find .settings-action-card in desktop.css"
card_body = m.group(1)
assert 'display: flex !important' not in card_body, "ERROR: display: flex !important still present in .settings-action-card!"
assert 'display: flex;' in card_body, "ERROR: display: flex; missing in .settings-action-card!"
print("[PASS] desktop.css .settings-action-card display: flex is clean (no !important)")

# 2. Check override rules in desktop.css
assert 'html.role-super .locked-card' in desktop_css, "ERROR: html.role-super .locked-card missing in desktop.css"
assert 'html.role-super [id^="lockPerm_"]' in desktop_css, "ERROR: html.role-super [id^=\"lockPerm_\"] missing in desktop.css"
assert '.settings-action-card[style*="display: none"]' in desktop_css, "ERROR: display: none override missing in desktop.css"
print("[PASS] desktop.css has strict role and display:none overrides")

# 3. Check override rules in index.html
assert 'html.role-super .locked-card' in index_html, "ERROR: html.role-super .locked-card missing in index.html"
assert 'html.role-super [id^="lockPerm_"]' in index_html, "ERROR: html.role-super [id^=\"lockPerm_\"] missing in index.html"
print("[PASS] index.html has strict role and display:none overrides")

# 4. Check isSuperAdmin and applyRolePermissions in index.html
assert "admin@autoride.com" in index_html, "ERROR: admin@autoride.com fallback missing in isSuperAdmin"
assert "lockPerm_system_config" in index_html, "ERROR: lockPerm_system_config missing"
assert "setProperty('display', 'none', 'important')" in index_html, "ERROR: setProperty display none important missing in applyRolePermissions"
print("[PASS] isSuperAdmin and applyRolePermissions safeguards verified")

print("\nALL VERIFICATIONS PASSED!")
