with open('AutorideSystem/customer_mobile/www/js/app.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if 'inspMileage' in line and '<input' in line:
            print(f"Customer app.js Line {idx+1}: {line.strip()[:120]}")

with open('AutorideSystem/admin_app/index.html', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        for target in ['fleetVehicleRateInput', 'extRfAmt_', 'extRfRef_', 'refundRefInput_', 'umEditName', 'umEditPhone', 'umLoyaltyInput', 'umNewPass', 'editNote_', 'umFreezeReason', 'chatSearchInput', 'acUserSearchInput', 'acInput', 'manualSmtpEmail', 'manualSmtpPass', 'testEmailRecipient']:
            if target in line and '<input' in line:
                print(f"Admin HTML Line {idx+1} ({target}): {line.strip()[:120]}")
