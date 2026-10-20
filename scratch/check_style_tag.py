with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos_modal_css = text.find('#desktopCameraModal {')
print('pos_modal_css:', pos_modal_css)

# find previous <style and next </style
pos_style_open = text.rfind('<style', 0, pos_modal_css)
pos_style_close = text.find('</style>', pos_modal_css)

print('pos_style_open:', pos_style_open)
print('pos_style_close:', pos_style_close)

# check if any other </style> between open and modal_css
other_close = text.rfind('</style>', pos_style_open, pos_modal_css)
print('other_close between open and modal_css:', other_close)
