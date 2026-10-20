with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("File size:", len(text))
# Check required elements
assert 'calc(64px + env(safe-area-inset-top, 0px))' in text, "Missing safe area in mobile-header"
assert 'calc(76px + env(safe-area-inset-top, 0px))' in text, "Missing safe area in main-content"
assert 'calc(88px + env(safe-area-inset-bottom, 0px) + 24px)' in text, "Missing safe area in main-content padding-bottom"
assert 'calc(68px + env(safe-area-inset-bottom, 0px))' in text, "Missing safe area in bottom-nav"
assert 'mainContentEl.scrollTo({ top: 0, behavior: \'instant\' })' in text, "Missing switchTab scroll-to-top"
assert 'window.innerHeight >= 600' in text, "Missing switchTab landscape innerHeight guard"
assert 'Open Re-Authorize &amp; Email Tools' in text, "Missing button text"
assert 'max-width: 100%' in text, "Missing max-width on button"
print("ALL ADMIN_APP ASSERTIONS PASSED!")
