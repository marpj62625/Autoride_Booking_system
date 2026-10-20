with open('admin_app/index.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

targets = [
    'blackoutReason', 'nlFormTitle', 'nlFormDiscount', 'nlFormCode', 'nlFormContent',
    'staffName', 'staffEmail', 'staffPass',
    'superAdminEditEmail', 'superAdminCurrentPassword', 'superAdminNewPassword', 'superAdminConfirmPassword',
    'inspectMileage', 'inspectFuelChargeAmount', 'inspectFuelChargeNotes', 'inspectDriverOTHours', 'inspectDriverOTAmount', 'inspectDriverOTNotes', 'inspectNotes',
    'loginEmail', 'loginPass',
    'penaltyAmount', 'penaltyNotes',
    'activitySearch', 'pastBookingsSearch', 'archivedBookingsSearch', 'verificationsSearch', 'umSearch', 'fleetCalendarSearch'
]

for idx, line in enumerate(lines, 1):
    for t in targets:
        if t in line:
            print(f"Line {idx}: {line.strip()[:140]}")
