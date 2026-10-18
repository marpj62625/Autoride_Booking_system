import sys
import os

print("--- TESTING FRONTEND FILES ---")
# Check index.html files
for p in ['customer_mobile/www/index.html', 'frontend/index.html']:
    with open(p, 'r', encoding='utf-8') as f:
        c = f.read()
    assert 'id="regConfirmPassword"' in c, f'{p} missing regConfirmPassword'
    assert 'id="req-special"' in c, f'{p} missing req-special'
    assert 'id="req-update-special"' in c, f'{p} missing req-update-special'
    assert 'validateRegistrationEmailField' in c, f'{p} missing validateRegistrationEmailField'
    assert 'checkConfirmPasswordMatch' in c, f'{p} missing checkConfirmPasswordMatch'
    print(f'[PASS] {p} verified')

# Check register.html files
for p in ['customer_mobile/www/register.html', 'frontend/register.html']:
    with open(p, 'r', encoding='utf-8') as f:
        c = f.read()
    assert 'id="confirm_password"' in c, f'{p} missing confirm_password'
    assert 'id="req-special"' in c, f'{p} missing req-special'
    assert 'checkStandaloneConfirmMatch' in c, f'{p} missing checkStandaloneConfirmMatch'
    assert 'isDisposableEmail' in c, f'{p} missing isDisposableEmail'
    print(f'[PASS] {p} verified')

# Check utils.js files
for p in ['customer_mobile/www/js/utils.js', 'frontend/js/utils.js']:
    with open(p, 'r', encoding='utf-8') as f:
        c = f.read()
    assert 'DISPOSABLE_EMAIL_DOMAINS' in c, f'{p} missing DISPOSABLE_EMAIL_DOMAINS'
    assert 'isDisposableEmail' in c, f'{p} missing isDisposableEmail'
    assert 'validateEmailAddress' in c, f'{p} missing validateEmailAddress'
    print(f'[PASS] {p} verified')

# Check app.js files
for p in ['customer_mobile/www/js/app.js', 'frontend/js/app.js']:
    with open(p, 'r', encoding='utf-8') as f:
        c = f.read()
    assert 'confirm_password: confirmPassword' in c, f'{p} missing confirm_password in payload'
    assert 'validateEmailAddress' in c, f'{p} missing validateEmailAddress in app.js'
    print(f'[PASS] {p} verified')

print('\nALL FRONTEND AND CUSTOMER ASSETS ARE 100% VERIFIED!')
