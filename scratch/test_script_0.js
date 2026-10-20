
        (function() {
            try {
                var raw = localStorage.getItem('admin_user');
                var loggedIn = false;
                if (raw) {
                    var parsed = JSON.parse(raw);
                    if (parsed && (parsed.id || (parsed.user && (!parsed.savedAt || Date.now() - parsed.savedAt < 7*24*60*60*1000)))) {
                        loggedIn = true;
                        var _u = parsed.user || parsed;
                        var _r = (_u && _u.role) ? String(_u.role).toLowerCase() : '';
                        if (!(_r.includes('super') || _r === 'super_admin')) {
                            document.documentElement.classList.add('role-staff');
                        }
                    }
                }
                if (!loggedIn) {
                    var style = document.createElement('style');
                    style.id = 'earlyAuthHideStyle';
                    style.innerHTML = 'body > *:not(#adminLoginOverlay):not(#adminLoadingOverlay):not(script):not(style) { display: none !important; }';
                    (document.head || document.documentElement).appendChild(style);
                }
            } catch(e) {}
        })();
        if ('serviceWorker' in navigator && !window.Capacitor) {
            window.addEventListener('load', () => {
                const swScope = window.location.pathname.includes('/admin_app/') ? '/admin_app/' : './';
                navigator.serviceWorker.register('sw.js', { scope: swScope })
                    .then(reg => console.log('[Admin PWA] Service Worker registered:', reg.scope))
                    .catch(err => console.error('[Admin PWA] Service Worker registration failed:', err));
            });
        } else if ('serviceWorker' in navigator && window.Capacitor) {
            navigator.serviceWorker.getRegistrations().then(regs => {
                for (let r of regs) r.unregister();
            }).catch(() => {});
        }
    