import re

with open('customer_mobile/www/js/app.js', 'r', encoding='latin-1') as f:
    js = f.read()

# Fix Header Row Overflow
old_header = '''      /* Header row: icon + name + status badge */
      '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">' +
        '<div style="display:flex;align-items:center;gap:12px;">' +'''

new_header = '''      /* Header row: icon + name + status badge */
      '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;gap:12px;">' +
        '<div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0;">' +'''

js = js.replace(old_header, new_header)


# Fix Date Row Wrapping
old_date = '''      /* Date row */
      '<div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;margin-bottom:16px;">' +
        '<div>' +
          '<div style="font-size:0.6rem;color:var(--text-muted);font-weight:600;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;">Pick-up</div>' +
          '<div style="font-size:0.85rem;font-weight:700;color:var(--text-primary);">' + startFmt + '</div>' +
        '</div>' +
        '<div style="color:var(--text-muted);font-size:0.9rem;font-weight:400;margin-top:14px;">&rarr;</div>' +
        '<div>' +
          '<div style="font-size:0.6rem;color:var(--text-muted);font-weight:600;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;">Return</div>' +
          '<div style="font-size:0.85rem;font-weight:700;color:var(--text-primary);">' + endFmt + ' <i class="fas fa-chevron-right" style="font-size:0.7rem;margin-left:4px;color:var(--text-muted);"></i></div>' +
        '</div>' +
      '</div>' +'''

new_date = '''      /* Date row */
      '<div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;margin-bottom:16px;">' +
        '<div style="min-width:0;">' +
          '<div style="font-size:0.6rem;color:var(--text-muted);font-weight:600;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;white-space:nowrap;">Pick-up</div>' +
          '<div style="font-size:0.85rem;font-weight:700;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + startFmt + '</div>' +
        '</div>' +
        '<div style="color:var(--text-muted);font-size:0.9rem;font-weight:400;margin-top:14px;text-align:center;">&rarr;</div>' +
        '<div style="min-width:0;">' +
          '<div style="font-size:0.6rem;color:var(--text-muted);font-weight:600;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;white-space:nowrap;">Return</div>' +
          '<div style="display:flex;align-items:center;gap:4px;font-size:0.85rem;font-weight:700;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"><span>' + endFmt + '</span><i class="fas fa-chevron-right" style="font-size:0.7rem;color:var(--text-muted);flex-shrink:0;"></i></div>' +
        '</div>' +
      '</div>' +'''

js = js.replace(old_date, new_date)

with open('customer_mobile/www/js/app.js', 'w', encoding='latin-1') as f:
    f.write(js)

print("Fixed flexbox truncating and wrapping bugs")
