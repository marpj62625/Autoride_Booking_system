import json
import re

with open('scratch/detailed_inputs_catalog.json', 'r', encoding='utf-8') as f:
    catalog = json.load(f)

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

# Organize all fields into functional areas
# 1. Customer Frontend
# 2. Admin Frontend
# 3. Backend Endpoints

with open('scratch/full_system_limits_inventory.md', 'w', encoding='utf-8') as md:
    md.write("# COMPLETE SYSTEM INPUT FIELDS & LIMITS INVENTORY\n\n")
    
    # ------------------ PART 1: CUSTOMER SIDE ------------------
    md.write("## PART 1: CUSTOMER APP (Mobile & Web)\n\n")
    md.write("| Category | Field ID / Name | Type | Current Limit (`maxlength` / `min`-`max`) | Recommended / Target Limit | Status |\n")
    md.write("|---|---|---|---|---|---|\n")
    
    for it in cleaned_cust_html:
        if it['type'] in ['hidden', 'checkbox', 'radio']:
            continue
        curr = it['maxlength'] or (f"{it['min']} to {it['max']}" if it['min'] or it['max'] else "None")
        status = "Protected" if it['maxlength'] or it['min'] or it['max'] else "NEEDS LIMIT"
        md.write(f"| Customer HTML | `{it['id']}` | {it['type']} | {curr} | {it['placeholder'][:25]} | {status} |\n")
        
    for it in cleaned_cust_js:
        if it['type'] in ['hidden', 'checkbox', 'radio']:
            continue
        curr = it['maxlength'] or (f"{it['min']} to {it['max']}" if it['min'] or it['max'] else "None")
        status = "Protected" if it['maxlength'] or it['min'] or it['max'] else "NEEDS LIMIT"
        md.write(f"| Customer Dynamic JS | `{it['id']}` | {it['type']} | {curr} | {it['placeholder'][:25]} | {status} |\n")

    # ------------------ PART 2: ADMIN SIDE ------------------
    md.write("\n\n## PART 2: ADMIN APP (Desktop & Mobile)\n\n")
    md.write("| Module / Area | Field ID / Name | Type | Current Limit | Recommended Limit | Severity / Risk |\n")
    md.write("|---|---|---|---|---|---|\n")
    
    for it in cleaned_admin:
        if it['type'] in ['hidden', 'checkbox', 'radio']:
            continue
        eid = it['id']
        itype = it['type']
        curr = it['maxlength'] or (f"{it['min']} to {it['max']}" if it['min'] or it['max'] else "None")
        
        # Categorize
        mod = "Admin General"
        risk = "Medium"
        rec = "Set limit"
        
        if 'walkin' in eid.lower():
            mod = "Walk-in Booking Modal"
            risk = "HIGH (Customer info input directly by staff)"
            if 'phone' in eid.lower(): rec = "maxlength=11 (numeric only)"
            elif 'name' in eid.lower(): rec = "maxlength=50 (letters & spaces)"
            elif 'address' in eid.lower(): rec = "maxlength=100"
            elif 'license' in eid.lower(): rec = "maxlength=13"
            else: rec = "maxlength=50"
        elif any(k in eid.lower() for k in ['vbrand', 'vmodel', 'vplate', 'vrate', 'vyear', 'vcolor', 'vseats', 'vmileage', 'vfuel', 'vtrans', 'vehicle']):
            mod = "Vehicle Add/Edit Form"
            risk = "HIGH (Vehicle specs, plates, rates)"
            if 'plate' in eid.lower(): rec = "maxlength=8 (e.g. ABC 1234)"
            elif 'rate' in eid.lower() or 'price' in eid.lower(): rec = "min=500 max=50000"
            elif 'year' in eid.lower(): rec = "min=2000 max=2027"
            elif 'seats' in eid.lower(): rec = "min=2 max=30"
            elif 'mileage' in eid.lower() or 'odo' in eid.lower(): rec = "min=0 max=999999"
            else: rec = "maxlength=50"
        elif 'nl' in eid.lower() or 'promo' in eid.lower() or 'coupon' in eid.lower():
            mod = "Promos & Newsletters"
            risk = "HIGH (Promo codes, titles, percentage)"
            if 'code' in eid.lower(): rec = "maxlength=15 (alphanumeric)"
            elif 'discount' in eid.lower(): rec = "min=1 max=99 (%)"
            elif 'title' in eid.lower(): rec = "maxlength=80"
            elif 'content' in eid.lower(): rec = "maxlength=1000"
            else: rec = "maxlength=100"
        elif 'maint' in eid.lower():
            mod = "Maintenance & Logs"
            risk = "Medium"
            rec = "maxlength=100 or select bounds"
        elif 'blackout' in eid.lower():
            mod = "Blackout Dates"
            risk = "Medium"
            if 'reason' in eid.lower(): rec = "maxlength=100"
            else: rec = "valid date range"
        elif 'faq' in eid.lower() or 'chat' in eid.lower():
            mod = "Live Chat & FAQ Management"
            risk = "Medium"
            rec = "maxlength=250"
        elif 'search' in eid.lower():
            mod = "Search & Filter Bars"
            risk = "Low"
            rec = "maxlength=50 (strip dangerous chars)"
        elif 'sort' in eid.lower() or 'filter' in eid.lower() or 'pagesize' in eid.lower():
            mod = "Dropdown Select Filter"
            risk = "Low (Enum select)"
            rec = "Restricted to enum values"
        elif 'date' in eid.lower() or itype == 'date':
            mod = "Date Range Pickers"
            risk = "Medium"
            rec = "Valid date range bounds"
        elif 'setting' in eid.lower() or 'smtp' in eid.lower() or 'email' in eid.lower():
            mod = "System Settings"
            risk = "HIGH (Configuration & credentials)"
            rec = "maxlength=60 or 100"
            
        md.write(f"| {mod} | `{eid}` | {itype} | {curr} | {rec} | {risk} |\n")

    # ------------------ PART 3: BACKEND API VALIDATION ------------------
    md.write("\n\n## PART 3: BACKEND API PAYLOAD LIMITS (`backend/app.py`)\n\n")
    md.write("| Endpoint | Method | Key Incoming Fields | Missing / Needed Backend Guard |\n")
    md.write("|---|---|---|---|\n")
    md.write("| `/api/auth/register` | POST | `first_name`, `last_name`, `email`, `password` | Enforce max len: name <= 30, email <= 60, pass <= 64 |\n")
    md.write("| `/api/auth/login` | POST | `email`, `password` | Enforce max len: email <= 60, pass <= 64 |\n")
    md.write("| `/api/user/profile` | PUT | `first_name`, `last_name`, `phone`, `email` | Enforce max len: name <= 30, phone == 11, email <= 60 |\n")
    md.write("| `/api/user/driver-license` | POST/PUT | `license_number`, `name_on_license`, `address`, `license_class`, `emergency_contact_name`, `emergency_contact_phone` | Enforce: class <= 15, address <= 100, name <= 50, em_name <= 50, em_phone == 11 |\n")
    md.write("| `/api/bookings` | POST | `destination`, `delivery_address`, `start_date`, `end_date`, `service_type` | Enforce: dest <= 60, delivery_addr <= 100. (Note: rental duration limit is deferred per user) |\n")
    md.write("| `/api/admin/walkin` | POST | `customer_name`, `contact_number`, `address`, `emergency_name`, `emergency_phone`, `license_number` | Enforce: name <= 50, phone == 11, addr <= 100, license == 13 |\n")
    md.write("| `/api/vehicles` (Admin) | POST/PUT | `brand`, `model`, `plate_number`, `daily_rate`, `year`, `seats` | Enforce: brand <= 30, model <= 30, plate <= 8, rate (500-50000), year (2000-2027), seats (2-30) |\n")
    md.write("| `/api/admin/newsletter` | POST | `title`, `promo_code`, `discount_percent`, `content` | Enforce: title <= 80, promo_code <= 15, discount (1-99), content <= 1000 |\n")
    md.write("| `/api/reviews` | POST | `rating`, `comment` | Enforce: rating in 1-5, comment <= 300 |\n")
    md.write("| `/api/chat/send` | POST | `message` | Enforce: message <= 250 |\n")
    md.write("| `/api/bookings/refund-request` | POST | `account_name`, `account_number`, `notes` | Enforce: acct_name <= 50, acct_num <= 16, notes <= 200 |\n")

    # ------------------ PART 4: BUSINESS / SYSTEM BOUNDARY LIMITS ------------------
    md.write("\n\n## PART 4: SYSTEM BUSINESS LIMITS & CONSTRAINTS\n\n")
    md.write("| Area / Feature | Current Value | Recommended Limit / Guard | Notes |\n")
    md.write("|---|---|---|---|\n")
    md.write("| **Image & File Uploads** (License, Proof of Payment, Inspection) | Unlimited base64 / Multipart | **Max 5 MB per file**, JPG/PNG/WEBP only | Prevents memory exhaustion / payload crash |\n")
    md.write("| **Driver Age Limit** | Validated in utils/backend | **18 to 75 years old** | Already enforced in validation |\n")
    md.write("| **License Expiry Range** | Validated in utils/backend | **Current date up to +10 years** | Already enforced in validation |\n")
    md.write("| **Rental Duration Limit** | `max_booking_duration_days` | **[DEFERRED - WAG GALAWIN]** | Explicitly kept as-is per user instruction |\n")
    md.write("| **Mileage / Odometer Reading** | Number input without max | **Min: last recorded odometer, Max: 999,999 km** | Rejects negative or impossible numbers |\n")
    md.write("| **Fuel Tank Level** | Enum select | **Full, 3/4, 1/2, 1/4, Empty** | Strict enum selection |\n")
    md.write("| **Security Deposit & Refund Amounts** | Number input | **Min: 0, Max: Booking total price** | Prevents negative or over-refund amounts |\n")

print("Full inventory generated successfully in scratch/full_system_limits_inventory.md")
