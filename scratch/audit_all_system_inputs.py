import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def audit_file(filepath, label):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"=== {label} ({filepath}) ===")
    
    # 1. Navigation / Pages / Views
    nav_links = re.findall(r'<a[^>]+href=[\'"]#([^\'"]+)[\'"][^>]*>(.*?)</a>', content, re.DOTALL)
    print(f"--- Nav Links (#anchors) ---")
    for href, text in nav_links[:20]:
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        if clean_text:
            print(f"  #{href} -> {clean_text}")

    # 2. Sections / Views
    sections = re.findall(r'<(?:div|section)[^>]+id=[\'"]([^\'"]*(?:page|section|view|tab|modal)[^\'"]*)[\'"]', content, re.IGNORECASE)
    print(f"\n--- Key Sections / Views / Tabs / Modals ({len(sections)}) ---")
    for s in sorted(set(sections))[:35]:
        print(f"  {s}")

    # 3. Forms
    forms = re.findall(r'<form[^>]*id=[\'"]([^\'"]+)[\'"][^>]*>', content)
    print(f"\n--- Forms ({len(forms)}) ---")
    for fm in forms:
        print(f"  Form ID: {fm}")

    # 4. Inputs by type
    inputs = re.findall(r'<input[^>]+name=[\'"]([^\'"]+)[\'"][^>]*type=[\'"]([^\'"]+)[\'"]|<input[^>]+type=[\'"]([^\'"]+)[\'"][^>]*name=[\'"]([^\'"]+)[\'"]|<input[^>]+id=[\'"]([^\'"]+)[\'"]', content)
    print(f"\n--- Sample Inputs ({len(inputs)}) ---")
    for inp in inputs[:30]:
        print(f"  Input: {inp}")

    # 5. Buttons / Actions
    buttons = re.findall(r'<button[^>]+onclick=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</button>', content, re.DOTALL)
    print(f"\n--- Total Action Buttons with onclick: {len(buttons)} ---")
    actions = set()
    for fn, txt in buttons:
        fn_name = fn.split('(')[0].strip()
        clean_txt = re.sub(r'<[^>]+>', '', txt).strip()
        actions.add(f"{fn_name} [{clean_txt[:25]}]")
    for act in sorted(list(actions))[:30]:
        print(f"  {act}")
    print("\n" + "="*50 + "\n")

audit_file('admin_app/index.html', 'ADMIN WEB / MOBILE')
audit_file('customer_app/index.html', 'CUSTOMER WEB')
audit_file('customer_mobile/www/index.html', 'CUSTOMER MOBILE')
