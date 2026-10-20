with open("backend/app.py", "r", encoding="utf-8") as f:
    backend_code = f.read()

def show_func(fn_name, n_lines=40):
    pos = backend_code.find(f"def {fn_name}(")
    if pos == -1:
        print(f"Function {fn_name} not found!")
        return
    line_no = backend_code[:pos].count('\n') + 1
    snippet = backend_code[pos:pos+1500]
    lines = snippet.split('\n')[:n_lines]
    print(f"\n==================== {fn_name} (Line {line_no}) ====================")
    for i, l in enumerate(lines):
        print(f"{line_no + i}: {l}")

targets = [
    "admin_reset_user_violations",
    "chat_endpoint",
    "chat_mark_read",
    "edit_penalty",
    "reject_driver",
    "save_payment",
    "update_addon",
    "update_license_info",
    "update_vehicle_location",
    "add_vehicle",
    "update_vehicle"
]

for t in targets:
    show_func(t, 25)
