import re

with open('customer_mobile/www/index.html', 'r', encoding='latin-1') as f:
    html = f.read()

# 1. Update Header to have the Back Chevron
header_old = '''<div style="padding:16px 20px 12px; text-align:center;">
    <h1 style="font-size:1.4rem;font-weight:800;color:var(--text-primary);">My Bookings</h1>
  </div>'''

header_new = '''<div style="padding:16px 20px 12px; display:flex; align-items:center; justify-content:center; position:relative;">
    <i class="fas fa-chevron-left" style="position:absolute; left:20px; color:var(--primary); font-size:1.2rem; cursor:pointer;" onclick="showPage('page-home')"></i>
    <h1 style="font-size:1.2rem;font-weight:800;color:var(--text-primary);">My Bookings</h1>
  </div>'''

html = html.replace(header_old, header_new)

# 2. Update bookingFilterTabs to segmented control
tabs_old = '''<div style="display:flex;gap:8px;padding:4px 0;overflow-x:auto;scrollbar-width:none;" id="bookingFilterTabs">
      <button onclick="filterBookingsList('all',this)" style="flex:none;padding:6px 16px;border-radius:20px;border:1px solid var(--primary);font-size:0.75rem;font-weight:600;background:var(--primary);color:var(--on-primary);cursor:pointer;">All</button>
      <button onclick="filterBookingsList('Confirmed',this)" style="flex:none;padding:6px 16px;border-radius:20px;border:1px solid var(--border);font-size:0.75rem;font-weight:600;background:var(--bg-card);color:var(--text-secondary);cursor:pointer;">Active</button>
      <button onclick="filterBookingsList('Completed',this)" style="flex:none;padding:6px 16px;border-radius:20px;border:1px solid var(--border);font-size:0.75rem;font-weight:600;background:var(--bg-card);color:var(--text-secondary);cursor:pointer;">Done</button>
      <button onclick="filterBookingsList('Cancelled',this)" style="flex:none;padding:6px 16px;border-radius:20px;border:1px solid var(--border);font-size:0.75rem;font-weight:600;background:var(--bg-card);color:var(--text-secondary);cursor:pointer;">Cancelled</button>
    </div>'''

tabs_new = '''<div style="display:flex;border:1px solid var(--border);border-radius:24px;overflow:hidden;margin:16px;background:var(--bg-card);" id="bookingFilterTabs">
      <button onclick="filterBookingsList('all',this)" style="flex:1;padding:10px 0;border:none;background:var(--primary);color:#fff;font-size:0.75rem;font-weight:600;cursor:pointer;border-right:1px solid var(--border);">All</button>
      <button onclick="filterBookingsList('Confirmed',this)" style="flex:1;padding:10px 0;border:none;background:transparent;color:var(--text-secondary);font-size:0.75rem;font-weight:600;cursor:pointer;border-right:1px solid var(--border);">Active</button>
      <button onclick="filterBookingsList('Completed',this)" style="flex:1;padding:10px 0;border:none;background:transparent;color:var(--text-secondary);font-size:0.75rem;font-weight:600;cursor:pointer;border-right:1px solid var(--border);">Done</button>
      <button onclick="filterBookingsList('Cancelled',this)" style="flex:1;padding:10px 0;border:none;background:transparent;color:var(--text-secondary);font-size:0.75rem;font-weight:600;cursor:pointer;">Cancelled</button>
    </div>'''

html = html.replace(tabs_old, tabs_new)

with open('customer_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(html)

with open('customer_mobile/www/js/app.js', 'r', encoding='latin-1') as f:
    js = f.read()

# Update JS for segmented control
js_tabs_old = '''  var tabs = document.querySelectorAll('#bookingFilterTabs button');
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

js_tabs_new = '''  var tabs = document.querySelectorAll('#bookingFilterTabs button');
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].style.background = 'transparent';
    tabs[i].style.color = 'var(--text-secondary)';
  }
  if (btn) {
    btn.style.background = 'var(--primary)';
    btn.style.color = '#fff';
  }'''

js = js.replace(js_tabs_old, js_tabs_new)

# Update renderBookingsList
# It has a block starting from return '<div style="background:#2a2a2a;... and ending at '</div></div>';
old_render_block = r'''    return '<div style="background:#2a2a2a;border:1px solid rgba\(255,255,255,0\.12\);border-radius:20px;overflow:hidden;margin-bottom:14px;cursor:pointer;box-shadow:0 4px 16px rgba\(0,0,0,0\.4\);" onclick="openBookingDetail\(' \+ b\.id \+ '\)">' \+
      '<div style="height:4px;background:' \+ color \+ ';"></div>' \+
      '<div style="padding:16px;">' \+

      /\* Header row: icon \+ name \+ status badge \*/
      '<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">' \+
      '<div style="width:48px;height:48px;border-radius:14px;background:#3a3a3a;display:flex;align-items:center;justify-content:center;flex-shrink:0;">' \+
      '<i class="fas fa-car" style="color:#888;font-size:1\.2rem;"></i></div>' \+
      '<div style="flex:1;min-width:0;">' \+
      '<div style="font-weight:700;font-size:0\.95rem;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' \+ vehicleName \+ '</div>' \+
      \(vehicleSub \? '<div style="font-size:0\.72rem;color:#999;margin-top:2px;">' \+ vehicleSub \+ '</div>' : ''\) \+
      '</div>' \+
      '<span style="padding:4px 10px;border-radius:20px;font-size:0\.65rem;font-weight:700;letter-spacing:0\.3px;background:' \+ color \+ '33;color:' \+ color \+ ';flex-shrink:0;border:1px solid ' \+ color \+ '66;">' \+ b\.status \+ '</span>' \+
      '</div>' \+

      /\* Date row \*/
      '<div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;margin-bottom:14px;">' \+
      '<div style="background:#3a3a3a;border-radius:12px;padding:10px 12px;">' \+
      '<div style="font-size:0\.58rem;color:#999;font-weight:600;text-transform:uppercase;letter-spacing:0\.6px;margin-bottom:3px;">Pick-up</div>' \+
      '<div style="font-size:0\.8rem;font-weight:700;color:#fff;">' \+ startFmt \+ '</div>' \+
      '</div>' \+
      '<div style="color:#666;font-size:0\.8rem;font-weight:700;">-&gt;</div>' \+
      '<div style="background:#3a3a3a;border-radius:12px;padding:10px 12px;text-align:right;">' \+
      '<div style="font-size:0\.58rem;color:#999;font-weight:600;text-transform:uppercase;letter-spacing:0\.6px;margin-bottom:3px;">Return</div>' \+
      '<div style="font-size:0\.8rem;font-weight:700;color:#fff;">' \+ endFmt \+ '</div>' \+
      '</div>' \+
      '</div>' \+

      /\* Footer row: payment badge \+ price \*/
      '<div style="display:flex;align-items:center;justify-content:space-between;padding-top:12px;border-top:1px solid rgba\(255,255,255,0\.08\);">' \+
      '<span style="padding:4px 10px;border-radius:20px;font-size:0\.65rem;font-weight:700;background:' \+ payColor \+ '33;color:' \+ payColor \+ ';border:1px solid ' \+ payColor \+ '66;">' \+ \(b\.payment_status \|\| 'Unpaid'\) \+ '</span>' \+
      '<div style="font-weight:800;font-size:1rem;color:#fff;">' \+ formatPHP\(b\.total_price\) \+ '</div>' \+
      '</div>' \+

      '</div></div>';'''

new_render_block = r'''    return '<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;margin:0 16px 14px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,0.05);" onclick="openBookingDetail(' + b.id + ')">' +
      '<div style="padding:16px;">' +
      
      /* Header row: icon + name + status badge */
      '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">' +
        '<div style="display:flex;align-items:center;gap:12px;">' +
          '<div style="width:40px;height:40px;border-radius:50%;background:rgba(0,177,79,0.1);display:flex;align-items:center;justify-content:center;flex-shrink:0;">' +
            '<i class="fas fa-car" style="color:var(--primary);font-size:1.2rem;"></i>' +
          '</div>' +
          '<div style="flex:1;min-width:0;">' +
            '<div style="font-weight:700;font-size:1rem;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + vehicleName + '</div>' +
            (vehicleSub ? '<div style="font-size:0.75rem;color:var(--text-muted);margin-top:2px;">' + vehicleSub + '</div>' : '') +
          '</div>' +
        '</div>' +
        '<span style="padding:6px 12px;border-radius:6px;font-size:0.75rem;font-weight:600;background:' + color + ';color:#fff;flex-shrink:0;">' + b.status + '</span>' +
      '</div>' +

      '<div style="border-top:1px solid var(--border);margin-bottom:16px;"></div>' +

      /* Date row */
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
      '</div>' +

      '<div style="border-top:1px solid var(--border);margin-bottom:16px;"></div>' +

      /* Footer row: payment badge + price */
      '<div style="display:flex;align-items:center;justify-content:space-between;">' +
        '<span style="padding:6px 12px;border-radius:6px;font-size:0.75rem;font-weight:600;background:' + payColor + ';color:#fff;">' + (b.payment_status || 'Unpaid') + '</span>' +
        '<div style="font-weight:800;font-size:1.1rem;color:var(--primary);">' + formatPHP(b.total_price) + '</div>' +
      '</div>' +

      '</div></div>';'''

# I'll just use a regex substitution
js = re.sub(old_render_block, new_render_block, js)

with open('customer_mobile/www/js/app.js', 'w', encoding='latin-1') as f:
    f.write(js)

print("Updated Bookings to Light Mode / Grab Theme")
