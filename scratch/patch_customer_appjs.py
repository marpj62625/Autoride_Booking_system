files = ['customer_mobile/www/js/app.js', 'frontend/js/app.js']

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    target = "target.classList.add('active');"
    replacement = "target.classList.add('active');\n  try { window.scrollTo({ top: 0, behavior: 'instant' }); } catch(e) {}"

    if target in content:
        content = content.replace(target, replacement, 1) # only in showPage
        print(f"[{file_path}] Patched showPage scroll-to-top")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        print(f"[{file_path}] WARNING: target not matched")
