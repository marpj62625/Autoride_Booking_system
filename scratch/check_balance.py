with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos_modal = text.find('id="desktopCameraModal"')
pos_chpwd = text.find('id="page-change-password"')

print("page-change-password at:", pos_chpwd)
print("desktopCameraModal at:", pos_modal)

# Check if desktopCameraModal is before or after the closing tag of page-change-password
# Let's count div balance between pos_chpwd and pos_modal
sub = text[pos_chpwd:pos_modal]
opens = sub.count('<div')
closes = sub.count('</div>')
print(f"Between change-pwd and modal: opens={opens}, closes={closes}, net open={opens - closes}")
