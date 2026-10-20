import os

def patch_sidebar(filepath):
    print(f"Patching closable sidebar in {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add close button in drawer-header
    old_header = """<div class="side-drawer" id="sideDrawer">



    <div class="drawer-header">



        <div class="logo-wrap" style="margin-bottom: 10px;">"""

    new_header = """<div class="side-drawer" id="sideDrawer">

    <div class="drawer-header" style="position: relative;">
        <button type="button" onclick="toggleDrawer(false)" class="drawer-close-btn" title="Close Sidebar"
                style="position: absolute; right: 14px; top: 18px; width: 34px; height: 34px; border-radius: 8px; border: 1px solid var(--border); background: rgba(0,0,0,0.04); color: var(--text-main); font-size: 1rem; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; z-index: 10;"
                onmouseover="this.style.background='var(--border)';"
                onmouseout="this.style.background='rgba(0,0,0,0.04)';">
            <i class="fas fa-times"></i>
        </button>

        <div class="logo-wrap" style="margin-bottom: 10px;">"""

    if old_header in content:
        content = content.replace(old_header, new_header, 1)
        print("  Added Close (X) button to drawer header successfully")
    else:
        print("  Warning: old_header not found, checking alternatives...")
        # Try normalized spacing
        import re
        pattern = r'<div class="side-drawer" id="sideDrawer">\s*<div class="drawer-header">\s*<div class="logo-wrap" style="margin-bottom: 10px;">'
        if re.search(pattern, content):
            content = re.sub(pattern, new_header, content, count=1)
            print("  Added Close (X) button via regex successfully")

    # 2. Add collapse menu item before closing drawer
    old_logout = """<a href="javascript:void(0);" class="drawer-item" onclick="adminAuth.logout()" style="color: #ef4444;"><i class="fas fa-sign-out-alt"></i> Logout</a>"""
    new_logout = """<a href="javascript:void(0);" class="drawer-item" onclick="adminAuth.logout()" style="color: #ef4444;"><i class="fas fa-sign-out-alt"></i> Logout</a>

            <a href="javascript:void(0);" class="drawer-item" onclick="toggleDrawer(false)" style="color: var(--text-muted); font-size: 0.8rem; border-top: 1px dashed var(--border); margin-top: 8px; padding-top: 10px;">
                <i class="fas fa-chevron-left"></i> Close Sidebar
            </a>"""

    if old_logout in content:
        content = content.replace(old_logout, new_logout, 1)
        print("  Added bottom Close Sidebar link successfully")

    # 3. Enhance toggleDrawer function
    old_fn = """    function toggleDrawer(show) {



        const drawer = document.getElementById('sideDrawer');



        const overlay = document.getElementById('drawerOverlay');



        if (show) {



            overlay.style.display = 'block';



            setTimeout(() => {



                overlay.style.opacity = '1';



                drawer.style.left = '0';



            }, 10);



        } else {



            drawer.style.left = '-280px';



            overlay.style.opacity = '0';



            setTimeout(() => overlay.style.display = 'none', 300);



        }



    }"""

    new_fn = """    function toggleDrawer(show) {
        const drawer = document.getElementById('sideDrawer');
        const overlay = document.getElementById('drawerOverlay');
        if (!drawer) return;

        const isOpen = (drawer.style.left === '0px' || drawer.classList.contains('open'));
        const shouldOpen = (show !== undefined) ? !!show : !isOpen;

        if (shouldOpen) {
            drawer.classList.add('open');
            if (overlay) {
                overlay.style.display = 'block';
                setTimeout(() => overlay.style.opacity = '1', 10);
            }
            drawer.style.left = '0px';
        } else {
            drawer.classList.remove('open');
            drawer.style.left = '-280px';
            if (overlay) {
                overlay.style.opacity = '0';
                setTimeout(() => overlay.style.display = 'none', 300);
            }
        }
    }

    // Close drawer when pressing Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && typeof toggleDrawer === 'function') {
            toggleDrawer(false);
        }
    });"""

    if old_fn in content:
        content = content.replace(old_fn, new_fn, 1)
        print("  Updated toggleDrawer function with toggle support & Esc key handler")
    else:
        print("  Warning: old_fn not found directly, checking regex...")
        import re
        pattern_fn = r'function toggleDrawer\(show\)\s*\{[\s\S]*?setTimeout\(\(\) => overlay\.style\.display = \'none\', 300\);\s*\}\s*\}'
        if re.search(pattern_fn, content):
            content = re.sub(pattern_fn, new_fn, content, count=1)
            print("  Updated toggleDrawer function via regex")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Finished patching {filepath}!")

if __name__ == '__main__':
    patch_sidebar('AutorideSystem/admin_app/index.html')
    patch_sidebar('AutorideSystem/admin_mobile/www/index.html')
