# coding: utf-8
"""
Make admin loading overlay:
- Small background spinner for GET requests (read)
- Full-screen blocking overlay for POST/PUT/DELETE (write actions)
"""
import re

def apply(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()
    orig = html

    # 1. Update showAdminLoading to support blocking mode
    old_fn = """    var _adminFetchCount = 0;
    function showAdminLoading(show) {
        var el = document.getElementById('adminLoadingOverlay');
        if (el) el.style.display = show ? 'flex' : 'none';
        document.body.style.overflow = show ? 'hidden' : '';
    }"""

    new_fn = """    var _adminFetchCount = 0;
    var _adminBlockCount = 0;
    function showAdminLoading(show, blocking) {
        var el = document.getElementById('adminLoadingOverlay');
        if (!el) return;
        if (show) {
            if (blocking) {
                _adminBlockCount++;
                // Full-screen blocking overlay for write operations
                el.style.position = 'fixed';
                el.style.inset = '0';
                el.style.bottom = '';
                el.style.right = '';
                el.style.width = '100%';
                el.style.height = '100%';
                el.style.background = 'rgba(255,255,255,0.85)';
                el.style.flexDirection = 'column';
                el.style.gap = '14px';
                el.style.pointerEvents = 'all';
                document.body.style.overflow = 'hidden';
                // Show text
                var p = el.querySelector('p');
                if (p) p.style.display = 'block';
                // Bigger spinner
                var sp = el.querySelector('div');
                if (sp) { sp.style.width = '44px'; sp.style.height = '44px'; sp.style.borderWidth = '4px'; }
            } else {
                // Small background indicator for reads
                el.style.position = 'fixed';
                el.style.bottom = '24px';
                el.style.right = '24px';
                el.style.inset = '';
                el.style.width = 'auto';
                el.style.height = 'auto';
                el.style.background = 'transparent';
                el.style.flexDirection = 'row';
                el.style.gap = '8px';
                el.style.pointerEvents = 'none';
                document.body.style.overflow = '';
                var p2 = el.querySelector('p');
                if (p2) p2.style.display = 'none';
                var sp2 = el.querySelector('div');
                if (sp2) { sp2.style.width = '28px'; sp2.style.height = '28px'; sp2.style.borderWidth = '3px'; }
            }
            el.style.display = 'flex';
        } else {
            if (blocking && _adminBlockCount > 0) _adminBlockCount--;
            if (_adminBlockCount === 0) {
                document.body.style.overflow = '';
            }
            el.style.display = 'none';
        }
    }"""

    if old_fn in html:
        html = html.replace(old_fn, new_fn)
        print(f"  Updated showAdminLoading in {path.split('\\\\')[-2]}/{path.split('\\\\')[-1]}")
    else:
        print(f"  WARNING: showAdminLoading pattern not found in {path.split('\\\\')[-1]}")
        return False

    # 2. Update fetch wrapper to detect write methods and use blocking mode
    old_wrapper = """        window.fetch = function(url, opts) {
            var us = typeof url === 'string' ? url : '';
            var skip = _SKIP.some(function(s) { return us.indexOf(s) >= 0; });
            if (!skip) { _adminFetchCount++; showAdminLoading(true); }
            var p = _orig.apply(this, arguments);
            p.then(function() {
                if (!skip) { _adminFetchCount = Math.max(0, _adminFetchCount - 1); if (_adminFetchCount === 0) showAdminLoading(false); }
            }, function() {
                if (!skip) { _adminFetchCount = Math.max(0, _adminFetchCount - 1); if (_adminFetchCount === 0) showAdminLoading(false); }
            });
            return p;
        };"""

    new_wrapper = """        window.fetch = function(url, opts) {
            var us = typeof url === 'string' ? url : '';
            var skip = _SKIP.some(function(s) { return us.indexOf(s) >= 0; });
            var method = (opts && opts.method ? opts.method : 'GET').toUpperCase();
            var isWrite = ['POST','PUT','DELETE','PATCH'].indexOf(method) >= 0;
            if (!skip) { _adminFetchCount++; showAdminLoading(true, isWrite); }
            var p = _orig.apply(this, arguments);
            p.then(function() {
                if (!skip) {
                    _adminFetchCount = Math.max(0, _adminFetchCount - 1);
                    if (_adminFetchCount === 0) showAdminLoading(false, isWrite);
                }
            }, function() {
                if (!skip) {
                    _adminFetchCount = Math.max(0, _adminFetchCount - 1);
                    if (_adminFetchCount === 0) showAdminLoading(false, isWrite);
                }
            });
            return p;
        };"""

    if old_wrapper in html:
        html = html.replace(old_wrapper, new_wrapper)
        print(f"  Updated fetch wrapper")
    else:
        print(f"  WARNING: fetch wrapper pattern not found")

    # 3. Also add "Please wait..." <p> back to the overlay (was removed)
    # Find the adminLoadingOverlay div and ensure it has a <p> element
    old_overlay_no_p = '<div id="adminLoadingOverlay" style="display:none;position:fixed;bottom:24px;right:24px;width:auto;height:auto;background:transparent;z-index:99999;align-items:center;justify-content:center;flex-direction:row;gap:8px;pointer-events:none;"><div style="width:28px;height:28px;border:3px solid #e2e8f0;border-top-color:#00B14F;border-radius:50%;animation:adminSpin 0.75s linear infinite;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,0.12);"></div></div>'
    new_overlay_with_p = '<div id="adminLoadingOverlay" style="display:none;position:fixed;bottom:24px;right:24px;width:auto;height:auto;background:transparent;z-index:99999;align-items:center;justify-content:center;flex-direction:row;gap:8px;pointer-events:none;"><div style="width:28px;height:28px;border:3px solid #e2e8f0;border-top-color:#00B14F;border-radius:50%;animation:adminSpin 0.75s linear infinite;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,0.12);"></div><p style="display:none;color:#374151;font-size:0.9rem;font-weight:600;">Please wait...</p></div>'

    if old_overlay_no_p in html:
        html = html.replace(old_overlay_no_p, new_overlay_with_p)
        print(f"  Added <p> back to overlay")

    if html != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Saved.")
        return True
    return False

import os
files = [
    r"c:\Users\patri\OneDrive\Desktop\AutorideSystem2sides\AutorideSystem\admin_app\index.html",
    r"c:\Users\patri\OneDrive\Desktop\AutorideSystem2sides\AutorideSystem\admin_mobile\www\index.html",
]
for f in files:
    if os.path.exists(f):
        apply(f)

print("Done")
