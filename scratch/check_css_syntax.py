with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos_modal_css = text.find('#desktopCameraModal {')
print(text[pos_modal_css - 300 : pos_modal_css + 600])
