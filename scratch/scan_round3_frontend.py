from html.parser import HTMLParser

class InputScanner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = []
        self.textareas = []
        self.selects = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == 'input':
            self.inputs.append(attr_dict)
        elif tag == 'textarea':
            self.textareas.append(attr_dict)
        elif tag == 'select':
            self.selects.append(attr_dict)

def scan_file(filepath, label):
    print(f"\n==================== SCANNING {label} ({filepath}) ====================")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = InputScanner()
    parser.feed(content)

    print(f"Total <input> elements: {len(parser.inputs)}")
    print(f"Total <textarea> elements: {len(parser.textareas)}")
    print(f"Total <select> elements: {len(parser.selects)}")

    # 1. Number inputs without min or max
    print("\n--- [1] Number inputs without min or max ---")
    num_issues = 0
    for inp in parser.inputs:
        itype = inp.get('type', 'text').lower()
        if itype == 'number':
            iid = inp.get('id', 'NO_ID')
            iname = inp.get('name', 'NO_NAME')
            has_min = 'min' in inp
            has_max = 'max' in inp
            if not has_min or not has_max:
                print(f"  [MISSING BOUND] id='{iid}' name='{iname}' min={inp.get('min')} max={inp.get('max')}")
                num_issues += 1
    if num_issues == 0:
        print("  All number inputs have min and max bounds!")

    # 2. Text-like inputs without maxlength
    print("\n--- [2] Text-like inputs without maxlength ---")
    text_issues = 0
    for inp in parser.inputs:
        itype = inp.get('type', 'text').lower()
        if itype in ('text', 'search', 'email', 'password', 'tel', 'url'):
            iid = inp.get('id', 'NO_ID')
            iname = inp.get('name', 'NO_NAME')
            if 'maxlength' not in inp:
                print(f"  [MISSING MAXLENGTH] type='{itype}' id='{iid}' name='{iname}' placeholder='{inp.get('placeholder', '')}'")
                text_issues += 1
    if text_issues == 0:
        print("  All text inputs have maxlength!")

    # 3. Textareas without maxlength
    print("\n--- [3] Textareas without maxlength ---")
    ta_issues = 0
    for ta in parser.textareas:
        iid = ta.get('id', 'NO_ID')
        iname = ta.get('name', 'NO_NAME')
        if 'maxlength' not in ta:
            print(f"  [MISSING MAXLENGTH] textarea id='{iid}' name='{iname}' placeholder='{ta.get('placeholder', '')}'")
            ta_issues += 1
    if ta_issues == 0:
        print("  All textareas have maxlength!")

    # 4. File inputs without accept
    print("\n--- [4] File inputs ---")
    file_issues = 0
    for inp in parser.inputs:
        itype = inp.get('type', '').lower()
        if itype == 'file':
            iid = inp.get('id', 'NO_ID')
            iname = inp.get('name', 'NO_NAME')
            acc = inp.get('accept', None)
            if not acc:
                print(f"  [MISSING ACCEPT] file input id='{iid}' name='{iname}'")
                file_issues += 1
            else:
                print(f"  [OK FILE] id='{iid}' accept='{acc}'")

    # 5. Date inputs
    print("\n--- [5] Date inputs ---")
    for inp in parser.inputs:
        itype = inp.get('type', '').lower()
        if itype in ('date', 'datetime-local'):
            iid = inp.get('id', 'NO_ID')
            iname = inp.get('name', 'NO_NAME')
            print(f"  [DATE INPUT] id='{iid}' name='{iname}' min='{inp.get('min')}' max='{inp.get('max')}'")

scan_file('AutorideSystem/customer_mobile/www/index.html', 'CUSTOMER FRONTEND')
scan_file('AutorideSystem/admin_app/index.html', 'ADMIN FRONTEND')
