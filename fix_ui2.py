import re

with open('customer_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# 1. Update Browse Vehicles header to Grab style
vehicles_old = '''<div style="padding:16px 20px 8px;display:flex;align-items:center;justify-content:space-between;">
    <div>
      <p style="font-size:0.75rem;color:var(--text-muted);font-weight:500;">Explore</p>
      <h1 style="font-size:1.6rem;font-weight:900;color:var(--text-primary);letter-spacing:-0.5px;">Vehicles</h1>
    </div>
    <button onclick="showOverlay('page-favorites')" style="width:40px;height:40px;border-radius:14px;background:var(--bg-card2);border:1px solid var(--border);color:#dc2626;font-size:1rem;cursor:pointer;position:relative;">
      <i class="fas fa-heart"></i>
    </button>
  </div>
  <div style="padding:0 16px 12px;position:relative;">
    <i class="fas fa-search" style="position:absolute;left:28px;top:50%;transform:translateY(-50%);color:var(--text-muted);font-size:0.875rem;"></i>
    <input type="text" id="vehicleSearch" placeholder="Search cars, brands, types..." oninput="searchVehicles(this.value)"
      style="width:100%;padding:12px 44px 12px 40px;background:var(--bg-card2);border:1px solid var(--border);border-radius:16px;color:var(--text-primary);font-size:0.875rem;outline:none;">
  </div>'''

vehicles_new = '''<div style="background:var(--primary); padding-bottom:16px; border-bottom-left-radius: 16px; border-bottom-right-radius: 16px;">
    <div style="padding:16px 20px 12px;display:flex;align-items:center;justify-content:space-between;">
      <div>
        <p style="font-size:0.75rem;color:rgba(255,255,255,0.8);font-weight:500;">Explore</p>
        <h1 style="font-size:1.6rem;font-weight:900;color:var(--on-primary);letter-spacing:-0.5px;">Vehicles</h1>
      </div>
      <button onclick="showOverlay('page-favorites')" style="width:40px;height:40px;border-radius:14px;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.2);color:var(--on-primary);font-size:1rem;cursor:pointer;position:relative;">
        <i class="fas fa-heart"></i>
      </button>
    </div>
    <div style="padding:0 16px;position:relative;">
      <i class="fas fa-search" style="position:absolute;left:32px;top:50%;transform:translateY(-50%);color:var(--primary);font-size:1rem;"></i>
      <input type="text" id="vehicleSearch" placeholder="Search for cars, locations..." oninput="searchVehicles(this.value)"
        style="width:100%;padding:12px 44px 12px 44px;background:#ffffff;border:none;border-radius:12px;color:var(--text-primary);font-size:0.95rem;outline:none;box-shadow:0 4px 12px rgba(0,0,0,0.08); font-weight:500;">
      <i class="fas fa-microphone" style="position:absolute;right:32px;top:50%;transform:translateY(-50%);color:var(--primary);font-size:1rem;"></i>
    </div>
  </div>'''

content = content.replace(vehicles_old, vehicles_new)

# 2. Update Bookings UI
bookings_old = '''<div style="padding:16px 20px 8px;">
    <p style="font-size:0.75rem;color:var(--text-muted);font-weight:500;">Your</p>
    <h1 style="font-size:1.6rem;font-weight:900;color:var(--text-primary);letter-spacing:-0.5px;">Bookings</h1>
  </div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:0 16px 12px;">
    <div id="bkStatTotal" style="background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:12px;text-align:center;">
      <div style="font-size:1.3rem;font-weight:900;color:var(--text-secondary);">0</div>
      <div style="font-size:0.65rem;color:var(--text-muted);font-weight:600;margin-top:2px;">Total</div>
    </div>
    <div id="bkStatDone" style="background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:12px;text-align:center;">
      <div style="font-size:1.3rem;font-weight:900;color:#a78bfa;">0</div>
      <div style="font-size:0.65rem;color:var(--text-muted);font-weight:600;margin-top:2px;">Completed</div>
    </div>
    <div id="bkStatSpent" style="background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:12px;text-align:center;">
      <div style="font-size:1.3rem;font-weight:900;color:#34d399;">-</div>
      <div style="font-size:0.65rem;color:var(--text-muted);font-weight:600;margin-top:2px;">Total Spent</div>
    </div>
  </div>'''

bookings_new = '''<div style="padding:16px 20px 12px; text-align:center;">
    <h1 style="font-size:1.4rem;font-weight:800;color:var(--text-primary);">My Bookings</h1>
  </div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:0 16px 16px;">
    <div id="bkStatTotal" style="background:var(--bg-card);border:1px solid var(--border);border-radius:50%;width:80px;height:80px;display:flex;flex-direction:column;align-items:center;justify-content:center;margin:0 auto;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
      <div style="font-size:1.4rem;font-weight:900;color:var(--text-primary);">0</div>
      <div style="font-size:0.65rem;color:var(--text-muted);font-weight:600;margin-top:2px;">Total</div>
    </div>
    <div id="bkStatDone" style="background:var(--bg-card);border:1px solid var(--border);border-radius:50%;width:80px;height:80px;display:flex;flex-direction:column;align-items:center;justify-content:center;margin:0 auto;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
      <div style="font-size:1.4rem;font-weight:900;color:var(--text-primary);">0</div>
      <div style="font-size:0.65rem;color:var(--text-muted);font-weight:600;margin-top:2px;">Completed</div>
    </div>
    <div id="bkStatSpent" style="background:var(--bg-card);border:1px solid var(--border);border-radius:50%;width:80px;height:80px;display:flex;flex-direction:column;align-items:center;justify-content:center;margin:0 auto;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
      <div style="font-size:1.2rem;font-weight:900;color:var(--primary);">-</div>
      <div style="font-size:0.65rem;color:var(--text-muted);font-weight:600;margin-top:2px;">Total Spent</div>
    </div>
  </div>'''

content = content.replace(bookings_old, bookings_new)

with open('customer_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(content)

print("Updated Browse and Bookings UI successfully")
