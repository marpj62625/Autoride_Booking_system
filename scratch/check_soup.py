from bs4 import BeautifulSoup

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
modal = soup.find(id='desktopCameraModal')
if modal is None:
    print("Modal NOT FOUND in soup!")
else:
    print("Modal found in soup!")
    print("Modal tag:", modal.name, modal.attrs)
    parents = []
    p = modal.parent
    while p:
        parents.append(f"{p.name} id='{p.get('id', '')}' class='{p.get('class', '')}'")
        p = p.parent
    print("Parents:", " -> ".join(parents))
