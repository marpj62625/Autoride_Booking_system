with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# Fix vehicle image upload labels (line 1765, 1768) - light gray bg that looks white in dark mode
content = content.replace(
    'background:#f1f5f9;border:1.5px solid var(--border);border-radius:14px;color:#475569;',
    'background:var(--surface-container);border:1.5px solid var(--border);border-radius:14px;color:var(--text-secondary);'
)

# Fix inspection inputs (lines 3248-3259) - hardcoded #0f172a
content = content.replace(
    'background: #0f172a; color: white; border: 1px solid var(--border);',
    'background: var(--surface-container); color: var(--text-primary); border: 1px solid var(--border);'
)

# Fix #334155 backgrounds (used in various elements)
content = content.replace('background:#334155;', 'background:var(--surface-container);')
content = content.replace('background: #334155;', 'background: var(--surface-container);')
content = content.replace('color:#334155;', 'color:var(--text-primary);')
content = content.replace('color: #334155;', 'color: var(--text-primary);')

# Fix #1e293b backgrounds
content = content.replace('background:#1e293b;', 'background:var(--surface-container);')
content = content.replace('background: #1e293b;', 'background: var(--surface-container);')
content = content.replace('#1e293b 0%', 'var(--surface-container) 0%')
content = content.replace('#0f172a 100%', 'var(--surface) 100%')

# Fix remaining #475569 colors  
content = content.replace('color:#475569;', 'color:var(--text-secondary);')
content = content.replace('color: #475569;', 'color: var(--text-secondary);')

# Fix remaining #64748b
content = content.replace('color:#64748b;', 'color:var(--text-muted);')
content = content.replace('color: #64748b;', 'color: var(--text-muted);')

with open('admin_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(content)

print('Fixed all remaining hardcoded colors')

# Final count
import re
for color in ['#f1f5f9', '#e2e8f0', '#334155', '#475569', '#0f172a', '#1e293b', '#64748b']:
    count = content.count(color)
    if count > 0:
        print(f'  {color}: {count} remaining')
