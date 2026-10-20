import json
import re

with open('scratch/detailed_inputs_catalog.json', 'r', encoding='utf-8') as f:
    catalog = json.load(f)

# Let's inspect admin fields
admin_fields = catalog['admin_html']
customer_html = catalog['customer_html']
customer_js = catalog['customer_js']

def clean_list(items):
    seen = set()
    cleaned = []
    for it in items:
        eid = it['id']
        itype = it['type']
        if not eid or eid in ['null', 'undefined']:
            continue
        key = (eid, itype)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(it)
    return cleaned

cleaned_cust_html = clean_list(customer_html)
cleaned_cust_js = clean_list(customer_js)
cleaned_admin = clean_list(admin_fields)

print(f"Unique Customer HTML fields: {len(cleaned_cust_html)}")
print(f"Unique Customer JS fields: {len(cleaned_cust_js)}")
print(f"Unique Admin HTML fields: {len(cleaned_admin)}")

# Group admin fields by module/purpose based on ID prefixes and context
modules = {
    'Vehicle Management (Add/Edit Vehicles)': [],
    'Walk-in / Direct Bookings': [],
    'Booking Management & Pricing / Adjustments': [],
    'Customer & Driver Verification / Licensing': [],
    'Newsletter, Promos & Discounts': [],
    'Blackout Dates & Availability': [],
    'System Maintenance & Log Retention': [],
    'System Settings, Email & Payments': [],
    'Reports, Analytics & Date Filtering': [],
    'Admin Search, Sorting & Table Filters': [],
    'Other Admin Inputs': []
}

for item in cleaned_admin:
    eid = item['id'].lower()
    t = item['type']
    ctx = item['context'].lower()
    
    if any(k in eid for k in ['vehicle', 'car', 'vbrand', 'vmodel', 'vplate', 'vrate', 'vyear', 'vcolor', 'vseats', 'vmileage', 'vfuel', 'vtrans']) and 'search' not in eid and 'filter' not in eid:
        modules['Vehicle Management (Add/Edit Vehicles)'].append(item)
    elif 'walkin' in eid:
        modules['Walk-in / Direct Bookings'].append(item)
    elif any(k in eid for k in ['booking', 'pricing', 'quicktotal', 'quickamount', 'quickbalance', 'refund', 'reschedule', 'penalty', 'deposit']) and 'search' not in eid and 'sort' not in eid and 'filter' not in eid:
        modules['Booking Management & Pricing / Adjustments'].append(item)
    elif any(k in eid for k in ['verify', 'license', 'driver', 'rejectreason', 'approvenotes']):
        modules['Customer & Driver Verification / Licensing'].append(item)
    elif any(k in eid for k in ['nlform', 'newsletter', 'promo', 'discount', 'coupon']):
        modules['Newsletter, Promos & Discounts'].append(item)
    elif any(k in eid for k in ['blackout']):
        modules['Blackout Dates & Availability'].append(item)
    elif any(k in eid for k in ['maint']):
        modules['System Maintenance & Log Retention'].append(item)
    elif any(k in eid for k in ['setting', 'email', 'smtp', 'gateway', 'pay', 'company', 'contact']):
        modules['System Settings, Email & Payments'].append(item)
    elif any(k in eid for k in ['datefrom', 'dateto', 'chart', 'metric', 'export']):
        modules['Reports, Analytics & Date Filtering'].append(item)
    elif any(k in eid for k in ['search', 'sort', 'filter', 'pagesize', 'page']):
        modules['Admin Search, Sorting & Table Filters'].append(item)
    else:
        modules['Other Admin Inputs'].append(item)

print("\n--- ADMIN MODULE BREAKDOWN ---")
for mod, items in modules.items():
    print(f"{mod}: {len(items)} fields")

# Inspect "Other Admin Inputs" to see what they are
print("\nSample 'Other Admin Inputs':")
for it in modules['Other Admin Inputs'][:20]:
    print(f"  [{it['type']}] id={it['id']} ph={it['placeholder'][:25]} ctx={it['context'][:30]}")
