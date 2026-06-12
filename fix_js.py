import re

with open('customer_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

content = content.replace(
    '.chip.active { background:var(--primary); color:var(--text-primary);',
    '.chip.active { background:var(--primary); color:var(--on-primary);'
)

with open('customer_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(content)

with open('customer_mobile/www/js/app.js', 'r', encoding='latin-1') as f:
    js_content = f.read()

js_old = '''  var tabs = document.querySelectorAll('#bookingFilterTabs button');
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].style.background = 'transparent';
    tabs[i].style.color = '#52525b';
  }
  if (btn) {
    btn.style.background = 'linear-gradient(135deg,#dc2626,#9b1a1a)';
    btn.style.color = '#fff';
  }'''

js_new = '''  var tabs = document.querySelectorAll('#bookingFilterTabs button');
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].style.background = 'var(--bg-card)';
    tabs[i].style.color = 'var(--text-secondary)';
    tabs[i].style.borderColor = 'var(--border)';
  }
  if (btn) {
    btn.style.background = 'var(--primary)';
    btn.style.color = 'var(--on-primary)';
    btn.style.borderColor = 'var(--primary)';
  }'''

js_content = js_content.replace(js_old, js_new)

# Also fix the booking item badges in app.js
# Usually "Confirmed" badge uses #dc2626 or something? Let's check app.js for hardcoded badges
def replace_badges(match):
    # Just in case, if they have hardcoded reds for confirmed
    pass

with open('customer_mobile/www/js/app.js', 'w', encoding='latin-1') as f:
    f.write(js_content)

print("Updated app.js and chip CSS successfully")
