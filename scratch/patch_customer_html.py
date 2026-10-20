import re

files = ['customer_mobile/www/index.html', 'frontend/index.html']

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update .page rule
    old_page = ".page { display:none; min-height:100vh; padding-bottom:80px; }"
    new_page = """.page {
  display:none;
  min-height:100vh;
  padding-bottom: calc(75px + env(safe-area-inset-bottom, 0px) + 24px) !important;
  box-sizing: border-box;
  scroll-margin-top: calc(64px + env(safe-area-inset-top, 0px));
}"""
    if old_page in content:
        content = content.replace(old_page, new_page)
        print(f"[{file_path}] Replaced .page rule")
    else:
        print(f"[{file_path}] WARNING: old_page not matched directly")

    # 2. Update .bottom-nav
    old_bnav = "position:fixed; bottom:0; left:0; right:0; height:65px; background:var(--bg-card); border-top:1px solid var(--border); display:flex; justify-content:space-around; align-items:center; padding:0 5px; padding-bottom:env(safe-area-inset-bottom); z-index:1000; box-shadow:0 -2px 12px rgba(0,0,0,0.08);"
    new_bnav = "position:fixed; bottom:0; left:0; right:0; height:calc(65px + env(safe-area-inset-bottom, 0px)); background:var(--bg-card); border-top:1px solid var(--border); display:flex; justify-content:space-around; align-items:center; padding:0 5px env(safe-area-inset-bottom, 0px); box-sizing:border-box; z-index:1000; box-shadow:0 -2px 12px rgba(0,0,0,0.08); transition:height 0.2s ease, padding 0.2s ease;"
    if old_bnav in content:
        content = content.replace(old_bnav, new_bnav)
        print(f"[{file_path}] Replaced .bottom-nav rule")
    else:
        print(f"[{file_path}] WARNING: old_bnav not matched directly")

    # 3. Add landscape media query
    landscape_css = """
/* Customer Mobile Landscape & Compact Screen Adaptability */
@media (orientation: landscape) and (max-height: 520px) {
  .bottom-nav {
    height: calc(48px + env(safe-area-inset-bottom, 0px)) !important;
    padding-bottom: env(safe-area-inset-bottom, 0px) !important;
  }
  .bottom-nav button span {
    display: none !important;
  }
  .bottom-nav button i {
    font-size: 1.15rem !important;
  }
  .page {
    padding-bottom: calc(52px + env(safe-area-inset-bottom, 0px) + 16px) !important;
  }
  .auth-box {
    padding: 20px 16px !important;
    margin: 10px auto !important;
  }
}
"""
    if "/* Customer Mobile Landscape" not in content:
        # Insert before </style>
        first_style_end = content.find("</style>")
        if first_style_end != -1:
            content = content[:first_style_end] + "\n" + landscape_css + "\n" + content[first_style_end:]
            print(f"[{file_path}] Added customer landscape media query")
        else:
            print(f"[{file_path}] WARNING: </style> not found")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[{file_path}] Saved successfully")
