import re

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

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

with open('scratch/admin_r2_tags.txt', 'w', encoding='utf-8') as out:
    for t in targets:
        for idx, line in enumerate(lines, 1):
            if t in line:
                out.write(f"Line {idx} ({t}):\n{line}\n")
                break

print("Extracted all 32 tags to scratch/admin_r2_tags.txt!")
