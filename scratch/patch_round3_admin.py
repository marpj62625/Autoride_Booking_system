import sys

ADMIN_HTML = 'AutorideSystem/admin_app/index.html'

with open(ADMIN_HTML, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    # 1. driverWageInput
    (
        '<input type="text" id="driverWageInput" placeholder="e.g. 500 per day"',
        '<input type="text" id="driverWageInput" maxlength="50" placeholder="e.g. 500 per day"'
    ),
    # 2. driverSearchInput
    (
        '<input type="text" id="driverSearchInput" oninput="Drivers.applyFilters()"',
        '<input type="text" id="driverSearchInput" maxlength="50" oninput="Drivers.applyFilters()"'
    ),
    # 3. fleetVehicleRateInput
    (
        '<input type="number" id="fleetVehicleRateInput" value="${curRate}" step="50" min="0"',
        '<input type="number" id="fleetVehicleRateInput" value="${curRate}" step="50" min="0" max="50000"'
    ),
    # 4. refundRefInput_${b.id}
    (
        '<input type="text" id="refundRefInput_${b.id}" placeholder="e.g. TXN123456789"',
        '<input type="text" id="refundRefInput_${b.id}" maxlength="50" placeholder="e.g. TXN123456789"'
    ),
    # 5. extRfAmt_${extensionId}
    (
        '<input id="extRfAmt_${extensionId}" type="number" step="0.01" value="${parseFloat(refundAmount).toFixed(2)}"',
        '<input id="extRfAmt_${extensionId}" type="number" step="0.01" min="0" max="500000" value="${parseFloat(refundAmount).toFixed(2)}"'
    ),
    # 6. extRfRef_${extensionId}
    (
        '<input id="extRfRef_${extensionId}" type="text" placeholder="Reference # (optional)"',
        '<input id="extRfRef_${extensionId}" type="text" maxlength="50" placeholder="Reference # (optional)"'
    ),
    # 7. umEditName
    (
        '<input id="umEditName" type="text" value="${u.full_name || \'\'}" placeholder="Full Name"',
        '<input id="umEditName" type="text" maxlength="50" value="${u.full_name || \'\'}" placeholder="Full Name"'
    ),
    # 8. umEditPhone
    (
        '<input id="umEditPhone" type="text" value="${u.phone || \'\'}" placeholder="Phone Number"',
        '<input id="umEditPhone" type="text" maxlength="11" value="${u.phone || \'\'}" placeholder="Phone Number"'
    ),
    # 9. umLoyaltyInput
    (
        '<input id="umLoyaltyInput" type="number" value="${u.loyalty_points || 0}" placeholder="Points"',
        '<input id="umLoyaltyInput" type="number" min="0" max="100000" value="${u.loyalty_points || 0}" placeholder="Points"'
    ),
    # 10. umNewPass
    (
        '<input id="umNewPass" type="password" placeholder="New password (min 8 chars)"',
        '<input id="umNewPass" type="password" maxlength="64" placeholder="New password (min 8 chars)"'
    ),
    # 11. editNote_${u.id}
    (
        '<input type="text" id="editNote_${u.id}" placeholder="e.g., Customer dispute approved / Strike reduction granted"',
        '<input type="text" id="editNote_${u.id}" maxlength="200" placeholder="e.g., Customer dispute approved / Strike reduction granted"'
    ),
    # 12. umFreezeReason
    (
        '${!u.is_frozen ? `<input id="umFreezeReason" type="text" placeholder="Reason for freezing..."',
        '${!u.is_frozen ? `<input id="umFreezeReason" type="text" maxlength="200" placeholder="Reason for freezing..."'
    ),
    # 13. chatSearchInput
    (
        '\'<input type="text" id="chatSearchInput" placeholder="Search conversations by name, email, or message..." autocomplete="off"\'',
        '\'<input type="text" id="chatSearchInput" maxlength="50" placeholder="Search conversations by name, email, or message..." autocomplete="off"\''
    ),
    # 14. acUserSearchInput
    (
        '\'<input type="text" id="acUserSearchInput" placeholder="Search by name or email..." oninput="AdminChat.searchUsers(this.value)"\'',
        '\'<input type="text" id="acUserSearchInput" maxlength="50" placeholder="Search by name or email..." oninput="AdminChat.searchUsers(this.value)"\''
    ),
    # 15. acInput
    (
        '\'<input type="text" id="acInput" placeholder="Type a message..." onkeydown="if(event.key===\\\'Enter\\\')AdminChat.send()"\'',
        '\'<input type="text" id="acInput" maxlength="500" placeholder="Type a message..." onkeydown="if(event.key===\\\'Enter\\\')AdminChat.send()"\''
    ),
    # 16. manualSmtpEmail
    (
        '<input id="manualSmtpEmail" type="email" placeholder="Your Gmail address (e.g. yourname@gmail.com)"',
        '<input id="manualSmtpEmail" type="email" maxlength="60" placeholder="Your Gmail address (e.g. yourname@gmail.com)"'
    ),
    # 17. manualSmtpPass
    (
        '<input id="manualSmtpPass" type="password" placeholder="16-character Gmail App Password"',
        '<input id="manualSmtpPass" type="password" maxlength="64" placeholder="16-character Gmail App Password"'
    ),
    # 18. testEmailRecipient
    (
        '<input id="testEmailRecipient" type="email" placeholder="Enter recipient email..."',
        '<input id="testEmailRecipient" type="email" maxlength="60" placeholder="Enter recipient email..."'
    ),
    # 19. settings generator password
    (
        '<input type="password" id="${inputId}" data-key="${s.key}" value="${val}" placeholder="${placeholder}" style="width: 100%; box-sizing: border-box; padding: 12px 42px 12px 14px;',
        '<input type="password" id="${inputId}" data-key="${s.key}" maxlength="255" value="${val}" placeholder="${placeholder}" style="width: 100%; box-sizing: border-box; padding: 12px 42px 12px 14px;'
    ),
    # 20. settings generator public key
    (
        '<input type="text" data-key="${s.key}" value="${val}" placeholder="${placeholder}" style="width: 100%; box-sizing: border-box; padding: 12px 14px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.86rem; font-family: monospace; font-weight: 600; outline: none;">',
        '<input type="text" data-key="${s.key}" maxlength="500" value="${val}" placeholder="${placeholder}" style="width: 100%; box-sizing: border-box; padding: 12px 14px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.86rem; font-family: monospace; font-weight: 600; outline: none;">'
    ),
    # 21. settings generator textarea
    (
        '<textarea data-key="${s.key}" style="width: 100%; box-sizing: border-box; height: ${height}; padding: 12px;',
        '<textarea data-key="${s.key}" maxlength="5000" style="width: 100%; box-sizing: border-box; height: ${height}; padding: 12px;'
    ),
    # 22. settings generator default text
    (
        '<input type="text" data-key="${s.key}" value="${val}" style="width: 100%; box-sizing: border-box; padding: 12px 14px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.88rem; font-weight: 600; outline: none; transition: border-color 0.2s;">',
        '<input type="text" data-key="${s.key}" maxlength="500" value="${val}" style="width: 100%; box-sizing: border-box; padding: 12px 14px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.88rem; font-weight: 600; outline: none; transition: border-color 0.2s;">'
    )
]

all_ok = True
for idx, (old, new) in enumerate(replacements):
    cnt = content.count(old)
    if cnt != 1:
        print(f"FAILED: item {idx+1} found {cnt} occurrences: {old[:50]}...")
        all_ok = False
    else:
        print(f"OK: item {idx+1}")

if not all_ok:
    print("\nAborting: Not all items matched uniquely.")
    sys.exit(1)

for old, new in replacements:
    content = content.replace(old, new, 1)

with open(ADMIN_HTML, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nSUCCESS: All {len(replacements)} Round 3 admin targets patched into admin_app/index.html")
