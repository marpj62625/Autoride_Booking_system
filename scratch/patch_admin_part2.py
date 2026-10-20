import re

file_path = 'admin_app/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Patch .mobile-header
header_pattern = r'(\.mobile-header\s*\{)([^}]+)(\})'
m_h = re.search(header_pattern, content)
if m_h:
    new_header_inner = """
            height: calc(64px + env(safe-area-inset-top, 0px));
            padding: env(safe-area-inset-top, 0px) 16px 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background: rgba(255, 255, 255, 0.96);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            z-index: 1000;
            box-sizing: border-box;
            transition: height 0.2s ease, padding 0.2s ease;
        """
    content = content[:m_h.start(2)] + new_header_inner + content[m_h.end(2):]
    print("Patched .mobile-header")
else:
    print("FAILED to find .mobile-header")

# 2. Patch .main-content
main_pattern = r'(\.main-content\s*\{)([^}]+)(\})'
m_m = re.search(main_pattern, content)
if m_m:
    new_main_inner = """
            flex: 1;
            padding-top: calc(76px + env(safe-area-inset-top, 0px)) !important;
            padding-left: calc(16px + env(safe-area-inset-left, 0px)) !important;
            padding-right: calc(16px + env(safe-area-inset-right, 0px)) !important;
            padding-bottom: calc(88px + env(safe-area-inset-bottom, 0px) + 24px) !important;
            width: 100%;
            max-width: 100vw;
            box-sizing: border-box;
            overflow-y: auto;
            -webkit-overflow-scrolling: touch;
        """
    content = content[:m_m.start(2)] + new_main_inner + content[m_m.end(2):]
    print("Patched .main-content")
else:
    print("FAILED to find .main-content")

# 3. Patch .bottom-nav
bottom_nav_pattern = r'(\.bottom-nav\s*\{)([^}]+)(\})'
m_b = re.search(bottom_nav_pattern, content)
if m_b:
    new_bottom_inner = """
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: calc(68px + env(safe-area-inset-bottom, 0px));
            background: rgba(255, 255, 255, 0.96);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-around;
            align-items: center;
            padding: 0 4px env(safe-area-inset-bottom, 0px);
            box-sizing: border-box;
            z-index: 1000;
            transition: height 0.2s ease, padding 0.2s ease;
        """
    content = content[:m_b.start(2)] + new_bottom_inner + content[m_b.end(2):]
    print("Patched .bottom-nav")
else:
    print("FAILED to find .bottom-nav")

# 4. Add tab-content scroll-margin and landscape media query right after .bottom-nav
extra_css = """
        /* Universal tab-content responsive layout & scroll anchor offset */
        .tab-content {
            scroll-margin-top: calc(76px + env(safe-area-inset-top, 0px));
            max-width: 100%;
            box-sizing: border-box;
            word-wrap: break-word;
        }

        /* Mobile Landscape & Short Screen Responsiveness */
        @media (orientation: landscape) and (max-height: 550px) {
            .mobile-header {
                height: calc(46px + env(safe-area-inset-top, 0px)) !important;
                padding: env(safe-area-inset-top, 0px) 12px 0 !important;
            }
            .mobile-header .logo-wrap img {
                width: 24px !important;
                height: 24px !important;
            }
            .mobile-header .logo-wrap span {
                font-size: 0.9rem !important;
            }
            .mobile-header .admin-badge {
                padding: 1px 6px !important;
                font-size: 0.65rem !important;
            }
            .main-content {
                padding-top: calc(52px + env(safe-area-inset-top, 0px)) !important;
                padding-bottom: calc(54px + env(safe-area-inset-bottom, 0px) + 12px) !important;
                overflow-y: auto !important;
            }
            .tab-content {
                scroll-margin-top: calc(52px + env(safe-area-inset-top, 0px)) !important;
            }
            .bottom-nav {
                height: calc(48px + env(safe-area-inset-bottom, 0px)) !important;
                padding-bottom: env(safe-area-inset-bottom, 0px) !important;
            }
            .bottom-nav .nav-item span {
                display: none !important;
            }
            .bottom-nav .nav-item i {
                font-size: 1.15rem !important;
            }
            .page-title {
                font-size: 1.25rem !important;
                margin-bottom: 2px !important;
            }
            .page-subtitle {
                display: none !important;
            }
            #fleet-calendar {
                padding: 8px !important;
            }
            #fleet-calendar .fc-header {
                flex-wrap: wrap !important;
                gap: 6px !important;
            }
        }
"""
# Insert extra_css after .bottom-nav definition
m_b_new = re.search(r'\.bottom-nav\s*\{[^}]+\}', content)
if m_b_new:
    insert_pos = m_b_new.end()
    content = content[:insert_pos] + "\n" + extra_css + "\n" + content[insert_pos:]
    print("Inserted tab-content and landscape CSS")
else:
    print("FAILED to insert extra CSS")

# 5. Patch switchTab fleet-calendar innerHeight check and scroll-to-top
old_switch = """                const target = document.getElementById(tabId);
            if (target) {
                target.style.display = 'block';
                const mainContentEl = document.querySelector('.main-content');
                if (mainContentEl) {
                    if (tabId === 'fleet-calendar' && window.innerWidth >= 769) {
                        mainContentEl.style.overflowY = 'hidden';
                    } else {
                        mainContentEl.style.overflowY = '';
                    }
                }"""

new_switch = """                const target = document.getElementById(tabId);
            if (target) {
                target.style.display = 'block';
                const mainContentEl = document.querySelector('.main-content');
                if (mainContentEl) {
                    mainContentEl.scrollTo({ top: 0, behavior: 'instant' });
                    // Lock outer overflow only on genuine desktop screens (both width >= 769 AND height >= 600)
                    if (tabId === 'fleet-calendar' && window.innerWidth >= 769 && window.innerHeight >= 600) {
                        mainContentEl.style.overflowY = 'hidden';
                    } else {
                        mainContentEl.style.overflowY = 'auto';
                    }
                }"""

if old_switch in content:
    content = content.replace(old_switch, new_switch)
    print("Patched switchTab scroll-to-top and overflow check")
else:
    print("WARNING: switchTab pattern not matched directly, inspecting")

# 6. Patch Settings Email Connector button
old_btn = """<button type="button" onclick="toggleSmtpConfigModal()" class="btn-premium" style="padding: 10px 18px; font-size: 0.82rem; font-weight: 700; background: var(--primary); color: white; border-radius: 10px; cursor: pointer; white-space: nowrap; display: inline-flex; align-items: center; gap: 8px;">
                                <i class="fas fa-plug"></i> Open Re-Authorize &amp; Email Tools
                            </button>"""

new_btn = """<button type="button" onclick="toggleSmtpConfigModal()" class="btn-premium" style="padding: 10px 14px; font-size: 0.82rem; font-weight: 700; background: var(--primary); color: white; border-radius: 10px; cursor: pointer; max-width: 100%; white-space: normal; text-align: center; display: inline-flex; align-items: center; justify-content: center; gap: 8px; box-sizing: border-box;">
                                <i class="fas fa-plug"></i> Open Re-Authorize &amp; Email Tools
                            </button>"""

if old_btn in content:
    content = content.replace(old_btn, new_btn)
    print("Patched Settings Email Connector button")
else:
    print("WARNING: old_btn not matched directly")

# 7. Patch settings-fields-grid minmax
old_grid = """<div class="settings-fields-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 16px; margin-top: 14px;">"""
new_grid = """<div class="settings-fields-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 230px), 1fr)); gap: 16px; margin-top: 14px;">"""

if old_grid in content:
    content = content.replace(old_grid, new_grid)
    print("Patched settings-fields-grid minmax")
else:
    print("WARNING: old_grid not matched directly")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Saved patched admin_app/index.html")
