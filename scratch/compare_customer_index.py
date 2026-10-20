with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text_cm = f.read()

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text_fe = f.read()

print('customer_mobile index.html len:', len(text_cm))
print('frontend index.html len:', len(text_fe))

import re
m_cm = re.search(r'\.bottom-nav\s*\{([^}]+)\}', text_cm)
if m_cm:
    print('customer_mobile .bottom-nav:', m_cm.group(1).strip().replace('\n', ' '))

m_fe = re.search(r'\.bottom-nav\s*\{([^}]+)\}', text_fe)
if m_fe:
    print('frontend .bottom-nav:', m_fe.group(1).strip().replace('\n', ' '))
