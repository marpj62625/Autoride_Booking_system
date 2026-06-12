with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# 1. Fix Staff modal Cancel button (line 1741)
content = content.replace(
    'background: var(--surface); border: 1px solid var(--border); border-radius: 10px; color: white; font-weight: 600;\">Cancel</button>',
    'background: transparent; border: 1px solid var(--border); border-radius: 10px; color: var(--text-secondary); font-weight: 600;\">Cancel</button>'
)

# 2. Fix Vehicle modal Cancel button (line 1917) - light gray bg in dark mode
content = content.replace(
    'style=\"flex:1;padding:16px;background:#f1f5f9;border:1.5px solid #e2e8f0;border-radius:14px;color:#475569;font-size:1rem;font-weight',
    'style=\"flex:1;padding:16px;background:transparent;border:1.5px solid var(--border);border-radius:14px;color:var(--text-secondary);font-size:1rem;font-weight'
)

# 3. Fix Change Password modal Cancel button (line 1944)
content = content.replace(
    'background: var(--surface); border: 1px solid var(--border); border-radius: 10px; color: white; font-weight: 600;\">Cancel</button>',
    'background: transparent; border: 1px solid var(--border); border-radius: 10px; color: var(--text-secondary); font-weight: 600;\">Cancel</button>'
)

# 4. Fix Assign Driver Cancel button (line 1496)
content = content.replace(
    'background: #334155; border: none; border-radius: 10px; color: white; font-weight: 600;\">Cancel</button>',
    'background: transparent; border: 1px solid var(--border); border-radius: 10px; color: var(--text-secondary); font-weight: 600;\">Cancel</button>'
)

# 5. Fix Cancel Booking button (line 3283)
content = content.replace(
    'background: #475569; border: none; color: white;\">Cancel Booking</button>',
    'background: transparent; border: 1px solid var(--border); color: var(--text-secondary);\">Cancel Booking</button>'
)

# 6. Fix any remaining #f1f5f9 (light mode gray backgrounds that look white in dark mode)
# These are likely input backgrounds or card backgrounds - let's check what they are
import re
lines = content.split('\\n')
for i, line in enumerate(lines):
    if '#f1f5f9' in line and ('input' in line.lower() or 'select' in line.lower() or 'background' in line.lower()):
        pass  # We'll handle these contextually

# 7. Fix input/select backgrounds that show as white blocks
# The inputs in vehicle modal use #f1f5f9 which looks white in dark mode
content = content.replace('background:#f1f5f9;border:1.5px solid #e2e8f0;border-radius:12px;color:#0f172a;', 'background:var(--bg-input, var(--surface-container));border:1.5px solid var(--border);border-radius:12px;color:var(--text-primary);')
content = content.replace('background: #f1f5f9;border:1.5px solid #e2e8f0;border-radius:12px;color:#0f172a;', 'background:var(--bg-input, var(--surface-container));border:1.5px solid var(--border);border-radius:12px;color:var(--text-primary);')
content = content.replace('background:#f1f5f9; border:1.5px solid #e2e8f0; border-radius:12px; color:#0f172a;', 'background:var(--bg-input, var(--surface-container));border:1.5px solid var(--border);border-radius:12px;color:var(--text-primary);')

# 8. Also fix any remaining #0f172a text colors (hardcoded dark text)
content = content.replace('color:#0f172a', 'color:var(--text-primary)')
content = content.replace('color: #0f172a', 'color: var(--text-primary)')

# 9. Fix #334155 backgrounds
content = content.replace('background:#334155', 'background:var(--surface-container)')
content = content.replace('background: #334155', 'background: var(--surface-container)')

# 10. Fix #e2e8f0 borders
content = content.replace('border-color: #e2e8f0', 'border-color: var(--border)')
content = content.replace('border:1.5px solid #e2e8f0', 'border:1.5px solid var(--border)')
content = content.replace('border: 1.5px solid #e2e8f0', 'border: 1.5px solid var(--border)')
content = content.replace('border:1px solid #e2e8f0', 'border:1px solid var(--border)')

with open('admin_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(content)

print('Fixed all Cancel buttons, inputs, and hardcoded light-mode colors')
