import sys

ADMIN_HTML = 'AutorideSystem/admin_app/index.html'

with open(ADMIN_HTML, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    # 1. quickTotalPrice
    (
        '<input type="number" id="quickTotalPrice" step="50" min="0" oninput="FleetCalendar.recalcQuickBalance()"',
        '<input type="number" id="quickTotalPrice" step="50" min="0" max="500000" oninput="FleetCalendar.recalcQuickBalance()"'
    ),
    # 2. quickAmountPaid
    (
        '<input type="number" id="quickAmountPaid" step="50" min="0" oninput="FleetCalendar.recalcQuickBalance()"',
        '<input type="number" id="quickAmountPaid" step="50" min="0" max="500000" oninput="FleetCalendar.recalcQuickBalance()"'
    ),
    # 3. addonPriceInput
    (
        '<input type="number" id="addonPriceInput" placeholder="e.g. 150"',
        '<input type="number" id="addonPriceInput" min="0" max="10000" placeholder="e.g. 150"'
    ),
    # 4. insurancePriceInput
    (
        '<input type="number" id="insurancePriceInput" placeholder="e.g. 500"',
        '<input type="number" id="insurancePriceInput" min="0" max="20000" placeholder="e.g. 500"'
    ),
    # 5. locationFeeInput
    (
        '<input type="number" id="locationFeeInput" placeholder="0" value="0"',
        '<input type="number" id="locationFeeInput" min="0" max="10000" placeholder="0" value="0"'
    ),
    # 6. vehicleSearch
    (
        '<input id="vehicleSearch" type="text" placeholder="Search brand, model or plate..."',
        '<input id="vehicleSearch" type="text" maxlength="50" placeholder="Search brand, model or plate..."'
    ),
    # 7. nlSubSearchInput
    (
        '<input type="text" id="nlSubSearchInput" oninput="NewsletterAdmin.filterSubscribers()"',
        '<input type="text" id="nlSubSearchInput" maxlength="60" oninput="NewsletterAdmin.filterSubscribers()"'
    ),
    # 8. chatCtrlAiGreeting
    (
        '<textarea id="chatCtrlAiGreeting" rows="3"',
        '<textarea id="chatCtrlAiGreeting" maxlength="500" rows="3"'
    ),
    # 9. chatCtrlAiFallback
    (
        '<textarea id="chatCtrlAiFallback" rows="3"',
        '<textarea id="chatCtrlAiFallback" maxlength="500" rows="3"'
    ),
    # 10. faqFormChipLabel
    (
        '<input type="text" id="faqFormChipLabel" placeholder="e.g. 💳 20% DP &amp; Balance"',
        '<input type="text" id="faqFormChipLabel" maxlength="40" placeholder="e.g. 💳 20% DP &amp; Balance"'
    ),
    # 11. faqFormCategory
    (
        '<input type="text" id="faqFormCategory" placeholder="e.g. payment, general, fuel"',
        '<input type="text" id="faqFormCategory" maxlength="30" placeholder="e.g. payment, general, fuel"'
    ),
    # 12. faqFormQuestion
    (
        '<input type="text" id="faqFormQuestion" placeholder="e.g. How does the 20% downpayment and balance payment work?"',
        '<input type="text" id="faqFormQuestion" maxlength="150" placeholder="e.g. How does the 20% downpayment and balance payment work?"'
    ),
    # 13. faqFormKeywords
    (
        '<input type="text" id="faqFormKeywords" placeholder="e.g. 20%, downpayment, dp, balance, upon pickup"',
        '<input type="text" id="faqFormKeywords" maxlength="200" placeholder="e.g. 20%, downpayment, dp, balance, upon pickup"'
    ),
    # 14. faqFormAnswer
    (
        '<textarea id="faqFormAnswer" rows="5" placeholder="Enter clear policy explanation or instructions..."',
        '<textarea id="faqFormAnswer" maxlength="1000" rows="5" placeholder="Enter clear policy explanation or instructions..."'
    ),
    # 15. settingsSearchInput
    (
        '<input type="text" id="settingsSearchInput" placeholder="Search settings (e.g. strike, suspension, mileage, chat, discount)..."',
        '<input type="text" id="settingsSearchInput" maxlength="60" placeholder="Search settings (e.g. strike, suspension, mileage, chat, discount)..."'
    ),
    # 16. addonNameInput
    (
        '<input type="text" id="addonNameInput" placeholder="e.g. GPS Navigator"',
        '<input type="text" id="addonNameInput" maxlength="50" placeholder="e.g. GPS Navigator"'
    ),
    # 17. addonDescInput
    (
        '<textarea id="addonDescInput" placeholder="Briefly describe this add-on..." rows="3"',
        '<textarea id="addonDescInput" maxlength="250" placeholder="Briefly describe this add-on..." rows="3"'
    ),
    # 18. insuranceNameInput
    (
        '<input type="text" id="insuranceNameInput" placeholder="e.g. Standard Protection"',
        '<input type="text" id="insuranceNameInput" maxlength="50" placeholder="e.g. Standard Protection"'
    ),
    # 19. insuranceDescInput
    (
        '<textarea id="insuranceDescInput" placeholder="Briefly describe what this insurance covers..." rows="3"',
        '<textarea id="insuranceDescInput" maxlength="250" placeholder="Briefly describe what this insurance covers..." rows="3"'
    ),
    # 20. locationNameInput
    (
        '<input type="text" id="locationNameInput" placeholder="e.g. San Pablo City, Laguna"',
        '<input type="text" id="locationNameInput" maxlength="60" placeholder="e.g. San Pablo City, Laguna"'
    ),
    # 21. locationProvinceInput
    (
        '<input type="text" id="locationProvinceInput" placeholder="Laguna"',
        '<input type="text" id="locationProvinceInput" maxlength="40" placeholder="Laguna"'
    ),
    # 22. locationMuniInput
    (
        '<input type="text" id="locationMuniInput" placeholder="San Pablo City"',
        '<input type="text" id="locationMuniInput" maxlength="40" placeholder="San Pablo City"'
    ),
    # 23. locationBrgyInput
    (
        '<input type="text" id="locationBrgyInput" placeholder="Leave empty for all"',
        '<input type="text" id="locationBrgyInput" maxlength="40" placeholder="Leave empty for all"'
    ),
    # 24. newInstructionInput
    (
        '<input type="text" id="newInstructionInput" placeholder="e.g. Bring 2 valid IDs upon pickup."',
        '<input type="text" id="newInstructionInput" maxlength="150" placeholder="e.g. Bring 2 valid IDs upon pickup."'
    ),
    # 25. newMobilePassword
    (
        '<input id="newMobilePassword" type="password" placeholder="********"',
        '<input id="newMobilePassword" type="password" maxlength="64" placeholder="********"'
    ),
    # 26. confirmMobilePassword
    (
        '<input id="confirmMobilePassword" type="password" placeholder="********"',
        '<input id="confirmMobilePassword" type="password" maxlength="64" placeholder="********"'
    ),
    # 27. pushNotifTitle
    (
        '<input type="text" id="pushNotifTitle" placeholder="e.g. System Update"',
        '<input type="text" id="pushNotifTitle" maxlength="80" placeholder="e.g. System Update"'
    ),
    # 28. pushNotifBody
    (
        '<textarea id="pushNotifBody" rows="4" placeholder="Type your message here..."',
        '<textarea id="pushNotifBody" maxlength="500" rows="4" placeholder="Type your message here..."'
    ),
    # 29. staffReqPermReason
    (
        '<textarea id="staffReqPermReason" placeholder="e.g. Need access to manage incoming holiday blackout dates for customers..."',
        '<textarea id="staffReqPermReason" maxlength="250" placeholder="e.g. Need access to manage incoming holiday blackout dates for customers..."'
    ),
    # 30. gpsConfigDeviceName
    (
        '<input type="text" id="gpsConfigDeviceName" placeholder="e.g. Tracker Unit 1 (ESP32)"',
        '<input type="text" id="gpsConfigDeviceName" maxlength="50" placeholder="e.g. Tracker Unit 1 (ESP32)"'
    ),
    # 31. gpsConfigToken
    (
        '<input type="password" id="gpsConfigToken" placeholder="Paste Blynk Auth Token from hardware / console"',
        '<input type="password" id="gpsConfigToken" maxlength="50" placeholder="Paste Blynk Auth Token from hardware / console"'
    ),
    # 32. gpsConfigServer
    (
        '<input type="text" id="gpsConfigServer" value="sgp1.blynk.cloud"',
        '<input type="text" id="gpsConfigServer" maxlength="50" value="sgp1.blynk.cloud"'
    ),
]

all_ok = True
for idx, (old, new) in enumerate(replacements):
    cnt = content.count(old)
    if cnt != 1:
        print(f"ERROR: item {idx+1} found {cnt} occurrences of: {old[:50]}...")
        all_ok = False
    else:
        print(f"OK: item {idx+1} verified uniquely")

if not all_ok:
    print("\nAborting patch: some targets were not unique.")
    sys.exit(1)

for old, new in replacements:
    content = content.replace(old, new, 1)

with open(ADMIN_HTML, 'w', encoding='utf-8') as f:
    f.write(content)

print("\nSUCCESS: All 32 targets patched into admin_app/index.html")
