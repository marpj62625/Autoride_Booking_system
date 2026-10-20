css_rules = """
/* Safe-area insets & responsive fluid layout */
:root {
  --sat: env(safe-area-inset-top, 0px);
  --sab: env(safe-area-inset-bottom, 0px);
  --sal: env(safe-area-inset-left, 0px);
  --sar: env(safe-area-inset-right, 0px);
}

html, body {
  max-width: 100vw;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

@media (max-width: 768px) {
  .container {
    padding-left: calc(1rem + var(--sal)) !important;
    padding-right: calc(1rem + var(--sar)) !important;
    box-sizing: border-box;
  }
}
"""

for path in ['customer_mobile/www/style.css', 'frontend/style.css']:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if '/* Safe-area insets & responsive fluid layout */' not in content:
        content += "\n" + css_rules
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[{path}] Appended safe-area & fluid layout rules")
    else:
        print(f"[{path}] Already contains rules")
