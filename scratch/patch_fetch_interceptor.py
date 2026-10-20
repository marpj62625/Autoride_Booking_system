interceptor = '''
    // Global fetch interceptor to automatically attach authenticated admin credentials
    (function() {
        const _origFetch = window.fetch;
        window.fetch = async function(resource, init) {
            init = init || {};
            try {
                const adminUser = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
                if (adminUser && adminUser.id) {
                    init.headers = init.headers || {};
                    if (init.headers instanceof Headers) {
                        if (!init.headers.has('X-Admin-Id')) init.headers.set('X-Admin-Id', String(adminUser.id));
                    } else if (Array.isArray(init.headers)) {
                        init.headers.push(['X-Admin-Id', String(adminUser.id)]);
                    } else {
                        init.headers['X-Admin-Id'] = init.headers['X-Admin-Id'] || String(adminUser.id);
                    }
                }
            } catch (_) {}
            return _origFetch(resource, init);
        };
    })();
'''

files = ['admin_app/index.html', 'admin_mobile/www/index.html']
for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    target = "    window.apiFetch = async function(path, options = {}) {"
    if target in content and "Global fetch interceptor" not in content:
        content = content.replace(target, interceptor + "\n" + target, 1)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully patched {filepath}")
    else:
        print(f"Skipped {filepath} (already patched or target not found)")
