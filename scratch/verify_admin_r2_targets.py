with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

targets = [
    'id="quickTotalPrice"',
    'id="quickAmountPaid"',
    'id="addonPriceInput"',
    'id="insurancePriceInput"',
    'id="locationFeeInput"',
    'id="vehicleSearch"',
    'id="nlSubSearchInput"',
    'id="chatCtrlAiGreeting"',
    'id="chatCtrlAiFallback"',
    'id="faqFormChipLabel"',
    'id="faqFormCategory"',
    'id="faqFormQuestion"',
    'id="faqFormKeywords"',
    'id="faqFormAnswer"',
    'id="settingsSearchInput"',
    'id="addonNameInput"',
    'id="addonDescInput"',
    'id="insuranceNameInput"',
    'id="insuranceDescInput"',
    'id="locationNameInput"',
    'id="locationProvinceInput"',
    'id="locationMuniInput"',
    'id="locationBrgyInput"',
    'id="newInstructionInput"',
    'id="newMobilePassword"',
    'id="confirmMobilePassword"',
    'id="pushNotifTitle"',
    'id="pushNotifBody"',
    'id="staffReqPermReason"',
    'id="gpsConfigDeviceName"',
    'id="gpsConfigToken"',
    'id="gpsConfigServer"'
]

for t in targets:
    cnt = content.count(t)
    print(f"Target {t:<28}: found {cnt} occurrences")
