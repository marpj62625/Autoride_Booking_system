with open('admin_app/index.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

targets = [
    'walkinCustName', 'walkinCustPhone', 'walkinCustAddress', 'walkinEmergName', 'walkinEmergPhone', 'walkinEmergRel',
    'walkinPickupLocation', 'walkinBasePrice', 'walkinExtraFee', 'walkinDiscount', 'walkinAmountPaid', 'walkinCustomerSearch',
    'vPlate', 'vColor', 'vYear', 'vRate', 'vMileageKm', 'vOdometer', 'vGpsDeviceName', 'vGpsDeviceToken',
    'nlFormTitle', 'nlFormCode', 'nlFormDiscount', 'nlFormContent', 'blackoutReason',
    'inspectMileage', 'inspectFuelChargeAmount', 'inspectFuelChargeNotes', 'inspectDriverOTHours', 'inspectDriverOTAmount', 'inspectDriverOTNotes', 'inspectNotes',
    'penaltyAmount', 'penaltyNotes',
    'staffName', 'staffEmail', 'staffPass', 'superAdminEditEmail', 'superAdminCurrentPassword', 'superAdminNewPassword', 'superAdminConfirmPassword',
    'loginEmail', 'loginPass'
]

results = {}
for idx, line in enumerate(lines, 1):
    for t in targets:
        if f'id="{t}"' in line or f"id='{t}'" in line:
            results[t] = (idx, line.strip())

print(f"Found {len(results)} / {len(targets)} targets:")
for t in targets:
    if t in results:
        print(f"Line {results[t][0]:<5} {t:<26} -> {results[t][1][:80]}")
    else:
        print(f"MISSING {t}")
