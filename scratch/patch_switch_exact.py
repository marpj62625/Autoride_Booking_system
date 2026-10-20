file_path = 'admin_app/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

target = """                if (mainContentEl) {
                    if (tabId === 'fleet-calendar' && window.innerWidth >= 769) {
                        mainContentEl.style.overflowY = 'hidden';
                    } else {
                        mainContentEl.style.overflowY = '';
                    }
                }"""

replacement = """                if (mainContentEl) {
                    mainContentEl.scrollTo({ top: 0, behavior: 'instant' });
                    // Lock overflow ONLY on true desktop monitors (width >= 769 AND height >= 600)
                    if (tabId === 'fleet-calendar' && window.innerWidth >= 769 && window.innerHeight >= 600) {
                        mainContentEl.style.overflowY = 'hidden';
                    } else {
                        mainContentEl.style.overflowY = 'auto';
                    }
                }"""

if target in text:
    text = text.replace(target, replacement)
    print("Successfully patched switchTab overflow & scroll reset!")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
else:
    print("FAILED to find exact target")
