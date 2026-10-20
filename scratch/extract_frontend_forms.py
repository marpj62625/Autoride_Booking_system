import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')

def extract_forms(dirpath):
    print(f"\n=================== FORMS IN {dirpath} ===================")
    for root, dirs, files in os.walk(dirpath):
        for f in files:
            if f.endswith('.html'):
                fpath = os.path.join(root, f)
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                    c = fp.read()
                
                # Find inputs with id or name
                inputs = re.findall(r'<(?:input|select|textarea)[^>]+(?:id|name)=[\'"]([^\'"]+)[\'"][^>]*>', c)
                forms = re.findall(r'<form[^>]+id=[\'"]([^\'"]+)[\'"]', c)
                buttons = re.findall(r'<button[^>]+(?:id=[\'"]([^\'"]+)[\'"]|onclick=[\'"]([^\'"]+)[\'"])', c)
                
                if inputs or forms:
                    rel = os.path.relpath(fpath, dirpath)
                    print(f"\n--- File: {rel} ---")
                    if forms:
                        print(f"  Forms: {forms}")
                    uniq_inputs = sorted(list(set(inputs)))
                    print(f"  Inputs/Selects ({len(uniq_inputs)}): {uniq_inputs}")

extract_forms('frontend')
