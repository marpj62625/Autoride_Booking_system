with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos_style_open = text.find('<style>')
pos_modal_css = text.find('#desktopCameraModal {')

sub = text[pos_style_open:pos_modal_css]
opens = sub.count('{')
closes = sub.count('}')
print(f"Before #desktopCameraModal: opens={opens}, closes={closes}, diff={opens - closes}")
