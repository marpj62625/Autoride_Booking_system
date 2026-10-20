with open('AutorideSystem/backend/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def find_func_or_route(query):
    print(f"=== SEARCH: {query} ===")
    for idx, line in enumerate(lines):
        if query in line:
            print(f"Line {idx+1}: {line.strip()[:100]}")

find_func_or_route("def upload_license")
find_func_or_route("def update_license_info")
find_func_or_route("def save_license_details")
find_func_or_route("def process_refund")
find_func_or_route("def mark_booking_paid")
find_func_or_route("def verify_email")
find_func_or_route("def user_forgot_password")
find_func_or_route("def user_change_password")
find_func_or_route("def change_admin_password")
find_func_or_route("def create_admin")
find_func_or_route("def update_admin")
find_func_or_route("driver_fee")
