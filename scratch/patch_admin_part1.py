import re

file_path = 'admin_app/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Scope overflow: hidden on html, body to body.admin-login-active
old_login_style = """    /* Prevent default margins and scrolling on body when login overlay is active */
    html, body {
        margin: 0;
        padding: 0;
        height: 100%;
        width: 100%;
        overflow: hidden;
    }"""

new_login_style = """    /* Responsive viewport & body setup: only lock scrolling when login overlay is explicitly visible */
    html {
        margin: 0;
        padding: 0;
        width: 100%;
        min-height: 100%;
        overflow-x: hidden;
    }
    body {
        margin: 0;
        padding: 0;
        width: 100%;
        min-height: 100vh;
        overflow-x: hidden;
    }
    body.admin-login-locked {
        overflow: hidden !important;
    }"""

if old_login_style in content:
    content = content.replace(old_login_style, new_login_style)
    print("Replaced login style on html, body")
else:
    print("WARNING: old_login_style not found directly, checking regex")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated admin_app/index.html part 1")
