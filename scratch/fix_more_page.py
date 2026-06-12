# -*- coding: utf-8 -*-
"""Apply More page desktop grid CSS."""

with open('frontend/index.html', 'r', encoding='latin-1') as f:
    html = f.read()

# Find and replace the More constrain-width rule
old_marker = html.find('/* \x3f\x3f More: constrain width \x3f\x3f */')
if old_marker == -1:
    print('Marker not found, trying alternate')
    old_marker = html.find('#page-more .scroll-content {\n            max-width: 640px')
    if old_marker == -1:
        print('FAILED to find target')
        raise SystemExit(1)

# Find end of this CSS block
block_end = html.find('\n\n          ', old_marker) + 2
old_block = html[old_marker:block_end]
print('Replacing block at', old_marker, '->', block_end)
print('OLD:', repr(old_block[:80]))

new_block = (
    '/* More page: desktop grid layout */\n'
    '          #page-more .scroll-content {\n'
    '            max-width: none;\n'
    '            padding: 32px 36px;\n'
    '          }\n'
    '\n'
    '          /* Greeting banner */\n'
    '          .more-greeting-banner {\n'
    '            display: flex;\n'
    '            align-items: center;\n'
    '            padding: 28px 32px;\n'
    '            background: linear-gradient(135deg, rgba(0,177,79,0.06), rgba(0,177,79,0.02));\n'
    '            border: 1px solid rgba(0,177,79,0.12);\n'
    '            border-radius: 20px;\n'
    '            margin-bottom: 28px;\n'
    '          }\n'
    '\n'
    '          /* 2x2 grid */\n'
    '          .more-grid {\n'
    '            display: grid;\n'
    '            grid-template-columns: repeat(2, 1fr);\n'
    '            gap: 16px;\n'
    '          }\n'
    '\n'
    '          /* Desktop card: vertical */\n'
    '          .more-card {\n'
    '            flex-direction: column;\n'
    '            align-items: flex-start;\n'
    '            padding: 28px 24px 24px;\n'
    '            border-radius: 20px;\n'
    '            border: 1px solid var(--border-light);\n'
    '            box-shadow: 0 2px 12px rgba(0,0,0,0.06);\n'
    '            gap: 16px;\n'
    '            margin-bottom: 0;\n'
    '            transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;\n'
    '          }\n'
    '\n'
    '          .more-card:hover {\n'
    '            transform: translateY(-3px);\n'
    '            box-shadow: 0 8px 24px rgba(0,0,0,0.1);\n'
    '            border-color: var(--primary);\n'
    '          }\n'
    '\n'
    '          .more-card-icon { width: 56px; height: 56px; border-radius: 16px; }\n'
    '          .more-card-body h4 { font-size: 1.05rem; font-weight: 800; }\n'
    '          .more-card-body p { font-size: 0.85rem; line-height: 1.4; }\n'
    '          .more-card-arrow { display: none; }\n'
    '          .more-signout-mobile { display: none !important; }\n'
    '\n'
    '          '
)

html = html[:old_marker] + new_block + html[block_end:]

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Done. File size:', len(html))
