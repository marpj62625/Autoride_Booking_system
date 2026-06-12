import re

with open('customer_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# 1. Fix Splash Screen
content = content.replace(
    '<div id="page-splash" style="display:flex;background:linear-gradient(160deg,#0052ff 0%,#0040CC 50%,#001a66 100%);',
    '<div id="page-splash" style="display:flex;background:linear-gradient(160deg,var(--primary-light) 0%,var(--primary) 50%,var(--primary-dark) 100%);'
)

# 2. Fix Home Banner
content = content.replace(
    '<div id="homeBanner" style="background:linear-gradient(160deg,#0052ff 0%,#0040CC 60%,#001a66 100%);',
    '<div id="homeBanner" style="background:linear-gradient(160deg,var(--primary-light) 0%,var(--primary) 60%,var(--primary-dark) 100%);'
)

# 3. Fix Quick Actions
quick_actions_old = '''<button onclick="showPage('page-vehicles')" style="background:none;border:none;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
        <div style="width:52px;height:52px;border-radius:18px;background:rgba(0,177,79,0.1);display:flex;align-items:center;justify-content:center;">
          <div style="width:32px;height:32px;border-radius:12px;background:var(--primary);display:flex;align-items:center;justify-content:center;"><i class="fas fa-car" style="color:var(--on-primary);font-size:0.875rem;"></i></div>
        </div>
        <span style="font-size:0.6rem;font-weight:600;color:var(--text-secondary);text-align:center;line-height:1.2;">Browse Cars</span>
      </button>
      <button onclick="showPage('page-bookings')" style="background:none;border:none;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
        <div style="width:52px;height:52px;border-radius:18px;background:rgba(0,177,79,0.1);display:flex;align-items:center;justify-content:center;">
          <div style="width:32px;height:32px;border-radius:12px;background:var(--primary);display:flex;align-items:center;justify-content:center;"><i class="fas fa-calendar-check" style="color:var(--text-primary);font-size:0.875rem;"></i></div>
        </div>
        <span style="font-size:0.6rem;font-weight:600;color:var(--text-secondary);text-align:center;line-height:1.2;">My Bookings</span>
      </button>
      <button onclick="showOverlay('page-support')" style="background:none;border:none;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
        <div style="width:52px;height:52px;border-radius:18px;background:rgba(0,177,79,0.1);display:flex;align-items:center;justify-content:center;">
          <div style="width:32px;height:32px;border-radius:12px;background:var(--primary);display:flex;align-items:center;justify-content:center;"><i class="fas fa-headset" style="color:var(--text-primary);font-size:0.875rem;"></i></div>
        </div>
        <span style="font-size:0.6rem;font-weight:600;color:var(--text-secondary);text-align:center;line-height:1.2;">Support</span>
      </button>
      <button onclick="showOverlay('page-livechat')" style="background:none;border:none;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
        <div style="position:relative;width:52px;height:52px;border-radius:18px;background:rgba(0,177,79,0.1);display:flex;align-items:center;justify-content:center;">
          <div style="width:32px;height:32px;border-radius:12px;background:var(--primary);display:flex;align-items:center;justify-content:center;"><i class="fas fa-comments" style="color:var(--text-primary);font-size:0.875rem;"></i></div>
          <span id="chatUnreadBadge" style="display:none;position:absolute;top:-4px;right:-4px;background:var(--danger);color:#fff;border-radius:50%;width:18px;height:18px;font-size:0.6rem;font-weight:700;align-items:center;justify-content:center;"></span>
        </div>
        <span style="font-size:0.6rem;font-weight:600;color:var(--text-secondary);text-align:center;line-height:1.2;">Live Chat</span>
      </button>'''

quick_actions_new = '''<button onclick="showPage('page-vehicles')" style="background:none;border:none;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
        <div style="width:52px;height:52px;border-radius:50%;background:var(--primary);display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,177,79,0.2);">
          <i class="fas fa-car" style="color:var(--on-primary);font-size:1.2rem;"></i>
        </div>
        <span style="font-size:0.6rem;font-weight:600;color:var(--text-secondary);text-align:center;line-height:1.2;">Browse Cars</span>
      </button>
      <button onclick="showPage('page-bookings')" style="background:none;border:none;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
        <div style="width:52px;height:52px;border-radius:50%;background:var(--primary);display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,177,79,0.2);">
          <i class="fas fa-calendar-check" style="color:var(--on-primary);font-size:1.2rem;"></i>
        </div>
        <span style="font-size:0.6rem;font-weight:600;color:var(--text-secondary);text-align:center;line-height:1.2;">My Bookings</span>
      </button>
      <button onclick="showOverlay('page-support')" style="background:none;border:none;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
        <div style="width:52px;height:52px;border-radius:50%;background:var(--primary);display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,177,79,0.2);">
          <i class="fas fa-headset" style="color:var(--on-primary);font-size:1.2rem;"></i>
        </div>
        <span style="font-size:0.6rem;font-weight:600;color:var(--text-secondary);text-align:center;line-height:1.2;">Support</span>
      </button>
      <button onclick="showOverlay('page-livechat')" style="background:none;border:none;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
        <div style="position:relative;width:52px;height:52px;border-radius:50%;background:var(--primary);display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,177,79,0.2);">
          <i class="fas fa-comments" style="color:var(--on-primary);font-size:1.2rem;"></i>
          <span id="chatUnreadBadge" style="display:none;position:absolute;top:0;right:0;background:var(--danger);color:#fff;border-radius:50%;width:16px;height:16px;font-size:0.55rem;font-weight:700;align-items:center;justify-content:center;border:2px solid var(--bg-card);"></span>
        </div>
        <span style="font-size:0.6rem;font-weight:600;color:var(--text-secondary);text-align:center;line-height:1.2;">Live Chat</span>
      </button>'''

content = content.replace(quick_actions_old, quick_actions_new)

# 4. Fix Pills
pills_old = '''.pill-confirmed { background:var(--primary); color:var(--on-primary); }
.pill-approved { background:var(--primary); color:var(--on-primary); }
.pill-picked-up { background:var(--primary); color:var(--on-primary); }
.pill-completed { background:var(--primary); color:var(--on-primary); }
.pill-cancelled { background:#f8d7da; color:#842029; }
.pill-rejected { background:#f8d7da; color:#842029; }
.pill-unpaid { background:#f8d7da; color:#842029; }
.pill-partially-paid { background:#fff3cd; color:#856404; }
.pill-paid { background:var(--primary); color:var(--on-primary); }'''

pills_new = '''.pill-confirmed { background:transparent; color:var(--primary); border:1px solid var(--primary); }
.pill-approved { background:transparent; color:var(--primary); border:1px solid var(--primary); }
.pill-picked-up { background:transparent; color:var(--primary); border:1px solid var(--primary); }
.pill-completed { background:transparent; color:var(--primary); border:1px solid var(--primary); }
.pill-cancelled { background:transparent; color:var(--danger); border:1px solid var(--danger); }
.pill-rejected { background:transparent; color:var(--danger); border:1px solid var(--danger); }
.pill-unpaid { background:transparent; color:var(--danger); border:1px solid var(--danger); }
.pill-partially-paid { background:transparent; color:var(--warning); border:1px solid var(--warning); }
.pill-paid { background:transparent; color:var(--primary); border:1px solid var(--primary); }'''

content = content.replace(pills_old, pills_new)

with open('customer_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(content)

print("Fixed hardcoded colors and UI properly")
