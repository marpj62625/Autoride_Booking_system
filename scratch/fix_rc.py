# coding: utf-8
import re, os

# U+FFFD as latin-1 byte sequence (how it's stored in the mixed-encoding file)
REPL = chr(0xef) + chr(0xbf) + chr(0xbd)

def fix(path):
    raw = open(path, 'rb').read()
    # Fix lone 0x97 byte (Windows-1252 em dash)
    raw = raw.replace(b'\x97', b'-')
    text = raw.decode('latin-1')

    # Password placeholder: 8 replacement chars -> 8 asterisks
    text = text.replace(REPL * 8, '********')

    subs = [
        ('backgrounds ' + REPL + ' keep',    'backgrounds - keep'),
        ('containers '  + REPL + ' keep',    'containers - keep'),
        ('Settings tab ' + REPL + ' stat',   'Settings tab - stat'),
        ('overrides '   + REPL + ' restore', 'overrides - restore'),
        ('Daily Rate '  + REPL + ' half',    'Daily Rate - half'),
        ('Location '    + REPL + ' full',    'Location - full'),
        ('Status '      + REPL + ' full',    'Status - full'),
        ('preference '  + REPL + ' default', 'preference - default'),
        ('modal open '  + REPL + ' clear',   'modal open - clear'),
        ('button '      + REPL + ' uses',    'button - uses'),
        ('tab '         + REPL + ' show exit','tab - show exit'),
        ('Chart '       + REPL + ' use',     'Chart - use'),
        ('plate'        + REPL + '"',        'plate..."'),
        ('details'      + REPL + '"',        'details..."'),
        ('(max 4 '      + REPL + ' first',   '(max 4 - first'),
        ("}) : '"       + REPL + "';",       "}) : 'N/A';"),
        ("'refreshing"  + REPL + "'",        "'refreshing...'"),
        ("u.phone || '" + REPL + "'",        "u.phone || 'N/A'"),
        ('globals '     + REPL + ' defined', 'globals - defined'),
    ]
    for old, new in subs:
        text = text.replace(old, new)

    # Stat card display value: ;"><REPL></div>  ->  ;"> - </div>
    text = re.sub(re.escape(';">' + REPL + '</div>'), ';">-</div>', text)

    # JS string literals with lone REPL -> '-'
    text = re.sub("'" + re.escape(REPL) + "'", "'-'", text)
    text = re.sub('"' + re.escape(REPL) + '"', '"-"', text)

    remaining = text.count(REPL)
    print(f'  {path}: {remaining} REPL chars remaining')
    if remaining:
        for m in re.finditer(re.escape(REPL), text):
            p = m.start()
            print(f'    {repr(text[max(0,p-40):p+41])}')

    # Re-encode: latin-1 bytes -> interpret as utf-8 -> write as clean utf-8
    out = text.encode('latin-1').decode('utf-8', errors='replace')
    open(path, 'wb').write(out.encode('utf-8'))
    print(f'  Written: {path}')

fix('admin_mobile/www/index.html')
if os.path.exists('admin_mobile/android/app/src/main/assets/public/index.html'):
    fix('admin_mobile/android/app/src/main/assets/public/index.html')
