import re

# 1. Patch customer_mobile/www/js/app.js
cust_file = "customer_mobile/www/js/app.js"
with open(cust_file, "r", encoding="utf-8") as f:
    cust_content = f.read()

# extNewEnd
old_ext = "parts.push('<input type=\"date\" id=\"extNewEnd\" min=\"' + minDate + '\" onchange=\"calcExtPrice(\\'' + currentEndDate + '\\',' + rate + ')\""
new_ext = "parts.push('<input type=\"date\" id=\"extNewEnd\" min=\"' + minDate + '\" max=\"2099-12-31\" onchange=\"calcExtPrice(\\'' + currentEndDate + '\\',' + rate + ')\""
assert old_ext in cust_content, "extNewEnd target not found in customer app.js"
cust_content = cust_content.replace(old_ext, new_ext, 1)

# modStart & modEnd
old_mod = """        '<div class="form-group"><label>New Start Date</label><input type="date" id="modStart" value="' + currentStart + '"></div>' +
        '<div class="form-group"><label>New End Date</label><input type="date" id="modEnd" value="' + currentEnd + '"></div>' +"""

new_mod = """        '<div class="form-group"><label>New Start Date</label><input type="date" id="modStart" min="2020-01-01" max="2099-12-31" value="' + currentStart + '"></div>' +
        '<div class="form-group"><label>New End Date</label><input type="date" id="modEnd" min="2020-01-01" max="2099-12-31" value="' + currentEnd + '"></div>' +"""

assert old_mod in cust_content, "modStart/modEnd target not found in customer app.js"
cust_content = cust_content.replace(old_mod, new_mod, 1)

with open(cust_file, "w", encoding="utf-8") as f:
    f.write(cust_content)
print("Successfully patched customer_mobile/www/js/app.js!")

# Also patch frontend/js/app.js to keep in sync
fe_cust_file = "frontend/js/app.js"
with open(fe_cust_file, "r", encoding="utf-8") as f:
    fe_cust_content = f.read()
if old_ext in fe_cust_content:
    fe_cust_content = fe_cust_content.replace(old_ext, new_ext, 1)
if old_mod in fe_cust_content:
    fe_cust_content = fe_cust_content.replace(old_mod, new_mod, 1)
with open(fe_cust_file, "w", encoding="utf-8") as f:
    f.write(fe_cust_content)
print("Successfully patched frontend/js/app.js!")

# 2. Patch admin_app/index.html
admin_file = "admin_app/index.html"
with open(admin_file, "r", encoding="utf-8") as f:
    admin_content = f.read()

replacements = [
    # popupDateFrom / To
    ('<input type="date" id="popupDateFrom" onchange="applyPopupFilters()">',
     '<input type="date" id="popupDateFrom" min="2020-01-01" max="2099-12-31" onchange="applyPopupFilters()">'),
    ('<input type="date" id="popupDateTo" onchange="applyPopupFilters()">',
     '<input type="date" id="popupDateTo" min="2020-01-01" max="2099-12-31" onchange="applyPopupFilters()">'),
    
    # dashDateFrom / To
    ('<input type="date" id="dashDateFrom" onchange="syncAndRefreshDashboardDates()"',
     '<input type="date" id="dashDateFrom" min="2020-01-01" max="2099-12-31" onchange="syncAndRefreshDashboardDates()"'),
    ('<input type="date" id="dashDateTo" onchange="syncAndRefreshDashboardDates()"',
     '<input type="date" id="dashDateTo" min="2020-01-01" max="2099-12-31" onchange="syncAndRefreshDashboardDates()"'),
    
    # blackoutStartDate / EndDate
    ('<input type="date" id="blackoutStartDate" required style="width: 100%;',
     '<input type="date" id="blackoutStartDate" min="2020-01-01" max="2099-12-31" required style="width: 100%;'),
    ('<input type="date" id="blackoutEndDate" required style="width: 100%;',
     '<input type="date" id="blackoutEndDate" min="2020-01-01" max="2099-12-31" required style="width: 100%;'),

    # quickBalanceAmount
    ('<input type="text" id="quickBalanceAmount" readonly',
     '<input type="text" id="quickBalanceAmount" maxlength="20" readonly'),

    # walkinStartDate / EndDate
    ('<input type="date" id="walkinStartDate" required onchange="WalkinBooking.recalculate()"',
     '<input type="date" id="walkinStartDate" min="2020-01-01" max="2099-12-31" required onchange="WalkinBooking.recalculate()"'),
    ('<input type="date" id="walkinEndDate" required onchange="WalkinBooking.recalculate()"',
     '<input type="date" id="walkinEndDate" min="2020-01-01" max="2099-12-31" required onchange="WalkinBooking.recalculate()"'),

    # fleetExportStartDate / EndDate
    ('<input type="date" id="fleetExportStartDate" style="width: 100%;',
     '<input type="date" id="fleetExportStartDate" min="2020-01-01" max="2099-12-31" style="width: 100%;'),
    ('<input type="date" id="fleetExportEndDate" style="width: 100%;',
     '<input type="date" id="fleetExportEndDate" min="2020-01-01" max="2099-12-31" style="width: 100%;'),

    # expDate
    ('<input type="date" id="expDate" required style="width: 100%;',
     '<input type="date" id="expDate" min="2020-01-01" max="2099-12-31" required style="width: 100%;'),

    # rptDateFrom / To
    ('<input type="date" id="rptDateFrom" onchange="Reports.refresh()"',
     '<input type="date" id="rptDateFrom" min="2020-01-01" max="2099-12-31" onchange="Reports.refresh()"'),
    ('<input type="date" id="rptDateTo" onchange="Reports.refresh()"',
     '<input type="date" id="rptDateTo" min="2020-01-01" max="2099-12-31" onchange="Reports.refresh()"'),

    # vNextService / vLtoExpiry
    ('<input type="date" id="vNextService" style="width:100%;',
     '<input type="date" id="vNextService" min="2020-01-01" max="2099-12-31" style="width:100%;'),
    ('<input type="date" id="vLtoExpiry" style="width:100%;',
     '<input type="date" id="vLtoExpiry" min="2020-01-01" max="2099-12-31" style="width:100%;'),

    # inspectDriverOTAmount
    ('<input type="text" id="inspectDriverOTAmount" readonly value="0.00"',
     '<input type="text" id="inspectDriverOTAmount" maxlength="20" readonly value="0.00"'),

    # editSuspCustom dynamic input
    ('<input type="datetime-local" id="editSuspCustom_${u.id}" style="display:none;',
     '<input type="datetime-local" id="editSuspCustom_${u.id}" min="2020-01-01T00:00" max="2099-12-31T23:59" style="display:none;')
]

for old_s, new_s in replacements:
    assert old_s in admin_content, f"Admin pattern not found: {old_s[:40]}"
    admin_content = admin_content.replace(old_s, new_s, 1)

with open(admin_file, "w", encoding="utf-8") as f:
    f.write(admin_content)

print(f"Successfully patched all {len(replacements)} admin targets!")
