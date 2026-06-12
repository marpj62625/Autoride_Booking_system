import sys
sys.path.append('backend')
from app import send_receipt_email

details = {
    'id': 999,
    'full_name': 'Flow G You',
    'brand': 'Toyota',
    'model': 'Vios',
    'start_date': '2026-05-28',
    'end_date': '2026-05-30',
    'total_price': 5000,
    'amount_paid': 5000,
    'base_price': 4000,
    'addon_price': 1000,
    'addons': '["GPS Navigation"]',
    'payment_type': 'Full',
    'method': 'Cash',
    'reference_number': 'TEST_REF_999',
    'insurance_price': 0,
    'discount_amount': 0,
    'balance_amount': 0,
    'insurance_type': 'Basic Protection'
}

try:
    send_receipt_email('flowgyou@gmail.com', details)
    print("Function ran successfully without exceptions.")
except Exception as e:
    print("ERROR RUNNING FUNCTION:", str(e))
