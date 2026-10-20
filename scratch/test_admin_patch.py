with open('admin_app/index.html', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

patches = [
    # 1. activitySearch
    (
        '<input id="activitySearch" type="text" placeholder="Search by name, action or details..."',
        '<input id="activitySearch" type="text" maxlength="50" placeholder="Search by name, action or details..."'
    ),
    # 2. pastBookingsSearch
    (
        '<input type="text" id="pastBookingsSearch" placeholder="Search by customer, ID, or vehicle..." style="width: 100%; padding: 10px 10px 10px 36px; background: var(--surface-container); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.85rem;" oninput="filterPastBookings()">',
        '<input type="text" id="pastBookingsSearch" maxlength="50" placeholder="Search by customer, ID, or vehicle..." style="width: 100%; padding: 10px 10px 10px 36px; background: var(--surface-container); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.85rem;" oninput="filterPastBookings()">'
    ),
    # 3. archivedBookingsSearch
    (
        '<input type="text" id="archivedBookingsSearch" placeholder="Search by customer, booking #, or vehicle..." style="width: 100%; padding: 10px 10px 10px 36px; background: var(--surface-container); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.85rem;" oninput="ArchivedBookings.onSearch(this.value)">',
        '<input type="text" id="archivedBookingsSearch" maxlength="50" placeholder="Search by customer, booking #, or vehicle..." style="width: 100%; padding: 10px 10px 10px 36px; background: var(--surface-container); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.85rem;" oninput="ArchivedBookings.onSearch(this.value)">'
    ),
    # 4. verificationsSearch
    (
        '<input type="text" id="verificationsSearch" oninput="Verifications.onSearch(this.value)" placeholder="Search name, license no, email..." style="width: 100%; padding: 11px 14px 11px 40px; background: var(--surface); border: 1.5px solid var(--border); border-radius: 12px; color: var(--text-main); font-size: 0.85rem; font-weight: 600; outline: none; box-sizing: border-box;">',
        '<input type="text" id="verificationsSearch" maxlength="50" oninput="Verifications.onSearch(this.value)" placeholder="Search name, license no, email..." style="width: 100%; padding: 11px 14px 11px 40px; background: var(--surface); border: 1.5px solid var(--border); border-radius: 12px; color: var(--text-main); font-size: 0.85rem; font-weight: 600; outline: none; box-sizing: border-box;">'
    ),
    # 5. blackoutReason
    (
        '<input type="text" id="blackoutReason" required placeholder="e.g. Christmas Holiday, Car Maintenance" style="width: 100%; padding: 8px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 0.85rem; box-sizing: border-box; color: #0f172a !important; background: #ffffff !important;">',
        '<input type="text" id="blackoutReason" required maxlength="100" placeholder="e.g. Christmas Holiday, Car Maintenance" style="width: 100%; padding: 8px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 0.85rem; box-sizing: border-box; color: #0f172a !important; background: #ffffff !important;">'
    ),
    # 6. nlFormTitle
    (
        '<input type="text" id="nlFormTitle" required placeholder="e.g. Summer Weekend Roadtrip Special — 15% OFF" style="width: 100%; box-sizing: border-box; padding: 9px 12px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 0.85rem; color: #0f172a !important; background: #fff !important;">',
        '<input type="text" id="nlFormTitle" required maxlength="80" placeholder="e.g. Summer Weekend Roadtrip Special — 15% OFF" style="width: 100%; box-sizing: border-box; padding: 9px 12px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 0.85rem; color: #0f172a !important; background: #fff !important;">'
    ),
    # 7. nlFormDiscount
    (
        '<input type="number" id="nlFormDiscount" min="1" max="99" placeholder="e.g. 15" style="width: 100%; box-sizing: border-box; padding: 9px 12px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 0.85rem; color: #0f172a !important; background: #fff !important;">',
        '<input type="number" id="nlFormDiscount" min="1" max="90" placeholder="e.g. 15" style="width: 100%; box-sizing: border-box; padding: 9px 12px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 0.85rem; color: #0f172a !important; background: #fff !important;">'
    ),
    # 8. nlFormCode
    (
        '<input type="text" id="nlFormCode" placeholder="e.g. SUMMER15 (Leave blank if no voucher)" style="width: 100%; box-sizing: border-box; padding: 9px 12px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 0.85rem; font-family: monospace; font-weight: 700; color: #0f172a !important; background: #fff !important; text-transform: uppercase;">',
        '<input type="text" id="nlFormCode" placeholder="e.g. SUMMER15 (Leave blank if no voucher)" maxlength="15" oninput="this.value = this.value.toUpperCase().replace(/[^A-Z0-9_-]/g, \'\').slice(0, 15)" style="width: 100%; box-sizing: border-box; padding: 9px 12px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 0.85rem; font-family: monospace; font-weight: 700; color: #0f172a !important; background: #fff !important; text-transform: uppercase;">'
    ),
    # 9. nlFormContent
    (
        '<textarea id="nlFormContent" required rows="4" placeholder="Write your newsletter announcement, promotional details, instructions or tips here..." style="width: 100%; box-sizing: border-box; padding: 9px 12px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 0.85rem; color: #0f172a !important; background: #fff !important; font-family: inherit; resize: vertical;"></textarea>',
        '<textarea id="nlFormContent" required rows="4" maxlength="1000" placeholder="Write your newsletter announcement, promotional details, instructions or tips here..." style="width: 100%; box-sizing: border-box; padding: 9px 12px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 0.85rem; color: #0f172a !important; background: #fff !important; font-family: inherit; resize: vertical;"></textarea>'
    ),
    # 10. expAmount & expDesc
    (
        '<input type="number" step="0.01" id="expAmount" required min="0" style="width: 100%; padding: 12px; background: var(--surface-container); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.9rem;">',
        '<input type="number" step="0.01" id="expAmount" required min="1" max="1000000" style="width: 100%; padding: 12px; background: var(--surface-container); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.9rem;">'
    ),
    (
        '<textarea id="expDesc" required style="width: 100%; height: 80px; padding: 12px; background: var(--surface-container); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.9rem; font-family: inherit; resize: vertical;"></textarea>',
        '<textarea id="expDesc" required maxlength="250" style="width: 100%; height: 80px; padding: 12px; background: var(--surface-container); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.9rem; font-family: inherit; resize: vertical;"></textarea>'
    ),
    # 11. staffName, staffEmail, staffPass
    (
        '<input id="staffName" type="text" required placeholder="John Doe" style="width: 100%; padding: 12px 14px; background: var(--bg-input); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); outline: none; box-sizing: border-box;" onfocus="this.style.borderColor=\'var(--primary)\'" onblur="this.style.borderColor=\'var(--border)\'">',
        '<input id="staffName" type="text" required maxlength="50" placeholder="John Doe" style="width: 100%; padding: 12px 14px; background: var(--bg-input); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); outline: none; box-sizing: border-box;" onfocus="this.style.borderColor=\'var(--primary)\'" onblur="this.style.borderColor=\'var(--border)\'">'
    ),
    (
        '<input id="staffEmail" type="email" required placeholder="john@autoride.com" style="width: 100%; padding: 12px 14px; background: var(--bg-input); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); outline: none; box-sizing: border-box;" onfocus="this.style.borderColor=\'var(--primary)\'" onblur="this.style.borderColor=\'var(--border)\'">',
        '<input id="staffEmail" type="email" required maxlength="60" placeholder="john@autoride.com" style="width: 100%; padding: 12px 14px; background: var(--bg-input); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); outline: none; box-sizing: border-box;" onfocus="this.style.borderColor=\'var(--primary)\'" onblur="this.style.borderColor=\'var(--border)\'">'
    ),
    (
        '<input id="staffPass" type="password" placeholder="********" style="width: 100%; padding: 12px 14px; background: var(--bg-input); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); outline: none; box-sizing: border-box;" onfocus="this.style.borderColor=\'var(--primary)\'" onblur="this.style.borderColor=\'var(--border)\'">',
        '<input id="staffPass" type="password" maxlength="64" placeholder="********" style="width: 100%; padding: 12px 14px; background: var(--bg-input); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); outline: none; box-sizing: border-box;" onfocus="this.style.borderColor=\'var(--primary)\'" onblur="this.style.borderColor=\'var(--border)\'">'
    ),
    # 12. superAdminEditEmail, superAdminCurrentPassword, superAdminNewPassword, superAdminConfirmPassword
    (
        '<input id="superAdminEditEmail" type="email" placeholder="superadmin@autoride.com" style="width: 100%; padding: 11px 12px 11px 36px; background: var(--surface-container, #f4f6fb); border: 1.5px solid var(--border, #dde2ee); border-radius: 10px; color: var(--text-main, #0f1117); font-size: 0.88rem; box-sizing: border-box;">',
        '<input id="superAdminEditEmail" type="email" maxlength="60" placeholder="superadmin@autoride.com" style="width: 100%; padding: 11px 12px 11px 36px; background: var(--surface-container, #f4f6fb); border: 1.5px solid var(--border, #dde2ee); border-radius: 10px; color: var(--text-main, #0f1117); font-size: 0.88rem; box-sizing: border-box;">'
    ),
    (
        '<input id="superAdminCurrentPassword" type="password" placeholder="Enter current password to verify" style="width: 100%; padding: 11px 12px 11px 36px; background: var(--surface-container, #f4f6fb); border: 1.5px solid var(--border, #dde2ee); border-radius: 10px; color: var(--text-main, #0f1117); font-size: 0.88rem; box-sizing: border-box;">',
        '<input id="superAdminCurrentPassword" type="password" maxlength="64" placeholder="Enter current password to verify" style="width: 100%; padding: 11px 12px 11px 36px; background: var(--surface-container, #f4f6fb); border: 1.5px solid var(--border, #dde2ee); border-radius: 10px; color: var(--text-main, #0f1117); font-size: 0.88rem; box-sizing: border-box;">'
    ),
    (
        '<input id="superAdminNewPassword" type="password" placeholder="Min. 6 characters" style="width: 100%; padding: 11px 12px 11px 36px; background: var(--surface-container, #f4f6fb); border: 1.5px solid var(--border, #dde2ee); border-radius: 10px; color: var(--text-main, #0f1117); font-size: 0.88rem; box-sizing: border-box;">',
        '<input id="superAdminNewPassword" type="password" maxlength="64" placeholder="Min. 6 characters" style="width: 100%; padding: 11px 12px 11px 36px; background: var(--surface-container, #f4f6fb); border: 1.5px solid var(--border, #dde2ee); border-radius: 10px; color: var(--text-main, #0f1117); font-size: 0.88rem; box-sizing: border-box;">'
    ),
    (
        '<input id="superAdminConfirmPassword" type="password" placeholder="Re-enter new password" style="width: 100%; padding: 11px 12px 11px 36px; background: var(--surface-container, #f4f6fb); border: 1.5px solid var(--border, #dde2ee); border-radius: 10px; color: var(--text-main, #0f1117); font-size: 0.88rem; box-sizing: border-box;">',
        '<input id="superAdminConfirmPassword" type="password" maxlength="64" placeholder="Re-enter new password" style="width: 100%; padding: 11px 12px 11px 36px; background: var(--surface-container, #f4f6fb); border: 1.5px solid var(--border, #dde2ee); border-radius: 10px; color: var(--text-main, #0f1117); font-size: 0.88rem; box-sizing: border-box;">'
    ),
    # 13. inspectMileage, inspectFuelChargeAmount, inspectFuelChargeNotes, inspectDriverOTHours, inspectDriverOTNotes, inspectNotes
    (
        '<input type="number" id="inspectMileage" placeholder="0" required style="width: 100%; padding: 12px; background: #f4f6fb; border: 1px solid var(--border); border-radius: 12px; color: #0f1117; font-weight: 600;">',
        '<input type="number" id="inspectMileage" min="0" max="999999" placeholder="0" required style="width: 100%; padding: 12px; background: #f4f6fb; border: 1px solid var(--border); border-radius: 12px; color: #0f1117; font-weight: 600;">'
    ),
    (
        '<input type="number" id="inspectFuelChargeAmount" min="0" step="50" placeholder="0" style="width: 100%; padding: 10px 10px 10px 24px; background: #ffffff; border: 1.5px solid #fb7185; border-radius: 10px; font-size: 0.95rem; font-weight: 800; color: #9f1239; outline: none;">',
        '<input type="number" id="inspectFuelChargeAmount" min="0" max="10000" step="50" placeholder="0" style="width: 100%; padding: 10px 10px 10px 24px; background: #ffffff; border: 1.5px solid #fb7185; border-radius: 10px; font-size: 0.95rem; font-weight: 800; color: #9f1239; outline: none;">'
    ),
    (
        '<input type="text" id="inspectFuelChargeNotes" placeholder="e.g. Refuel to Full Tank: missing 1/4 tank" style="width: 100%; padding: 10px 12px; background: #ffffff; border: 1px solid #fda4af; border-radius: 10px; font-size: 0.8rem; color: #0f172a; outline: none;">',
        '<input type="text" id="inspectFuelChargeNotes" maxlength="150" placeholder="e.g. Refuel to Full Tank: missing 1/4 tank" style="width: 100%; padding: 10px 12px; background: #ffffff; border: 1px solid #fda4af; border-radius: 10px; font-size: 0.8rem; color: #0f172a; outline: none;">'
    ),
    (
        '<input type="number" id="inspectDriverOTHours" min="0" step="0.5" value="0" placeholder="0" oninput="Inspections.onDriverOTChange()" style="width: 100%; padding: 10px 12px; background: #ffffff; border: 1.5px solid #86efac; border-radius: 10px; font-size: 0.95rem; font-weight: 800; color: #14532d; outline: none;">',
        '<input type="number" id="inspectDriverOTHours" min="0" max="24" step="0.5" value="0" placeholder="0" oninput="Inspections.onDriverOTChange()" style="width: 100%; padding: 10px 12px; background: #ffffff; border: 1.5px solid #86efac; border-radius: 10px; font-size: 0.95rem; font-weight: 800; color: #14532d; outline: none;">'
    ),
    (
        '<input type="text" id="inspectDriverOTNotes" placeholder="e.g. Trip Ticket #0482: Batangas trip excess 3.5 hrs (renter paid cash)" style="width: 100%; padding: 10px 12px; background: #ffffff; border: 1px solid #bbf7d0; border-radius: 10px; font-size: 0.8rem; color: #0f172a; outline: none;">',
        '<input type="text" id="inspectDriverOTNotes" maxlength="150" placeholder="e.g. Trip Ticket #0482: Batangas trip excess 3.5 hrs (renter paid cash)" style="width: 100%; padding: 10px 12px; background: #ffffff; border: 1px solid #bbf7d0; border-radius: 10px; font-size: 0.8rem; color: #0f172a; outline: none;">'
    ),
    (
        '<textarea id="inspectNotes" placeholder="Describe any scratches, dents, or cleaness issues..." style="width: 100%; padding: 12px; background: #f4f6fb; border: 1px solid var(--border); border-radius: 12px; color: #0f1117; font-size: 0.85rem; height: 80px; resize: none;"></textarea>',
        '<textarea id="inspectNotes" maxlength="300" placeholder="Describe any scratches, dents, or cleaness issues..." style="width: 100%; padding: 12px; background: #f4f6fb; border: 1px solid var(--border); border-radius: 12px; color: #0f1117; font-size: 0.85rem; height: 80px; resize: none;"></textarea>'
    ),
    # 14. umSearch
    (
        '<input type="text" id="umSearch" oninput="UserMgmt.applyFilters()" placeholder="Search name, email, phone..." style="width:100%; padding:12px 14px 12px 42px; background:#ffffff; border:1.5px solid #cbd5e1; border-radius:50px; color:#0f172a; font-size:0.88rem; font-weight:600; outline:none; box-sizing:border-box;">',
        '<input type="text" id="umSearch" maxlength="50" oninput="UserMgmt.applyFilters()" placeholder="Search name, email, phone..." style="width:100%; padding:12px 14px 12px 42px; background:#ffffff; border:1.5px solid #cbd5e1; border-radius:50px; color:#0f172a; font-size:0.88rem; font-weight:600; outline:none; box-sizing:border-box;">'
    ),
    # 15. fleetCalendarSearch
    (
        '<input type="text" id="fleetCalendarSearch" placeholder="Filter customer or car..." oninput="FleetCalendar.onSearch(this.value)"',
        '<input type="text" id="fleetCalendarSearch" maxlength="50" placeholder="Filter customer or car..." oninput="FleetCalendar.onSearch(this.value)"'
    ),
    # 16. loginEmail, loginPass
    (
        '<input type="email" id="loginEmail" placeholder="Email Address" autocomplete="email"',
        '<input type="email" id="loginEmail" maxlength="60" placeholder="Email Address" autocomplete="email"'
    ),
    (
        '<input type="password" id="loginPass" placeholder="Password" autocomplete="current-password"',
        '<input type="password" id="loginPass" maxlength="64" placeholder="Password" autocomplete="current-password"'
    ),
    # 17. penaltyAmount_${b.id}, penaltyNotes_${b.id}
    (
        '<input type="number" id="penaltyAmount_${b.id}" placeholder="Amount (PHP)" style="width:100%;padding:6px;border-radius:6px;border:1px solid #feb2b2;font-size:0.78rem;box-sizing:border-box;color:#0f172a !important;background:#ffffff !important;">',
        '<input type="number" id="penaltyAmount_${b.id}" min="0" max="100000" placeholder="Amount (PHP)" style="width:100%;padding:6px;border-radius:6px;border:1px solid #feb2b2;font-size:0.78rem;box-sizing:border-box;color:#0f172a !important;background:#ffffff !important;">'
    ),
    (
        '<textarea id="penaltyNotes_${b.id}" placeholder="Reason/Details" style="width:100%;padding:6px;border-radius:6px;border:1px solid #feb2b2;font-size:0.78rem;box-sizing:border-box;font-family:inherit;color:#0f172a !important;background:#ffffff !important;"></textarea>',
        '<textarea id="penaltyNotes_${b.id}" maxlength="250" placeholder="Reason/Details" style="width:100%;padding:6px;border-radius:6px;border:1px solid #feb2b2;font-size:0.78rem;box-sizing:border-box;font-family:inherit;color:#0f172a !important;background:#ffffff !important;"></textarea>'
    )
]

for idx, (target, replacement) in enumerate(patches, 1):
    cnt = content.count(target)
    if cnt == 1:
        print(f"[{idx}] OK: exact 1 match found.")
    else:
        print(f"[{idx}] ERROR: found {cnt} matches for {target[:50]}...")
