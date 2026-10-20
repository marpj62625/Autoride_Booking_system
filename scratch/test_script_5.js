
    function escapeHtml(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    /**
     * Data Privacy Act of 2012 (RA 10173) Dynamic Redaction
     * Automatically masks personal email addresses to protect customer PII.
     */
    function maskEmail(email) {
        if (!email || typeof email !== 'string' || !email.includes('@')) return email || '';
        if (email.includes('*')) return email;
        const parts = email.split('@');
        const u = parts[0], d = parts[1];
        if (u.length <= 2) return u[0] + '*@' + d;
        if (u.length <= 5) return u[0] + '*'.repeat(u.length - 2) + u[u.length - 1] + '@' + d;
        return u.substring(0, 2) + '*'.repeat(Math.max(3, u.length - 4)) + u.substring(u.length - 2) + '@' + d;
    }
    window.maskEmail = maskEmail;

    function showInlineError(el, message) {
        if (!el) return;
        el.style.borderColor = '#dc2626';
        el.style.outline = '0';
        var existing = el.parentNode && el.parentNode.querySelector('[data-inline-err="' + el.id + '"]');
        if (existing) existing.remove();
        var errSpan = document.createElement('span');
        errSpan.setAttribute('data-inline-err', el.id);
        errSpan.style.cssText = 'display:block;color:#dc2626;font-size:0.78rem;margin-top:3px;font-weight:500;';
        errSpan.textContent = message;
        el.parentNode.insertBefore(errSpan, el.nextSibling);
    }

    function clearInlineError(el) {
        if (!el) return;
        el.style.borderColor = '';
        el.style.outline = '';
        var existing = el.parentNode && el.parentNode.querySelector('[data-inline-err="' + el.id + '"]');
        if (existing) existing.remove();
    }

    // API URL: auto-detect - works on Vercel (web) and Android APK (Capacitor)
    const API_BASE = (function() {
        // 1. Mobile devices / Android APK / Capacitor
        const isMobileOrCap = (typeof window.Capacitor !== 'undefined' && window.Capacitor) ||
                              window.location.protocol === 'capacitor:' ||
                              window.location.protocol === 'file:' ||
                              /android|iphone|ipad|ipod/i.test(navigator.userAgent || '');
        if (isMobileOrCap) {
            return 'https://autoride-booking-system.vercel.app';
        }

        // 2. Local PC development (only if explicitly running on port 5000)
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            if (window.location.port === '5000') {
                return 'http://localhost:5000';
            }
            return 'https://autoride-booking-system.vercel.app';
        }

        // 3. Web: Vercel or HTTPS
        if (window.location.hostname.includes('vercel.app') || window.location.protocol === 'https:') {
            return window.location.origin;
        }

        // 4. Default Fallback
        return 'https://autoride-booking-system.vercel.app';
    })();

    const API_URL = API_BASE + '/api';
    window.API_BASE = API_BASE;
    window.API_URL = API_URL;








    // Admin notification globals - defined early so initSession can call them



    window.adminNotifList = [];



    window._adminNotifKnownIds = new Set();



    window._adminToastTimer = null;







    window._adminToastDismiss = function() {
        const toast = document.getElementById('adminNotifToast');
        if (toast) {
            if (window.anime) {
                anime({
                    targets: toast,
                    translateY: [0, -20],
                    opacity: [1, 0],
                    duration: 250,
                    easing: 'easeInCubic',
                    complete: function() {
                        toast.classList.remove('show');
                        toast.style.opacity = '';
                        toast.style.transform = '';
                    }
                });
            } else {
                toast.classList.remove('show');
            }
        }



        if (window._adminToastTimer) { clearTimeout(window._adminToastTimer); window._adminToastTimer = null; }



    };







    window._adminShowToast = function(title, msg) {



        const toast = document.getElementById('adminNotifToast');



        const titleEl = document.getElementById('adminToastTitle');



        const msgEl = document.getElementById('adminToastMsg');



        if (!toast || !titleEl || !msgEl) return;



        titleEl.textContent = title || 'New Notification';



        msgEl.textContent = msg || '';



        toast.classList.add('show');
        if (window.anime) {
            anime({
                targets: toast,
                translateY: [-20, 0],
                opacity: [0, 1],
                scale: [0.95, 1],
                duration: 350,
                easing: 'easeOutBack'
            });
        }



        if (window._adminToastTimer) clearTimeout(window._adminToastTimer);



        window._adminToastTimer = setTimeout(function() { window._adminToastDismiss(); }, 4500);



    };







    window.loadAdminNotifications = function(adminId) {
        if (!adminId || adminId === 'undefined' || adminId === 'null') return;
        fetch(API_URL + '/admin/notifications?admin_id=' + adminId)



            .then(r => r.json())



            .then(data => {



                const list = Array.isArray(data) ? data : [];



                // Detect new notifications (not seen in previous poll)



                const isFirstLoad = window._adminNotifKnownIds.size === 0 && window.adminNotifList.length === 0;



                if (!isFirstLoad) {



                    const newOnes = list.filter(n => !window._adminNotifKnownIds.has(n.id) && !n.is_read);



                    if (newOnes.length === 1) {



                        window._adminShowToast(newOnes[0].title, newOnes[0].message);



                        // Auto-refresh Extensions tab if it's an extension request



                        if (newOnes[0].type === 'admin_extension_request') {



                            if (typeof Extensions !== 'undefined') Extensions.load();



                        }



                        // Auto-refresh bookings for payment/cancel/refund notifications



                        // Auto-refresh bookings for payment/cancel/refund/new booking notifications
                        if (newOnes[0].type === 'admin_payment_proof' || newOnes[0].type === 'admin_booking_cancelled' || newOnes[0].type === 'admin_refund_request' || newOnes[0].type === 'admin_new_booking' || newOnes[0].type === 'admin_no_show' || newOnes[0].type === 'admin_return_reminder' || newOnes[0].type === 'admin_return_warning' || newOnes[0].type === 'admin_return_overdue') {
                            if (typeof Bookings !== 'undefined' && typeof Bookings.refresh === 'function') {
                                Bookings.refresh();
                            }
                            if (typeof Dashboard !== 'undefined' && typeof Dashboard.refresh === 'function') {
                                Dashboard.refresh();
                            }
                        }

                        // Auto-refresh verifications and users for license upload notifications
                        if (newOnes[0].type === 'license' || newOnes[0].type === 'admin_license_upload') {
                            if (typeof Verifications !== 'undefined' && typeof Verifications.refresh === 'function') {
                                Verifications.refresh();
                            }
                            if (typeof UserMgmt !== 'undefined' && typeof UserMgmt.refresh === 'function') {
                                UserMgmt.refresh();
                            }
                        }
                    } else if (newOnes.length > 1) {
                        window._adminShowToast('New Notifications', `You have ${newOnes.length} new notifications.`);

                        // Refresh extensions if any are extension requests
                        if (newOnes.some(n => n.type === 'admin_extension_request')) {
                            if (typeof Extensions !== 'undefined') Extensions.load();
                        }

                        // Auto-refresh bookings for payment/cancel/refund notifications
                        if (newOnes.some(n => n.type === 'admin_payment_proof' || n.type === 'admin_booking_cancelled' || n.type === 'admin_refund_request' || n.type === 'admin_new_booking' || n.type === 'admin_no_show')) {
                            if (typeof Bookings !== 'undefined' && typeof Bookings.refresh === 'function') {
                                Bookings.refresh();
                            }
                            if (typeof Dashboard !== 'undefined' && typeof Dashboard.refresh === 'function') {
                                Dashboard.refresh();
                            }
                        }

                        // Auto-refresh verifications and users for license upload notifications
                        if (newOnes.some(n => n.type === 'license' || n.type === 'admin_license_upload')) {
                            if (typeof Verifications !== 'undefined' && typeof Verifications.refresh === 'function') {
                                Verifications.refresh();
                            }
                            if (typeof UserMgmt !== 'undefined' && typeof UserMgmt.refresh === 'function') {
                                UserMgmt.refresh();
                            }
                        }
                    }
                }



                // Update known IDs



                list.forEach(n => window._adminNotifKnownIds.add(n.id));



                window.adminNotifList = list;



                if (typeof window.updateAdminNotifBadge === 'function') window.updateAdminNotifBadge();



            }).catch(() => {});



    };







    window.updateAdminNotifBadge = function() {



        const unread = (window.adminNotifList || []).filter(n => !n.is_read).length;



        const badge = document.getElementById('adminNotifBadge');



        if (!badge) return;



        if (unread > 0) {



            badge.textContent = unread > 99 ? '99+' : String(unread);



            badge.style.display = 'flex';
            if (window.anime) {
                anime({
                    targets: '#adminNotifBtn i',
                    rotate: [-14, 14, -10, 10, -5, 5, 0],
                    duration: 700,
                    easing: 'easeInOutSine'
                });
                anime({
                    targets: badge,
                    scale: [0, 1.25, 1],
                    duration: 400,
                    easing: 'easeOutBack'
                });
            }



        } else {



            badge.style.display = 'none';



        }



    };







    window.toggleAdminNotifPanel = function() {



        const panel = document.getElementById('adminNotifPanel');



        const list = document.getElementById('adminNotifList');



        if (!panel) return;



        const isVisible = panel.style.display !== 'none';



        panel.style.display = isVisible ? 'none' : 'block';



        if (!isVisible) {



            const user = typeof adminAuth !== 'undefined' ? adminAuth.getUser() : null;



            if (user && user.id) {



                fetch(API_URL + '/admin/notifications/read-all', {



                    method: 'POST',



                    headers: { 'Content-Type': 'application/json' },



                    body: JSON.stringify({ admin_id: user.id })



                }).then(() => {



                    (window.adminNotifList || []).forEach(n => n.is_read = true);



                    window.updateAdminNotifBadge();



                }).catch(() => {});



            }



            const notifs = window.adminNotifList || [];



            if (!notifs.length) {



                list.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:16px 0;font-size:0.875rem;">No notifications yet</p>';



            } else {



                list.innerHTML = notifs.map(n => {

                    const ts = n.created_at ? new Date(n.created_at).toLocaleString() : '';

                    const isNoShow = n.type === 'admin_no_show';
                    const unreadStyle = n.is_read ? '' : (isNoShow ? 'border-left:3px solid #ef4444;padding-left:8px;background:rgba(239,68,68,0.08);' : 'border-left:3px solid #00B14F;padding-left:8px;background:rgba(0,177,79,0.08);');

                    let onClickAction = '';
                    if (n.type === 'license' || n.type === 'admin_license_upload') {
                        onClickAction = "onclick=\"switchTab('users');\" style=\"cursor:pointer;\"";
                    } else if (n.type === 'admin_new_booking' || n.type === 'admin_booking_cancelled' || n.type === 'admin_payment_proof' || n.type === 'admin_extension_request' || n.type === 'admin_refund_request' || n.type === 'admin_no_show') {
                        onClickAction = "onclick=\"switchTab('bookings');\" style=\"cursor:pointer;\"";
                    } else {
                        onClickAction = "onclick=\"switchTab('chat');\" style=\"cursor:pointer;\"";
                    }

                    let bId = n.booking_id;
                    if (isNoShow && !bId && n.title) {
                        const match = n.title.match(/Booking #(\d+)/);
                        if (match) bId = match[1];
                    }
                    const noShowBtn = (isNoShow && bId) ? `<div style="margin-top:6px;"><button onclick="event.stopPropagation();Bookings.markNoShow(${bId})" style="padding:5px 12px;background:#ef4444;color:#fff;border:none;border-radius:7px;font-size:0.72rem;font-weight:700;cursor:pointer;"><i class='fas fa-user-slash' style='margin-right:4px;'></i>Mark No Show</button></div>` : '';

                    return `<div ${onClickAction} style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06);${unreadStyle}">

                        <strong style="font-size:0.85rem;color:${isNoShow ? '#fca5a5' : '#f1f5f9'};">${isNoShow ? '🚫 ' : ''}${n.title || ''}</strong>

                        <p style="font-size:0.78rem;color:#94a3b8;margin-top:3px;">${n.message || ''}</p>

                        <small style="color:var(--text-muted);">${ts}</small>

                        ${noShowBtn}

                    </div>`;

                }).join('');



            }



        }



    };



    // Close ANY open modal, panel, or overlay when clicking on its backdrop
    document.addEventListener('click', function(e) {
        // 1. Notification Panel
        const notifPanel = document.getElementById('adminNotifPanel');
        const notifBtn = document.getElementById('adminNotifBtn');
        if (notifPanel && notifPanel.style.display !== 'none') {
            if (!notifPanel.contains(e.target) && !notifBtn?.contains(e.target)) {
                notifPanel.style.display = 'none';
            }
        }

        // 2. All Full-Screen Modals with backdrop (Clicking outside modal card/content)
        if (e.target && e.target.id === 'systemConfigModal') {
            handleSystemConfigCloseAttempt(e);
            return;
        }
        if (e.target && e.target.id === 'sysConfigUnsavedModal') {
            cancelSysConfigUnsavedPrompt(e);
            return;
        }

        const modalBackdropIds = [
            'inspectionModal', 'bookingDetailsModal', 'vehicleModal', 'umModal',
            'licensePreviewModal', 'receiptPreviewModal', 'changePasswordModal',
            'blackoutsModal', 'exitConfirmModal', 'pushNotifModal', 'superAdminProfileModal',
            'staffModal', 'archiveMaintenanceModal', 'vehicleDetailModal',
            'staffPermissionsSuperModal', 'recordExpenseModal', 'adminChatControlsModal',
            'adminFaqFormModal', 'chartPopupModal', 'newsletterModal',
            'addonsConfigModal', 'insuranceConfigModal', 'locationsConfigModal', 'smtpConfigModal', 'gpsConfigModal',
            'gpsTripHistoryModal', 'staffRequestPermModal', 'fleetExportModal', 'fleetImportModal'
        ];
        if (e.target && modalBackdropIds.includes(e.target.id)) {
            if (e.target.id === 'umModal') {
                if (typeof UserMgmt !== 'undefined' && UserMgmt.closeModal) UserMgmt.closeModal();
                else e.target.style.display = 'none';
                return;
            }
            e.target.style.display = 'none';
            if (typeof modalClose === 'function') modalClose();
            return;
        }

        const modalBackdrops = document.querySelectorAll('.premium-modal, .modal, [id$="Modal"], [id$="Overlay"]');
        modalBackdrops.forEach(modal => {
            if (modal.id === 'adminLoginOverlay' || modal.id === 'adminLoadingOverlay') return;
            if (modal.id === 'systemConfigModal' || modal.id === 'sysConfigUnsavedModal') return;
            if (modal.style.display !== 'none' && modal.style.display !== '' && e.target === modal) {
                modal.style.display = 'none';
                if (typeof modalClose === 'function') modalClose();
            }
        });
    });

    // Close on Escape key press (Desktop) - Closes top-most open modal/panel
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const notifPanel = document.getElementById('adminNotifPanel');
            if (notifPanel && notifPanel.style.display !== 'none') {
                notifPanel.style.display = 'none';
                return;
            }

            const openModals = Array.from(document.querySelectorAll('.premium-modal, .modal, [id$="Modal"], [id$="Overlay"]'))
                .filter(m => m.style.display !== 'none' && m.style.display !== '' && m.id !== 'adminLoginOverlay');
            if (openModals.length > 0) {
                const topModal = openModals[openModals.length - 1];
                if (topModal.id === 'systemConfigModal') {
                    handleSystemConfigCloseAttempt(e);
                    return;
                }
                if (topModal.id === 'sysConfigUnsavedModal') {
                    cancelSysConfigUnsavedPrompt(e);
                    return;
                }
                topModal.style.display = 'none';
            }
        }
    });

    // Helper to close any currently active modal/popup on mobile back action
    function closeTopAdminModal() {
        const notifPanel = document.getElementById('adminNotifPanel');
        if (notifPanel && notifPanel.style.display !== 'none') {
            notifPanel.style.display = 'none';
            return true;
        }

        const openModals = Array.from(document.querySelectorAll('.premium-modal, .modal, [id$="Modal"], [id$="Overlay"]'))
            .filter(m => m.style.display !== 'none' && m.style.display !== '' && m.id !== 'adminLoginOverlay');
        if (openModals.length > 0) {
            const topModal = openModals[openModals.length - 1];
            if (topModal.id === 'systemConfigModal') {
                handleSystemConfigCloseAttempt();
                return true;
            }
            if (topModal.id === 'sysConfigUnsavedModal') {
                cancelSysConfigUnsavedPrompt();
                return true;
            }
            topModal.style.display = 'none';
            return true;
        }
        return false;
    }

    // Handle Mobile Hardware Back Button & Browser Popstate
    window.addEventListener('popstate', function() {
        closeTopAdminModal();
    });

    if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App) {
        window.Capacitor.Plugins.App.addListener('backButton', function() {
            const closed = closeTopAdminModal();
            if (!closed) {
                window.history.back();
            }
        });
    }








    window.saveAdminFcmToken = function(token) {



        const user = typeof adminAuth !== 'undefined' ? adminAuth.getUser() : null;



        if (!token || !user || !user.id) return;



        fetch(API_URL + '/admin/fcm-token', {



            method: 'POST',



            headers: { 'Content-Type': 'application/json' },



            body: JSON.stringify({ admin_id: user.id, fcm_token: token })



        }).catch(() => {});



    };



    



    // Global API fetcher for production




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

    window.apiFetch = async function(path, options = {}) {



        let cleanPath = path.startsWith('/') ? path.slice(1) : path;



        let url = `${API_URL}/${cleanPath}`;



        return fetch(url, options);



    };



    const apiFetch = window.apiFetch;











    const SESSION_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days (sliding window)







    const adminAuth = {



        login: async function() {
            const emailEl = document.getElementById('loginEmail');
            const passEl = document.getElementById('loginPass');
            const email = (emailEl || {}).value || '';
            const password = (passEl || {}).value || '';
            const btn = document.getElementById('loginBtn');
            const errEl = document.getElementById('loginError');

            if (emailEl) clearInlineError(emailEl);
            if (passEl) clearInlineError(passEl);

            let hasError = false;

            // Empty-field and format validation
            if (!email.trim()) {
                if (emailEl) showInlineError(emailEl, 'Please enter your email address');
                hasError = true;
            } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
                if (emailEl) showInlineError(emailEl, 'Please enter a valid email address');
                hasError = true;
            }

            if (!password.trim()) {
                if (passEl) showInlineError(passEl, 'Please enter your password');
                hasError = true;
            }

            if (hasError) {
                if (errEl) { errEl.style.display = 'none'; }
                return;
            }

            if (!btn) return;
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Authenticating...';
            if (errEl) { errEl.textContent = ''; errEl.style.display = 'none'; }

            try {
                const res = await fetch(`${API_URL}/admin/login`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });

                let data = {};
                try { data = await res.json(); } catch(_) {}

                if (res.ok) {
                    localStorage.setItem('admin_user', JSON.stringify({ user: data, savedAt: Date.now() }));
                    this.initSession();
                } else {
                    if (errEl) {
                        errEl.textContent = (res.status >= 500 ? 'Server error: ' : '') + (data.error || `Login failed (${res.status})`) + (data.detail ? ' [check Vercel logs]' : '');
                        errEl.style.display = 'block';
                    }
                    if (window.anime) {
                        const box = document.querySelector('.admin-login-box');
                        if (box) {
                            anime({ targets: box, translateX: [-10, 10, -7, 7, -4, 4, 0], duration: 400, easing: 'easeInOutSine' });
                        }
                    }
                }
            } catch (err) {
                console.error('Login error:', err);
                if (errEl) { errEl.textContent = 'Connection error - check your internet and try again.'; errEl.style.display = 'block'; }
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        },



                getUser: () => {
            try {
                const raw = localStorage.getItem('admin_user');
                if (!raw) return null;
                const parsed = JSON.parse(raw);
                if (!parsed) return null;

                let userObj = null;
                if (parsed.user && typeof parsed.user === 'object') {
                    // Check expiry if savedAt is present
                    if (parsed.savedAt && (Date.now() - parsed.savedAt > SESSION_TTL_MS)) {
                        localStorage.removeItem('admin_user');
                        return null; // expired
                    }
                    // Sliding window session renewal
                    if (parsed.savedAt && (Date.now() - parsed.savedAt > 15 * 60 * 1000)) {
                        parsed.savedAt = Date.now();
                        try { localStorage.setItem('admin_user', JSON.stringify(parsed)); } catch(_) {}
                    }
                    userObj = parsed.user;
                } else if (parsed.id) {
                    userObj = parsed;
                } else if (parsed.data && typeof parsed.data === 'object' && parsed.data.id) {
                    userObj = parsed.data;
                }

                if (userObj && (userObj.id || userObj.user_id || userObj.email)) {
                    if (!userObj.id && userObj.user_id) userObj.id = userObj.user_id;
                    return userObj;
                }
                return null;
            } catch(e) { return null; }
        },



        logout: function() {
            try {
                var adminUser = adminAuth.getUser();
                if (adminUser && adminUser.id) {
                    fetch(API_BASE_URL + '/user/fcm-token/clear', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: adminUser.id })
                    }).catch(function() {});
                }
            } catch(e) {}
            localStorage.removeItem('admin_user');
            location.reload(); 
        },

        logoutAndExit: function() {
            try {
                var adminUser = adminAuth.getUser();
                if (adminUser && adminUser.id) {
                    fetch(API_BASE_URL + '/user/fcm-token/clear', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: adminUser.id })
                    }).catch(function() {});
                }
            } catch(e) {}
            localStorage.removeItem('admin_user');
            if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App) {
                window.Capacitor.Plugins.App.exitApp();
            } else {


                location.reload();



            }



        },



        initSession: function() {



            const user = this.getUser();



            if (user) {



                // Load saved theme preference - default to LIGHT



                var savedAdminTheme = localStorage.getItem('adminTheme');



                if (savedAdminTheme === 'dark') {



                    document.documentElement.setAttribute('data-theme', 'dark');



                    const icon = document.getElementById('adminDarkModeIcon');



                    const label = document.getElementById('adminDarkModeLabel');



                    if (icon) icon.className = 'fas fa-sun';



                    if (label) label.textContent = 'Light Mode';



                } else {



                    document.documentElement.removeAttribute('data-theme');



                }



                const earlyStyle = document.getElementById('earlyAuthHideStyle');
                if (earlyStyle) earlyStyle.remove();
                const overlay = document.getElementById('adminLoginOverlay');
                if (overlay) overlay.style.display = 'none';





                const nameEl = document.getElementById('adminName') || document.getElementById('settingsName');



                const roleEl = document.getElementById('adminRole') || document.getElementById('settingsRole');



                const avatarEl = document.getElementById('adminAvatar') || document.getElementById('settingsAvatar');



                



                if (nameEl) nameEl.textContent = user.full_name;



                if (roleEl) roleEl.textContent = user.role.replace('_', ' ').toUpperCase();
                if (avatarEl) avatarEl.textContent = user.full_name[0].toUpperCase();

                const emailEl = document.getElementById('settingsEmail');
                if (emailEl && user.email) emailEl.textContent = user.email;

                const isSuper = isSuperAdmin();
                applyRolePermissions();
                if (typeof StaffPermissions !== 'undefined') StaffPermissions.init();

                const superAdminPill = document.getElementById('superAdminProfileEditPill');
                if (superAdminPill) superAdminPill.style.display = isSuper ? 'flex' : 'none';
                const superAdminCard = document.getElementById('superAdminEditProfileCard');
                if (superAdminCard) superAdminCard.style.display = isSuper ? 'flex' : 'none';
                const regularPassCard = document.getElementById('adminChangePasswordCard');
                if (regularPassCard) regularPassCard.style.display = isSuper ? 'none' : 'flex';

                // Register FCM token if available from native layer



                if (window._adminFcmToken) saveAdminFcmToken(window._adminFcmToken);







                // Load admin notifications and poll every 30s for new ones



                loadAdminNotifications(user.id);



                setInterval(function() { loadAdminNotifications(user.id); }, 6000);

                // Active view real-time heartbeat (every 8s)
                setInterval(function() {
                    if (document.hidden) return;
                    var activeTabEl = document.querySelector('.tab-content.active, [data-tab-content].active');
                    var activeId = activeTabEl ? activeTabEl.id : '';
                    if (activeId === 'bookings' && typeof Bookings !== 'undefined' && typeof Bookings.refresh === 'function') {
                        Bookings.refresh();
                    } else if (activeId === 'verifications' && typeof Verifications !== 'undefined' && typeof Verifications.refresh === 'function') {
                        Verifications.refresh();
                    } else if (activeId === 'users' && typeof UserMgmt !== 'undefined' && typeof UserMgmt.refresh === 'function') {
                        UserMgmt.refresh();
                    }
                }, 8000);

                // Immediate refresh on window focus / tab visibility change
                window.addEventListener('focus', function() {
                    if (user && user.id) loadAdminNotifications(user.id);
                    var activeTabEl = document.querySelector('.tab-content.active, [data-tab-content].active');
                    var activeId = activeTabEl ? activeTabEl.id : '';
                    if (activeId === 'bookings' && typeof Bookings !== 'undefined') Bookings.refresh();
                    if (activeId === 'verifications' && typeof Verifications !== 'undefined') Verifications.refresh();
                    if (activeId === 'users' && typeof UserMgmt !== 'undefined') UserMgmt.refresh();
                });
                document.addEventListener('visibilitychange', function() {
                    if (!document.hidden) {
                        if (user && user.id) loadAdminNotifications(user.id);
                        var activeTabEl = document.querySelector('.tab-content.active, [data-tab-content].active');
                        var activeId = activeTabEl ? activeTabEl.id : '';
                        if (activeId === 'bookings' && typeof Bookings !== 'undefined') Bookings.refresh();
                        if (activeId === 'verifications' && typeof Verifications !== 'undefined') Verifications.refresh();
                        if (activeId === 'users' && typeof UserMgmt !== 'undefined') UserMgmt.refresh();
                    }
                });







                // Start chat badge polling every 30s



                if (typeof AdminChat !== 'undefined') {



                    AdminChat.updateNavBadge();



                    setInterval(function() { AdminChat.updateNavBadge(); }, 30000);



                }







                let targetTab = 'dashboard';
                if (typeof window !== 'undefined' && window.location.hash) {
                    const hashVal = window.location.hash.replace('#', '');
                    const tabElem = document.getElementById(hashVal);
                    if (tabElem && tabElem.classList.contains('tab-content')) {
                        targetTab = hashVal;
                    }
                }
                
                if (isSuper) {
                    switchTab(targetTab);
                    if (targetTab === 'dashboard') {
                        refreshDashboard();
                    }
                } else {
                    switchTab(targetTab !== 'dashboard' ? targetTab : 'vehicles');
                }



            } else {



                const overlay = document.getElementById('adminLoginOverlay');



                if (overlay) overlay.style.display = 'flex';



            }



        }



    };



    
    function isSuperAdmin() {
        try {
            const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
            if (!user) return false;
            const r = (user.role || '').toLowerCase().replace(/_/g, ' ').trim();
            return r.includes('super admin') || r.includes('superadmin') || user.role === 'super_admin';
        } catch(_) { return false; }
    }
    window.isSuperAdmin = isSuperAdmin;

    function applyRolePermissions() {
        const isSuper = isSuperAdmin();
        if (isSuper) {
            document.documentElement.classList.remove('role-staff');
            document.body && document.body.classList.remove('role-staff');
            document.documentElement.classList.add('role-super');
            document.body && document.body.classList.add('role-super');
        } else {
            document.documentElement.classList.remove('role-super');
            document.body && document.body.classList.remove('role-super');
            document.documentElement.classList.add('role-staff');
            document.body && document.body.classList.add('role-staff');
        }

        // Apply explicit styles
        document.querySelectorAll('[data-tab="dashboard"]').forEach(el => {
            el.style.display = isSuper ? (el.tagName === 'A' || el.tagName === 'BUTTON' ? 'flex' : 'block') : 'none';
        });
        document.querySelectorAll('[data-tab="staff"]').forEach(el => {
            el.style.display = isSuper ? (el.tagName === 'A' || el.tagName === 'BUTTON' ? 'flex' : 'block') : 'none';
        });
        document.querySelectorAll('[data-tab="activity"]').forEach(el => {
            el.style.display = isSuper ? (el.tagName === 'A' || el.tagName === 'BUTTON' ? 'flex' : 'block') : 'none';
        });

        const nlDrawer = document.getElementById('nlDrawerLink');
        if (nlDrawer) nlDrawer.style.display = isSuper ? 'flex' : 'none';
        const nlConfig = document.getElementById('mobileNewsletterConfig');
        if (nlConfig) nlConfig.style.display = isSuper ? 'block' : 'none';

        const archDrawer = document.getElementById('archiveDrawerLink');
        if (archDrawer) archDrawer.style.display = isSuper ? 'flex' : 'none';
        const archConfig = document.getElementById('adminMaintenanceConfig');
        if (archConfig) archConfig.style.display = isSuper ? 'block' : 'none';

        const saPermCard = document.getElementById('superAdminPermissionsCard');
        if (saPermCard) saPermCard.style.display = isSuper ? 'flex' : 'none';

        // Delegatable controls (granted by Super Admin or requested by staff)
        const hasChatAI = isSuper || (typeof StaffPermissions !== 'undefined' && StaffPermissions.isGranted('perm_chat_ai'));
        const chatCard = document.getElementById('adminChatControlsConfigCard');
        if (chatCard) chatCard.style.display = hasChatAI ? 'block' : 'none';
        const chatLock = document.getElementById('lockPerm_chat_ai');
        if (chatLock) chatLock.style.display = (!isSuper && !hasChatAI) ? 'flex' : 'none';

        const hasBlackouts = isSuper || (typeof StaffPermissions !== 'undefined' && StaffPermissions.isGranted('perm_blackout_dates'));
        const blackoutsCard = document.getElementById('mobileBlackoutsConfig');
        if (blackoutsCard) blackoutsCard.style.display = hasBlackouts ? 'block' : 'none';
        const blackoutsLock = document.getElementById('lockPerm_blackout_dates');
        if (blackoutsLock) blackoutsLock.style.display = (!isSuper && !hasBlackouts) ? 'flex' : 'none';

        const hasAddons = isSuper || (typeof StaffPermissions !== 'undefined' && StaffPermissions.isGranted('perm_addons'));
        const addonsCard = document.getElementById('mobileAddonsConfig');
        if (addonsCard) addonsCard.style.display = hasAddons ? 'block' : 'none';
        const insuranceCard = document.getElementById('mobileInsuranceConfig');
        if (insuranceCard) insuranceCard.style.display = hasAddons ? 'block' : 'none';
        const addonsLock = document.getElementById('lockPerm_addons');
        if (addonsLock) addonsLock.style.display = (!isSuper && !hasAddons) ? 'flex' : 'none';

        const hasLocations = isSuper || (typeof StaffPermissions !== 'undefined' && StaffPermissions.isGranted('perm_locations'));
        const locationsCard = document.getElementById('mobileLocationsConfig');
        if (locationsCard) locationsCard.style.display = hasLocations ? 'block' : 'none';
        const locationsLock = document.getElementById('lockPerm_locations');
        if (locationsLock) locationsLock.style.display = (!isSuper && !hasLocations) ? 'flex' : 'none';

        const hasSysConfig = isSuper || (typeof StaffPermissions !== 'undefined' && StaffPermissions.isGranted('perm_system_config'));
        const sysConfigCard = document.getElementById('mobileSystemConfig');
        if (sysConfigCard) sysConfigCard.style.display = hasSysConfig ? 'block' : 'none';
        const sysConfigLock = document.getElementById('lockPerm_system_config');
        if (sysConfigLock) sysConfigLock.style.display = (!isSuper && !hasSysConfig) ? 'flex' : 'none';

        const hasReports = isSuper || (typeof StaffPermissions !== 'undefined' && StaffPermissions.isGranted('perm_reports_view'));
        document.querySelectorAll('[data-tab="reports"]').forEach(el => {
            el.style.display = hasReports ? (el.tagName === 'A' || el.tagName === 'BUTTON' ? 'flex' : 'block') : 'none';
        });

        const superAdminPill = document.getElementById('superAdminProfileEditPill');
        if (superAdminPill) superAdminPill.style.display = isSuper ? 'flex' : 'none';
        const superAdminCard = document.getElementById('superAdminEditProfileCard');
        if (superAdminCard) superAdminCard.style.display = isSuper ? 'flex' : 'none';
        const regularPassCard = document.getElementById('adminChangePasswordCard');
        if (regularPassCard) regularPassCard.style.display = isSuper ? 'none' : 'flex';
    }
    window.applyRolePermissions = applyRolePermissions;

    
    // ==================== STAFF PERMISSIONS & ACCESS REQUESTS MODULE ====================
    const StaffPermissions = {
        _permissions: {},
        _staffList: [],
        _requests: [],
        _selectedStaffId: null,
        _activeRequestKey: null,

        meta: {
            perm_chat_ai: {
                label: 'Live Chat FAQ & AI Controls',
                icon: 'fas fa-robot',
                desc: 'Manage live chat FAQ quick buttons and AI chatbot settings'
            },
            perm_blackout_dates: {
                label: 'Blackout Dates Management',
                icon: 'fas fa-calendar-times',
                desc: 'Block specific dates on the booking calendar'
            },
            perm_addons: {
                label: 'Add-ons & Pricing Management',
                icon: 'fas fa-plus-circle',
                desc: 'Create and price rental add-ons (helmets, car seats, GPS)'
            },
            perm_locations: {
                label: 'Locations & Delivery Zones',
                icon: 'fas fa-map-marker-alt',
                desc: 'Manage pickup/dropoff branches and delivery fees'
            },
            perm_system_config: {
                label: 'System Rules Configuration',
                icon: 'fas fa-cogs',
                desc: 'Manage rental duration limits, buffer hours, and rules'
            },
            perm_reports_view: {
                label: 'Analytics & Reports View',
                icon: 'fas fa-chart-pie',
                desc: 'View operational statistics and the analytics reports tab'
            }
        },

        async init() {
            const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
            if (!user) return;
            const isSuper = (typeof isSuperAdmin === 'function') && isSuperAdmin();

            if (isSuper) {
                this.pollPendingRequests();
            } else {
                await this.fetchMyPermissions(user.id);
            }
        },

        isGranted(permKey) {
            if (typeof isSuperAdmin === 'function' && isSuperAdmin()) return true;
            return Boolean(this._permissions && this._permissions[permKey] && this._permissions[permKey].granted);
        },

        async fetchMyPermissions(staffId) {
            try {
                const res = await fetch(`${API_BASE}/api/admin/permissions?staff_id=${staffId}`);
                if (res.ok) {
                    const data = await res.json();
                    this._permissions = data.permissions || {};
                    if (typeof applyRolePermissions === 'function') applyRolePermissions();
                }
            } catch (err) {
                console.error('[StaffPermissions] fetchMyPermissions error:', err);
            }
        },

        async pollPendingRequests() {
            const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
            if (!user) return;
            try {
                const res = await fetch(`${API_BASE}/api/admin/permissions/requests?user_id=${user.id}&status=pending`);
                if (res.ok) {
                    const data = await res.json();
                    const count = (data.requests || []).length;
                    const badge = document.getElementById('pendingRequestsBadge');
                    const modalBadge = document.getElementById('permModalRequestsBadge');
                    if (badge) {
                        badge.style.display = count > 0 ? 'inline-block' : 'none';
                        badge.textContent = `${count} NEW`;
                    }
                    if (modalBadge) {
                        modalBadge.style.display = count > 0 ? 'inline-block' : 'none';
                        modalBadge.textContent = count;
                    }
                }
            } catch (err) {}
        },

        async openSuperAdminModal() {
            const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
            if (!user) return;
            const modal = document.getElementById('staffPermissionsSuperModal');
            if (!modal) return;
            modal.style.display = 'flex';

            // Load staff list
            const selectEl = document.getElementById('permStaffSelect');
            if (selectEl) selectEl.innerHTML = '<option value="">Loading staff accounts...</option>';

            try {
                const res = await fetch(`${API_BASE}/api/admin/list?requester_id=${user.id}`);
                if (res.ok) {
                    const staffData = await res.json();
                    this._staffList = (staffData || []).filter(s => s.role !== 'super_admin');
                    if (this._staffList.length === 0) {
                        if (selectEl) selectEl.innerHTML = '<option value="">No staff accounts found</option>';
                        document.getElementById('permGridContainer').innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:30px;color:var(--text-muted);">No staff accounts registered yet. Create a staff account in Staff Management.</div>';
                        return;
                    }

                    if (selectEl) {
                        selectEl.innerHTML = this._staffList.map(s => `
                            <option value="${s.id}">${s.full_name || 'Staff'} (${s.email || 'No email'})</option>
                        `).join('');
                    }

                    this._selectedStaffId = this._staffList[0].id;
                    await this.loadSelectedStaffPermissions();
                }
            } catch (err) {
                console.error('Error loading staff for permissions modal:', err);
            }

            // Also load requests count & list in background
            this.loadRequests();
        },

        closeSuperAdminModal() {
            const modal = document.getElementById('staffPermissionsSuperModal');
            if (modal) modal.style.display = 'none';
        },

        handleBackdropClick(e) {
            if (e.target && e.target.id === 'staffPermissionsSuperModal') this.closeSuperAdminModal();
        },

        switchSuperTab(tab) {
            const viewToggles = document.getElementById('permSuperViewToggles');
            const viewRequests = document.getElementById('permSuperViewRequests');
            const btnToggles = document.getElementById('permTabToggles');
            const btnRequests = document.getElementById('permTabRequests');

            if (tab === 'toggles') {
                if (viewToggles) viewToggles.style.display = 'block';
                if (viewRequests) viewRequests.style.display = 'none';
                if (btnToggles) { btnToggles.style.background = 'var(--primary)'; btnToggles.style.color = '#fff'; btnToggles.style.borderColor = 'transparent'; }
                if (btnRequests) { btnRequests.style.background = 'transparent'; btnRequests.style.color = 'var(--text-muted)'; btnRequests.style.borderColor = 'var(--border)'; }
            } else {
                if (viewToggles) viewToggles.style.display = 'none';
                if (viewRequests) viewRequests.style.display = 'block';
                if (btnToggles) { btnToggles.style.background = 'transparent'; btnToggles.style.color = 'var(--text-muted)'; btnToggles.style.borderColor = 'var(--border)'; }
                if (btnRequests) { btnRequests.style.background = 'var(--primary)'; btnRequests.style.color = '#fff'; btnRequests.style.borderColor = 'transparent'; }
                this.loadRequests();
            }
        },

        async onStaffSelected() {
            const selectEl = document.getElementById('permStaffSelect');
            if (selectEl) {
                this._selectedStaffId = selectEl.value;
                await this.loadSelectedStaffPermissions();
            }
        },

        async loadSelectedStaffPermissions() {
            if (!this._selectedStaffId) return;
            const container = document.getElementById('permGridContainer');
            if (!container) return;
            container.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:24px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Loading permissions...</div>';

            try {
                const res = await fetch(`${API_BASE}/api/admin/permissions?staff_id=${this._selectedStaffId}`);
                if (res.ok) {
                    const data = await res.json();
                    const perms = data.permissions || {};

                    container.innerHTML = Object.keys(this.meta).map(key => {
                        const m = this.meta[key];
                        const isGranted = Boolean(perms[key] && perms[key].granted);
                        return `
                            <div style="background:var(--surface-card);border:1px solid ${isGranted ? 'rgba(0,177,79,0.35)' : 'var(--border)'};border-radius:14px;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;gap:10px;box-sizing:border-box;width:100%;max-width:100%;min-width:0;transition:all 0.2s;">
                                <div style="display:flex;align-items:center;gap:10px;flex:1;min-width:0;">
                                    <div style="width:36px;height:36px;flex-shrink:0;border-radius:10px;background:${isGranted ? 'rgba(0,177,79,0.15)' : 'rgba(255,255,255,0.05)'};display:flex;align-items:center;justify-content:center;">
                                        <i class="${m.icon}" style="color:${isGranted ? 'var(--primary)' : 'var(--text-muted)'};font-size:1rem;"></i>
                                    </div>
                                    <div style="flex:1;min-width:0;">
                                        <div style="font-size:0.86rem;font-weight:700;color:var(--text-main);word-break:break-word;">${m.label}</div>
                                        <div style="font-size:0.68rem;color:var(--text-muted);word-break:break-word;line-height:1.3;margin-top:2px;">${m.desc}</div>
                                    </div>
                                </div>
                                <label style="position:relative;display:inline-block;width:44px;height:24px;margin:0;cursor:pointer;flex-shrink:0;">
                                    <input type="checkbox" ${isGranted ? 'checked' : ''} onchange="StaffPermissions.togglePermission('${key}', this.checked)" style="opacity:0;width:0;height:0;">
                                    <span class="ctrl-slider" style="position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background-color:#ccc;transition:.3s;border-radius:24px;"></span>
                                </label>
                            </div>
                        `;
                    }).join('');
                } else {
                    const errData = await res.json().catch(() => ({}));
                    container.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:24px;color:#ef4444;"><i class="fas fa-exclamation-triangle"></i> Failed to load permissions: ${errData.error || ('Status ' + res.status)}</div>`;
                }
            } catch (err) {
                container.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:24px;color:#ef4444;"><i class="fas fa-exclamation-triangle"></i> Connection error: ${err.message || err}</div>`;
            }
        },

        async togglePermission(permKey, isGranted) {
            const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
            if (!user || !this._selectedStaffId) return;

            try {
                const res = await fetch(`${API_BASE}/api/admin/permissions/grant`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        requester_id: user.id,
                        staff_id: this._selectedStaffId,
                        permission_key: permKey,
                        is_granted: isGranted
                    })
                });

                if (res.ok) {
                    if (typeof showNotification === 'function') {
                        showNotification(isGranted ? 'Permission granted to staff' : 'Permission revoked', 'success');
                    }
                    this.loadSelectedStaffPermissions();
                } else {
                    const d = await res.json().catch(() => ({}));
                    alert(d.error || 'Failed to update permission');
                    this.loadSelectedStaffPermissions();
                }
            } catch (err) {
                alert('Connection error');
                this.loadSelectedStaffPermissions();
            }
        },

        async grantAllCurrentStaff(isGranted) {
            const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
            if (!user || !this._selectedStaffId) return;
            const container = document.getElementById('permGridContainer');
            if (container) container.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:24px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Updating permissions...</div>';
            const keys = Object.keys(this.meta);
            for (const k of keys) {
                try {
                    await fetch(`${API_BASE}/api/admin/permissions/grant`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            requester_id: user.id,
                            staff_id: this._selectedStaffId,
                            permission_key: k,
                            is_granted: isGranted
                        })
                    });
                } catch(e) {}
            }
            if (typeof showNotification === 'function') {
                showNotification(isGranted ? 'All permissions granted' : 'All permissions revoked', 'success');
            }
            await this.loadSelectedStaffPermissions();
        },

        async loadRequests() {
            const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
            if (!user) return;
            const container = document.getElementById('permRequestsList');
            if (!container) return;
            container.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Loading access requests...</div>';

            try {
                const res = await fetch(`${API_BASE}/api/admin/permissions/requests?user_id=${user.id}`);
                if (res.ok) {
                    const data = await res.json();
                    const requests = data.requests || [];
                    this._requests = requests;

                    const pendingCount = requests.filter(r => r.status === 'pending').length;
                    const badge = document.getElementById('pendingRequestsBadge');
                    const modalBadge = document.getElementById('permModalRequestsBadge');
                    if (badge) {
                        badge.style.display = pendingCount > 0 ? 'inline-block' : 'none';
                        badge.textContent = `${pendingCount} NEW`;
                    }
                    if (modalBadge) {
                        modalBadge.style.display = pendingCount > 0 ? 'inline-block' : 'none';
                        modalBadge.textContent = pendingCount;
                    }

                    if (requests.length === 0) {
                        container.innerHTML = '<div style="text-align:center;padding:36px;color:var(--text-muted);"><i class="fas fa-check-circle" style="font-size:2rem;color:var(--primary);opacity:0.4;margin-bottom:8px;display:block;"></i>No access requests from staff.</div>';
                        return;
                    }

                    container.innerHTML = requests.map(r => {
                        const isPending = r.status === 'pending';
                        const statusColor = isPending ? '#f59e0b' : (r.status === 'approved' ? '#10b981' : '#ef4444');
                        return `
                            <div style="background:var(--surface-card);border:1px solid ${isPending ? 'rgba(245,158,11,0.4)' : 'var(--border)'};border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:10px;">
                                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">
                                    <div>
                                        <div style="font-size:0.95rem;font-weight:700;color:var(--text-main);display:flex;align-items:center;gap:8px;">
                                            ${r.staff_name || 'Staff Member'}
                                            <span style="font-size:0.65rem;color:var(--text-muted);font-weight:500;">(${r.staff_email})</span>
                                        </div>
                                        <div style="font-size:0.8rem;color:var(--primary);font-weight:700;margin-top:2px;">
                                            Requested: ${r.permission_label}
                                        </div>
                                    </div>
                                    <span style="font-size:0.65rem;font-weight:800;text-transform:uppercase;padding:3px 10px;border-radius:12px;background:${statusColor}22;color:${statusColor};border:1px solid ${statusColor}44;">
                                        ${r.status}
                                    </span>
                                </div>
                                ${r.reason ? `<div style="font-size:0.75rem;color:var(--text-secondary);background:var(--surface-solid);padding:10px 12px;border-radius:8px;border:1px solid var(--border);"><strong>Reason:</strong> ${r.reason}</div>` : ''}
                                <div style="display:flex;justify-content:space-between;align-items:center;font-size:0.68rem;color:var(--text-muted);padding-top:6px;border-top:1px solid var(--border);">
                                    <span>Submitted: ${new Date(r.created_at).toLocaleDateString()}</span>
                                    ${isPending ? `
                                        <div style="display:flex;gap:8px;">
                                            <button type="button" onclick="StaffPermissions.reviewRequest(${r.id}, 'reject')" style="padding:6px 14px;border-radius:8px;border:1px solid rgba(239,68,68,0.3);background:rgba(239,68,68,0.1);color:#ef4444;font-size:0.72rem;font-weight:700;cursor:pointer;">
                                                <i class="fas fa-times"></i> Reject
                                            </button>
                                            <button type="button" onclick="StaffPermissions.reviewRequest(${r.id}, 'approve')" class="btn-premium" style="padding:6px 16px;border-radius:8px;border:none;background:var(--primary);color:#fff;font-size:0.72rem;font-weight:700;cursor:pointer;">
                                                <i class="fas fa-check"></i> Approve &amp; Grant
                                            </button>
                                        </div>
                                    ` : `<span style="font-weight:600;">Reviewed</span>`}
                                </div>
                            </div>
                        `;
                    }).join('');
                } else {
                    const errData = await res.json().catch(() => ({}));
                    container.innerHTML = `<div style="text-align:center;padding:24px;color:#ef4444;"><i class="fas fa-exclamation-triangle"></i> Failed to load requests: ${errData.error || ('Status ' + res.status)}</div>`;
                }
            } catch (err) {
                container.innerHTML = `<div style="text-align:center;padding:24px;color:#ef4444;"><i class="fas fa-exclamation-triangle"></i> Connection error: ${err.message || err}</div>`;
            }
        },

        async reviewRequest(reqId, action) {
            const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
            if (!user) return;

            try {
                const res = await fetch(`${API_BASE}/api/admin/permissions/requests/${reqId}/review`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        requester_id: user.id,
                        action: action
                    })
                });

                if (res.ok) {
                    const data = await res.json();
                    if (typeof showNotification === 'function') {
                        showNotification(`Request ${action === 'approve' ? 'approved & permission granted' : 'rejected'}.`, 'success');
                    }
                    this.loadRequests();
                    this.loadSelectedStaffPermissions();
                } else {
                    const d = await res.json().catch(() => ({}));
                    alert(d.error || 'Failed to review request');
                }
            } catch (err) {
                alert('Connection error');
            }
        },

        // ---------- STAFF ADMIN REQUEST WORKFLOW ----------
        openRequestModal(permKey) {
            this._activeRequestKey = permKey;
            const m = this.meta[permKey];
            if (!m) return;

            const modal = document.getElementById('staffRequestPermModal');
            const titleEl = document.getElementById('staffReqPermTitle');
            const descEl = document.getElementById('staffReqPermDesc');
            const reasonEl = document.getElementById('staffReqPermReason');

            if (titleEl) titleEl.textContent = m.label;
            if (descEl) descEl.textContent = m.desc;
            if (reasonEl) reasonEl.value = '';

            if (modal) modal.style.display = 'flex';
        },

        closeRequestModal() {
            const modal = document.getElementById('staffRequestPermModal');
            if (modal) modal.style.display = 'none';
        },

        handleRequestBackdrop(e) {
            if (e.target && e.target.id === 'staffRequestPermModal') this.closeRequestModal();
        },

        async submitRequest() {
            const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
            if (!user || !this._activeRequestKey) return;

            const reasonEl = document.getElementById('staffReqPermReason');
            const reason = reasonEl ? reasonEl.value.trim() : '';
            const btn = document.getElementById('staffReqSubmitBtn');
            const origText = btn ? btn.innerHTML : 'Submit';

            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
            }

            try {
                const res = await fetch(`${API_BASE}/api/admin/permissions/request`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        staff_id: user.id,
                        permission_key: this._activeRequestKey,
                        reason: reason
                    })
                });

                const data = await res.json().catch(() => ({}));
                if (res.ok) {
                    this.closeRequestModal();
                    if (typeof showNotification === 'function') {
                        showNotification(data.message || 'Access request submitted to Super Admin!', 'success');
                    } else {
                        alert(data.message || 'Request submitted!');
                    }

                    // Update button on locked card
                    const lockCardBtn = document.querySelector(`#lockPerm_${this._activeRequestKey} button`);
                    if (lockCardBtn) {
                        lockCardBtn.disabled = true;
                        lockCardBtn.innerHTML = '⏳ Pending Review';
                        lockCardBtn.style.background = 'rgba(245,158,11,0.15)';
                        lockCardBtn.style.color = '#f59e0b';
                        lockCardBtn.style.borderColor = 'rgba(245,158,11,0.3)';
                    }
                } else {
                    alert(data.error || 'Failed to submit request');
                }
            } catch (err) {
                alert('Connection error. Please try again.');
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = origText;
                }
            }
        }
    };
    window.StaffPermissions = StaffPermissions;

    window.adminAuth = adminAuth;







    // --- MODAL SCROLL LOCK ---



    // NOTE: Do NOT lock body overflow - fixed modals don't need it



    // and Android WebView does not reliably restore scroll after overflow:hidden



    window.modalOpen = function() {
        if (typeof anime !== 'undefined') {
            const openModals = document.querySelectorAll('.modal[style*="display: flex"], .modal[style*="display: block"], [id$="Modal"][style*="display: flex"], [id$="Modal"][style*="display: block"]');
            openModals.forEach(m => {
                const card = m.querySelector('.modal-content') || m.querySelector('div[style*="background"]') || m.firstElementChild;
                if (card) {
                    anime({
                        targets: card,
                        scale: [0.93, 1],
                        opacity: [0, 1],
                        duration: 300,
                        easing: 'easeOutBack'
                    });
                }
            });
        }
        // No body lock needed - modal is position:fixed and covers the screen



    };



    window.modalClose = function() {



        // Ensure scroll is always fully restored on close



        document.body.style.overflow = '';



        document.body.style.overflowY = '';



        document.documentElement.style.overflow = '';



        document.documentElement.style.overflowY = '';



        // Force a reflow to make Android WebView re-enable touch scroll



        document.body.getBoundingClientRect();



    };







    // --- DARK MODE TOGGLE ---



    function toggleDarkMode() {



        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';



        const icon = document.getElementById('adminDarkModeIcon');



        const label = document.getElementById('adminDarkModeLabel');



        if (isDark) {



            document.documentElement.removeAttribute('data-theme');



            localStorage.setItem('adminTheme', 'light');



            if (icon) icon.className = 'fas fa-moon';



            if (label) label.textContent = 'Dark Mode';



        } else {



            document.documentElement.setAttribute('data-theme', 'dark');



            localStorage.setItem('adminTheme', 'dark');



            if (icon) icon.className = 'fas fa-sun';



            if (label) label.textContent = 'Light Mode';



        }



    }







    // --- SYSTEM CONFIG MODAL ---



    function toggleSystemConfigModal() {



        const modal = document.getElementById('systemConfigModal');



        if (modal) {



            modal.style.display = 'flex';



            // Load settings when modal opens



            if (typeof Settings !== 'undefined' && Settings.fetch) {



                Settings.fetch();



            }



        }



    }







    function closeSystemConfigModal() {
        const modal = document.getElementById('systemConfigModal');
        if (modal) {
            modal.style.display = 'none';
        }
        const unsavedModal = document.getElementById('sysConfigUnsavedModal');
        if (unsavedModal) {
            unsavedModal.style.display = 'none';
        }
    }

    function handleSystemConfigCloseAttempt(e) {
        if (e) {
            if (typeof e.stopPropagation === 'function') e.stopPropagation();
            if (typeof e.preventDefault === 'function') e.preventDefault();
        }
        if (typeof Settings === 'undefined' || !Settings.getChanges) {
            closeSystemConfigModal();
            return;
        }
        const changes = Settings.getChanges();
        if (!changes || changes.length === 0) {
            closeSystemConfigModal();
            return;
        }
        showSysConfigUnsavedModal(changes);
    }

    function closeSystemConfigModalBackdrop(event) {
        if (event && typeof event.stopPropagation === 'function') event.stopPropagation();
        // Only trigger if clicking on the backdrop or outside the inner modal content
        if (event.target === event.currentTarget || !event.target.closest('#systemConfigModal .modal-content')) {
            handleSystemConfigCloseAttempt(event);
        }
    }

    function showSysConfigUnsavedModal(changes) {
        const modal = document.getElementById('sysConfigUnsavedModal');
        const list = document.getElementById('sysConfigUnsavedList');
        const count = document.getElementById('sysConfigUnsavedCount');
        if (!modal || !list) return;

        if (count) count.textContent = changes.length;

        list.innerHTML = changes.map(c => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 9px 6px; border-bottom: 1px solid rgba(0,0,0,0.06); font-size: 0.82rem; gap: 10px;">
                <div style="font-weight: 700; color: var(--text-main, #0f172a); min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    ${c.label}
                </div>
                <div style="display: flex; align-items: center; gap: 6px; flex-shrink: 0; font-size: 0.76rem;">
                    <span style="color: #dc2626; background: rgba(239,68,68,0.1); padding: 2px 7px; border-radius: 6px; text-decoration: line-through; font-weight: 600; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; word-break: break-all;">${c.oldValue}</span>
                    <i class="fas fa-arrow-right" style="color: var(--text-muted, #94a3b8); font-size: 0.65rem;"></i>
                    <span style="color: #00B14F; background: rgba(0,177,79,0.12); padding: 2px 7px; border-radius: 6px; font-weight: 800; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; word-break: break-all;">${c.newValue}</span>
                </div>
            </div>
        `).join('');

        modal.style.display = 'flex';
        const sysModal = document.getElementById('systemConfigModal');
        if (sysModal) sysModal.style.display = 'flex';
    }

    function cancelSysConfigUnsavedPrompt(e) {
        if (e) {
            if (typeof e.stopPropagation === 'function') e.stopPropagation();
            if (typeof e.preventDefault === 'function') e.preventDefault();
        }
        const modal = document.getElementById('sysConfigUnsavedModal');
        if (modal) modal.style.display = 'none';
        const sysModal = document.getElementById('systemConfigModal');
        if (sysModal) sysModal.style.display = 'flex';
    }

    function confirmDiscardAndCloseSysConfig(e) {
        if (e) {
            if (typeof e.stopPropagation === 'function') e.stopPropagation();
            if (typeof e.preventDefault === 'function') e.preventDefault();
        }
        if (typeof Settings !== 'undefined' && Settings.discardChanges) {
            Settings.discardChanges();
        }
        closeSystemConfigModal();
        if (typeof showNotification === 'function') {
            showNotification('Changes discarded', 'info');
        }
    }

    async function confirmSaveAndCloseSysConfig(btn, e) {
        if (e) {
            if (typeof e.stopPropagation === 'function') e.stopPropagation();
            if (typeof e.preventDefault === 'function') e.preventDefault();
        }
        if (!btn) btn = document.getElementById('btnConfirmSaveSysConfig');
        const origHtml = btn ? btn.innerHTML : '';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        }
        try {
            if (typeof Settings !== 'undefined' && Settings.save) {
                const ok = await Settings.save();
                if (ok) {
                    closeSystemConfigModal();
                }
            } else {
                closeSystemConfigModal();
            }
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = origHtml || '<i class="fas fa-check"></i> Save & Close';
            }
        }
    }

    window.handleSystemConfigCloseAttempt = handleSystemConfigCloseAttempt;
    window.showSysConfigUnsavedModal = showSysConfigUnsavedModal;
    window.cancelSysConfigUnsavedPrompt = cancelSysConfigUnsavedPrompt;
    window.confirmDiscardAndCloseSysConfig = confirmDiscardAndCloseSysConfig;
    window.confirmSaveAndCloseSysConfig = confirmSaveAndCloseSysConfig;







    // --- ADD-ONS CONFIG MODAL ---



    let addonsList = [];



    function addonsApiCall(path, method = 'GET', body = null) {



        const options = {



            method: method,



            headers: {



                'Content-Type': 'application/json'



            }



        };



        if (body) {



            options.body = JSON.stringify(body);



        }



        return fetch(API_BASE + path, options)



            .then(res => {



                if (!res.ok) {



                    return res.json().then(err => Promise.reject(err));



                }



                return res.json();



            });



    }



    function toggleAddonsModal() {



        const modal = document.getElementById('addonsConfigModal');



        if (modal) {



            modal.style.display = 'flex';



            fetchAddons();



            // Show/hide create form based on role
            const _user = adminAuth.getUser();
            const addonForm = document.getElementById('addonCreateForm');
            if (addonForm) addonForm.style.display = (_user && _user.role === 'super_admin') ? 'block' : 'none';



        }



    }



    function closeAddonsModal() {



        const modal = document.getElementById('addonsConfigModal');



        if (modal) {



            modal.style.display = 'none';



            resetAddonForm();



        }



    }



    function closeAddonsModalBackdrop(event) {



        if (event.target === event.currentTarget) {



            closeAddonsModal();



        }



    }



    function fetchAddons() {



        const listDiv = document.getElementById('addonsAdminList');



        if (listDiv) {



            listDiv.innerHTML = '<p style="font-size: 0.8rem; color: var(--text-muted); text-align: center; padding: 10px;">Loading addons...</p>';



        }



        addonsApiCall('/addons', 'GET')



            .then(function(addons) {



                addonsList = addons || [];



                renderAddons();



            })



            .catch(function(err) {



                console.error('Error fetching addons:', err);



                if (listDiv) {



                    listDiv.innerHTML = '<p style="font-size: 0.8rem; color: var(--danger); text-align: center; padding: 10px;">Error loading addons.</p>';



                }



            });



    }



    function renderAddons() {



        const listDiv = document.getElementById('addonsAdminList');



        if (!listDiv) return;



        if (addonsList.length === 0) {



            listDiv.innerHTML = '<p style="font-size: 0.8rem; color: var(--text-muted); text-align: center; padding: 10px;">No addons found.</p>';



            return;



        }



        listDiv.innerHTML = addonsList.map(function(addon, i) {



            return `
                <div class="stat-card" style="padding: 10px; display: flex; align-items: center; justify-content: space-between; background: var(--surface-container); border: 1px solid var(--border); margin-bottom: 8px;">
                    <div style="flex: 1; min-width: 0; padding-right: 10px;">
                        <h5 style="margin: 0; font-size: 0.9rem; color: var(--text-main);">${addon.name}</h5>
                        <p style="margin: 3px 0 0; font-size: 0.75rem; color: var(--primary); font-weight: 700;">&#8369;${addon.price_per_day}/day</p>
                        ${addon.description ? `<p style="margin: 3px 0 0; font-size: 0.7rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${addon.description}</p>` : ''}
                    </div>
                    <div style="display: flex; gap: 12px; align-items: center; flex-shrink: 0;">
                        <button onclick="editAddon(${i})" style="background:none;border:none;color:var(--primary);font-size:1.1rem;padding:6px;cursor:pointer;display:flex;align-items:center;" title="Edit">
                            <i class="fas fa-pen-to-square"></i>
                        </button>
                        ${(function(){ const _u = adminAuth.getUser(); return _u && _u.role === 'super_admin' ? `<button onclick="deleteAddon(${addon.id})" style="background:none;border:none;color:var(--danger);font-size:1.1rem;padding:6px;cursor:pointer;display:flex;align-items:center;" title="Delete"><i class="fas fa-trash-can"></i></button>` : ''; })()}
                    </div>
                </div>
            `;



        }).join('');



    }



    function editAddon(index) {



        const addon = addonsList[index];



        if (!addon) return;



        document.getElementById('addonIdInput').value = addon.id;



        document.getElementById('addonNameInput').value = addon.name;



        document.getElementById('addonPriceInput').value = addon.price_per_day;



        document.getElementById('addonDescInput').value = addon.description || '';



        document.getElementById('addonFormTitle').textContent = 'Edit Add-on';



        document.getElementById('addonCancelEditBtn').style.display = 'block';



    }



    function resetAddonForm() {



        document.getElementById('addonIdInput').value = '';



        document.getElementById('addonNameInput').value = '';



        document.getElementById('addonPriceInput').value = '';



        document.getElementById('addonDescInput').value = '';



        document.getElementById('addonFormTitle').textContent = 'Create New Add-on';



        document.getElementById('addonCancelEditBtn').style.display = 'none';



    }



    function saveAddon() {



        const id = document.getElementById('addonIdInput').value;



        const nameVal = document.getElementById('addonNameInput').value;



        const name = nameVal.trim ? nameVal.trim() : nameVal;



        const price = document.getElementById('addonPriceInput').value;



        const desc = document.getElementById('addonDescInput').value;



        const user = adminAuth.getUser();
        if (typeof isSuperAdmin === 'function' && !isSuperAdmin()) {
            console.log('[Dashboard] Suppressing dashboard stats refresh for non-superadmin');
            return;
        }



        const adminId = user ? user.id : null;



        if (!name || !price || !adminId) {



            showNotification('Name, price and admin authorization are required.', 'error');



            return;



        }

        // Only super_admin can save addons
        if (!user || user.role !== 'super_admin') {
            showNotification('Only Super Admin can manage add-ons.', 'error');
            return;
        }



        const payload = {



            name: name,



            price_per_day: parseFloat(price),



            description: desc,



            admin_id: adminId



        };



        const url = id ? `/addons/${id}` : '/addons';



        const method = id ? 'PUT' : 'POST';



        addonsApiCall(url, method, payload)



            .then(function() {



                showNotification(id ? 'Addon updated successfully' : 'Addon created successfully', 'success');



                resetAddonForm();



                fetchAddons();



            })



            .catch(function(err) {



                console.error('Error saving addon:', err);



                showNotification('Error saving addon: ' + (err.error || 'Unknown error'), 'error');



            });



    }



    function deleteAddon(addonId) {



        if (!confirm('Are you sure you want to delete this addon?')) return;



        const user = adminAuth.getUser();



        const adminId = user ? user.id : null;



        if (!adminId) {



            showNotification('Unauthorized', 'error');



            return;



        }

        // Only super_admin can delete addons
        if (!user || user.role !== 'super_admin') {
            showNotification('Only Super Admin can delete add-ons.', 'error');
            return;
        }



        addonsApiCall(`/addons/${addonId}?admin_id=${adminId}`, 'DELETE')



            .then(function() {



                showNotification('Addon deleted successfully', 'success');



                fetchAddons();



            })



            .catch(function(err) {



                console.error('Error deleting addon:', err);



                showNotification('Error deleting addon.', 'error');



            });



    }

    // --- INSURANCE CONFIG MODAL ---
    let insuranceList = [];

    function insuranceApiCall(path, method = 'GET', body = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        if (body) {
            options.body = JSON.stringify(body);
        }
        // Normalize path: ensure it routes through /api for Vercel serverless backend
        const cleanPath = path.startsWith('/api') ? path : ('/api' + (path.startsWith('/') ? path : '/' + path));
        return fetch(API_BASE + cleanPath, options)
            .then(async res => {
                const text = await res.text();
                let data;
                try {
                    data = JSON.parse(text);
                } catch(e) {
                    throw new Error(`Server returned non-JSON response (${res.status}): ${text.substring(0, 100)}`);
                }
                if (!res.ok) {
                    return Promise.reject(data || { error: `Request failed with status ${res.status}` });
                }
                return data;
            });
    }

    function toggleInsuranceModal() {
        const modal = document.getElementById('insuranceConfigModal');
        if (modal) {
            modal.style.display = 'flex';
            fetchInsuranceOptions();
            const _user = adminAuth.getUser();
            const insForm = document.getElementById('insuranceCreateForm');
            if (insForm) insForm.style.display = (_user && (_user.role === 'super_admin' || _user.role === 'admin')) ? 'block' : 'none';
        }
    }

    function closeInsuranceModal() {
        const modal = document.getElementById('insuranceConfigModal');
        if (modal) {
            modal.style.display = 'none';
            resetInsuranceForm();
        }
    }

    function closeInsuranceModalBackdrop(event) {
        if (event.target === event.currentTarget) {
            closeInsuranceModal();
        }
    }

    function fetchInsuranceOptions() {
        const listDiv = document.getElementById('insuranceAdminList');
        if (listDiv) {
            listDiv.innerHTML = '<p style="font-size: 0.8rem; color: var(--text-muted); text-align: center; padding: 10px;">Loading insurance packages...</p>';
        }
        insuranceApiCall('/api/insurance-options?all=true', 'GET')
            .then(function(packages) {
                insuranceList = packages || [];
                renderInsuranceOptions();
            })
            .catch(function(err) {
                console.error('Error fetching insurance packages:', err);
                if (listDiv) {
                    listDiv.innerHTML = '<p style="font-size: 0.8rem; color: var(--danger); text-align: center; padding: 10px;">Error loading insurance packages.</p>';
                }
            });
    }

    function renderInsuranceOptions() {
        const listDiv = document.getElementById('insuranceAdminList');
        if (!listDiv) return;

        if (insuranceList.length === 0) {
            listDiv.innerHTML = '<p style="font-size: 0.8rem; color: var(--text-muted); text-align: center; padding: 10px;">No insurance packages found.</p>';
            return;
        }

        const user = adminAuth.getUser();
        const canManage = user && (user.role === 'super_admin' || user.role === 'admin');

        listDiv.innerHTML = insuranceList.map(function(ins) {
            const priceText = parseFloat(ins.price_per_day) === 0 ? 'Included (₱0.00)' : `₱${parseFloat(ins.price_per_day).toLocaleString('en-US', { minimumFractionDigits: 2 })}/day`;
            return `
                <div class="stat-card" style="padding: 12px 14px; display: flex; align-items: center; justify-content: space-between; gap: 10px; background: var(--surface-container); border: 1px solid var(--border); margin-bottom: 8px; border-radius: 12px; box-sizing: border-box;">
                    <div style="flex: 1; min-width: 0;">
                        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px;">
                            <h5 style="margin: 0; font-size: 0.92rem; color: var(--text-main); font-weight: 700; word-break: break-word;">${ins.name}</h5>
                            <span style="font-size: 0.74rem; color: var(--primary); font-weight: 800; background: rgba(0,177,79,0.1); padding: 2px 8px; border-radius: 6px; white-space: nowrap; display: inline-block;">${priceText}</span>
                        </div>
                        ${ins.description ? `<p style="margin: 0; font-size: 0.72rem; color: var(--text-muted); line-height: 1.3;">${ins.description}</p>` : ''}
                    </div>
                    ${canManage ? `
                    <div style="display: flex; gap: 6px; align-items: center; flex-shrink: 0;">
                        <button onclick="editInsuranceOption(${ins.id})" title="Edit" style="background: rgba(0, 177, 79, 0.1); color: var(--primary); border: none; border-radius: 8px; width: 32px; height: 32px; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <i class="fas fa-edit" style="font-size: 0.85rem;"></i>
                        </button>
                        <button onclick="deleteInsuranceOption(${ins.id})" title="Delete" style="background: rgba(239, 68, 68, 0.1); color: var(--danger); border: none; border-radius: 8px; width: 32px; height: 32px; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <i class="fas fa-trash" style="font-size: 0.85rem;"></i>
                        </button>
                    </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }

    function editInsuranceOption(insId) {
        const ins = insuranceList.find(i => i.id === insId);
        if (!ins) return;

        document.getElementById('insuranceIdInput').value = ins.id;
        document.getElementById('insuranceNameInput').value = ins.name;
        document.getElementById('insurancePriceInput').value = ins.price_per_day;
        document.getElementById('insuranceDescInput').value = ins.description || '';
        document.getElementById('insuranceFormTitle').textContent = 'Edit Insurance Package';
        document.getElementById('insuranceCancelEditBtn').style.display = 'block';
        document.getElementById('insuranceNameInput').focus();
    }

    function resetInsuranceForm() {
        document.getElementById('insuranceIdInput').value = '';
        document.getElementById('insuranceNameInput').value = '';
        document.getElementById('insurancePriceInput').value = '';
        document.getElementById('insuranceDescInput').value = '';
        document.getElementById('insuranceFormTitle').textContent = 'Create New Insurance Package';
        document.getElementById('insuranceCancelEditBtn').style.display = 'none';
    }

    function saveInsuranceOption() {
        const id = document.getElementById('insuranceIdInput').value;
        const nameVal = document.getElementById('insuranceNameInput').value;
        const name = nameVal.trim ? nameVal.trim() : nameVal;
        const price = document.getElementById('insurancePriceInput').value;
        const desc = document.getElementById('insuranceDescInput').value;
        const user = adminAuth.getUser();
        const adminId = user ? user.id : null;

        if (!adminId) {
            showNotification('Unauthorized. Please log in.', 'error');
            return;
        }

        if (!name) {
            showNotification('Package name is required.', 'error');
            return;
        }

        if (price === '' || isNaN(parseFloat(price)) || parseFloat(price) < 0) {
            showNotification('Valid price per day is required (0 for free).', 'error');
            return;
        }

        const payload = {
            name: name,
            price_per_day: parseFloat(price),
            description: desc,
            admin_id: adminId
        };

        const saveBtn = document.getElementById('insuranceSaveBtn');
        const origText = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

        const req = id
            ? insuranceApiCall(`/api/insurance-options/${id}`, 'PUT', payload)
            : insuranceApiCall('/api/insurance-options', 'POST', payload);

        req.then(function() {
            showNotification(id ? 'Insurance package updated successfully!' : 'Insurance package created successfully!', 'success');
            resetInsuranceForm();
            fetchInsuranceOptions();
        })
        .catch(function(err) {
            console.error('Error saving insurance option:', err);
            showNotification('Error saving package: ' + (err.error || 'Unknown error'), 'error');
        })
        .finally(function() {
            saveBtn.disabled = false;
            saveBtn.innerHTML = origText;
        });
    }

    function deleteInsuranceOption(insId) {
        if (!confirm('Are you sure you want to delete this insurance package?')) return;

        const user = adminAuth.getUser();
        const adminId = user ? user.id : null;

        if (!adminId) {
            showNotification('Unauthorized', 'error');
            return;
        }

        insuranceApiCall(`/api/insurance-options/${insId}?admin_id=${adminId}`, 'DELETE')
            .then(function() {
                showNotification('Insurance package deleted successfully', 'success');
                fetchInsuranceOptions();
            })
            .catch(function(err) {
                console.error('Error deleting insurance option:', err);
                showNotification('Error deleting insurance package.', 'error');
            });
    }

    // --- LOCATIONS CONFIG MODAL ---
    let locationsList = [];

    function locationsApiCall(path, method = 'GET', body = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        if (body) {
            options.body = JSON.stringify(body);
        }
        return fetch(API_BASE + path, options)
            .then(res => {
                if (!res.ok) {
                    return res.json().then(err => Promise.reject(err));
                }
                return res.json();
            });
    }

    function toggleLocationsModal() {
        const modal = document.getElementById('locationsConfigModal');
        if (modal) {
            modal.style.display = 'flex';
            fetchLocations();
            const _user = adminAuth.getUser();
            const locForm = document.getElementById('locationCreateForm');
            if (locForm) locForm.style.display = (_user && (_user.role === 'super_admin')) ? 'block' : 'none';
        }
    }

    function closeLocationsModal() {
        const modal = document.getElementById('locationsConfigModal');
        if (modal) {
            modal.style.display = 'none';
            resetLocationForm();
        }
    }

    function closeLocationsModalBackdrop(event) {
        if (event.target === event.currentTarget) {
            closeLocationsModal();
        }
    }

    function fetchLocations() {
        const listDiv = document.getElementById('locationsAdminList');
        if (listDiv) {
            listDiv.innerHTML = '<p style="font-size: 0.8rem; color: var(--text-muted); text-align: center; padding: 10px;">Loading locations...</p>';
        }
        locationsApiCall('/locations', 'GET')
            .then(function(locs) {
                locationsList = locs || [];
                renderLocations();
            })
            .catch(function(err) {
                console.error('Error fetching locations:', err);
                if (listDiv) {
                    listDiv.innerHTML = '<p style="font-size: 0.8rem; color: var(--danger); text-align: center; padding: 10px;">Error loading locations.</p>';
                }
            });
    }

    function renderLocations() {
        const listDiv = document.getElementById('locationsAdminList');
        if (!listDiv) return;
        if (locationsList.length === 0) {
            listDiv.innerHTML = '<p style="font-size: 0.8rem; color: var(--text-muted); text-align: center; padding: 10px;">No locations found.</p>';
            return;
        }
        listDiv.innerHTML = locationsList.map(function(loc, i) {
            return `
                <div class="stat-card" style="padding: 10px; display: flex; align-items: center; justify-content: space-between; background: var(--surface-container); border: 1px solid var(--border); margin-bottom: 8px;">
                    <div style="flex: 1; min-width: 0; padding-right: 10px;">
                        <h5 style="margin: 0; font-size: 0.9rem; color: var(--text-main);">${loc.name}</h5>
                        <p style="margin: 3px 0 0; font-size: 0.75rem; color: var(--primary); font-weight: 700;">Delivery Fee: &#8369;${loc.delivery_fee}</p>
                        <p style="margin: 3px 0 0; font-size: 0.7rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            ${loc.barangay ? loc.barangay + ', ' : ''}${loc.municipality}, ${loc.province}
                        </p>
                    </div>
                    <div style="display: flex; gap: 12px; align-items: center; flex-shrink: 0;">
                        <button onclick="editLocation(${i})" style="background:none;border:none;color:var(--primary);font-size:1.1rem;padding:6px;cursor:pointer;display:flex;align-items:center;" title="Edit">
                            <i class="fas fa-pen-to-square"></i>
                        </button>
                        ${(function(){ const _u = adminAuth.getUser(); return _u && _u.role === 'super_admin' ? `<button onclick="deleteLocation(${loc.id})" style="background:none;border:none;color:var(--danger);font-size:1.1rem;padding:6px;cursor:pointer;display:flex;align-items:center;" title="Delete"><i class="fas fa-trash-can"></i></button>` : ''; })()}
                    </div>
                </div>
            `;
        }).join('');
    }

    function editLocation(index) {
        const loc = locationsList[index];
        if (!loc) return;
        document.getElementById('locationIdInput').value = loc.id;
        document.getElementById('locationNameInput').value = loc.name;
        document.getElementById('locationProvinceInput').value = loc.province || '';
        document.getElementById('locationMuniInput').value = loc.municipality || '';
        document.getElementById('locationBrgyInput').value = loc.barangay || '';
        document.getElementById('locationFeeInput').value = loc.delivery_fee;
        document.getElementById('locationFormTitle').textContent = 'Edit Location';
        document.getElementById('locationCancelEditBtn').style.display = 'block';
    }

    function resetLocationForm() {
        document.getElementById('locationIdInput').value = '';
        document.getElementById('locationNameInput').value = '';
        document.getElementById('locationProvinceInput').value = '';
        document.getElementById('locationMuniInput').value = '';
        document.getElementById('locationBrgyInput').value = '';
        document.getElementById('locationFeeInput').value = '0';
        document.getElementById('locationFormTitle').textContent = 'Create New Location';
        document.getElementById('locationCancelEditBtn').style.display = 'none';
    }

    function saveLocation() {
        const id = document.getElementById('locationIdInput').value;
        const name = document.getElementById('locationNameInput').value.trim();
        const province = document.getElementById('locationProvinceInput').value.trim();
        const muni = document.getElementById('locationMuniInput').value.trim();
        const brgy = document.getElementById('locationBrgyInput').value.trim();
        const fee = document.getElementById('locationFeeInput').value;
        const user = adminAuth.getUser();
        const adminId = user ? user.id : null;

        if (!name || !province || !muni || !adminId) {
            showNotification('Zone Name, Province, Municipality and admin authorization are required.', 'error');
            return;
        }

        if (!user || user.role !== 'super_admin') {
            showNotification('Only Super Admin can manage locations.', 'error');
            return;
        }

        const payload = {
            name: name,
            province: province,
            municipality: muni,
            barangay: brgy,
            delivery_fee: parseFloat(fee) || 0,
            requester_id: adminId
        };

        const url = id ? `/admin/locations/${id}` : '/admin/locations';
        const method = id ? 'PUT' : 'POST';

        locationsApiCall(url, method, payload)
            .then(function() {
                showNotification(id ? 'Location updated successfully' : 'Location created successfully', 'success');
                resetLocationForm();
                fetchLocations();
            })
            .catch(function(err) {
                console.error('Error saving location:', err);
                showNotification('Error saving location: ' + (err.error || 'Unknown error'), 'error');
            });
    }

    function deleteLocation(locId) {
        if (!confirm('Are you sure you want to delete this location?')) return;
        const user = adminAuth.getUser();
        const adminId = user ? user.id : null;

        if (!adminId) {
            showNotification('Unauthorized', 'error');
            return;
        }

        if (!user || user.role !== 'super_admin') {
            showNotification('Only Super Admin can delete locations.', 'error');
            return;
        }

        locationsApiCall(`/admin/locations/${locId}?requester_id=${adminId}`, 'DELETE')
            .then(function() {
                showNotification('Location deleted successfully', 'success');
                fetchLocations();
            })
            .catch(function(err) {
                console.error('Error deleting location:', err);
                showNotification('Error deleting location.', 'error');
            });
    }







    // --- VEHICLES MODULE (REFINED) ---



    const Vehicles = {



        data: [],



        _filter: 'all',







        setFilter(filter, btn) {



            this._filter = filter;



            document.querySelectorAll('.veh-chip').forEach(b => {



                const active = b.dataset.filter === filter;



                b.style.background  = active ? 'var(--primary)' : 'var(--surface-container)';



                b.style.borderColor = active ? 'var(--primary)' : 'var(--border)';



                b.style.color       = active ? '#fff' : 'var(--text-secondary)';



            });



            this.applyFilters();



        },







        applyFilters() {
            const q = (document.getElementById('vehicleSearch')?.value || '').toLowerCase().trim();
            const categoryFilter = document.getElementById('vehicleCategoryFilter')?.value || 'all';
            const f = this._filter;

            const filtered = this.data.filter(v => {
                const status = (v.status || '').toLowerCase();
                const matchF = f === 'all' || status === f;

                let matchCat = true;
                if (categoryFilter !== 'all') {
                    matchCat = (v.vehicle_type || '') === categoryFilter;
                }

                const matchQ = !q ||
                    (v.brand        || '').toLowerCase().includes(q) ||
                    (v.model        || '').toLowerCase().includes(q) ||
                    (v.plate_number || '').toLowerCase().includes(q) ||
                    (v.vehicle_type || '').toLowerCase().includes(q);

                return matchF && matchCat && matchQ;



            });



            this._render(filtered);



        },



        async refresh() {



            const listContainer = document.getElementById('vehiclesList');
            showSkeleton('vehiclesList', 'list');



            if (!listContainer.innerHTML.trim() || listContainer.innerHTML.includes('Loading vehicles')) {



                listContainer.innerHTML = '<div style="text-align: center; padding: 50px; color: var(--text-muted);">Loading vehicles...</div>';



            }



            try {



                const res = await fetch(`${API_URL}/vehicles`);



                if (!res.ok) throw new Error('Server not reachable');



                this.data = await res.json();



                // Reset search + chips



                const s = document.getElementById('vehicleSearch');



                if (s) s.value = '';



                this._filter = 'all';



                document.querySelectorAll('.veh-chip').forEach(b => {



                    const active = b.dataset.filter === 'all';



                    b.style.background  = active ? 'var(--primary)' : 'var(--surface-container)';



                    b.style.borderColor = active ? 'var(--primary)' : 'var(--border)';



                    b.style.color       = active ? '#fff' : 'var(--text-secondary)';



                });



                this._render(this.data);



            } catch (err) {



                console.error('Vehicles Refresh Error:', err);



                listContainer.innerHTML = `<div style="text-align: center; padding: 50px; color: var(--danger);">



                    <i class="fas fa-exclamation-circle" style="font-size: 2rem; margin-bottom: 10px;"></i><br>



                    Could not load vehicles. Check your connection.<br>



                    <button onclick="Vehicles.refresh()" style="margin-top:10px; color:white; background:var(--primary); border:none; padding:8px 15px; border-radius:5px;">Retry</button>



                </div>`;



            }



        },



        



        galleryDetails: [],







        CAR_DATA: {



            "Toyota": ["Vios", "Fortuner", "Innova", "Hilux", "Wigo", "Rush", "Raize", "Hiace"],



            "Mitsubishi": ["Montero Sport", "Mirage G4", "L300", "Xpander", "Strada"],



            "Nissan": ["Navara", "Terra", "Almera", "Urvan", "Patrol"],



            "Honda": ["Civic", "City", "BR-V", "CR-V", "Brio", "HR-V"],



            "Hyundai": ["Starex", "Accent", "Tucson", "Santa Fe", "Creta", "Staria"],



            "Ford": ["Everest", "Ranger", "Territory", "Mustang"],



            "Suzuki": ["Ertiga", "Swift", "Dzire", "Jimny", "S-Presso"],



            "Isuzu": ["mu-X", "D-MAX", "Traviz"],
            "Kia": ["Seltos", "Carnival", "Stonic", "Soluto", "Sportage"],
            "MG": ["MG 5", "MG ZS", "MG GT", "MG HS"],
            "Geely": ["Coolray", "Okavango", "Azkarra", "Emgrand"],
            "Subaru": ["Forester", "XV", "Outback", "WRX"],
            "Mazda": ["Mazda 2", "Mazda 3", "CX-3", "CX-5", "CX-9", "BT-50"],
            "Chevrolet": ["Tracker", "Trailblazer", "Colorado", "Suburban"]



        },







        CAR_SPECS: {



            "Vios": { seats: "5", type: "Sedan", fuel: "Gasoline" },



            "Fortuner": { seats: "7", type: "SUV", fuel: "Diesel" },



            "Innova": { seats: "7", type: "MPV", fuel: "Diesel" },



            "Hilux": { seats: "5", type: "Pickup", fuel: "Diesel" },



            "Wigo": { seats: "5", type: "Hatchback", fuel: "Gasoline" },



            "Rush": { seats: "7", type: "SUV", fuel: "Gasoline" },



            "Raize": { seats: "5", type: "SUV", fuel: "Gasoline" },



            "Hiace": { seats: "12", type: "Van", fuel: "Diesel" },



            "Montero Sport": { seats: "7", type: "SUV", fuel: "Diesel" },



            "Mirage G4": { seats: "5", type: "Sedan", fuel: "Gasoline" },



            "L300": { seats: "10", type: "Van", fuel: "Diesel" },



            "Xpander": { seats: "7", type: "MPV", fuel: "Gasoline" },



            "Strada": { seats: "5", type: "Pickup", fuel: "Diesel" },



            "Navara": { seats: "5", type: "Pickup", fuel: "Diesel" },



            "Terra": { seats: "7", type: "SUV", fuel: "Diesel" },



            "Almera": { seats: "5", type: "Sedan", fuel: "Gasoline" },



            "Urvan": { seats: "12", type: "Van", fuel: "Diesel" },



            "Civic": { seats: "5", type: "Sedan", fuel: "Gasoline" },



            "City": { seats: "5", type: "Sedan", fuel: "Gasoline" },



            "BR-V": { seats: "7", type: "SUV", fuel: "Gasoline" },



            "CR-V": { seats: "7", type: "SUV", fuel: "Diesel" },



            "Brio": { seats: "5", type: "Hatchback", fuel: "Gasoline" },



            "Ertiga": { seats: "7", type: "MPV", fuel: "Gasoline" },



            "Jimny": { seats: "4", type: "SUV", fuel: "Gasoline" },



            "Everest": { seats: "7", type: "SUV", fuel: "Diesel" },



            "Ranger": { seats: "5", type: "Pickup", fuel: "Diesel" }



        },







        updateModels(selectedModel = null) {
            const brand = document.getElementById('vBrand').value;
            const modelSelect = document.getElementById('vModel');
            const modelDataList = document.getElementById('vModelList');
            if (modelDataList) modelDataList.innerHTML = '';

            if (modelSelect) {
                modelSelect.innerHTML = '<option value="">Select Model</option>';
                const models = (brand && this.CAR_DATA && this.CAR_DATA[brand]) ? this.CAR_DATA[brand] : [];

                models.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.textContent = m;
                    modelSelect.appendChild(opt);

                    if (modelDataList) {
                        const dOpt = document.createElement('option');
                        dOpt.value = m;
                        modelDataList.appendChild(dOpt);
                    }
                });

                // If selectedModel exists but is not in predefined list (e.g. custom or older model), preserve it
                if (selectedModel && !models.includes(selectedModel)) {
                    const customOpt = document.createElement('option');
                    customOpt.value = selectedModel;
                    customOpt.textContent = selectedModel;
                    modelSelect.appendChild(customOpt);
                }

                if (selectedModel) {
                    modelSelect.value = selectedModel;
                    this.applySpecs(selectedModel);
                }
            }
        },

        applySpecs(model) {



            const editingId = document.getElementById('editId').value;



            if (!model || editingId) return; // Don't auto-fill if editing existing



            const specs = this.CAR_SPECS[model];



            if (specs) {



                if (specs.seats) document.getElementById('vSeats').value = specs.seats;



                if (specs.type) document.getElementById('vType').value = specs.type;



                if (specs.fuel) document.getElementById('vFuel').value = specs.fuel;



            }



        },







        render() { this._render(this.data); },
        renderVehicles() { this.applyFilters(); },







        _render(vehicles) {



            const listContainer = document.getElementById('vehiclesList');



            if (!vehicles || vehicles.length === 0) {



                listContainer.innerHTML = `



                    <div style="text-align:center;padding:60px 20px;background:var(--surface);border-radius:var(--radius-lg);border:1px solid var(--border);">



                        <i class="fas fa-car-crash" style="font-size:3rem;color:var(--text-muted);opacity:0.3;margin-bottom:15px;"></i>



                        <p style="color:var(--text-muted);font-weight:600;">No vehicles found.</p>



                    </div>`;



                return;



            }







            const statusColor = s => {



                switch ((s||'').toLowerCase()) {



                    case 'available':   return '#00B14F';



                    case 'rented':      return '#00B14F';



                    case 'maintenance': return '#f59e0b';



                    default:            return '#ef4444';



                }



            };







            listContainer.innerHTML = `<ul style="list-style:none;margin:0;padding:0;">` +
                vehicles.map((v, i) => {
                    const sc = statusColor(v.status);
                    
                    // Fallback placeholder logic for missing or document/license images
                    const isDocImg = (v.vehicle_image || '').match(/license|cropped|driver|id_card|passport|doc/i);
                    const carImgSrc = (v.vehicle_image && !isDocImg) ? v.vehicle_image : '';
                    
                    const imgHtml = carImgSrc
                        ? `<img src="${carImgSrc}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" style="width:100%;height:100%;object-fit:cover;border-radius:12px;"><div style="display:none;width:100%;height:100%;align-items:center;justify-content:center;background:rgba(99,102,241,0.08);border-radius:12px;"><i class="fas fa-car" style="font-size:1.6rem;color:var(--primary);opacity:0.6;"></i></div>`
                        : `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:rgba(99,102,241,0.08);border-radius:12px;"><i class="fas fa-car" style="font-size:1.6rem;color:var(--primary);opacity:0.6;"></i></div>`;

                    const transBadge = `<span style="display:inline-block;padding:2px 6px;border-radius:6px;background:rgba(99,102,241,0.1);color:#4f46e5;font-size:0.65rem;font-weight:700;margin-right:4px;">${v.transmission || 'Auto'}</span>`;
                    const fuelBadge = `<span style="display:inline-block;padding:2px 6px;border-radius:6px;background:rgba(234,179,8,0.12);color:#854d0e;font-size:0.65rem;font-weight:700;">${v.fuel_type || 'Gas'}</span>`;

                    const statusDropdownHtml = `
                        <select onchange="Vehicles.quickChangeStatus(${v.id}, this.value)" style="display:inline-block;padding:3px 8px;border-radius:20px;background:${sc};color:#fff;font-size:0.65rem;font-weight:800;border:none;cursor:pointer;outline:none;">
                            <option value="Available" ${v.status === 'Available' ? 'selected' : ''} style="background:#fff;color:#000;">Available</option>
                            <option value="Booked" ${v.status === 'Booked' ? 'selected' : ''} style="background:#fff;color:#000;">Booked</option>
                            <option value="Rented" ${v.status === 'Rented' ? 'selected' : ''} style="background:#fff;color:#000;">Rented</option>
                            <option value="Maintenance" ${v.status === 'Maintenance' ? 'selected' : ''} style="background:#fff;color:#000;">Maintenance</option>
                            <option value="Repair" ${v.status === 'Repair' ? 'selected' : ''} style="background:#fff;color:#000;">Repair</option>
                            <option value="Unavailable" ${v.status === 'Unavailable' ? 'selected' : ''} style="background:#fff;color:#000;">Unavailable</option>
                        </select>
                    `;

                    return `
                    <li style="display:flex;align-items:center;gap:14px;padding:14px 16px;background:var(--surface-card,var(--surface));${i === 0 ? 'border-radius:16px 16px 0 0;' : ''}${i === vehicles.length-1 ? 'border-radius:0 0 16px 16px;' : ''}border-bottom:${i < vehicles.length-1 ? '1px solid var(--border)' : 'none'};">
                        <div style="flex-shrink:0;width:72px;height:56px;background:var(--surface-container);border-radius:12px;display:flex;align-items:center;justify-content:center;overflow:hidden;">
                            ${imgHtml}
                        </div>
                        <div style="flex:1;min-width:0;">
                            <div style="display:flex;align-items:center;justify-space-between;margin-bottom:2px;">
                                <div style="font-size:0.95rem;font-weight:900;color:var(--primary);letter-spacing:-0.3px;">₱${Number(v.daily_rate||0).toLocaleString()}</div>
                                <div style="display:flex;align-items:center;gap:3px;">${transBadge}${fuelBadge}</div>
                            </div>
                            <div style="font-size:0.85rem;font-weight:700;color:var(--text-main);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${v.brand||''} ${v.model||''}</div>
                            <div style="font-size:0.72rem;color:var(--text-muted);font-weight:600;margin-bottom:5px;">${v.plate_number||'NO PLATE'}</div>
                            ${statusDropdownHtml}
                        </div>
                        <div style="flex-shrink:0;display:flex;flex-direction:column;gap:12px;align-items:center;">
                            <button onclick="Vehicles.view(${v.id})" style="background:none;border:none;color:var(--primary);font-size:1.05rem;padding:4px;cursor:pointer;" title="View Details"><i class="fas fa-eye"></i></button>
                            <button onclick="Vehicles.edit(${v.id})" style="background:none;border:none;color:var(--text-muted);font-size:1.05rem;padding:4px;cursor:pointer;"><i class="fas fa-pen-to-square"></i></button>
                            ${(()=>{ const _cu = adminAuth.getUser(); return _cu && _cu.role === 'super_admin' ? `<button onclick="Vehicles.delete(${v.id})" style="background:none;border:none;color:var(--danger);font-size:1.05rem;padding:4px;cursor:pointer;"><i class="fas fa-trash-can"></i></button>` : ''; })()}
                        </div>
                    </li>`;
                }).join('') + `</ul>`;
        },

        async quickChangeStatus(id, newStatus) {
            try {
                const res = await fetch(`${API_URL}/vehicles/${id}/status`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });
                if (res.ok) {
                    if (typeof showNotification === 'function') showNotification(`Status changed to ${newStatus}`, 'success');
                    const v = this.data.find(x => x.id == id);
                    if (v) v.status = newStatus;
                    this.applyFilters();
                } else {
                    let errMsg = 'Failed to update status';
                    try {
                        const errData = await res.json();
                        if (errData && errData.error) errMsg = errData.error;
                    } catch(e) {}
                    if (typeof showNotification === 'function') showNotification(errMsg, 'error');
                    this.refresh();
                }
            } catch (err) {
                console.error("quickChangeStatus error:", err);
                if (typeof showNotification === 'function') showNotification('Network error updating status', 'error');
                this.refresh();
            }
        },

        openModal(id = null) {
            document.getElementById('editId').value = id || '';
            document.getElementById('modalTitle').textContent = id ? 'Edit Vehicle' : 'Add New Vehicle';
            document.getElementById('submitBtnText').textContent = id ? 'Update Vehicle' : 'Add Vehicle';

            const addAnotherBtn = document.getElementById('saveAddAnotherBtn');
            if (addAnotherBtn) addAnotherBtn.style.display = id ? 'none' : 'inline-flex';

            if (id) {
                const v = this.data.find(x => x.id == id);
                if (!v) return;

                document.getElementById('vBrand').value = v.brand;
                this.updateModels(v.model);
                document.getElementById('vPlate').value = v.plate_number;
                document.getElementById('vColor').value = v.color || '';
                document.getElementById('vType').value = v.vehicle_type || 'Sedan';
                document.getElementById('vTrans').value = v.transmission || 'Automatic';
                document.getElementById('vFuel').value = v.fuel_type || 'Gasoline';
                document.getElementById('vSeats').value = v.seats || 5;
                document.getElementById('vLocation').value = v.location || 'Tanauan/Sto. Tomas, Batangas';
                document.getElementById('vStatus').value = v.status || 'Available';
                document.getElementById('vRate').value = v.daily_rate;
                document.getElementById('vYear').value = v.year_model || v.year || '';
                document.getElementById('vMileageType').value = v.mileage_type || 'limited';
                document.getElementById('vMileageKm').value = v.mileage_km_per_day || 250;
                document.getElementById('vMileageKmDiv').style.display = (v.mileage_type === 'unlimited') ? 'none' : 'block';

                document.getElementById('vOdometer').value = v.odometer || 0;
                document.getElementById('vFuelLevel').value = v.fuel_level || 'Full Tank';
                document.getElementById('vNextService').value = v.next_service_schedule || '';
                document.getElementById('vLtoExpiry').value = v.lto_expiry_date || '';
                document.getElementById('vGpsDeviceName').value = v.gps_device_name || '';
                document.getElementById('vGpsDeviceToken').value = v.gps_device_token || '';

                this.galleryDetails = v.gallery_details || [];
                this.renderGalleryManager();
            } else {
                document.getElementById('vehicleForm').reset();
                this.updateModels();
                document.getElementById('vYear').value = '';
                document.getElementById('vMileageType').value = 'limited';
                document.getElementById('vMileageKm').value = 250;
                document.getElementById('vMileageKmDiv').style.display = 'block';

                document.getElementById('vOdometer').value = 0;
                document.getElementById('vFuelLevel').value = 'Full Tank';
                document.getElementById('vNextService').value = '';
                document.getElementById('vLtoExpiry').value = '';
                document.getElementById('vGpsDeviceName').value = '';
                document.getElementById('vGpsDeviceToken').value = '';

                document.getElementById('vExistingGallery').style.display = 'none';
                this.galleryDetails = [];
            }

            VehiclePhotos.clear();
            document.getElementById('vehicleModal').style.display = 'block';
        },

        renderGalleryManager() {



            const container = document.getElementById('vGalleryManager');



            const section = document.getElementById('vExistingGallery');



            



            if (this.galleryDetails.length === 0) {



                section.style.display = 'none';



                return;



            }







            section.style.display = 'block';



            container.innerHTML = this.galleryDetails.map((img, index) => `



                <div style="flex: 0 0 90px; position: relative; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); background: rgba(15, 23, 42, 0.5);">



                    <img src="${img.image_path}" style="width: 100%; height: 70px; object-fit: cover;">



                    <div style="display: flex; justify-content: space-between; padding: 4px; background: rgba(0,0,0,0.6);">



                        <button type="button" onclick="Vehicles.moveImage(${index}, -1)" style="background:none; border:none; color:white;"><i class="fas fa-chevron-left"></i></button>



                        <button type="button" onclick="Vehicles.deleteImage(${img.id})" style="background:none; border:none; color:#ef4444;"><i class="fas fa-trash-alt"></i></button>



                        <button type="button" onclick="Vehicles.moveImage(${index}, 1)" style="background:none; border:none; color:white;"><i class="fas fa-chevron-right"></i></button>



                    </div>



                </div>



            `).join('');



        },







        async moveImage(index, direction) {



            const newIndex = index + direction;



            if (newIndex < 0 || newIndex >= this.galleryDetails.length) return;







            const item = this.galleryDetails.splice(index, 1)[0];



            this.galleryDetails.splice(newIndex, 0, item);



            



            this.renderGalleryManager();



            



            const id = document.getElementById('editId').value;



            try {



                await fetch(`${API_URL}/vehicles/${id}/images/order`, {



                    method: 'PUT',



                    headers: { 'Content-Type': 'application/json' },



                    body: JSON.stringify({ order: this.galleryDetails.map(img => img.id) })



                });



            } catch (err) { console.error('Order update failed:', err); }



        },







        async deleteImage(id) {



            if (!id) {



                alert('Error: Image ID is missing.');



                return;



            }



            if (!confirm('Delete this image permanently?')) return;



            



            try {



                const url = `${API_URL}/vehicles/images/${id}`;



                



                const res = await fetch(url, { method: 'DELETE' });



                



                if (res.ok) {



                    const data = await res.json();



                    



                    this.galleryDetails = this.galleryDetails.filter(img => img.id !== id);



                    this.renderGalleryManager();



                    



                    alert('Image deleted successfully!');



                    await this.refresh();



                } else {



                    const errData = await res.json().catch(() => ({}));



                    console.error('Mobile: Delete failed server-side:', errData);



                    alert('Failed to delete image: ' + (errData.error || 'Server error ' + res.status));



                }



            } catch (err) {



                console.error('Mobile: Network error during image deletion:', err);



                alert('Network error: Could not reach the server at ' + API_BASE);



            }



        },



        async submitForm(addAnother = false) {



            const id = document.getElementById('editId').value;



            const isEdit = !!id;







            // Validate photos for new vehicles
            if (!VehiclePhotos.validate(isEdit)) return;

            // Clear previous inline errors
            const fieldIds = ['vBrand', 'vModel', 'vPlate', 'vRate', 'vYear', 'vMileageKm'];
            fieldIds.forEach(fid => {
                const el = document.getElementById(fid);
                if (el) clearInlineError(el);
            });

            let hasError = false;

            const brandEl = document.getElementById('vBrand');
            if (!brandEl.value.trim()) { showInlineError(brandEl, 'Brand is required'); hasError = true; }

            const modelEl = document.getElementById('vModel');
            if (!modelEl.value.trim()) { showInlineError(modelEl, 'Model is required'); hasError = true; }

            const plateEl = document.getElementById('vPlate');
            if (!plateEl.value.trim()) { showInlineError(plateEl, 'Plate Number is required'); hasError = true; }

            const rateEl = document.getElementById('vRate');
            if (!rateEl.value || parseFloat(rateEl.value) <= 0) { showInlineError(rateEl, 'Valid daily rate is required'); hasError = true; }

            const yearEl = document.getElementById('vYear');
            if (yearEl.value && (yearEl.value.length !== 4 || isNaN(yearEl.value) || parseInt(yearEl.value) < 1990 || parseInt(yearEl.value) > 2030)) {
                showInlineError(yearEl, 'Must be a valid 4-digit year (1990-2030)'); hasError = true;
            }

            const mileageTypeEl = document.getElementById('vMileageType');
            const mileageKmEl = document.getElementById('vMileageKm');
            if (mileageTypeEl.value === 'limited' && (!mileageKmEl.value || parseInt(mileageKmEl.value) <= 0)) {
                showInlineError(mileageKmEl, 'Limit must be greater than 0'); hasError = true;
            }

            if (hasError) {
                showNotification('Please fix the highlighted errors.', 'error');
                return;
            }

            const brand = brandEl.value.trim();
            const model = modelEl.value.trim();

            const formData = new FormData();



            formData.append('brand', brand);



            formData.append('model', model);



            formData.append('name', `${brand} ${model}`);



            formData.append('plate_number', document.getElementById('vPlate').value);



            formData.append('color', document.getElementById('vColor').value || '');



            formData.append('vehicle_type', document.getElementById('vType').value);



            formData.append('transmission', document.getElementById('vTrans').value);



            formData.append('fuel_type', document.getElementById('vFuel').value);

            const seatsRaw = document.getElementById('vSeats').value;
            formData.append('seats', parseInt(seatsRaw) || 5);

            formData.append('location', document.getElementById('vLocation').value);

            formData.append('status', document.getElementById('vStatus').value);
            const rateRaw = document.getElementById('vRate').value;
            formData.append('daily_rate', parseFloat(String(rateRaw).replace(/[^0-9.]/g, '')) || 0);
            formData.append('year_model', document.getElementById('vYear').value || '');
            formData.append('mileage_type', document.getElementById('vMileageType').value);
            formData.append('mileage_km_per_day', document.getElementById('vMileageKm').value || 250);

            formData.append('odometer', document.getElementById('vOdometer').value || 0);
            formData.append('fuel_level', document.getElementById('vFuelLevel').value || 'Full Tank');
            formData.append('next_service_schedule', document.getElementById('vNextService').value || '');
            formData.append('lto_expiry_date', document.getElementById('vLtoExpiry').value || '');
        const vGpsDeviceNameEl = document.getElementById('vGpsDeviceName');
        const vGpsDeviceTokenEl = document.getElementById('vGpsDeviceToken');
        if (vGpsDeviceNameEl) formData.append('gps_device_name', vGpsDeviceNameEl.value.trim());
        if (vGpsDeviceTokenEl) formData.append('gps_device_token', vGpsDeviceTokenEl.value.trim());







            // Append new photos



            VehiclePhotos.appendTo(formData);







            const method = isEdit ? 'PUT' : 'POST';



            const url = isEdit ? `${API_URL}/vehicles/${id}/` : `${API_URL}/vehicles/`;







            // Disable submit buttons during upload



            const submitBtn = document.getElementById('submitBtnText');



            const addAnotherBtn = document.getElementById('saveAddAnotherBtn');



            const origText = submitBtn.textContent;



            submitBtn.disabled = true;



            submitBtn.textContent = 'Saving...';



            if (addAnotherBtn) addAnotherBtn.disabled = true;







            try {



                const res = await fetch(url, { method, body: formData });



                if (res.ok) {



                    showNotification(isEdit ? 'Vehicle updated!' : 'Vehicle added!', 'success');



                    this.refresh();



                    if (addAnother) {



                        // Reset form but keep modal open - clear photos completely



                        document.getElementById('vehicleForm').reset();



                        this.updateModels();



                        document.getElementById('vExistingGallery').style.display = 'none';



                        this.galleryDetails = [];



                        VehiclePhotos.clear();  // mandatory clear for "Save & Add Another"



                        document.getElementById('vehicleModal').scrollTop = 0; const _sb2 = document.getElementById('vModalScrollBody'); if (_sb2) _sb2.scrollTop = 0;



                    } else {



                        this.closeModal();



                    }



                } else {



                    const err = await res.json().catch(() => ({}));



                    showNotification(err.error || 'Error saving vehicle', 'error');



                }



            } catch (err) {



                showNotification('Connection failed', 'error');



            } finally {



                submitBtn.disabled = false;



                submitBtn.textContent = origText;



                if (addAnotherBtn) addAnotherBtn.disabled = false;



            }



        },







        closeModal() { document.getElementById('vehicleModal').style.display = 'none'; },



        async delete(id) {



            const currentUser = adminAuth.getUser();
            if (!currentUser || currentUser.role !== 'super_admin') {
                showNotification('Only Super Admin can delete vehicles.', 'error');
                return;
            }

            if (!confirm('Delete this vehicle?')) return;



            try {



                const res = await fetch(`${API_URL}/vehicles/${id}/?admin_id=${currentUser.id}`, { method: 'DELETE' });



                if (res.ok) this.refresh();



            } catch (err) { showNotification('Error deleting vehicle', 'error'); }



        },



        

        view(id) {
            const v = this.data.find(x => x.id == id);
            if (!v) { console.error('Vehicle not found:', id); return; }
            const statusColor = s => {
                switch ((s||'').toLowerCase()) {
                    case 'available': return '#10b981';
                    case 'rented': return '#3b82f6';
                    case 'maintenance': return '#f59e0b';
                    default: return '#64748b';
                }
            };
            const sc = statusColor(v.status);
            
            const isDocImg = (v.vehicle_image || '').match(/license|cropped|driver|id_card|passport|doc/i);
            const carImgSrc = (v.vehicle_image && !isDocImg) ? v.vehicle_image : '';
            
            const imgHtml = carImgSrc
                ? `<img src="${carImgSrc}" style="width:100%;height:220px;object-fit:cover;">`
                : `<div style="width:100%;height:180px;background:var(--surface-container,#f4f6fb);display:flex;align-items:center;justify-content:center;"><i class="fas fa-car" style="font-size:4rem;color:var(--primary);opacity:0.3;"></i></div>`;
            const galleryArr = Array.isArray(v.gallery) ? v.gallery : [];
            const galleryHtml = galleryArr.length > 1
                ? `<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;padding:12px 16px 0;">` +
                  galleryArr.slice(1,7).map(g => `<img src="${g}" style="width:100%;height:72px;object-fit:cover;border-radius:8px;cursor:pointer;" onclick="window.open('${g}','_blank')">`).join('') +
                  `</div>` : '';
            const fields = [
                ['Brand', v.brand || '-'], ['Model', v.model || '-'],
                ['Plate Number', v.plate_number || '-'], ['Type', v.vehicle_type || '-'],
                ['Transmission', v.transmission || '-'], ['Fuel Type', v.fuel_type || '-'],
                ['Seats', v.seats || '-'], ['Daily Rate', '₱' + Number(v.daily_rate||0).toLocaleString()],
                ['Location', v.location || '-'], ['Status', v.status || '-'],
                ['Color', v.color || v.color_display || '-'], ['Year Model', v.year_model || v.year || '-'],
                ['Odometer', v.odometer ? (Number(v.odometer).toLocaleString() + ' km') : '0 km'],
                ['Fuel Level', v.fuel_level || '-'],
                ['Next Service Date', v.next_service_schedule || '-'],
                ['LTO Expiry Date', v.lto_expiry_date || '-'],
            ];
            const fieldsHtml = `<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px 16px;padding:16px;">`
                + fields.map(([label,val]) => `<div><div style="font-size:0.62rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.4px;margin-bottom:3px;">${label}</div><div style="font-size:0.88rem;font-weight:600;color:var(--text-main);">${val}</div></div>`).join('')
                + `</div>`;
            document.getElementById('vdModalTitle').textContent = (v.brand||'') + ' ' + (v.model||'');
            document.getElementById('vehicleDetailContent').innerHTML =
                imgHtml + galleryHtml +
                `<div style="margin:12px 16px 0;"><span style="display:inline-block;padding:4px 14px;border-radius:20px;background:${sc};color:#fff;font-size:0.72rem;font-weight:800;">${v.status||'Unknown'}</span></div>` +
                fieldsHtml +
                (v.description ? `<div style="padding:0 16px 16px;font-size:0.85rem;color:var(--text-secondary);line-height:1.5;border-top:1px solid var(--border);padding-top:12px;">${v.description}</div>` : '');
            const modal = document.getElementById('vehicleDetailModal');
            if (modal) { modal.style.display = 'flex'; }
        },

async edit(id) { this.openModal(id); }



    };







    // ?? VEHICLE PHOTOS MODULE ??????????????????????????????????????????????????



    // Manages up to 4 new photos selected for a vehicle add/edit operation.



    // Each entry: { file: File, dataUrl: string, label: string }



    const VehiclePhotos = {



        MAX: 4,



        LABELS: ['Main', 'Front', 'Side', 'Rear'],



        _items: [],   // { file, dataUrl, label }







        clear() {



            this._items = [];



            this._render();



            // Reset the hidden file input so the same file can be re-selected



            const inp = document.getElementById('vGalleryPicker');



            if (inp) inp.value = '';



        },







        // Called when user picks files from gallery input



        onFilePick(input) {



            const files = Array.from(input.files);



            files.forEach(f => this._addFile(f));



            input.value = ''; // allow re-picking same file



        },







        // Called by "Take Photo" button - uses Capacitor Camera if available,



        // falls back to a hidden file input with capture="environment"



        async takePhoto() {



            const Camera = window.Capacitor?.Plugins?.Camera;



            if (Camera) {



                try {



                    const photo = await Camera.getPhoto({



                        quality: 85,



                        allowEditing: false,



                        resultType: 'base64',



                        source: 'CAMERA'



                    });



                    // Convert base64 to File



                    const byteStr = atob(photo.base64String);



                    const arr = new Uint8Array(byteStr.length);



                    for (let i = 0; i < byteStr.length; i++) arr[i] = byteStr.charCodeAt(i);



                    const blob = new Blob([arr], { type: 'image/jpeg' });



                    const file = new File([blob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' });



                    this._addFile(file);



                } catch (err) {



                    if (err.message !== 'User cancelled photos app') {



                        showNotification('Camera error: ' + err.message, 'error');



                    }



                }



            } else {



                // Fallback: trigger a file input with camera capture



                let cap = document.getElementById('vCameraCapture');



                if (!cap) {



                    cap = document.createElement('input');



                    cap.type = 'file';



                    cap.accept = 'image/*';



                    cap.capture = 'environment';



                    cap.id = 'vCameraCapture';



                    cap.style.display = 'none';



                    cap.addEventListener('change', () => {



                        Array.from(cap.files).forEach(f => this._addFile(f));



                        cap.value = '';



                    });



                    document.body.appendChild(cap);



                }



                cap.click();



            }



        },







        _addFile(file) {
            if (!file) return;
            const isImg = (file.type || "").toLowerCase().startsWith("image/") || /\.(jpe?g|png|webp|gif|heic)$/i.test(file.name || "");
            if (!isImg) {
                showNotification("Only image files (JPG, PNG, WebP) are allowed.", "error");
                return;
            }
            if (file.size > 5 * 1024 * 1024) {
                showNotification("Vehicle photo must be 5 MB or smaller.", "error");
                return;
            }
            if (this._items.length >= this.MAX) {



                showNotification(`Maximum ${this.MAX} photos allowed.`, 'error');



                return;



            }



            const reader = new FileReader();



            reader.onload = (e) => {



                const label = this.LABELS[this._items.length] || `Photo ${this._items.length + 1}`;



                this._items.push({ file, dataUrl: e.target.result, label });



                this._render();



            };



            reader.readAsDataURL(file);



        },







        remove(index) {



            this._items.splice(index, 1);



            // Re-assign labels after removal



            this._items.forEach((item, i) => { item.label = this.LABELS[i] || `Photo ${i + 1}`; });



            this._render();



        },







        _render() {



            const strip = document.getElementById('vPhotoStrip');



            if (!strip) return;



            if (this._items.length === 0) {



                strip.innerHTML = '';



                return;



            }



            strip.innerHTML = this._items.map((item, i) => `



                <div style="position: relative; flex-shrink: 0;">



                    <div style="width: 80px; height: 80px; border-radius: 10px; overflow: hidden; border: 2px solid ${i === 0 ? '#00B14F' : 'rgba(255,255,255,0.1)'};">



                        <img src="${item.dataUrl}" style="width: 100%; height: 100%; object-fit: cover;">



                    </div>



                    <div style="position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,0.65); text-align: center; font-size: 0.55rem; font-weight: 700; color: ${i === 0 ? '#00B14F' : '#94a3b8'}; padding: 2px 0; border-radius: 0 0 8px 8px;">



                        ${item.label}



                    </div>



                    <button type="button" onclick="VehiclePhotos.remove(${i})"



                        style="position: absolute; top: -6px; right: -6px; width: 20px; height: 20px; background: #ef4444; border: none; border-radius: 50%; color: white; font-size: 0.6rem; display: flex; align-items: center; justify-content: center; cursor: pointer; line-height: 1;">



                        <i class="fas fa-times"></i>



                    </button>



                </div>



            `).join('');



        },







        // Returns true if valid, false + shows toast if not



        validate(isEdit) {



            if (isEdit) return true; // editing: photos optional (existing gallery handles it)



            if (this._items.length === 0) {



                showNotification('Please add at least one vehicle photo (Main photo is required).', 'error');



                return false;



            }



            return true;



        },







        // Appends files to a FormData object



        appendTo(formData) {



            this._items.forEach(item => {



                formData.append('gallery', item.file);



            });



            // Set first photo as the main vehicle_image via URL after upload



            // (server will handle gallery[0] as primary)



        }



    };







    // Form Handler



    document.getElementById('vehicleForm').addEventListener('submit', async function(e) {



        e.preventDefault();



        await Vehicles.submitForm(false);



    });







    function toggleDrawer(show) {
        const drawer = document.getElementById('sideDrawer');
        const overlay = document.getElementById('drawerOverlay');
        const toggleBtn = document.getElementById('sidebarToggleBtn');
        if (!drawer) return;

        const isDesktop = (window.innerWidth >= 769);

        if (isDesktop) {
            // Desktop mode: dock or collapse sidebar
            const isCurrentlyCollapsed = document.body.classList.contains('sidebar-collapsed');
            const shouldCollapse = (show !== undefined) ? !show : !isCurrentlyCollapsed;

            if (shouldCollapse) {
                document.body.classList.add('sidebar-collapsed');
                drawer.classList.remove('open');
                drawer.style.left = '';
                if (toggleBtn) {
                    toggleBtn.setAttribute('title', 'Open Sidebar Navigation');
                    toggleBtn.setAttribute('aria-expanded', 'false');
                }
                try { localStorage.setItem('autoride_sidebar_collapsed', 'true'); } catch(e){}
            } else {
                document.body.classList.remove('sidebar-collapsed');
                drawer.classList.add('open');
                drawer.style.left = '';
                if (toggleBtn) {
                    toggleBtn.setAttribute('title', 'Close Sidebar Navigation');
                    toggleBtn.setAttribute('aria-expanded', 'true');
                }
                try { localStorage.setItem('autoride_sidebar_collapsed', 'false'); } catch(e){}
            }
            if (overlay) {
                overlay.style.display = 'none';
                overlay.style.opacity = '0';
            }
        } else {
            // Mobile mode: overlay drawer
            document.body.classList.remove('sidebar-collapsed');
            const isOpen = (drawer.style.left === '0px' || drawer.classList.contains('open'));
            const shouldOpen = (show !== undefined) ? !!show : !isOpen;

            if (shouldOpen) {
                drawer.classList.add('open');
                drawer.style.left = '0px';
                if (overlay) {
                    overlay.style.display = 'block';
                    setTimeout(() => { if (overlay) overlay.style.opacity = '1'; }, 10);
                }
                if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'true');
            } else {
                drawer.classList.remove('open');
                drawer.style.left = '-280px';
                if (overlay) {
                    overlay.style.opacity = '0';
                    setTimeout(() => { if (overlay) overlay.style.display = 'none'; }, 280);
                }
                if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'false');
            }
        }
    }

    // Keyboard shortcut (Escape key closes drawer/sidebar)
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && typeof toggleDrawer === 'function') {
            if (window.innerWidth >= 769) {
                if (!document.body.classList.contains('sidebar-collapsed')) {
                    toggleDrawer(false);
                }
            } else {
                const drawer = document.getElementById('sideDrawer');
                if (drawer && (drawer.style.left === '0px' || drawer.classList.contains('open'))) {
                    toggleDrawer(false);
                }
            }
        }
    });

    // Window resize handler: clean up state transitions
    window.addEventListener('resize', function() {
        const drawer = document.getElementById('sideDrawer');
        const overlay = document.getElementById('drawerOverlay');
        if (window.innerWidth < 769) {
            document.body.classList.remove('sidebar-collapsed');
        } else {
            if (drawer) drawer.style.left = '';
            if (overlay) {
                overlay.style.display = 'none';
                overlay.style.opacity = '0';
            }
        }
    });

    // Restore desktop sidebar preference
    try {
        if (window.innerWidth >= 769 && localStorage.getItem('autoride_sidebar_collapsed') === 'true') {
            document.body.classList.add('sidebar-collapsed');
        }
    } catch(e){}

    function navTo(tabId) {
        switchTab(tabId);
        // On mobile, close drawer overlay so user sees the page content.
        // On desktop, keep sidebar in current state so admin can navigate smoothly.
        if (window.innerWidth < 769) {
            toggleDrawer(false);
        }
    }







    let currentTab = 'dashboard';



    
    // ==================== FLEET CALENDAR ====================
    const FleetCalendar = {
        currentDate: new Date(),
        viewMonths: 2,
        _shouldScrollToToday: false,
        bookings: [],
        blackouts: [],
        vehicles: [],
        searchQuery: '',
        activeBookingId: null,
        selectedColor: null,

        // Curated, attractive pastel/solid palette for schedule monitoring
        paletteColors: [
            { bg: '#fde047', text: '#713f12', border: '#eab308' }, // Yellow (matches Excel JEAN ALOR)
            { bg: '#86efac', text: '#14532d', border: '#22c55e' }, // Light Green (matches Excel SUNLINE)
            { bg: '#93c5fd', text: '#1e3a8a', border: '#3b82f6' }, // Sky Blue
            { bg: '#fdba74', text: '#7c2d12', border: '#f97316' }, // Orange
            { bg: '#d8b4fe', text: '#581c87', border: '#a855f7' }, // Purple
            { bg: '#fca5a5', text: '#7f1d1d', border: '#ef4444' }, // Soft Red
            { bg: '#f472b6', text: '#831843', border: '#ec4899' }, // Pink
            { bg: '#5eead4', text: '#134e4a', border: '#14b8a6' }, // Teal
            { bg: '#fde68a', text: '#78350f', border: '#f59e0b' }, // Amber
            { bg: '#c7d2fe', text: '#312e81', border: '#6366f1' }, // Indigo
            { bg: '#bef264', text: '#365314', border: '#84cc16' }, // Lime
            { bg: '#67e8f9', text: '#164e63', border: '#06b6d4' }  // Cyan
        ],

        // Automatically determine or hash customer color so repeat bookings share the same color
        getBookingColor(booking) {
            if (booking.calendar_color && booking.calendar_color.trim()) {
                const hex = booking.calendar_color.trim();
                let r = 0, g = 0, b = 0;
                if (hex.startsWith('#') && hex.length === 7) {
                    r = parseInt(hex.substring(1, 3), 16);
                    g = parseInt(hex.substring(3, 5), 16);
                    b = parseInt(hex.substring(5, 7), 16);
                } else if (hex.startsWith('#') && hex.length === 4) {
                    r = parseInt(hex[1] + hex[1], 16);
                    g = parseInt(hex[2] + hex[2], 16);
                    b = parseInt(hex[3] + hex[3], 16);
                }
                const lum = 0.299 * r + 0.587 * g + 0.114 * b;
                const textColor = lum > 160 ? '#0f172a' : '#ffffff';
                return { bg: hex, text: textColor, border: lum > 160 ? 'rgba(0,0,0,0.25)' : 'rgba(255,255,255,0.3)' };
            }

            const key = (booking.customer_name || (booking.user_id ? 'user_' + booking.user_id : 'booking_' + booking.id)).toLowerCase().trim();
            let hash = 0;
            for (let i = 0; i < key.length; i++) {
                hash = (hash << 5) - hash + key.charCodeAt(i);
                hash |= 0;
            }
            return this.paletteColors[Math.abs(hash) % this.paletteColors.length];
        },

        getTimeHalf(timeStr, defaultHalf = 'AM') {
            if (!timeStr) return defaultHalf;
            let s = String(timeStr).trim().toLowerCase();
            if (s.includes('am')) return 'AM';
            if (s.includes('pm')) return 'PM';
            const parts = s.split(':').map(Number);
            if (!isNaN(parts[0])) return parts[0] >= 12 ? 'PM' : 'AM';
            return defaultHalf;
        },

        setViewMonths(num) {
            this.viewMonths = (num === 1) ? 1 : 2;
            this.refresh();
        },
        
        async refresh() {
            try {
                const year1 = this.currentDate.getFullYear();
                const month1 = this.currentDate.getMonth();
                const startStr = `${year1}-${String(month1+1).padStart(2,'0')}-01`;
                
                let endStr;
                if (this.viewMonths === 2) {
                    const m2Date = new Date(year1, month1 + 1, 1);
                    const year2 = m2Date.getFullYear();
                    const month2 = m2Date.getMonth();
                    const lastDayM2 = new Date(year2, month2 + 1, 0).getDate();
                    endStr = `${year2}-${String(month2+1).padStart(2,'0')}-${String(lastDayM2).padStart(2,'0')}`;
                } else {
                    const lastDay = new Date(year1, month1 + 1, 0).getDate();
                    endStr = `${year1}-${String(month1+1).padStart(2,'0')}-${String(lastDay).padStart(2,'0')}`;
                }
                
                // Fetch vehicles, fleet bookings and blackouts
                const [vRes, cRes, bRes] = await Promise.all([
                    fetch(`${API_BASE}/api/vehicles`),
                    fetch(`${API_BASE}/api/admin/fleet-bookings?start=${startStr}&end=${endStr}`),
                    fetch(`${API_BASE}/api/admin/blackout-dates`)
                ]);
                this.vehicles = await vRes.json();
                this.bookings = await cRes.json();
                this.blackouts = await bRes.json();
                this.render();
            } catch (e) {
                console.error("Failed to load Fleet Calendar data:", e);
                showNotification("Failed to load calendar data", "error");
            }
        },

        onSearch(val) {
            this.searchQuery = (val || '').toLowerCase().trim();
            this.render();
        },

        goToToday() {
            this.currentDate = new Date();
            this._shouldScrollToToday = true;
            this.refresh();
        },
        
        prevMonth() {
            this.currentDate.setMonth(this.currentDate.getMonth() - 1);
            this._shouldScrollToToday = false;
            this.refresh();
        },
        
        nextMonth() {
            this.currentDate.setMonth(this.currentDate.getMonth() + 1);
            this._shouldScrollToToday = false;
            this.refresh();
        },
        
        render() {
            const year1 = this.currentDate.getFullYear();
            const month1 = this.currentDate.getMonth();
            const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
            const dayNamesShort = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
            const today = new Date();

            const isTwoMonths = (this.viewMonths === 2);
            const m2Date = new Date(year1, month1 + 1, 1);
            const year2 = m2Date.getFullYear();
            const month2 = m2Date.getMonth();

            const daysInMonth1 = new Date(year1, month1 + 1, 0).getDate();
            const daysInMonth2 = new Date(year2, month2 + 1, 0).getDate();

            // Sync Toolbar Month Label
            const labelEl = document.getElementById('fleetCalendarMonthLabel');
            if (labelEl) {
                if (isTwoMonths) {
                    if (year1 === year2) {
                        labelEl.textContent = `${monthNames[month1]} & ${monthNames[month2]} ${year1}`;
                    } else {
                        labelEl.textContent = `${monthNames[month1]} ${year1} & ${monthNames[month2]} ${year2}`;
                    }
                } else {
                    labelEl.textContent = `${monthNames[month1]} ${year1}`;
                }
            }

            // Sync View Mode Buttons
            const btn2 = document.getElementById('fcView2MonthsBtn');
            const btn1 = document.getElementById('fcView1MonthBtn');
            if (btn2 && btn1) {
                if (isTwoMonths) {
                    btn2.style.background = '#00B14F';
                    btn2.style.color = '#ffffff';
                    btn2.style.fontWeight = '800';
                    btn1.style.background = 'transparent';
                    btn1.style.color = 'var(--text-muted)';
                    btn1.style.fontWeight = '700';
                } else {
                    btn1.style.background = '#00B14F';
                    btn1.style.color = '#ffffff';
                    btn1.style.fontWeight = '800';
                    btn2.style.background = 'transparent';
                    btn2.style.color = 'var(--text-muted)';
                    btn2.style.fontWeight = '700';
                }
            }

            // Build array of months
            const monthsList = [
                {
                    year: year1,
                    month: month1,
                    daysCount: daysInMonth1,
                    name: monthNames[month1],
                    isCurrent: (today.getFullYear() === year1 && today.getMonth() === month1)
                }
            ];
            if (isTwoMonths) {
                monthsList.push({
                    year: year2,
                    month: month2,
                    daysCount: daysInMonth2,
                    name: monthNames[month2],
                    isCurrent: (today.getFullYear() === year2 && today.getMonth() === month2)
                });
            }

            // Flatten all days
            const allDays = [];
            monthsList.forEach((mObj, mIdx) => {
                for (let d = 1; d <= mObj.daysCount; d++) {
                    const dayDate = new Date(mObj.year, mObj.month, d);
                    const dayOfWeek = dayDate.getDay();
                    const isWeekend = (dayOfWeek === 0 || dayOfWeek === 6);
                    const isToday = mObj.isCurrent && (today.getDate() === d);
                    const isLastDayOfFirstMonth = (isTwoMonths && mIdx === 0 && d === mObj.daysCount);

                    allDays.push({
                        year: mObj.year,
                        month: mObj.month,
                        day: d,
                        monthIdx: mIdx,
                        monthName: mObj.name,
                        dayOfWeek,
                        dayName: dayNamesShort[dayOfWeek],
                        isWeekend,
                        isToday,
                        isLastDayOfFirstMonth,
                        dateKey: `${mObj.year}-${String(mObj.month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
                    });
                }
            });

            const totalSlots = allDays.length * 2;
            const calStart = new Date(year1, month1, 1, 0, 0, 0);
            const calEnd = isTwoMonths
                ? new Date(year2, month2, daysInMonth2, 23, 59, 59)
                : new Date(year1, month1, daysInMonth1, 23, 59, 59);

            // Tier 1 (Month Row): Sticky top: 0
            // Vehicle cell spans 3 rows (or 2 if 1 month)
            const headerRowSpan = isTwoMonths ? 3 : 2;

            let monthRowHtml = `<th rowspan="${headerRowSpan}" class="fc-vcol fc-vhead" style="padding: 10px 12px; border: 1px solid var(--border); text-align: left; background: var(--surface-solid); font-weight: 800; min-width: 180px; width: 180px; max-width: 180px; position: sticky; left: 0; top: 0; z-index: 40; border-right: 2px solid var(--border); border-bottom: 2px solid var(--border); color: var(--text-main); font-size: 0.8rem; vertical-align: middle;">
                <div style="display:flex; align-items:center; gap:6px;">
                    <i class="fas fa-car-side" style="color:#00B14F;"></i>
                    <span class="fc-vhead-text">VEHICLE / UNIT</span>
                </div>
            </th>`;

            if (isTwoMonths) {
                // Month 1 Header (Authoritative Autoride Green)
                monthRowHtml += `<th colspan="${daysInMonth1 * 2}" style="padding: 6px 12px; border: 1px solid var(--border); border-right: 3px solid #009240; text-align: center; background: linear-gradient(135deg, #15803d, #00B14F); color: #ffffff; position: sticky; top: 0; z-index: 25; font-size: 0.78rem; font-weight: 900; letter-spacing: 0.5px; text-transform: uppercase;">
                    <div style="display:inline-flex; align-items:center; gap:8px;">
                        <i class="fas fa-calendar-alt" style="font-size: 0.75rem;"></i>
                        <span>${monthNames[month1]} ${year1}</span>
                        <span style="background: rgba(255,255,255,0.25); padding: 1px 7px; border-radius: 10px; font-size: 0.65rem; font-weight: 800;">${daysInMonth1} DAYS</span>
                    </div>
                </th>`;

                // Month 2 Header (Crisp Blue)
                monthRowHtml += `<th colspan="${daysInMonth2 * 2}" style="padding: 6px 12px; border: 1px solid var(--border); text-align: center; background: linear-gradient(135deg, #1d4ed8, #3b82f6); color: #ffffff; position: sticky; top: 0; z-index: 25; font-size: 0.78rem; font-weight: 900; letter-spacing: 0.5px; text-transform: uppercase;">
                    <div style="display:inline-flex; align-items:center; gap:8px;">
                        <i class="fas fa-calendar-check" style="font-size: 0.75rem;"></i>
                        <span>${monthNames[month2]} ${year2}</span>
                        <span style="background: rgba(255,255,255,0.25); padding: 1px 7px; border-radius: 10px; font-size: 0.65rem; font-weight: 800;">${daysInMonth2} DAYS</span>
                    </div>
                </th>`;
            }

            // Tier 2 (Days Row): Sticky top: isTwoMonths ? '28px' : '0'
            const daysTopOffset = isTwoMonths ? '28px' : '0';
            let daysRowHtml = '';
            if (!isTwoMonths) {
                daysRowHtml += monthRowHtml;
                monthRowHtml = '';
            }

            // Tier 3 (AM/PM Row): Sticky top: isTwoMonths ? '66px' : '38px'
            const ampmTopOffset = isTwoMonths ? '66px' : '38px';
            let ampmRowHtml = '';

            allDays.forEach(day => {
                const dowBg = day.isToday ? '#dcfce7' : (day.isWeekend ? '#fee2e2' : 'var(--surface-solid)');
                const dowColor = day.isToday ? '#15803d' : (day.isWeekend ? '#ef4444' : 'var(--text-muted)');
                const dateBg = day.isToday ? '#bbf7d0' : (day.isWeekend ? '#fef2f2' : 'var(--surface-solid)');
                const dateColor = day.isToday ? '#15803d' : 'var(--text-main)';
                const dividerStyle = day.isLastDayOfFirstMonth ? 'border-right: 3px solid #009240 !important;' : '';

                daysRowHtml += `<th colspan="2" class="${day.isToday ? 'fc-today-col' : ''}" style="padding: 4px 2px; border: 1px solid var(--border); ${dividerStyle} text-align: center; background: ${dowBg}; position: sticky; top: ${daysTopOffset}; z-index: 22;">
                    <div style="font-weight: 800; font-size: 0.62rem; color: ${dowColor}; text-transform: uppercase;">${day.dayName}</div>
                    <div style="font-weight: 900; font-size: 0.82rem; color: ${dateColor}; line-height: 1.1;">${day.day}</div>
                </th>`;

                ampmRowHtml += `<th style="padding: 2px; border: 1px solid var(--border); border-right: 1px dashed var(--border); border-bottom: 2px solid var(--border); text-align: center; font-weight: 800; font-size: 0.58rem; min-width: 28px; width: 28px; background: ${dateBg}; color: ${day.isToday ? '#15803d' : 'var(--text-muted)'}; position: sticky; top: ${ampmTopOffset}; z-index: 22;">AM</th>`;
                ampmRowHtml += `<th style="padding: 2px; border: 1px solid var(--border); ${dividerStyle} border-bottom: 2px solid var(--border); text-align: center; font-weight: 800; font-size: 0.58rem; min-width: 28px; width: 28px; background: ${dateBg}; color: ${day.isToday ? '#15803d' : 'var(--text-muted)'}; position: sticky; top: ${ampmTopOffset}; z-index: 22;">PM</th>`;
            });

            const monthRowEl = document.getElementById('fleetCalendarMonthRow');
            if (monthRowEl) {
                if (isTwoMonths) {
                    monthRowEl.style.display = '';
                    monthRowEl.innerHTML = monthRowHtml;
                } else {
                    monthRowEl.style.display = 'none';
                    monthRowEl.innerHTML = '';
                }
            }

            const daysOfWeekEl = document.getElementById('fleetCalendarDaysOfWeekRow');
            if (daysOfWeekEl) daysOfWeekEl.innerHTML = daysRowHtml;

            const headerRowEl = document.getElementById('fleetCalendarHeaderRow');
            if (headerRowEl) headerRowEl.innerHTML = ampmRowHtml;

            // Filter vehicles and calculate stats
            let filteredVehicles = this.vehicles || [];
            if (this.searchQuery) {
                filteredVehicles = filteredVehicles.filter(v => {
                    const matchVeh = (v.brand + ' ' + v.model + ' ' + (v.plate_number || '')).toLowerCase().includes(this.searchQuery);
                    if (matchVeh) return true;
                    return (this.bookings || []).some(b => {
                        if (String(b.vehicle_id) !== String(v.id)) return false;
                        return (b.customer_name || '').toLowerCase().includes(this.searchQuery) ||
                               String(b.id).includes(this.searchQuery);
                    });
                });
            }

            // Calculate active bookings count & utilization in this period
            const periodBookings = (this.bookings || []).filter(b => {
                const s = new Date(b.start_date);
                const e = new Date(b.end_date);
                return s <= calEnd && e >= calStart && b.status !== 'cancelled' && b.status !== 'rejected';
            });

            const statCountEl = document.getElementById('fleetStatBookingsCount');
            if (statCountEl) {
                statCountEl.innerHTML = `<i class="fas fa-bookmark" style="color: #00B14F; margin-right: 4px;"></i><strong>${periodBookings.length}</strong> Active Bookings ${isTwoMonths ? '(2 Months)' : ''}`;
            }

            let totalBookedDays = 0;
            periodBookings.forEach(b => {
                const s = new Date(b.start_date);
                const e = new Date(b.end_date);
                const sClamped = Math.max(calStart.getTime(), s.getTime());
                const eClamped = Math.min(calEnd.getTime(), e.getTime());
                const days = Math.max(1, Math.round((eClamped - sClamped) / (1000 * 60 * 60 * 24)) + 1);
                totalBookedDays += days;
            });
            const totalPeriodDays = allDays.length;
            const totalPossibleVehicleDays = Math.max(1, (this.vehicles || []).length * totalPeriodDays);
            const utilizationPct = Math.min(100, Math.round((totalBookedDays / totalPossibleVehicleDays) * 100));
            const statUtilEl = document.getElementById('fleetStatUtilization');
            if (statUtilEl) {
                statUtilEl.innerHTML = `<i class="fas fa-chart-pie" style="color: #3b82f6; margin-right: 4px;"></i>Utilization: <strong>${utilizationPct}%</strong>`;
            }

            // Build fast lookup map from date string YYYY-MM-DD to day index in allDays
            const dayIndexMap = {};
            allDays.forEach((d, idx) => {
                dayIndexMap[d.dateKey] = idx;
            });
            const calStartKey = allDays[0].dateKey;
            const calEndKey = allDays[allDays.length - 1].dateKey;
            const lastSlotOfMonth1 = isTwoMonths ? (daysInMonth1 * 2 - 1) : -1;

            // Render Body Rows (Gantt Schedule with Colspan - AM & PM slots)
            let bodyHtml = "";
            filteredVehicles.forEach(v => {
                let rowHtml = `<tr style="border-bottom: 1px solid var(--border); transition: background 0.15s; height: 54px;">`;
                
                // Sticky Vehicle Cell
                rowHtml += `<td class="fc-vcol" onmouseenter="FleetCalendar.showVehicleTooltip(event, ${v.id})" onmouseleave="FleetCalendar.hideTooltip()" onclick="FleetCalendar.handleVehicleClick(event, ${v.id})"
                    style="padding: 6px 8px; border: 1px solid var(--border); background: var(--surface-solid); position: sticky; left: 0; z-index: 10; box-shadow: 2px 0 5px rgba(0,0,0,0.06); border-right: 2px solid var(--border); min-width: 180px; width: 180px; max-width: 180px; cursor: pointer; vertical-align: middle;" title="Click to view details or change vehicle daily rate">
                    <div class="fc-vbox" style="background: #15803d; color: white; padding: 5px 8px; border-radius: 8px; font-weight: 800; font-size: 0.72rem; text-shadow: 0 1px 2px rgba(0,0,0,0.3); line-height: 1.25; box-shadow: 0 2px 4px rgba(0,0,0,0.12); display: flex; flex-direction: column; justify-content: center; transition: transform 0.15s, box-shadow 0.15s;"
                         onmouseover="this.style.transform='scale(1.02)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)';"
                         onmouseout="this.style.transform='none'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.12)';">
                        <div class="fc-vname" style="font-weight: 900; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; letter-spacing: 0.2px;">${v.brand} ${v.model}</div>
                        <div class="fc-vmeta" style="display: flex; align-items: center; justify-content: space-between; gap: 4px; margin-top: 3px;">
                            <span style="font-size: 0.62rem; color: #bbf7d0; font-weight: 700; letter-spacing: 0.3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${v.plate_number || 'NO PLATE'}</span>
                            <span style="font-size: 0.62rem; color: #fef08a; font-weight: 800; background: rgba(0,0,0,0.25); padding: 1px 5px; border-radius: 4px; white-space: nowrap; display: inline-flex; align-items: center; gap: 3px;" title="Daily Rental Rate">
                                ₱${parseFloat(v.daily_rate||0).toLocaleString()}/d <i class="fas fa-edit fc-vedit" style="font-size: 0.55rem; opacity: 0.85;"></i>
                            </span>
                        </div>
                    </div>
                </td>`;

                // Calculate slot ranges for all active bookings of vehicle v
                const vBookings = (this.bookings || []).filter(bk => {
                    if (String(bk.vehicle_id) !== String(v.id)) return false;
                    if (bk.status === 'cancelled' || bk.status === 'rejected') return false;
                    return true;
                }).map(bk => {
                    const sStr = String(bk.start_date || '').split('T')[0];
                    const eStr = String(bk.end_date || '').split('T')[0];
                    if (!sStr || !eStr) return null;
                    if (eStr < calStartKey || sStr > calEndKey) return null;

                    let startSlot = 0;
                    if (sStr >= calStartKey) {
                        const dIdx = dayIndexMap[sStr];
                        if (dIdx !== undefined) {
                            const half = FleetCalendar.getTimeHalf(bk.start_time, 'AM');
                            startSlot = dIdx * 2 + (half === 'PM' ? 1 : 0);
                        }
                    }

                    let endSlot = totalSlots - 1;
                    if (eStr <= calEndKey) {
                        const dIdx = dayIndexMap[eStr];
                        if (dIdx !== undefined) {
                            const half = FleetCalendar.getTimeHalf(bk.end_time, 'PM');
                            endSlot = dIdx * 2 + (half === 'PM' ? 1 : 0);
                        }
                    }

                    if (endSlot < startSlot) endSlot = startSlot;
                    startSlot = Math.max(0, Math.min(totalSlots - 1, startSlot));
                    endSlot = Math.max(0, Math.min(totalSlots - 1, endSlot));
                    return { booking: bk, startSlot, endSlot };
                }).filter(Boolean);

                vBookings.sort((a, b) => a.startSlot - b.startSlot);

                // Calculate blackout slot ranges
                const vBlackouts = (this.blackouts || []).filter(bo => {
                    const isAff = !bo.affected_vehicles || bo.affected_vehicles === 'all' || 
                                  bo.affected_vehicles.split(',').map(s => s.trim()).includes(String(v.id));
                    return isAff;
                }).map(bo => {
                    const sStr = String(bo.start_date || '').split('T')[0];
                    const eStr = String(bo.end_date || '').split('T')[0];
                    if (!sStr || !eStr) return null;
                    if (eStr < calStartKey || sStr > calEndKey) return null;

                    let startSlot = 0;
                    if (sStr >= calStartKey) {
                        const dIdx = dayIndexMap[sStr];
                        if (dIdx !== undefined) startSlot = dIdx * 2;
                    }

                    let endSlot = totalSlots - 1;
                    if (eStr <= calEndKey) {
                        const dIdx = dayIndexMap[eStr];
                        if (dIdx !== undefined) endSlot = dIdx * 2 + 1;
                    }

                    if (endSlot < startSlot) endSlot = startSlot;
                    startSlot = Math.max(0, Math.min(totalSlots - 1, startSlot));
                    endSlot = Math.max(0, Math.min(totalSlots - 1, endSlot));
                    return { blackout: bo, startSlot, endSlot };
                }).filter(Boolean);

                // Render slots 0 to totalSlots - 1
                let s = 0;
                while (s < totalSlots) {
                    const dayIdx = Math.floor(s / 2);
                    const half = (s % 2 === 0) ? 'AM' : 'PM';
                    const dayObj = allDays[dayIdx];
                    const isWeekend = dayObj ? dayObj.isWeekend : false;

                    // 1. Check booking covering slot s
                    const bkItem = vBookings.find(item => item.startSlot <= s && s <= item.endSlot);
                    if (bkItem) {
                        const bk = bkItem.booking;
                        const spanSlots = Math.min(bkItem.endSlot - s + 1, totalSlots - s);
                        const color = this.getBookingColor(bk);
                        const custName = (bk.customer_name || 'Customer').toUpperCase();
                        const rate = parseFloat(bk.total_price || 0);
                        const paid = parseFloat(bk.amount_paid || 0);
                        const bal = parseFloat(bk.balance_amount !== undefined ? bk.balance_amount : Math.max(0, rate - paid));

                        const cellEndSlot = s + spanSlots - 1;
                        const hasMonthDivider = (cellEndSlot === lastSlotOfMonth1);

                        rowHtml += `<td colspan="${spanSlots}"
                            onclick="FleetCalendar.openBookingQuickModal(${bk.id})"
                            onmouseenter="FleetCalendar.showBookingTooltip(event, ${bk.id})"
                            onmouseleave="FleetCalendar.hideTooltip()"
                            style="padding: 2px 3px; border: 1px solid rgba(0,0,0,0.12); ${hasMonthDivider ? 'border-right: 3px solid #009240 !important;' : ''} cursor: pointer; vertical-align: middle; height: 54px;">
                            <div style="background: ${color.bg}; color: ${color.text}; border: 1.5px solid ${color.border}; border-radius: 8px; padding: 4px 6px; font-weight: 800; line-height: 1.25; box-shadow: 0 2px 5px rgba(0,0,0,0.1); height: calc(100% - 2px); display: flex; flex-direction: column; justify-content: center; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; transition: transform 0.15s, box-shadow 0.15s;"
                                 onmouseover="this.style.transform='scale(1.01)'; this.style.boxShadow='0 4px 10px rgba(0,0,0,0.18)';"
                                 onmouseout="this.style.transform='none'; this.style.boxShadow='0 2px 5px rgba(0,0,0,0.1)';">
                                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: ${spanSlots === 1 ? '0.62rem' : '0.76rem'}; font-weight: 900; letter-spacing: 0.2px;">
                                    <i class="fas fa-user" style="font-size: 0.6rem; margin-right: 3px; opacity: 0.85;"></i>${custName}
                                </div>
                                <div style="font-size: 0.62rem; font-weight: 800; opacity: 0.95; display: flex; align-items: center; gap: 4px; margin-top: 1px; overflow: hidden;">
                                    <span>₱${Math.round(rate).toLocaleString()}</span>
                                    ${spanSlots > 1 ? (bal > 0 
                                        ? `<span style="background: #ef4444; color: white; padding: 1px 4px; border-radius: 4px; font-size: 0.55rem; font-weight: 800;">Bal: ₱${Math.round(bal).toLocaleString()}</span>` 
                                        : `<span style="background: #16a34a; color: white; padding: 1px 4px; border-radius: 4px; font-size: 0.55rem; font-weight: 800;">PAID</span>`) : ''
                                    }
                                </div>
                            </div>
                        </td>`;

                        s += spanSlots;
                        continue;
                    }

                    // 2. Check blackout covering slot s
                    const boItem = vBlackouts.find(item => item.startSlot <= s && s <= item.endSlot);
                    if (boItem) {
                        const spanSlots = Math.min(boItem.endSlot - s + 1, totalSlots - s);
                        const cellEndSlot = s + spanSlots - 1;
                        const hasMonthDivider = (cellEndSlot === lastSlotOfMonth1);
                        rowHtml += `<td colspan="${spanSlots}" style="padding: 0; border: 1px solid var(--border); ${hasMonthDivider ? 'border-right: 3px solid #009240 !important;' : ''} text-align: center; background: repeating-linear-gradient(45deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.15) 5px, rgba(239, 68, 68, 0.28) 5px, rgba(239, 68, 68, 0.28) 10px); min-width: 28px; height: 54px;" title="Blackout Blocked">
                            <span style="background: rgba(239,68,68,0.2); color: #dc2626; font-size: 0.58rem; font-weight: 800; padding: 1px 3px; border-radius: 4px;">OFF</span>
                        </td>`;
                        s += spanSlots;
                        continue;
                    }

                    // 3. Empty slot
                    let borderRight = (half === 'AM') ? '1px dashed var(--border)' : '1.5px solid var(--border)';
                    if (s === lastSlotOfMonth1) {
                        borderRight = '3px solid #009240 !important';
                    }
                    rowHtml += `<td style="padding: 0; border: 1px solid var(--border); border-right: ${borderRight}; text-align: center; min-width: 28px; width: 28px; height: 54px; background: ${isWeekend ? 'rgba(0,0,0,0.015)' : 'transparent'};"></td>`;
                    s++;
                }

                rowHtml += `</tr>`;
                bodyHtml += rowHtml;
            });

            if (filteredVehicles.length === 0) {
                bodyHtml = `<tr><td colspan="${totalSlots + 1}" style="text-align: center; padding: 40px; color: var(--text-muted); font-size: 0.88rem;">No vehicles or bookings matching "${this.searchQuery}"</td></tr>`;
            }
            
            const bodyEl = document.getElementById('fleetCalendarBody');
            if (bodyEl) bodyEl.innerHTML = bodyHtml;

            const scrollContainer = document.getElementById('fleetCalendarScrollContainer');
            if (scrollContainer) {
                if (!scrollContainer._hasHScrollWheel) {
                    scrollContainer._hasHScrollWheel = true;
                    scrollContainer.addEventListener('wheel', function(e) {
                        if (e.shiftKey) {
                            e.preventDefault();
                            scrollContainer.scrollLeft += (e.deltaY || e.deltaX);
                        }
                    }, { passive: false });
                }

                // If requested to scroll to today
                if (this._shouldScrollToToday) {
                    this._shouldScrollToToday = false;
                    setTimeout(() => {
                        const todayCell = document.querySelector('.fc-today-col');
                        if (todayCell) {
                            const offset = todayCell.offsetLeft - 240;
                            scrollContainer.scrollTo({ left: Math.max(0, offset), behavior: 'smooth' });
                        }
                    }, 50);
                }
            }
        },

        hideTooltip() {
            const tip = document.getElementById('fleetTooltip');
            if (tip) tip.style.display = 'none';
        },

        positionTooltip(e, tip) {
            tip.style.display = 'block';
            const rect = tip.getBoundingClientRect();
            let x = e.clientX + 16;
            let y = e.clientY + 12;
            if (x + rect.width > window.innerWidth - 12) {
                x = e.clientX - rect.width - 12;
            }
            if (y + rect.height > window.innerHeight - 12) {
                y = window.innerHeight - rect.height - 12;
            }
            tip.style.left = `${Math.max(10, x)}px`;
            tip.style.top = `${Math.max(10, y)}px`;
        },

        showVehicleTooltip(e, vId) {
            if (window.innerWidth <= 768) return;
            const v = (this.vehicles || []).find(x => x.id == vId);
            if (!v) return;
            const tip = document.getElementById('fleetTooltip');
            if (!tip) return;
            
            const imgHtml = v.vehicle_image ? `<img src="${v.vehicle_image}" style="width:100%;height:105px;object-fit:cover;border-radius:8px;margin-bottom:8px;display:block;">` : '';
            tip.innerHTML = `
                <div style="background:#0f172a;color:#f8fafc;padding:12px 14px;border-radius:12px;box-shadow:0 12px 28px rgba(0,0,0,0.45);border:1px solid #334155;font-size:0.75rem;line-height:1.4;">
                    ${imgHtml}
                    <div style="font-size:0.92rem;font-weight:900;color:#ffffff;margin-bottom:2px;">${v.brand} ${v.model}</div>
                    <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
                        <span style="background:rgba(0,177,79,0.2);color:#00B14F;border:1px solid rgba(0,177,79,0.4);padding:2px 7px;border-radius:4px;font-weight:800;font-size:0.65rem;">${v.plate_number || 'NO PLATE'}</span>
                        <span style="background:#1e293b;color:#94a3b8;padding:2px 7px;border-radius:4px;font-size:0.65rem;font-weight:700;">${v.vehicle_type || 'Vehicle'}</span>
                        <span style="margin-left:auto;font-size:0.65rem;font-weight:800;color:${v.status === 'Available' ? '#10b981' : v.status === 'Maintenance' ? '#ef4444' : '#f59e0b'};">${(v.status||'Available').toUpperCase()}</span>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;border-top:1px solid #334155;padding-top:6px;color:#cbd5e1;">
                        <div><span style="color:#94a3b8;font-size:0.65rem;">Transmission:</span><br><b style="color:#ffffff;font-size:0.75rem;">${v.transmission || 'Auto'}</b></div>
                        <div><span style="color:#94a3b8;font-size:0.65rem;">Fuel Type:</span><br><b style="color:#ffffff;font-size:0.75rem;">${v.fuel_type || 'Gasoline'}</b></div>
                        <div><span style="color:#94a3b8;font-size:0.65rem;">Seats:</span><br><b style="color:#ffffff;font-size:0.75rem;">${v.seats || 5} Seats</b></div>
                        <div><span style="color:#94a3b8;font-size:0.65rem;">Daily Rate:</span><br><b style="color:#10b981;font-size:0.75rem;">₱${parseFloat(v.daily_rate||0).toLocaleString()}/day</b></div>
                    </div>
                    <div style="margin-top:6px;border-top:1px solid #334155;padding-top:6px;display:flex;justify-content:space-between;align-items:center;">
                        <span style="color:#94a3b8;font-size:0.65rem;">Location:</span>
                        <span style="font-weight:700;color:#ffffff;font-size:0.72rem;">${v.location || 'Main Depot'}</span>
                    </div>
                </div>
            `;
            this.positionTooltip(e, tip);
        },

        showBookingTooltip(e, bId) {
            if (window.innerWidth <= 768) return;
            const b = (this.bookings || []).find(x => x.id == bId);
            if (!b) return;
            const tip = document.getElementById('fleetTooltip');
            if (!tip) return;
            
            const rate = parseFloat(b.total_price || 0);
            const dp = parseFloat(b.amount_paid || 0);
            const bal = parseFloat(b.balance_amount !== undefined ? b.balance_amount : Math.max(0, rate - dp));
            const fee = parseFloat(b.payment_fee || 0);
            const feePct = parseFloat(b.payment_fee_percent || 0);
            const totalWithFee = rate + fee;

            const sDate = b.start_date ? new Date(b.start_date).toLocaleDateString('en-PH', {month:'short', day:'numeric', year:'numeric'}) : 'N/A';
            const eDate = b.end_date ? new Date(b.end_date).toLocaleDateString('en-PH', {month:'short', day:'numeric', year:'numeric'}) : 'N/A';
            const sTime = b.start_time || '06:00';
            const eTime = b.end_time || '06:00';

            tip.innerHTML = `
                <div style="background:#ffffe1;color:#000000;padding:12px 14px;border:1.5px solid #222222;box-shadow:3px 3px 10px rgba(0,0,0,0.35);font-family:Arial, Helvetica, sans-serif;font-size:0.75rem;line-height:1.45;min-width:240px;max-width:320px;">
                    <div style="font-weight:bold;margin-bottom:6px;border-bottom:1px dashed #555;padding-bottom:5px;">
                        ${rate >= 1000 ? (rate / 1000) + 'k' : '₱' + rate.toLocaleString()}<br>
                        ${dp > 0 ? `-${dp.toLocaleString()}<br>` : '0 DP<br>'}
                        ${bal.toLocaleString()} balance<br>
                        ${fee > 0 ? `${fee.toLocaleString()} ${feePct}%<br>` : ''}
                        Total ${totalWithFee.toLocaleString()}
                    </div>
                    <div>
                        <b>Name:</b> ${b.customer_name || 'Customer'}<br>
                        <b>Contact no:</b> ${b.customer_phone || 'N/A'}<br>
                        <b>Complete Address:</b> ${b.customer_address || 'N/A'}<br>
                        ${(b.emergency_contact_name || b.emergency_name) ? `<b>Emergency Contact:</b> ${b.emergency_contact_name || b.emergency_name}${b.emergency_contact_phone || b.emergency_phone ? ' (' + (b.emergency_contact_phone || b.emergency_phone) + ')' : ''}<br>` : ''}
                        <b>Unit needed:</b> ${b.brand || ''} ${b.model || ''} ${b.plate_number ? '(' + b.plate_number + ')' : ''}<br>
                        <b>Date:</b> ${sDate} to ${eDate}<br>
                        <b>Time:</b> ${sTime} to ${eTime}<br>
                        <b>Payment Status:</b> <span style="font-weight:800; color:${bal === 0 ? '#16a34a' : '#dc2626'};">${b.payment_status || (bal === 0 ? 'Paid' : 'Unpaid')}</span>
                    </div>
                </div>
            `;
            this.positionTooltip(e, tip);
        },

        handleVehicleClick(e, vId) {
            this.hideTooltip();
            const v = (this.vehicles || []).find(x => x.id == vId);
            if (!v) return;
            this.openVehicleModal(v);
        },

        openVehicleModal(v) {
            const body = document.getElementById('fleetVehicleModalBody');
            if (!body) return;
            const imgHtml = v.vehicle_image ? `<img src="${v.vehicle_image}" style="width:100%;height:155px;object-fit:cover;border-radius:12px;margin-bottom:12px;">` : '';
            const curRate = parseFloat(v.daily_rate || 0);

            body.innerHTML = `
                ${imgHtml}
                <div style="font-size:1.15rem;font-weight:900;color:#0f172a;margin-bottom:4px;">${v.brand} ${v.model}</div>
                <div style="display:flex;align-items:center;gap:6px;margin-bottom:12px;flex-wrap:wrap;">
                    <span style="background:rgba(0,177,79,0.15);color:#00B14F;border:1px solid rgba(0,177,79,0.3);padding:3px 8px;border-radius:6px;font-weight:800;font-size:0.75rem;">${v.plate_number || 'NO PLATE'}</span>
                    <span style="background:#f1f5f9;color:#475569;padding:3px 8px;border-radius:6px;font-size:0.75rem;font-weight:700;">${v.vehicle_type || 'Vehicle'}</span>
                    <span style="background:${v.status === 'Available' ? '#dcfce7' : v.status === 'Maintenance' ? '#fee2e2' : '#fef3c7'};color:${v.status === 'Available' ? '#15803d' : v.status === 'Maintenance' ? '#b91c1c' : '#b45309'};padding:3px 8px;border-radius:6px;font-size:0.75rem;font-weight:800;margin-left:auto;">${(v.status||'Available').toUpperCase()}</span>
                </div>

                <!-- DIRECT DAILY RATE / PRICING MANAGER -->
                <div style="background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 14px; padding: 14px; margin-bottom: 14px; box-shadow: 0 2px 6px rgba(0,177,79,0.08);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <label style="font-size: 0.74rem; font-weight: 800; color: #166534; text-transform: uppercase; margin: 0; display:flex; align-items:center; gap:5px;">
                            <i class="fas fa-tags" style="color: #16a34a;"></i> Edit Vehicle Daily Rate (₱/Day)
                        </label>
                        <span style="font-size: 0.68rem; font-weight: 700; color: #15803d; background: rgba(34,197,94,0.18); padding: 2px 7px; border-radius: 6px;">Current: ₱${curRate.toLocaleString()}</span>
                    </div>

                    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
                        <div style="position: relative; flex: 1;">
                            <span style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); font-weight: 800; color: #64748b; font-size: 0.95rem;">₱</span>
                            <input type="number" id="fleetVehicleRateInput" value="${curRate}" step="50" min="0" max="50000"
                                   style="width: 100%; padding: 9px 10px 9px 26px; font-size: 1rem; font-weight: 900; color: #0f172a; background: white; border: 1.5px solid #cbd5e1; border-radius: 8px; outline: none; box-sizing: border-box;">
                        </div>
                        <button type="button" id="btnSaveFleetVehicleRate" onclick="FleetCalendar.saveVehicleDailyRate(${v.id})"
                                style="padding: 10px 15px; background: #00B14F; color: white; border: none; border-radius: 8px; font-weight: 800; font-size: 0.82rem; cursor: pointer; display: flex; align-items: center; gap: 6px; box-shadow: 0 3px 6px rgba(0,177,79,0.3); white-space: nowrap;">
                            <i class="fas fa-save"></i> Save Rate
                        </button>
                    </div>

                    <!-- Quick Adjust Buttons -->
                    <div style="display: flex; gap: 5px; align-items: center; flex-wrap: wrap;">
                        <span style="font-size: 0.65rem; color: #64748b; font-weight: 700;">Quick Adjust:</span>
                        <button type="button" onclick="FleetCalendar.adjustVehicleRateInput(-200)" style="padding: 2px 7px; font-size: 0.66rem; font-weight: 700; background: white; border: 1px solid #cbd5e1; border-radius: 5px; cursor: pointer; color: #475569;">-₱200</button>
                        <button type="button" onclick="FleetCalendar.adjustVehicleRateInput(-100)" style="padding: 2px 7px; font-size: 0.66rem; font-weight: 700; background: white; border: 1px solid #cbd5e1; border-radius: 5px; cursor: pointer; color: #475569;">-₱100</button>
                        <button type="button" onclick="FleetCalendar.adjustVehicleRateInput(100)" style="padding: 2px 7px; font-size: 0.66rem; font-weight: 700; background: white; border: 1px solid #cbd5e1; border-radius: 5px; cursor: pointer; color: #475569;">+₱100</button>
                        <button type="button" onclick="FleetCalendar.adjustVehicleRateInput(200)" style="padding: 2px 7px; font-size: 0.66rem; font-weight: 700; background: white; border: 1px solid #cbd5e1; border-radius: 5px; cursor: pointer; color: #475569;">+₱200</button>
                        <button type="button" onclick="FleetCalendar.adjustVehicleRateInput(500)" style="padding: 2px 7px; font-size: 0.66rem; font-weight: 700; background: white; border: 1px solid #cbd5e1; border-radius: 5px; cursor: pointer; color: #475569;">+₱500</button>
                    </div>
                </div>

                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;background:#f8fafc;padding:12px;border-radius:12px;border:1px solid #e2e8f0;margin-bottom:12px;font-size:0.8rem;">
                    <div><span style="color:#64748b;font-size:0.7rem;text-transform:uppercase;font-weight:700;">Transmission</span><br><b style="color:#0f172a;">${v.transmission || 'Automatic'}</b></div>
                    <div><span style="color:#64748b;font-size:0.7rem;text-transform:uppercase;font-weight:700;">Fuel Type</span><br><b style="color:#0f172a;">${v.fuel_type || 'Gasoline'}</b></div>
                    <div><span style="color:#64748b;font-size:0.7rem;text-transform:uppercase;font-weight:700;">Seating Capacity</span><br><b style="color:#0f172a;">${v.seats || 5} Seats</b></div>
                    <div><span style="color:#64748b;font-size:0.7rem;text-transform:uppercase;font-weight:700;">Location / Depot</span><br><b style="color:#0f172a;">${v.location || 'Main Depot'}</b></div>
                </div>
            `;
            const m = document.getElementById('fleetVehicleModal');
            m.style.display = 'flex';
            if (typeof modalOpen === 'function') modalOpen();
        },

        adjustVehicleRateInput(delta) {
            const inp = document.getElementById('fleetVehicleRateInput');
            if (!inp) return;
            const current = parseFloat(inp.value || 0);
            inp.value = Math.max(0, current + delta);
        },

        async saveVehicleDailyRate(vId) {
            const inp = document.getElementById('fleetVehicleRateInput');
            if (!inp) return;
            const newRate = parseFloat(inp.value || 0);
            if (isNaN(newRate) || newRate < 0) {
                showNotification('Please enter a valid rate', 'error');
                return;
            }

            const btn = document.getElementById('btnSaveFleetVehicleRate');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Saving...`;
            }

            try {
                const res = await fetch(`${API_BASE}/api/vehicles/${vId}/rate`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ daily_rate: newRate })
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.error || 'Failed to update vehicle rate');
                }

                // Update local vehicle state in calendar and global Vehicles array if present
                const v = (this.vehicles || []).find(x => x.id == vId);
                if (v) v.daily_rate = newRate;
                if (typeof Vehicles !== 'undefined' && Vehicles.data) {
                    const gV = Vehicles.data.find(x => x.id == vId);
                    if (gV) gV.daily_rate = newRate;
                }

                showNotification(`Vehicle daily rate updated to ₱${newRate.toLocaleString()}/day!`, 'success');

                const m = document.getElementById('fleetVehicleModal');
                if (m) {
                    m.style.display = 'none';
                    if (typeof modalClose === 'function') modalClose();
                }

                // Re-render the calendar to display updated rate badge immediately
                this.render();
            } catch (err) {
                console.error("Save vehicle rate error:", err);
                showNotification(err.message || 'Error updating vehicle rate', 'error');
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = `<i class="fas fa-save"></i> Save Rate`;
                }
            }
        },

        // Open the Working Pricing & Dispatch Modal directly on click
        openBookingQuickModal(bId) {
            this.hideTooltip();
            const b = (this.bookings || []).find(x => x.id == bId);
            if (!b) return;

            this.activeBookingId = bId;

            // Header titles
            const titleEl = document.getElementById('quickModalTitle');
            if (titleEl) titleEl.textContent = `${b.customer_name || 'Customer'}`;
            const subEl = document.getElementById('quickModalSubtitle');
            if (subEl) subEl.textContent = `Booking #${b.id} • ${b.brand || ''} ${b.model || ''} (${b.plate_number || 'No Plate'})`;

            // Active Color
            const activeColorObj = this.getBookingColor(b);
            this.selectedColor = b.calendar_color || activeColorObj.bg;
            this.updateModalColorPreview(this.selectedColor);

            // Populate palette swatches
            this.renderPaletteSwatches();

            // Custom picker sync
            const customPicker = document.getElementById('quickCustomColorPicker');
            if (customPicker) customPicker.value = this.selectedColor;

            // Summary Card
            const summaryCard = document.getElementById('quickModalSummaryCard');
            if (summaryCard) {
                const sDate = b.start_date ? new Date(b.start_date).toLocaleDateString('en-PH', {month:'short', day:'numeric', year:'numeric'}) : 'N/A';
                const eDate = b.end_date ? new Date(b.end_date).toLocaleDateString('en-PH', {month:'short', day:'numeric', year:'numeric'}) : 'N/A';
                summaryCard.innerHTML = `
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                        <div><strong style="color:#475569;">Schedule:</strong> ${sDate} ${b.start_time || '06:00'} &rarr; ${eDate} ${b.end_time || '06:00'}</div>
                        <div><strong style="color:#475569;">Contact:</strong> ${b.customer_phone || 'N/A'}</div>
                        <div><strong style="color:#475569;">Booking Status:</strong> <span style="font-weight:800; color:#0284c7; text-transform:uppercase;">${b.status || 'Active'}</span></div>
                        <div><strong style="color:#475569;">Destination:</strong> ${b.destination || 'N/A'}</div>
                    </div>
                `;
            }

            // Populate Working Pricing Fields
            const totalPrice = parseFloat(b.total_price || 0);
            const amountPaid = parseFloat(b.amount_paid || 0);
            const bal = parseFloat(b.balance_amount !== undefined ? b.balance_amount : Math.max(0, totalPrice - amountPaid));

            const totalInp = document.getElementById('quickTotalPrice');
            if (totalInp) totalInp.value = totalPrice;

            const paidInp = document.getElementById('quickAmountPaid');
            if (paidInp) paidInp.value = amountPaid;

            const balInp = document.getElementById('quickBalanceAmount');
            if (balInp) balInp.value = `₱${Math.round(bal).toLocaleString()}`;

            const statusSelect = document.getElementById('quickPaymentStatus');
            if (statusSelect) {
                statusSelect.value = b.payment_status || (bal === 0 ? 'Paid' : (amountPaid > 0 ? 'Partially Paid' : 'Unpaid'));
            }

            const methodSelect = document.getElementById('quickPaymentMethod');
            if (methodSelect) {
                methodSelect.value = b.payment_method || 'Cash';
            }

            const modal = document.getElementById('fleetBookingModal');
            if (modal) {
                modal.style.display = 'flex';
                if (typeof modalOpen === 'function') modalOpen();
            }
        },

        renderPaletteSwatches() {
            const container = document.getElementById('quickColorPalette');
            if (!container) return;

            let html = '';
            this.paletteColors.forEach(item => {
                const isSelected = this.selectedColor && this.selectedColor.toLowerCase() === item.bg.toLowerCase();
                html += `
                    <div onclick="FleetCalendar.selectPaletteColor('${item.bg}')"
                         style="width: 26px; height: 26px; border-radius: 6px; background: ${item.bg}; cursor: pointer; border: ${isSelected ? '2.5px solid #0f172a' : '1.5px solid rgba(0,0,0,0.15)'}; transform: ${isSelected ? 'scale(1.15)' : 'none'}; box-shadow: ${isSelected ? '0 3px 6px rgba(0,0,0,0.25)' : 'none'}; display: flex; align-items: center; justify-content: center; transition: all 0.15s;"
                         title="${item.bg}">
                        ${isSelected ? '<i class="fas fa-check" style="font-size: 0.65rem; color: #0f172a;"></i>' : ''}
                    </div>
                `;
            });
            container.innerHTML = html;
        },

        selectPaletteColor(hex) {
            this.selectedColor = hex;
            this.updateModalColorPreview(hex);
            this.renderPaletteSwatches();
            const customPicker = document.getElementById('quickCustomColorPicker');
            if (customPicker) customPicker.value = hex;
        },

        onCustomColorPick(hex) {
            this.selectedColor = hex;
            this.updateModalColorPreview(hex);
            this.renderPaletteSwatches();
        },

        updateModalColorPreview(hex) {
            const badge = document.getElementById('quickModalColorBadge');
            if (badge) badge.style.background = hex;
        },

        recalcQuickBalance() {
            const totalInp = document.getElementById('quickTotalPrice');
            const paidInp = document.getElementById('quickAmountPaid');
            if (totalInp) {
                if (totalInp.value.length > 7) totalInp.value = totalInp.value.slice(0, 7);
                if (Number(totalInp.value) > 500000) totalInp.value = 500000;
                if (Number(totalInp.value) < 0) totalInp.value = 0;
            }
            if (paidInp) {
                if (paidInp.value.length > 7) paidInp.value = paidInp.value.slice(0, 7);
                if (Number(paidInp.value) > 500000) paidInp.value = 500000;
                if (Number(paidInp.value) < 0) paidInp.value = 0;
            }

            const total = Math.min(500000, Math.max(0, parseFloat(totalInp?.value || 0)));
            const paid = Math.min(500000, Math.max(0, parseFloat(paidInp?.value || 0)));
            const bal = Math.max(0, total - paid);

            const balInp = document.getElementById('quickBalanceAmount');
            if (balInp) {
                balInp.value = `₱${Math.round(bal).toLocaleString()}`;
                if (bal === 0) {
                    balInp.style.background = '#dcfce7';
                    balInp.style.color = '#15803d';
                    balInp.style.borderColor = '#86efac';
                } else {
                    balInp.style.background = '#fee2e2';
                    balInp.style.color = '#dc2626';
                    balInp.style.borderColor = '#fca5a5';
                }
            }

            const statusSelect = document.getElementById('quickPaymentStatus');
            if (statusSelect) {
                if (bal === 0 && total > 0) {
                    statusSelect.value = 'Paid';
                } else if (paid > 0 && bal > 0) {
                    statusSelect.value = 'Partially Paid';
                } else if (paid === 0) {
                    statusSelect.value = 'Unpaid';
                }
            }
        },

        quickMarkPaid() {
            const totalInp = document.getElementById('quickTotalPrice');
            const total = Math.min(500000, Math.max(0, parseFloat(totalInp?.value || 0)));
            const paidInp = document.getElementById('quickAmountPaid');
            if (paidInp) paidInp.value = total;
            this.recalcQuickBalance();
        },

        async saveQuickPricing() {
            if (!this.activeBookingId) return;

            const total = Math.min(500000, Math.max(0, parseFloat(document.getElementById('quickTotalPrice')?.value || 0)));
            const paid = Math.min(500000, Math.max(0, parseFloat(document.getElementById('quickAmountPaid')?.value || 0)));
            const bal = Math.max(0, total - paid);
            const paymentStatus = document.getElementById('quickPaymentStatus')?.value || 'Unpaid';
            const paymentMethod = document.getElementById('quickPaymentMethod')?.value || 'Cash';
            const applyToCustomer = document.getElementById('quickApplyToCustomer')?.checked ?? true;

            const btn = document.getElementById('btnSaveQuickPricing');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Saving...`;
            }

            try {
                const res = await fetch(`${API_BASE}/api/admin/bookings/${this.activeBookingId}/quick-pricing`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        total_price: total,
                        amount_paid: paid,
                        balance_amount: bal,
                        payment_status: paymentStatus,
                        payment_method: paymentMethod,
                        calendar_color: this.selectedColor,
                        apply_to_customer: applyToCustomer
                    })
                });

                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.error || 'Failed to save pricing');
                }

                showNotification('Booking schedule & pricing updated successfully!', 'success');
                this.closeQuickModal();
                await this.refresh();
            } catch (err) {
                console.error("Save quick pricing error:", err);
                showNotification(err.message || 'Error updating booking', 'error');
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = `<i class="fas fa-save"></i> Save & Update`;
                }
            }
        },

        closeQuickModal() {
            const modal = document.getElementById('fleetBookingModal');
            if (modal) {
                modal.style.display = 'none';
                if (typeof modalClose === 'function') modalClose();
            }
        },

        openFullBookingDetails() {
            const bId = this.activeBookingId;
            this.closeQuickModal();
            if (bId && typeof Bookings !== 'undefined' && Bookings.view) {
                Bookings.view(bId);
            }
        },

        // --- FLEET EXPORT EXCEL SYSTEM ---
        async openExportModal() {
            const modal = document.getElementById('fleetExportModal');
            if (!modal) return;

            // Ensure vehicles are loaded
            if (!this.vehicles || this.vehicles.length === 0) {
                try {
                    let vRes = await fetch(`${API_BASE}/api/vehicles`);
                    if (vRes.status === 404) vRes = await fetch(`${API_BASE}/vehicles`);
                    this.vehicles = await vRes.json();
                } catch(e) {}
            }

            // Populate vehicle filter options
            const vSelect = document.getElementById('fleetExportVehicle');
            if (vSelect) {
                let vHtml = '<option value="all">🚗 All Vehicles</option>';
                const vehs = (this.vehicles && this.vehicles.length) ? this.vehicles : [];
                vehs.forEach(v => {
                    vHtml += `<option value="${v.id}">${v.brand} ${v.model} (${v.plate_number || 'No Plate'})</option>`;
                });
                vSelect.innerHTML = vHtml;
            }

            // Sync Month Label
            const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
            const year = this.currentDate.getFullYear();
            const month = this.currentDate.getMonth();
            const monthLabel = document.getElementById('fleetExportCurrentMonthLabel');
            if (monthLabel) {
                if (this.viewMonths === 2) {
                    const m2 = new Date(year, month + 1, 1);
                    const y2 = m2.getFullYear();
                    const m2Idx = m2.getMonth();
                    monthLabel.textContent = `${monthNames[month]} & ${monthNames[m2Idx]} ${y2 === year ? year : year + ' / ' + y2}`;
                } else {
                    monthLabel.textContent = `${monthNames[month]} ${year}`;
                }
            }

            // Initialize default custom dates
            const startInp = document.getElementById('fleetExportStartDate');
            const endInp = document.getElementById('fleetExportEndDate');
            const startStr = `${year}-${String(month+1).padStart(2,'0')}-01`;
            let endStr;
            if (this.viewMonths === 2) {
                const m2 = new Date(year, month + 1, 1);
                const y2 = m2.getFullYear();
                const m2Idx = m2.getMonth();
                const lastDayM2 = new Date(y2, m2Idx + 1, 0).getDate();
                endStr = `${y2}-${String(m2Idx+1).padStart(2,'0')}-${String(lastDayM2).padStart(2,'0')}`;
            } else {
                const lastDay = new Date(year, month + 1, 0).getDate();
                endStr = `${year}-${String(month+1).padStart(2,'0')}-${String(lastDay).padStart(2,'0')}`;
            }
            if (startInp && !startInp.value) startInp.value = startStr;
            if (endInp && !endInp.value) endInp.value = endStr;

            // Default scope to month
            this.setExportScope('month');

            modal.style.display = 'flex';
        },

        closeExportModal(e) {
            if (e && typeof e.stopPropagation === 'function') e.stopPropagation();
            const modal = document.getElementById('fleetExportModal');
            if (modal) modal.style.display = 'none';
        },

        setExportScope(scope) {
            this._exportScope = scope;
            const scopes = ['all', 'month', 'custom'];
            scopes.forEach(s => {
                const card = document.getElementById('fleetExportScope' + s.charAt(0).toUpperCase() + s.slice(1) + 'Card');
                const radio = document.getElementById('fleetExportScope' + s.charAt(0).toUpperCase() + s.slice(1));
                const isSelected = (s === scope);
                if (radio) radio.checked = isSelected;
                if (card) {
                    if (isSelected) {
                        card.style.borderColor = '#00B14F';
                        card.style.background = 'rgba(0, 177, 79, 0.08)';
                    } else {
                        card.style.borderColor = 'var(--border)';
                        card.style.background = 'var(--surface-container)';
                    }
                }
            });

            const customDiv = document.getElementById('fleetExportCustomDatesDiv');
            if (customDiv) {
                customDiv.style.display = (scope === 'custom') ? 'block' : 'none';
            }
        },

        setExportPreset(preset) {
            const today = new Date();
            let start, end;
            if (preset === 'today') {
                start = new Date(today);
                end = new Date(today);
            } else if (preset === 'this_week') {
                const day = today.getDay();
                start = new Date(today);
                start.setDate(today.getDate() - day);
                end = new Date(today);
                end.setDate(today.getDate() + (6 - day));
            } else if (preset === 'this_month') {
                start = new Date(today.getFullYear(), today.getMonth(), 1);
                end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            } else if (preset === 'next_month') {
                start = new Date(today.getFullYear(), today.getMonth() + 1, 1);
                end = new Date(today.getFullYear(), today.getMonth() + 2, 0);
            } else if (preset === 'this_year') {
                start = new Date(today.getFullYear(), 0, 1);
                end = new Date(today.getFullYear(), 11, 31);
            }
            const fmt = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
            if (start && end) {
                const sInp = document.getElementById('fleetExportStartDate');
                const eInp = document.getElementById('fleetExportEndDate');
                if (sInp) sInp.value = fmt(start);
                if (eInp) eInp.value = fmt(end);
            }
        },

        async executeExport(btn) {
            const scope = this._exportScope || 'month';
            const vehicleId = document.getElementById('fleetExportVehicle')?.value || 'all';
            const statusFilter = document.getElementById('fleetExportStatus')?.value || 'all';

            let startStr = '', endStr = '';
            let dateTitle = '';

            if (scope === 'all') {
                dateTitle = 'All_Records';
            } else if (scope === 'month') {
                const year = this.currentDate.getFullYear();
                const month = this.currentDate.getMonth();
                startStr = `${year}-${String(month+1).padStart(2,'0')}-01`;
                const lastDay = new Date(year, month + 1, 0).getDate();
                endStr = `${year}-${String(month+1).padStart(2,'0')}-${String(lastDay).padStart(2,'0')}`;
                dateTitle = `${year}_${String(month+1).padStart(2,'0')}`;
            } else if (scope === 'custom') {
                startStr = document.getElementById('fleetExportStartDate')?.value;
                endStr = document.getElementById('fleetExportEndDate')?.value;
                if (!startStr || !endStr) {
                    showNotification('Please provide both Start and End dates for custom range.', 'warning');
                    return;
                }
                if (startStr > endStr) {
                    showNotification('Start Date cannot be later than End Date.', 'warning');
                    return;
                }
                dateTitle = `${startStr}_to_${endStr}`;
            }

            const origHtml = btn ? btn.innerHTML : '';
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Excel...';
            }

            try {
                // Build query URL for backend Excel generator (with openpyxl visual grid matching ARC Monitoring)
                let url = `${API_BASE}/api/admin/fleet-calendar/export-excel?`;
                if (scope === 'all') {
                    url += 'all=true';
                } else {
                    url += `start=${startStr}&end=${endStr}`;
                }
                if (statusFilter && statusFilter !== 'all') {
                    url += `&status=${statusFilter}`;
                }
                if (vehicleId && vehicleId !== 'all') {
                    url += `&vehicle_id=${vehicleId}`;
                }

                let res = await fetch(url);
                if (res.status === 404 || res.status === 405) {
                    let fallbackUrl = url.replace('/api/admin/', '/admin/');
                    res = await fetch(fallbackUrl);
                }

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.error || 'Failed to generate Excel file from server');
                }

                const blob = await res.blob();
                const filename = `Autoride_Fleet_Monitoring_${dateTitle}_${new Date().toISOString().split('T')[0]}.xlsx`;

                // Handle mobile Capacitor app vs web browser
                const { Filesystem } = window.Capacitor?.Plugins || {};
                if (Filesystem) {
                    try {
                        const reader = new FileReader();
                        const base64Data = await new Promise((resolve, reject) => {
                            reader.onloadend = () => {
                                const b64 = reader.result.split(',')[1];
                                resolve(b64);
                            };
                            reader.onerror = reject;
                            reader.readAsDataURL(blob);
                        });
                        const resWrite = await Filesystem.writeFile({
                            path: filename,
                            data: base64Data,
                            directory: 'DOWNLOADS',
                            recursive: true
                        });
                        showNotification('Excel saved to Downloads: ' + filename, 'success');

                        try {
                            const { FileOpener } = window.Capacitor?.Plugins || {};
                            if (FileOpener) {
                                await FileOpener.open({
                                    filePath: resWrite.uri,
                                    contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                                });
                            }
                        } catch (e) { /* ignore */ }
                    } catch (capErr) {
                        const dlUrl = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = dlUrl;
                        a.download = filename;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        setTimeout(() => URL.revokeObjectURL(dlUrl), 3000);
                        showNotification('Excel downloaded successfully!', 'success');
                    }
                } else {
                    const dlUrl = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = dlUrl;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    setTimeout(() => URL.revokeObjectURL(dlUrl), 3000);
                    showNotification('Excel downloaded successfully!', 'success');
                }

                this.closeExportModal();
            } catch (err) {
                console.error("Export error:", err);
                showNotification('Export error: ' + (err.message || 'Unknown error'), 'error');
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = origHtml || '<i class="fas fa-file-excel"></i> Download Excel (.xlsx)';
                }
            }
        },

        // --- FLEET EXCEL IMPORT SYSTEM WITH SMART RENTER MATCHING ---
        _pendingImportRecords: [],

        openImportModal() {
            const modal = document.getElementById('fleetImportModal');
            if (!modal) return;
            this.resetImport();
            modal.style.display = 'flex';
        },

        closeImportModal(e) {
            if (e && typeof e.stopPropagation === 'function') e.stopPropagation();
            const modal = document.getElementById('fleetImportModal');
            if (modal) modal.style.display = 'none';
        },

        resetImport() {
            this._pendingImportRecords = [];
            const fileInput = document.getElementById('fcImportFileInput');
            if (fileInput) fileInput.value = '';

            const promptEl = document.getElementById('fcImportDropPrompt');
            if (promptEl) promptEl.style.display = 'block';

            const loadingEl = document.getElementById('fcImportLoadingState');
            if (loadingEl) loadingEl.style.display = 'none';

            const uploadZone = document.getElementById('fcImportUploadZone');
            if (uploadZone) uploadZone.style.display = 'block';

            const previewSection = document.getElementById('fcImportPreviewSection');
            if (previewSection) previewSection.style.display = 'none';

            const resetBtn = document.getElementById('fcImportResetBtn');
            if (resetBtn) resetBtn.style.display = 'none';

            const confirmBtn = document.getElementById('fcConfirmImportBtn');
            if (confirmBtn) confirmBtn.style.display = 'none';

            const countEl = document.getElementById('fcConfirmCount');
            if (countEl) countEl.textContent = '0';
        },

        async downloadImportTemplate() {
            try {
                let url = `${API_BASE}/api/admin/fleet-calendar/template-download`;
                let res = await fetch(url);
                if (res.status === 404 || res.status === 405) {
                    url = `${API_BASE}/admin/fleet-calendar/template-download`;
                    res = await fetch(url);
                }
                if (!res.ok) throw new Error('Failed to download template');
                const blob = await res.blob();
                const filename = 'Autoride_Fleet_Bookings_Template.xlsx';

                const { Filesystem } = window.Capacitor?.Plugins || {};
                if (Filesystem) {
                    const reader = new FileReader();
                    const base64Data = await new Promise((resolve, reject) => {
                        reader.onloadend = () => resolve(reader.result.split(',')[1]);
                        reader.onerror = reject;
                        reader.readAsDataURL(blob);
                    });
                    await Filesystem.writeFile({
                        path: filename,
                        data: base64Data,
                        directory: 'DOWNLOADS',
                        recursive: true
                    });
                    showNotification('Template saved to Downloads: ' + filename, 'success');
                } else {
                    const dlUrl = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = dlUrl;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    setTimeout(() => URL.revokeObjectURL(dlUrl), 3000);
                    showNotification('Sample template downloaded!', 'success');
                }
            } catch (err) {
                console.error("Template download error:", err);
                showNotification('Error downloading template: ' + (err.message || 'Server error'), 'error');
            }
        },

        handleImportDrop(e) {
            e.preventDefault();
            e.stopPropagation();
            if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                this.handleImportFileSelect(e.dataTransfer.files[0]);
            }
        },

        async handleImportFileSelect(file) {
            if (!file) return;
            const validExts = ['.xlsx', '.xls'];
            const fileName = (file.name || '').toLowerCase();
            const isValid = validExts.some(ext => fileName.endsWith(ext));
            if (!isValid) {
                showNotification('Please select a valid Excel file (.xlsx or .xls)', 'warning');
                return;
            }
            if (file.size > 10 * 1024 * 1024) {
                showNotification('Excel file must be 10 MB or smaller.', 'warning');
                return;
            }

            const promptEl = document.getElementById('fcImportDropPrompt');
            if (promptEl) promptEl.style.display = 'none';

            const loadingEl = document.getElementById('fcImportLoadingState');
            if (loadingEl) loadingEl.style.display = 'block';

            const nameEl = document.getElementById('fcImportLoadingFileName');
            if (nameEl) nameEl.textContent = `Analyzing "${file.name}"... Matching vehicles & customer profiles`;

            try {
                const formData = new FormData();
                formData.append('file', file);
                const autoCreate = document.getElementById('fcImportAutoCreate')?.checked ?? true;
                formData.append('auto_create_renters', autoCreate ? 'true' : 'false');

                let url = `${API_BASE}/api/admin/fleet-calendar/import-preview`;
                let res = await fetch(url, {
                    method: 'POST',
                    body: formData
                });
                if (res.status === 404 || res.status === 405) {
                    url = `${API_BASE}/admin/fleet-calendar/import-preview`;
                    res = await fetch(url, {
                        method: 'POST',
                        body: formData
                    });
                }

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.error || 'Failed to process Excel file');
                }

                const data = await res.json();
                const records = data.records || [];
                if (records.length === 0) {
                    throw new Error('No valid bookings found in this file. Please verify sheet format.');
                }

                const skipConflicts = document.getElementById('fcImportSkipConflicts')?.checked ?? true;
                records.forEach(r => {
                    r._selected = !(skipConflicts && r.is_conflict);
                });
                this._pendingImportRecords = records;

                // Summary badges
                const summary = data.summary || {};
                const prevTotal = document.getElementById('fcPrevTotal');
                if (prevTotal) prevTotal.textContent = summary.total_records || records.length;
                const prevVehicles = document.getElementById('fcPrevVehicles');
                if (prevVehicles) prevVehicles.textContent = summary.cars_matched || 0;
                const prevExistingRenters = document.getElementById('fcPrevExistingRenters');
                if (prevExistingRenters) prevExistingRenters.textContent = summary.existing_renters_matched || 0;
                const prevNewRenters = document.getElementById('fcPrevNewRenters');
                if (prevNewRenters) prevNewRenters.textContent = summary.new_renters_to_create || 0;
                const prevConflicts = document.getElementById('fcPrevConflicts');
                if (prevConflicts) prevConflicts.textContent = summary.conflicts || 0;

                this.renderImportPreviewTable();

                const uploadZone = document.getElementById('fcImportUploadZone');
                if (uploadZone) uploadZone.style.display = 'none';

                const previewSection = document.getElementById('fcImportPreviewSection');
                if (previewSection) previewSection.style.display = 'block';

                const resetBtn = document.getElementById('fcImportResetBtn');
                if (resetBtn) resetBtn.style.display = 'inline-block';

                const confirmBtn = document.getElementById('fcConfirmImportBtn');
                if (confirmBtn) confirmBtn.style.display = 'inline-flex';

                this._updateImportConfirmCount();

                showNotification(`Found ${records.length} bookings! (${summary.existing_renters_matched} matched existing renter accounts, ${summary.new_renters_to_create} new profiles ready)`, 'success');
            } catch (err) {
                console.error("Excel import error:", err);
                showNotification(err.message || 'Failed to parse Excel file', 'error');
                this.resetImport();
            }
        },

        renderImportPreviewTable() {
            const tbody = document.getElementById('fcImportPreviewTableBody');
            if (!tbody) return;

            const records = this._pendingImportRecords || [];
            if (records.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="padding: 24px; text-align: center; color: var(--text-muted);">No records found.</td></tr>`;
                return;
            }

            let html = '';
            records.forEach((rec, idx) => {
                const isSelected = rec._selected ? 'checked' : '';
                const rowBg = rec.is_conflict ? 'rgba(239, 68, 68, 0.05)' : 'transparent';

                let renterBadge = '';
                if (rec.user_match_status === 'existing_user') {
                    renterBadge = `<span style="display: inline-flex; align-items: center; gap: 4px; padding: 2px 7px; border-radius: 6px; font-size: 0.65rem; font-weight: 700; background: rgba(59,130,246,0.12); color: #1d4ed8; border: 1px solid rgba(59,130,246,0.25);">
                        <i class="fas fa-user-check"></i> Account Matched (ID #${rec.matched_user_id})
                    </span>`;
                } else if (rec.user_match_status === 'repeat_in_excel') {
                    renterBadge = `<span style="display: inline-flex; align-items: center; gap: 4px; padding: 2px 7px; border-radius: 6px; font-size: 0.65rem; font-weight: 700; background: rgba(245,158,11,0.12); color: #b45309; border: 1px solid rgba(245,158,11,0.25);">
                        <i class="fas fa-users"></i> Repeat Renter in File
                    </span>`;
                } else {
                    renterBadge = `<span style="display: inline-flex; align-items: center; gap: 4px; padding: 2px 7px; border-radius: 6px; font-size: 0.65rem; font-weight: 700; background: rgba(107,114,128,0.12); color: var(--text-muted); border: 1px solid rgba(107,114,128,0.2);">
                        <i class="fas fa-user-plus"></i> New Profile will be Created
                    </span>`;
                }

                let vehHtml = '';
                if (rec.vehicle_id) {
                    vehHtml = `<div style="font-weight: 700; color: var(--text-main); display: flex; align-items: center; gap: 6px;">
                        <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${rec.calendar_color || '#00B14F'};"></span>
                        ${escapeHtml(rec.vehicle_name || 'Vehicle')}
                    </div>
                    <div style="font-size: 0.68rem; color: var(--text-muted);">Plate: <strong>${escapeHtml(rec.plate_number || 'N/A')}</strong></div>`;
                } else {
                    vehHtml = `<div style="color: #dc2626; font-weight: 700;"><i class="fas fa-exclamation-triangle"></i> Car Not Found</div>
                    <div style="font-size: 0.68rem; color: var(--text-muted);">${escapeHtml(rec.raw_vehicle_name || 'Unknown')}</div>`;
                }

                let statusBadge = '';
                if (rec.is_conflict) {
                    statusBadge = `<span style="padding: 2px 8px; border-radius: 6px; font-size: 0.65rem; font-weight: 700; background: rgba(239,68,68,0.12); color: #dc2626; border: 1px solid rgba(239,68,68,0.3);" title="${escapeHtml(rec.conflict_reason || '')}">
                        ⚠️ ${escapeHtml(rec.conflict_reason || 'Conflict')}
                    </span>`;
                } else {
                    statusBadge = `<span style="padding: 2px 8px; border-radius: 6px; font-size: 0.65rem; font-weight: 700; background: rgba(0,177,79,0.1); color: #15803d; border: 1px solid rgba(0,177,79,0.25);">
                        ✅ Ready
                    </span>`;
                }

                html += `
                    <tr style="border-bottom: 1px solid var(--border); background: ${rowBg};">
                        <td style="padding: 8px 10px; text-align: center;">
                            <input type="checkbox" ${isSelected} onchange="FleetCalendar.toggleImportRow(${idx}, this.checked)" style="accent-color: #00B14F;">
                        </td>
                        <td style="padding: 8px 10px;">${vehHtml}</td>
                        <td style="padding: 8px 10px;">
                            <div style="font-weight: 700; color: var(--text-main);">${escapeHtml(rec.customer_name || 'Renter')}</div>
                            <div style="margin-top: 3px;">${renterBadge}</div>
                        </td>
                        <td style="padding: 8px 10px; text-align: center;">
                            <div style="font-weight: 700; color: var(--text-main); font-family: monospace;">${rec.start_date} &rarr; ${rec.end_date}</div>
                            <div style="font-size: 0.68rem; color: var(--text-muted);">${rec.total_days || 1} ${(rec.total_days === 1 ? 'day' : 'days')}</div>
                        </td>
                        <td style="padding: 8px 10px; text-align: right;">
                            <div style="font-weight: 700; color: #00B14F;">₱${Number(rec.total_price || 0).toLocaleString()}</div>
                            <div style="font-size: 0.65rem; color: var(--text-muted);">${escapeHtml(rec.payment_status || 'paid')}</div>
                        </td>
                        <td style="padding: 8px 10px; text-align: center;">${statusBadge}</td>
                    </tr>
                `;
            });

            tbody.innerHTML = html;
        },

        toggleSkipConflicts(skip) {
            (this._pendingImportRecords || []).forEach(r => {
                if (r.is_conflict) {
                    r._selected = !skip;
                }
            });
            this.renderImportPreviewTable();
            this._updateImportConfirmCount();
        },

        toggleSelectAllImport(checked) {
            const skipConflicts = document.getElementById('fcImportSkipConflicts')?.checked ?? true;
            (this._pendingImportRecords || []).forEach(r => {
                if (skipConflicts && r.is_conflict) {
                    r._selected = false;
                } else {
                    r._selected = checked;
                }
            });
            this.renderImportPreviewTable();
            this._updateImportConfirmCount();
        },

        toggleImportRow(idx, checked) {
            if (this._pendingImportRecords && this._pendingImportRecords[idx]) {
                this._pendingImportRecords[idx]._selected = checked;
            }
            this._updateImportConfirmCount();
        },

        _updateImportConfirmCount() {
            const selected = (this._pendingImportRecords || []).filter(r => r._selected && r.vehicle_id);
            const countEl = document.getElementById('fcConfirmCount');
            if (countEl) countEl.textContent = selected.length;
        },

        async confirmImport() {
            const selectedRecords = (this._pendingImportRecords || []).filter(r => r._selected);
            if (selectedRecords.length === 0) {
                showNotification('Please select at least 1 booking to import.', 'warning');
                return;
            }

            const unassignedCars = selectedRecords.filter(r => !r.vehicle_id);
            if (unassignedCars.length > 0) {
                showNotification(`Warning: ${unassignedCars.length} selected row(s) do not match any vehicle in your fleet and will be skipped.`, 'warning');
            }

            const validToImport = selectedRecords.filter(r => r.vehicle_id);
            if (validToImport.length === 0) {
                showNotification('None of the selected records have a matching vehicle in the fleet.', 'error');
                return;
            }

            const autoCreate = document.getElementById('fcImportAutoCreate')?.checked ?? true;
            const btn = document.getElementById('fcConfirmImportBtn');
            const origHtml = btn ? btn.innerHTML : '';
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing to Calendar...';
            }

            try {
                let currentUserId = 1;
                try {
                    const storedUser = localStorage.getItem('autoride_user');
                    if (storedUser) {
                        const parsed = JSON.parse(storedUser);
                        if (parsed && parsed.id) currentUserId = parsed.id;
                    }
                } catch(e) {}

                let url = `${API_BASE}/api/admin/fleet-calendar/import-confirm`;
                let res = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        records: validToImport,
                        auto_create_renters: autoCreate,
                        requester_id: currentUserId
                    })
                });
                if (res.status === 404 || res.status === 405) {
                    url = `${API_BASE}/admin/fleet-calendar/import-confirm`;
                    res = await fetch(url, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            records: validToImport,
                            auto_create_renters: autoCreate,
                            requester_id: currentUserId
                        })
                    });
                }

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.error || 'Failed to import bookings into database');
                }

                const result = await res.json();
                showNotification(
                    result.message || `Successfully synced ${result.imported_bookings || validToImport.length} bookings!`,
                    'success'
                );

                this.closeImportModal();

                // Instantly refresh Fleet Calendar to display all newly imported Gantt bars
                if (typeof this.refresh === 'function') {
                    this.refresh();
                } else if (typeof this.loadBookingsAndRender === 'function') {
                    this.loadBookingsAndRender();
                }
            } catch (err) {
                console.error("Import confirm error:", err);
                showNotification(err.message || 'Import failed', 'error');
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = origHtml || '<i class="fas fa-check-circle"></i> Confirm & Sync';
                }
            }
        }
    };

    // ==================== BLACKOUT DATES ====================
    const Blackouts = {
        data: [],
        
        async refresh() {
            try {
                const res = await fetch(`${API_BASE}/api/admin/blackout-dates`);
                this.data = await res.json();
                this.renderList();
                this.loadVehicles();
            } catch(e) {
                console.error("Failed to fetch blackouts:", e);
            }
        },
        
        async loadVehicles() {
            try {
                const res = await fetch(`${API_BASE}/api/vehicles`);
                const vehicles = await res.json();
                let html = `
                    <label style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 0.8rem; color: #0f172a; padding-bottom: 6px; border-bottom: 1px solid #f1f5f9; cursor: pointer; user-select: none;">
                        <input type="checkbox" id="blackoutVehiclesAll" onchange="Blackouts.toggleAllVehicles(this.checked)" style="width: 16px; height: 16px; accent-color: #00B14F; cursor: pointer;">
                        All Vehicles (System-wide Block)
                    </label>
                `;
                vehicles.forEach(v => {
                    html += `
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 0.78rem; color: #374151; cursor: pointer; padding: 2px 0; user-select: none;">
                            <input type="checkbox" class="blackout-vehicle-item" value="${v.id}" style="width: 15px; height: 15px; accent-color: #00B14F; cursor: pointer;">
                            ${v.brand} ${v.model} (${v.plate_number || 'No Plate'})
                        </label>
                    `;
                });
                document.getElementById('blackoutVehiclesContainer').innerHTML = html;
            } catch(e) {
                console.error(e);
            }
        },

        toggleAllVehicles(checked) {
            const items = document.querySelectorAll('.blackout-vehicle-item');
            items.forEach(el => {
                el.checked = checked;
                el.disabled = checked;
            });
        },
        
        renderList() {
            let html = "";
            this.data.forEach(b => {
                const start = new Date(b.start_date).toLocaleDateString('en-PH', {month:'short', day:'numeric', year:'numeric'});
                const end = new Date(b.end_date).toLocaleDateString('en-PH', {month:'short', day:'numeric', year:'numeric'});
                const scopeText = b.affected_vehicles === 'all' ? 'All Vehicles' : 'Specific Vehicle';
                html += `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                        <div>
                            <div style="font-weight: 700; font-size: 0.85rem; color: #0f172a;">${b.reason}</div>
                            <div style="font-size: 0.72rem; color: #64748b; margin-top: 2px;">
                                <i class="fas fa-calendar-alt" style="margin-right: 4px;"></i>${start} - ${end}
                                <span style="margin-left: 8px; padding: 2px 6px; background: #e2e8f0; border-radius: 4px; font-weight: 800; font-size: 0.6rem;">${scopeText.toUpperCase()}</span>
                            </div>
                        </div>
                        <button onclick="Blackouts.delete(${b.id})" style="background: none; border: none; color: #ef4444; cursor: pointer; padding: 6px;"><i class="fas fa-trash-alt"></i></button>
                    </div>`;
            });
            if (this.data.length === 0) {
                html = '<div style="text-align: center; padding: 20px; color: #64748b; font-size: 0.8rem;">No active blackout dates.</div>';
            }
            document.getElementById('blackoutsList').innerHTML = html;
        },
        
        async add(e) {
            e.preventDefault();
            const start_date = document.getElementById('blackoutStartDate').value;
            const end_date = document.getElementById('blackoutEndDate').value;
            const reason = document.getElementById('blackoutReason').value;
            
            const allChecked = document.getElementById('blackoutVehiclesAll') ? document.getElementById('blackoutVehiclesAll').checked : false;
            let affected_vehicles = 'all';
            
            if (!allChecked) {
                const checkedItems = Array.from(document.querySelectorAll('.blackout-vehicle-item:checked')).map(el => el.value);
                if (checkedItems.length === 0) {
                    showNotification("Please select at least one vehicle", "error");
                    return;
                }
                affected_vehicles = checkedItems.join(',');
            }
            
            const user = typeof adminAuth !== 'undefined' ? adminAuth.getUser() : null;
            const admin_id = user ? user.id : 1;
            
            try {
                const res = await fetch(`${API_BASE}/api/admin/blackout-dates`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ start_date, end_date, reason, affected_vehicles, admin_id })
                });
                const data = await res.json();
                if (res.ok) {
                    showNotification("Blackout period created successfully", "success");
                    document.getElementById('blackoutForm').reset();
                    this.refresh();
                    if (typeof FleetCalendar !== 'undefined') FleetCalendar.refresh();
                } else {
                    showNotification(data.error || "Failed to create blackout", "error");
                }
            } catch(err) {
                showNotification("Connection error", "error");
            }
        },
        
        async delete(id) {
            if (!confirm("Are you sure you want to delete this blackout period?")) return;
            try {
                const res = await fetch(`${API_BASE}/api/admin/blackout-dates/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    showNotification("Blackout period deleted", "success");
                    this.refresh();
                    if (typeof FleetCalendar !== 'undefined') FleetCalendar.refresh();
                } else {
                    showNotification("Failed to delete", "error");
                }
            } catch(e) {
                showNotification("Connection error", "error");
            }
        }
    };

    function toggleBlackoutsModal(show = true) {
        const modal = document.getElementById('blackoutsModal');
        modal.style.display = show ? 'flex' : 'none';
        if (show) {
            Blackouts.refresh();
        }
    }

    const NewsletterAdmin = {
        currentTab: 'broadcast',
        campaigns: [],
        subscribers: [],
        isEnabled: true,

        async checkVisibility() {
            try {
                const res = await fetch(`${API_BASE}/api/newsletter/toggle`);
                const data = await res.json();
                this.isEnabled = (data && data.enabled !== false);
                this.updateVisibilityUI();
            } catch(e) {
                console.error("Failed to check newsletter visibility:", e);
            }
        },

        async toggleVisibility() {
            const nextState = !this.isEnabled;
            const btn = document.getElementById('nlToggleVisibilityBtn');
            if (btn) btn.disabled = true;

            try {
                const res = await fetch(`${API_BASE}/api/newsletter/toggle`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ enabled: nextState })
                });
                const data = await res.json();
                if (res.ok) {
                    this.isEnabled = nextState;
                    this.updateVisibilityUI();
                    const msg = nextState 
                        ? "Newsletter & Privileges is now VISIBLE on customer app." 
                        : "Newsletter & Privileges is now HIDDEN from customer app.";
                    showNotification(msg, nextState ? "success" : "info");
                } else {
                    showNotification(data.error || "Failed to update visibility", "error");
                }
            } catch(e) {
                showNotification("Connection error", "error");
            } finally {
                if (btn) btn.disabled = false;
            }
        },

        updateVisibilityUI() {
            const badge = document.getElementById('nlVisibilityBadge');
            const icon = document.getElementById('nlVisibilityIcon');
            const btn = document.getElementById('nlToggleVisibilityBtn');
            const btnIcon = document.getElementById('nlToggleBtnIcon');
            const btnText = document.getElementById('nlToggleBtnText');
            const subtitle = document.getElementById('nlSettingsSubtitle');

            if (this.isEnabled) {
                if (badge) {
                    badge.textContent = 'VISIBLE';
                    badge.style.background = 'rgba(0,177,79,0.12)';
                    badge.style.color = '#00B14F';
                }
                if (icon) {
                    icon.className = 'fas fa-eye';
                    icon.style.color = '#00B14F';
                }
                if (btn) {
                    btn.style.borderColor = '#00B14F';
                    btn.style.background = 'rgba(0,177,79,0.12)';
                    btn.style.color = '#00B14F';
                }
                if (btnIcon) btnIcon.className = 'fas fa-toggle-on';
                if (btnText) btnText.textContent = 'Enabled (Shown)';
                if (subtitle) subtitle.textContent = 'Status: Active (Visible to Customers)';
            } else {
                if (badge) {
                    badge.textContent = 'HIDDEN';
                    badge.style.background = 'rgba(239,68,68,0.12)';
                    badge.style.color = '#ef4444';
                }
                if (icon) {
                    icon.className = 'fas fa-eye-slash';
                    icon.style.color = '#ef4444';
                }
                if (btn) {
                    btn.style.borderColor = '#64748b';
                    btn.style.background = 'rgba(100,116,139,0.12)';
                    btn.style.color = '#64748b';
                }
                if (btnIcon) btnIcon.className = 'fas fa-toggle-off';
                if (btnText) btnText.textContent = 'Disabled (Hidden)';
                if (subtitle) subtitle.textContent = 'Status: Disabled (Hidden from Customers)';
            }
        },

        switchTab(tab) {
            this.currentTab = tab;
            ['broadcast', 'campaigns', 'subscribers'].forEach(t => {
                const btn = document.getElementById('nlTabBtn_' + t);
                const pane = document.getElementById('nlTabPane_' + t);
                if (btn) {
                    const badge = btn.querySelector('.nl-count-badge');
                    if (t === tab) {
                        btn.style.background = '#3b82f6';
                        btn.style.color = '#ffffff';
                        btn.style.borderColor = '#3b82f6';
                        if (badge) {
                            badge.style.background = 'rgba(255, 255, 255, 0.25)';
                            badge.style.color = '#ffffff';
                        }
                    } else {
                        btn.style.background = '#f1f5f9';
                        btn.style.color = '#475569';
                        btn.style.borderColor = '#e2e8f0';
                        if (badge) {
                            badge.style.background = 'rgba(0, 0, 0, 0.08)';
                            badge.style.color = '#475569';
                        }
                    }
                }
                if (pane) pane.style.display = (t === tab) ? 'block' : 'none';
            });
            if (tab === 'campaigns') this.loadCampaigns();
            if (tab === 'subscribers') this.loadSubscribers();
        },

        async loadCampaigns() {
            const listEl = document.getElementById('nlAdminCampaignsList');
            if (listEl) listEl.innerHTML = '<div style="text-align:center;padding:20px;color:#64748b;"><i class="fas fa-spinner fa-spin"></i> Loading campaigns...</div>';
            try {
                const res = await fetch(`${API_BASE}/api/admin/newsletters`);
                const data = await res.json();
                this.campaigns = data.newsletters || [];
                const countEl = document.getElementById('adminCampaignCount');
                if (countEl) countEl.textContent = this.campaigns.length;
                this.renderCampaigns();
            } catch(e) {
                if (listEl) listEl.innerHTML = '<div style="color:#ef4444;text-align:center;padding:15px;">Failed to load campaigns.</div>';
            }
        },

        renderCampaigns() {
            const listEl = document.getElementById('nlAdminCampaignsList');
            if (!listEl) return;
            if (this.campaigns.length === 0) {
                listEl.innerHTML = '<div style="text-align:center;padding:30px;color:#94a3b8;font-size:0.85rem;"><i class="fas fa-bullhorn" style="font-size:2rem;margin-bottom:8px;display:block;opacity:0.4;"></i>No campaigns published yet.</div>';
                return;
            }
            listEl.innerHTML = this.campaigns.map(c => {
                const dateStr = c.created_at ? new Date(c.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '';
                return `
                    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:8px;">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
                            <div>
                                <span style="background:rgba(59,130,246,0.12);color:#2563eb;font-size:0.7rem;font-weight:700;padding:2px 8px;border-radius:6px;margin-right:6px;">${c.category || 'General'}</span>
                                ${c.promo_code ? `<span style="background:rgba(0,177,79,0.12);color:#00B14F;font-size:0.7rem;font-weight:800;padding:2px 8px;border-radius:6px;"><i class="fas fa-tag"></i> ${c.promo_code} (${c.discount_percent || 0}% OFF)</span>` : ''}
                                <h4 style="font-size:0.95rem;font-weight:700;color:#0f172a;margin:6px 0 2px;">${c.title}</h4>
                                <span style="font-size:0.72rem;color:#64748b;"><i class="far fa-clock"></i> ${dateStr}</span>
                            </div>
                            <button onclick="NewsletterAdmin.deleteCampaign(${c.id})" title="Delete Campaign" style="background:rgba(239,68,68,0.1);color:#ef4444;border:none;padding:6px 10px;border-radius:6px;cursor:pointer;font-size:0.8rem;transition:all 0.15s;">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        </div>
                        <p style="font-size:0.8rem;color:#475569;margin:0;line-height:1.45;white-space:pre-line;">${c.content || ''}</p>
                    </div>
                `;
            }).join('');
        },

        async submitCampaign(e) {
            e.preventDefault();
            const title = document.getElementById('nlFormTitle').value.trim();
            const category = document.getElementById('nlFormCategory').value;
            const promo_code = document.getElementById('nlFormCode').value.trim();
            const discount_percent = document.getElementById('nlFormDiscount').value;
            const content = document.getElementById('nlFormContent').value.trim();
            const broadcast_notification = document.getElementById('nlFormNotify').checked;

            if (!title || !content) {
                showNotification("Please fill in both title and content", "error");
                return;
            }

            const btn = document.getElementById('nlSubmitBtn');
            const origText = btn ? btn.innerHTML : '';
            if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Broadcasting...'; }

            try {
                const res = await fetch(`${API_BASE}/api/admin/newsletters`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        title, category, promo_code, discount_percent, content, broadcast_notification,
                        created_by: (typeof adminAuth !== 'undefined' && adminAuth.getUser()) ? adminAuth.getUser().name || 'Admin' : 'Admin'
                    })
                });
                const data = await res.json();
                if (res.ok) {
                    showNotification("Newsletter broadcasted successfully!", "success");
                    document.getElementById('nlBroadcastForm').reset();
                    this.switchTab('campaigns');
                } else {
                    showNotification(data.error || "Failed to broadcast newsletter", "error");
                }
            } catch(err) {
                showNotification("Connection error", "error");
            } finally {
                if (btn) { btn.disabled = false; btn.innerHTML = origText; }
            }
        },

        async deleteCampaign(id) {
            if (!confirm("Are you sure you want to delete this campaign?")) return;
            try {
                const res = await fetch(`${API_BASE}/api/admin/newsletters/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    showNotification("Campaign deleted successfully", "success");
                    this.loadCampaigns();
                } else {
                    showNotification("Failed to delete campaign", "error");
                }
            } catch(e) {
                showNotification("Connection error", "error");
            }
        },

        async loadSubscribers() {
            const listEl = document.getElementById('nlAdminSubscribersList');
            if (listEl) listEl.innerHTML = '<div style="text-align:center;padding:20px;color:#64748b;"><i class="fas fa-spinner fa-spin"></i> Loading audience...</div>';
            try {
                const res = await fetch(`${API_BASE}/api/admin/subscribers`);
                const data = await res.json();
                this.subscribers = data.subscribers || [];
                const totalEl = document.getElementById('nlStatTotal');
                const actEl = document.getElementById('nlStatActive');
                const unEl = document.getElementById('nlStatUnsub');
                const countBadge = document.getElementById('adminSubCount');
                if (totalEl) totalEl.textContent = data.total || 0;
                if (actEl) actEl.textContent = data.active_count || 0;
                if (unEl) unEl.textContent = data.unsubscribed_count || 0;
                if (countBadge) countBadge.textContent = data.active_count || 0;
                this.renderSubscribers(this.subscribers);
            } catch(e) {
                if (listEl) listEl.innerHTML = '<div style="color:#ef4444;text-align:center;padding:15px;">Failed to load subscribers.</div>';
            }
        },

        filterSubscribers() {
            const q = (document.getElementById('nlSubSearchInput').value || '').toLowerCase().trim();
            if (!q) {
                this.renderSubscribers(this.subscribers);
                return;
            }
            const filtered = this.subscribers.filter(s => 
                (s.email && s.email.toLowerCase().includes(q)) ||
                (s.user_name && s.user_name.toLowerCase().includes(q)) ||
                (s.status && s.status.toLowerCase().includes(q))
            );
            this.renderSubscribers(filtered);
        },

        renderSubscribers(list) {
            const listEl = document.getElementById('nlAdminSubscribersList');
            if (!listEl) return;
            if (!list || list.length === 0) {
                listEl.innerHTML = '<div style="text-align:center;padding:30px;color:#94a3b8;font-size:0.85rem;"><i class="fas fa-users-slash" style="font-size:2rem;margin-bottom:8px;display:block;opacity:0.4;"></i>No subscribers match this search.</div>';
                return;
            }
            listEl.innerHTML = list.map(s => {
                const dateStr = s.created_at ? new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '';
                const isActive = (s.status === 'active');
                return `
                    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;padding:10px 14px;display:flex;align-items:center;justify-content:space-between;gap:10px;">
                        <div style="flex:1;min-width:0;">
                            <div style="display:flex;align-items:center;gap:6px;">
                                <span style="font-size:0.875rem;font-weight:700;color:#0f172a;word-break:break-all;">${s.email}</span>
                                <span style="background:${isActive ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.12)'};color:${isActive ? '#16a34a' : '#ef4444'};font-size:0.68rem;font-weight:700;padding:2px 6px;border-radius:10px;text-transform:capitalize;">${s.status || 'active'}</span>
                            </div>
                            <div style="font-size:0.75rem;color:#64748b;margin-top:2px;">
                                ${s.user_name && s.user_name.trim() ? `<span><i class="fas fa-user" style="margin-right:4px;"></i>${s.user_name.trim()}</span> \u2022 ` : ''}
                                <span><i class="far fa-calendar-alt" style="margin-right:4px;"></i>Subscribed ${dateStr}</span>
                            </div>
                        </div>
                        <button onclick="NewsletterAdmin.deleteSubscriber(${s.id})" title="Remove Subscriber" style="background:transparent;border:none;color:#94a3b8;cursor:pointer;padding:6px;font-size:0.85rem;transition:color 0.15s;" onmouseover="this.style.color='#ef4444'" onmouseout="this.style.color='#94a3b8'">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                `;
            }).join('');
        },

        async deleteSubscriber(id) {
            if (!confirm("Remove this subscriber from audience?")) return;
            try {
                const res = await fetch(`${API_BASE}/api/admin/subscribers/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    showNotification("Subscriber removed", "success");
                    this.loadSubscribers();
                } else {
                    showNotification("Failed to remove subscriber", "error");
                }
            } catch(e) {
                showNotification("Connection error", "error");
            }
        }
    };

    window.closeDrawer = function() {
        if (typeof toggleDrawer === 'function') toggleDrawer(false);
    };

    
    // ==========================================
    // DATABASE ARCHIVING & MAINTENANCE CONTROLLERS
    // ==========================================

    function toggleArchiveMaintenanceModal(show = true) {
        const modal = document.getElementById('archiveMaintenanceModal');
        if (!modal) return;
        modal.style.display = show ? 'flex' : 'none';
        if (show && typeof ArchiveMaintenanceAdmin !== 'undefined') {
            ArchiveMaintenanceAdmin.loadStats();
        }
    }

    const ArchiveMaintenanceAdmin = {
        stats: null,
        async loadStats() {
            try {
                const res = await fetch(`${API_BASE}/api/admin/maintenance/stats`);
                if (!res.ok) throw new Error('Failed to load stats');
                const data = await res.json();
                this.stats = data;
                
                const setEl = (id, val) => {
                    const el = document.getElementById(id);
                    if (el) el.textContent = val !== undefined && val !== null ? val.toLocaleString() : '0';
                };

                setEl('maintStatActiveBookings', data.bookings?.active);
                setEl('maintStatArchivedBookings', data.bookings?.archived);
                setEl('maintStatEligibleBookings', data.bookings?.eligible_for_archive_30d);
                setEl('maintStatOldLogs', data.activity_logs?.older_than_30d);

                // Update archived count badge on bookings tab
                const badge = document.getElementById('archivedBookingsCountBadge');
                if (badge) {
                    const count = data.bookings?.archived || 0;
                    badge.textContent = count;
                    badge.style.display = count > 0 ? 'inline-block' : 'none';
                }
                const headerBadge = document.getElementById('archivedBookingsHeaderBadge');
                if (headerBadge) {
                    headerBadge.textContent = `${(data.bookings?.archived || 0).toLocaleString()} records`;
                }
            } catch (err) {
                console.error('Error loading maintenance stats:', err);
            }
        },

        async runBatchArchiveBookings() {
            const days = parseInt(document.getElementById('maintBatchBookingDays')?.value || '30', 10);
            const label = days === 0 ? 'ALL completed/cancelled bookings' : `finished bookings older than ${days} days`;
            if (!confirm(`Are you sure you want to batch-archive ${label}?

They will be safely secluded from operational queues to keep query latency fast. You can restore them anytime.`)) {
                return;
            }

            const btn = document.getElementById('btnRunBatchArchive');
            if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Archiving...'; }

            try {
                const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser()) || {};
                const res = await fetch(`${API_BASE}/api/admin/bookings/batch-archive`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ older_than_days: days, archived_by: user.name || user.username || 'Admin' })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Batch archive failed');

                if (typeof showNotification === 'function') {
                    showNotification(data.message || `Archived ${data.archived_count} bookings!`, 'success');
                } else {
                    alert(data.message || `Archived ${data.archived_count} bookings!`);
                }

                await this.loadStats();
                if (typeof Bookings !== 'undefined' && typeof Bookings.refresh === 'function') Bookings.refresh();
                if (typeof PastBookings !== 'undefined' && typeof PastBookings.load === 'function') PastBookings.load();
                if (typeof ArchivedBookings !== 'undefined' && typeof ArchivedBookings.load === 'function') ArchivedBookings.load();
            } catch (err) {
                if (typeof showNotification === 'function') {
                    showNotification(err.message, 'error');
                } else {
                    alert(err.message);
                }
            } finally {
                if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-archive"></i> Run Batch Archive'; }
            }
        },

        async runCleanupLogs() {
            const days = parseInt(document.getElementById('maintLogsDays')?.value || '30', 10);
            if (!confirm(`Permanently delete activity audit logs older than ${days} days?

(Tip: You can export a JSON backup first if you need an audit trail archive).`)) {
                return;
            }

            const btn = document.getElementById('btnRunCleanupLogs');
            if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Pruning...'; }

            try {
                const res = await fetch(`${API_BASE}/api/admin/maintenance/cleanup-logs`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ older_than_days: days })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Logs cleanup failed');

                if (typeof showNotification === 'function') {
                    showNotification(data.message || `Pruned ${data.deleted_count} old audit logs!`, 'success');
                } else {
                    alert(data.message || `Pruned ${data.deleted_count} old audit logs!`);
                }
                await this.loadStats();
            } catch (err) {
                if (typeof showNotification === 'function') showNotification(err.message, 'error');
                else alert(err.message);
            } finally {
                if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-eraser"></i> Prune Old Logs'; }
            }
        },

        async runCleanupNotifications() {
            const days = parseInt(document.getElementById('maintNotificationsDays')?.value || '30', 10);
            if (!confirm(`Purge read notifications older than ${days} days? Unread notifications will not be affected.`)) {
                return;
            }

            const btn = document.getElementById('btnRunCleanupNotifs');
            if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cleaning...'; }

            try {
                const res = await fetch(`${API_BASE}/api/admin/maintenance/cleanup-notifications`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ older_than_days: days })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Notifications cleanup failed');

                if (typeof showNotification === 'function') {
                    showNotification(data.message || `Cleaned ${data.deleted_count} read notifications!`, 'success');
                } else {
                    alert(data.message || `Cleaned ${data.deleted_count} read notifications!`);
                }
                await this.loadStats();
            } catch (err) {
                if (typeof showNotification === 'function') showNotification(err.message, 'error');
                else alert(err.message);
            } finally {
                if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-broom"></i> Clean Read Alerts'; }
            }
        },

        async runCleanupChats() {
            const days = parseInt(document.getElementById('maintChatsDays')?.value || '60', 10);
            if (!confirm(`Purge support chat messages older than ${days} days?`)) {
                return;
            }

            const btn = document.getElementById('btnRunCleanupChats');
            if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cleaning...'; }

            try {
                const res = await fetch(`${API_BASE}/api/admin/maintenance/cleanup-chats`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ older_than_days: days })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Chat cleanup failed');

                if (typeof showNotification === 'function') {
                    showNotification(data.message || `Cleaned ${data.deleted_count} chat messages!`, 'success');
                } else {
                    alert(data.message || `Cleaned ${data.deleted_count} chat messages!`);
                }
                await this.loadStats();
            } catch (err) {
                if (typeof showNotification === 'function') showNotification(err.message, 'error');
                else alert(err.message);
            } finally {
                if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-trash-alt"></i> Prune Old Messages'; }
            }
        },

        exportData(type) {
            const url = `${API_BASE}/api/admin/maintenance/export/${type}`;
            const link = document.createElement('a');
            link.href = url;
            link.target = '_blank';
            link.download = `${type}_backup_${new Date().toISOString().slice(0,10)}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };

    const ArchivedBookings = {
        data: [],
        filteredData: [],
        currentPage: 1,
        pageSize: 10,
        totalPages: 1,
        totalCount: 0,
        searchQuery: '',
        reasonFilter: 'all',
        _debounceTimer: null,

        async load() {
            const loadingEl = document.getElementById('archivedBookingsLoading');
            const emptyEl = document.getElementById('archivedBookingsEmpty');
            const tableEl = document.getElementById('archivedBookingsTable');

            if (loadingEl) loadingEl.style.display = 'block';
            if (emptyEl) emptyEl.classList.add('hidden');
            if (tableEl) tableEl.style.display = 'none';

            try {
                let url = `${API_BASE}/api/admin/bookings/archived?page=${this.currentPage}&page_size=${this.pageSize}`;
                if (this.searchQuery) url += `&search=${encodeURIComponent(this.searchQuery)}`;
                if (this.reasonFilter && this.reasonFilter !== 'all') url += `&reason=${encodeURIComponent(this.reasonFilter)}`;

                const res = await fetch(url);
                if (!res.ok) throw new Error('Failed to load archived bookings');
                const result = await res.json();

                this.data = result.bookings || [];
                this.filteredData = this.data;
                this.totalCount = result.total || 0;
                this.totalPages = result.pages || 1;
                this.currentPage = result.page || 1;

                // Update tab counter badge
                const badge = document.getElementById('archivedBookingsCountBadge');
                if (badge) {
                    badge.textContent = this.totalCount;
                    badge.style.display = this.totalCount > 0 ? 'inline-block' : 'none';
                }
                const headerBadge = document.getElementById('archivedBookingsHeaderBadge');
                if (headerBadge) {
                    headerBadge.textContent = `${this.totalCount.toLocaleString()} records`;
                }

                this.renderTable();
                this.updatePagination();
            } catch (err) {
                console.error('Error loading archived bookings:', err);
                if (tableEl) tableEl.style.display = 'none';
                if (emptyEl) {
                    emptyEl.classList.remove('hidden');
                    emptyEl.innerHTML = `
                        <i class="fas fa-exclamation-triangle" style="font-size: 2.5rem; color: #ef4444; margin-bottom: 12px;"></i>
                        <h4 style="font-size: 1rem; font-weight: 700; color: var(--text-main); margin-bottom: 6px;">Failed to load archived bookings</h4>
                        <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 12px;">${err.message}</p>
                        <button onclick="ArchivedBookings.load()" style="padding: 8px 18px; background: var(--primary); border: none; color: white; border-radius: 8px; font-size: 0.8rem; font-weight: 700; cursor: pointer;">Retry</button>
                    `;
                }
            } finally {
                if (loadingEl) loadingEl.style.display = 'none';
            }
        },

        renderTable() {
            const tbody = document.getElementById('archivedBookingsTableBody');
            const emptyEl = document.getElementById('archivedBookingsEmpty');
            const tableEl = document.getElementById('archivedBookingsTable');

            if (!tbody) return;

            if (this.filteredData.length === 0) {
                if (emptyEl) emptyEl.classList.remove('hidden');
                if (tableEl) tableEl.style.display = 'none';
                return;
            }

            if (emptyEl) emptyEl.classList.add('hidden');
            if (tableEl) tableEl.style.display = 'table';

            tbody.innerHTML = this.filteredData.map(b => {
                const startDateStr = b.start_date ? new Date(b.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A';
                const endDateStr = b.end_date ? new Date(b.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A';
                const archDateStr = b.archived_at ? new Date(b.archived_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Archived';
                const totalPrice = b.total_price ? parseFloat(b.total_price).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00';
                const reason = b.archive_reason || 'Archived record';

                return `
                    <tr style="border-bottom: 1px solid var(--border); transition: background 0.2s;">
                        <td style="padding: 12px 10px; font-size: 0.8rem; font-weight: 800; color: #8b5cf6;">#${b.id}</td>
                        <td style="padding: 12px 10px; font-size: 0.85rem; font-weight: 600; color: var(--text-main);">
                            <div>${b.customer_name || 'N/A'}</div>
                            ${b.customer_email ? `
                            <div style="font-size: 0.72rem; color: var(--text-muted); display: inline-flex; align-items: center; gap: 4px;">
                                <i class="fas fa-user-shield" style="color: #00B14F; font-size: 0.65rem;" title="Data Privacy Act (RA 10173) Protected"></i>
                                <span>${maskEmail(b.customer_email)}</span>
                            </div>` : ''}
                        </td>
                        <td style="padding: 12px 10px; font-size: 0.85rem; color: var(--text-secondary);">${b.car || b.vehicle || 'N/A'}</td>
                        <td style="padding: 12px 10px; font-size: 0.78rem; color: var(--text-secondary);">${startDateStr} - ${endDateStr}</td>
                        <td style="padding: 12px 10px;">
                            <span style="font-size: 0.72rem; font-weight: 800; padding: 2px 8px; border-radius: 12px; background: rgba(139,92,246,0.12); color: #8b5cf6; text-transform: uppercase;">${b.status || 'COMPLETED'}</span>
                        </td>
                        <td style="padding: 12px 10px; font-size: 0.78rem; color: var(--text-muted);">
                            <div><i class="fas fa-clock" style="margin-right: 4px; font-size: 0.7rem;"></i>${archDateStr}</div>
                            <div style="font-size: 0.7rem; color: #8b5cf6; font-weight: 600; margin-top: 2px;">${reason}</div>
                        </td>
                        <td style="padding: 12px 10px; text-align: right; font-size: 0.9rem; font-weight: 800; color: var(--text-main);">₱${totalPrice}</td>
                        <td style="padding: 12px 10px; text-align: center;">
                            <div style="display: flex; gap: 6px; justify-content: center; align-items: center;">
                                <button onclick="Bookings.view(${b.id})" style="padding: 6px 10px; background: var(--surface-container); border: 1px solid var(--border); color: var(--text-main); border-radius: 6px; font-size: 0.75rem; font-weight: 600; cursor: pointer;" title="View Details">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button onclick="ArchivedBookings.unarchiveSingle(${b.id})" style="padding: 6px 10px; background: rgba(139,92,246,0.15); border: 1px solid rgba(139,92,246,0.3); color: #8b5cf6; border-radius: 6px; font-size: 0.75rem; font-weight: 700; cursor: pointer;" title="Restore to Active">
                                    <i class="fas fa-box-open"></i> Restore
                                </button>
                                <button onclick="ArchivedBookings.deleteSinglePermanent(${b.id})" style="padding: 6px 10px; background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.25); color: #ef4444; border-radius: 6px; font-size: 0.75rem; font-weight: 700; cursor: pointer;" title="Permanent Delete">
                                    <i class="fas fa-trash-alt"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        },

        updatePagination() {
            const prevBtn = document.getElementById('archivedBookingsPrevBtn');
            const nextBtn = document.getElementById('archivedBookingsNextBtn');
            const pageInfo = document.getElementById('archivedBookingsPageInfo');

            if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
            if (nextBtn) nextBtn.disabled = this.currentPage >= this.totalPages;
            if (pageInfo) pageInfo.textContent = `Page ${this.currentPage} of ${Math.max(this.totalPages, 1)}`;
        },

        prevPage() {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.load();
            }
        },

        nextPage() {
            if (this.currentPage < this.totalPages) {
                this.currentPage++;
                this.load();
            }
        },

        onSearch(val) {
            clearTimeout(this._debounceTimer);
            this.searchQuery = (val || '').trim();
            this._debounceTimer = setTimeout(() => {
                this.currentPage = 1;
                this.load();
            }, 300);
        },

        onFilterReason(val) {
            this.reasonFilter = val;
            this.currentPage = 1;
            this.load();
        },

        async archiveSingle(id) {
            const reason = prompt(`Archive Booking #${id}?

Enter reason for archiving:`, 'Completed Rental Retention');
            if (reason === null) return;

            
            if (typeof anime !== 'undefined') {
                const btn = (window.event && (window.event.currentTarget || window.event.target));
                const row = btn && btn.closest ? btn.closest('tr') : null;
                if (row) anime({ targets: row, translateX: [0, 60], opacity: [1, 0], duration: 320, easing: 'easeInQuad' });
            }
try {
                const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser()) || {};
                const res = await fetch(`${API_BASE}/api/admin/bookings/${id}/archive`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reason: reason || 'Manual Admin Archive', archived_by: user.name || user.username || 'Admin' })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed to archive booking');

                if (typeof showNotification === 'function') {
                    showNotification(`Booking #${id} successfully archived!`, 'success');
                } else {
                    alert(`Booking #${id} successfully archived!`);
                }

                // Hide detail modal if open
                const modal = document.getElementById('bookingDetailsModal');
                if (modal) modal.style.display = 'none';

                if (typeof Bookings !== 'undefined' && typeof Bookings.refresh === 'function') Bookings.refresh();
                if (typeof PastBookings !== 'undefined' && typeof PastBookings.load === 'function') PastBookings.load();
                this.load();
            } catch (err) {
                if (typeof showNotification === 'function') showNotification(err.message, 'error');
                else alert(err.message);
            }
        },

        async unarchiveSingle(id) {
            if (!confirm(`Restore Booking #${id} back to active operational bookings?`)) {
                return;
            }

            if (typeof anime !== 'undefined') {
                const btn = (window.event && (window.event.currentTarget || window.event.target));
                const row = btn && btn.closest ? btn.closest('tr') : null;
                if (row) anime({ targets: row, translateX: [0, -60], opacity: [1, 0], duration: 320, easing: 'easeInQuad' });
            }

            try {
                const res = await fetch(`${API_BASE}/api/admin/bookings/${id}/unarchive`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed to unarchive booking');

                if (typeof showNotification === 'function') {
                    showNotification(`Booking #${id} restored to active operational records!`, 'success');
                } else {
                    alert(`Booking #${id} restored!`);
                }

                const modal = document.getElementById('bookingDetailsModal');
                if (modal) modal.style.display = 'none';

                if (typeof Bookings !== 'undefined' && typeof Bookings.refresh === 'function') Bookings.refresh();
                if (typeof PastBookings !== 'undefined' && typeof PastBookings.load === 'function') PastBookings.load();
                this.load();
            } catch (err) {
                if (typeof showNotification === 'function') showNotification(err.message, 'error');
                else alert(err.message);
            }
        },

        async deleteSinglePermanent(id) {
            if (!confirm(`⚠️ DANGER: Are you absolutely sure you want to PERMANENTLY delete Booking #${id} and all related payments/inspections/logs from the database?

This CANNOT be undone!`)) {
                return;
            }

            if (typeof anime !== 'undefined') {
                const btn = (window.event && (window.event.currentTarget || window.event.target));
                const row = btn && btn.closest ? btn.closest('tr') : null;
                if (row) anime({ targets: row, translateX: [0, 60], opacity: [1, 0], duration: 320, easing: 'easeInQuad' });
            }

            try {
                const res = await fetch(`${API_BASE}/api/admin/bookings/${id}/permanent`, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed to delete booking');

                if (typeof showNotification === 'function') {
                    showNotification(`Booking #${id} permanently purged.`, 'info');
                } else {
                    alert(`Booking #${id} purged.`);
                }

                const modal = document.getElementById('bookingDetailsModal');
                if (modal) modal.style.display = 'none';

                this.load();
                if (typeof ArchiveMaintenanceAdmin !== 'undefined') ArchiveMaintenanceAdmin.loadStats();
            } catch (err) {
                if (typeof showNotification === 'function') showNotification(err.message, 'error');
                else alert(err.message);
            }
        },

        promptBatchArchive() {
            toggleArchiveMaintenanceModal(true);
        }
    };


function toggleNewsletterModal(show = true) {
        const modal = document.getElementById('newsletterModal');
        if (!modal) return;
        modal.style.display = show ? 'flex' : 'none';
        if (show) {
            NewsletterAdmin.checkVisibility();
            NewsletterAdmin.switchTab('broadcast');
            NewsletterAdmin.loadCampaigns();
            NewsletterAdmin.loadSubscribers();
        }
    }

    function switchTab(tabId) {
        if (tabId === 'fleet-calendar' && typeof FleetCalendar !== 'undefined') FleetCalendar.refresh();



        currentTab = tabId;



        // Guard restricted tabs for non-superadmin
        if (typeof isSuperAdmin === 'function' && !isSuperAdmin()) {
            if (tabId === 'dashboard' || tabId === 'staff' || tabId === 'activity') {
                console.warn(`[Access Guard] Tab '${tabId}' is restricted to Super Admin. Redirecting to vehicles.`);
                tabId = 'vehicles';
            }
        }
        if (typeof applyRolePermissions === 'function') applyRolePermissions();

        // Stop ActiveNow timers when leaving bookings tab



        if (tabId !== 'bookings' && typeof ActiveNow !== 'undefined') ActiveNow.stop();



        // Stop chat polling when leaving chat tab



        if (tabId !== 'chat' && typeof AdminChat !== 'undefined') AdminChat.stopPolling();



        try {



            document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');



            document.querySelectorAll('.nav-item, .drawer-item').forEach(l => l.classList.remove('active'));



            



            const target = document.getElementById(tabId);
            if (target) {
                target.style.display = 'block';
                document.body.classList.toggle('fleet-calendar-active', tabId === 'fleet-calendar');
                const mainContentEl = document.querySelector('.main-content');
                if (mainContentEl) {
                    mainContentEl.scrollTo({ top: 0, behavior: 'instant' });
                    // Lock overflow ONLY on true desktop monitors (width >= 769 AND height >= 600)
                    if (tabId === 'fleet-calendar' && window.innerWidth >= 769 && window.innerHeight >= 600) {
                        mainContentEl.style.overflowY = 'hidden';
                    } else {
                        mainContentEl.style.overflowY = 'auto';
                    }
                }
                if (window.anime) {
                    anime({
                        targets: target,
                        opacity: [0, 1],
                        translateY: [12, 0],
                        duration: 300,
                        easing: 'easeOutCubic'
                    });
                }
            }
            document.querySelectorAll(`[data-tab="${tabId}"]`).forEach(el => {
                el.classList.add('active');
                if (window.anime) {
                    const icon = el.querySelector('i');
                    if (icon) {
                        anime({
                            targets: icon,
                            scale: [0.85, 1.25, 1],
                            duration: 350,
                            easing: 'easeOutBack'
                        });
                    }
                }
            });

            // Update URL hash for refresh persistence
            if (typeof window !== 'undefined') {
                window.location.hash = tabId;
            }



            



            // Only load data if not already loaded (prevents "Fetching..." flash on every tab switch)



            if (tabId === 'dashboard' && typeof refreshDashboard === 'function') refreshDashboard();
            if (tabId === 'vehicles' && typeof Vehicles !== 'undefined') Vehicles.refresh();



            if (tabId === 'bookings' && typeof Bookings !== 'undefined') Bookings.refresh();



            if (tabId === 'drivers' && typeof Drivers !== 'undefined') Drivers.refresh();



            if (tabId === 'verifications' && typeof Verifications !== 'undefined') Verifications.refresh();



            if (tabId === 'instructions' && typeof Instructions !== 'undefined') Instructions.refresh();



            if (tabId === 'staff' && typeof Staff !== 'undefined') Staff.refresh();



            if (tabId === 'reports' && typeof Reports !== 'undefined' && !Reports._loaded) {



                // Set default date range (current month) on first open



                const now = new Date();
                const y = now.getFullYear();
                document.getElementById('rptDateFrom').value = `${y}-01-01`;
                document.getElementById('rptDateTo').value = `${y}-12-31`;
                Reports._filter = 'year';
                Reports.refresh();



            }



            if (tabId === 'activity' && typeof Activity !== 'undefined') Activity.refresh();



            if (tabId === 'users' && typeof UserMgmt !== 'undefined') UserMgmt.refresh();



            if (tabId === 'chat' && typeof AdminChat !== 'undefined') {
                if (window._suppressChatInbox) {
                    window._suppressChatInbox = false;
                } else {
                    AdminChat.loadInbox();
                }



                // Clear nav badge when entering chat



                const b = document.getElementById('adminChatNavBadge');



                if (b) b.style.display = 'none';



            }







            if (tabId === 'gps' && typeof GPS !== 'undefined') GPS.startLive();



            else if (typeof GPS !== 'undefined') GPS.stopLive();



            



            if (tabId === 'settings') {



                const user = adminAuth.getUser();



                if (user) {



                    if(document.getElementById('settingsAvatar')) document.getElementById('settingsAvatar').textContent = user.full_name[0].toUpperCase();



                    if(document.getElementById('settingsName')) document.getElementById('settingsName').textContent = user.full_name;



                    if(document.getElementById('settingsRole')) document.getElementById('settingsRole').textContent = user.role.replace('_', ' ').toUpperCase();



                    if(document.getElementById('settingsEmail')) document.getElementById('settingsEmail').textContent = user.email || 'admin@autoride.com';

                    const isSuper = (user.role === 'super_admin') || (user.role || '').toLowerCase().includes('super');
                    const superAdminPill = document.getElementById('superAdminProfileEditPill');
                    if (superAdminPill) superAdminPill.style.display = isSuper ? 'flex' : 'none';
                    const superAdminCard = document.getElementById('superAdminEditProfileCard');
                    if (superAdminCard) superAdminCard.style.display = isSuper ? 'flex' : 'none';
                    const regularPassCard = document.getElementById('adminChangePasswordCard');
                    if (regularPassCard) regularPassCard.style.display = isSuper ? 'none' : 'flex';

                    if (typeof Settings !== 'undefined') Settings.fetch();



                }



            }



        } catch (err) {



            console.error('Error in switchTab:', err);



        }



    }







    const Bookings = {



        data: [],
        _sortBy: 'date_desc',
        _newSortBy: 'date_desc',

        getDurationDays(b) {
            if (b.days != null && !isNaN(b.days) && Number(b.days) > 0) return Number(b.days);
            if (b.total_days != null && !isNaN(b.total_days) && Number(b.total_days) > 0) return Number(b.total_days);
            if (b.start_date && b.end_date) {
                const start = new Date(b.start_date).getTime();
                const end = new Date(b.end_date).getTime();
                if (!isNaN(start) && !isNaN(end) && end >= start) {
                    return Math.max(1, Math.round((end - start) / 86400000));
                }
            }
            return 1;
        },

        getDate(b) {
            const d = b.created_at || b.start_date || b.booking_date;
            return d ? new Date(d).getTime() : 0;
        },

        getPickupTime(b) {
            if (!b.start_date) return Infinity;
            const timeStr = b.start_time ? String(b.start_time).substring(0, 5) : '00:00';
            const dateStr = String(b.start_date).split('T')[0];
            const ts = new Date(`${dateStr}T${timeStr}:00`).getTime();
            return isNaN(ts) ? (new Date(b.start_date).getTime() || Infinity) : ts;
        },

        getReturnTime(b) {
            if (!b.end_date) return Infinity;
            const timeStr = b.end_time ? String(b.end_time).substring(0, 5) : '23:59';
            const dateStr = String(b.end_date).split('T')[0];
            const ts = new Date(`${dateStr}T${timeStr}:00`).getTime();
            return isNaN(ts) ? (new Date(b.end_date).getTime() || Infinity) : ts;
        },

        getAmount(b) {
            const val = b.total_price != null ? b.total_price : (b.total_amount != null ? b.total_amount : b.amount);
            return Number(val) || 0;
        },

        getName(b) {
            return (b.customer_name || b.renter_name || b.full_name || 'Guest User').trim().toLowerCase();
        },

        setSort(key) {
            this._sortBy = key;
            const el = document.getElementById('allBookingsSort');
            if (el && el.value !== key) el.value = key;
            this.render();
        },

        setNewSort(key) {
            this._newSortBy = key;
            const el = document.getElementById('newBookingsSort');
            if (el && el.value !== key) el.value = key;
            this.renderNew();
        },

        sortBookings(list, sortKey) {
            const copy = [...list];
            switch (sortKey) {
                case 'pickup_asc':
                    return copy.sort((a, b) => {
                        const waitingStatuses = ['confirmed', 'approved', 'pending'];
                        const aWait = waitingStatuses.includes((a.status || '').toLowerCase()) ? 0 : 1;
                        const bWait = waitingStatuses.includes((b.status || '').toLowerCase()) ? 0 : 1;
                        if (aWait !== bWait) return aWait - bWait;
                        return this.getPickupTime(a) - this.getPickupTime(b);
                    });
                case 'return_asc':
                    return copy.sort((a, b) => {
                        const activeStatuses = ['picked up', 'ongoing'];
                        const aAct = activeStatuses.includes((a.status || '').toLowerCase()) ? 0 : 1;
                        const bAct = activeStatuses.includes((b.status || '').toLowerCase()) ? 0 : 1;
                        if (aAct !== bAct) return aAct - bAct;
                        return this.getReturnTime(a) - this.getReturnTime(b);
                    });
                case 'date_asc':
                    return copy.sort((a, b) => this.getDate(a) - this.getDate(b));
                case 'name_asc':
                    return copy.sort((a, b) => this.getName(a).localeCompare(this.getName(b)));
                case 'name_desc':
                    return copy.sort((a, b) => this.getName(b).localeCompare(this.getName(a)));
                case 'duration_desc':
                    return copy.sort((a, b) => this.getDurationDays(b) - this.getDurationDays(a));
                case 'duration_asc':
                    return copy.sort((a, b) => this.getDurationDays(a) - this.getDurationDays(b));
                case 'amount_desc':
                    return copy.sort((a, b) => this.getAmount(b) - this.getAmount(a));
                case 'amount_asc':
                    return copy.sort((a, b) => this.getAmount(a) - this.getAmount(b));
                case 'date_desc':
                default:
                    return copy.sort((a, b) => this.getDate(b) - this.getDate(a));
            }
        },



        _filter: 'all',

        updateOverviewCounts(bookingsList, stats) {
            let total = 0;
            let confirmed = 0;
            let pending = 0;
            let cancelled = 0;

            if (Array.isArray(bookingsList) && bookingsList.length > 0) {
                total = bookingsList.length;
                bookingsList.forEach(b => {
                    const s = (b && b.status ? b.status : '').toLowerCase().trim();
                    if (s === 'confirmed' || s === 'approved' || s === 'picked up' || s === 'ongoing') {
                        confirmed++;
                    } else if (s === 'pending') {
                        pending++;
                    } else if (s === 'cancelled' || s === 'rejected') {
                        cancelled++;
                    }
                });
            } else if (stats) {
                const breakdown = stats.bookingsByStatus || {};
                total = stats.total_bookings || 0;
                confirmed = (breakdown['confirmed'] || 0) + (breakdown['approved'] || 0) + (breakdown['picked up'] || 0) + (breakdown['ongoing'] || 0);
                pending = breakdown['pending'] || 0;
                cancelled = (breakdown['cancelled'] || 0) + (breakdown['rejected'] || 0);
            }

            const elTotal = document.getElementById('bookTotal');
            const elConfirmed = document.getElementById('bookConfirmed');
            const elPending = document.getElementById('bookPending');
            const elCancelled = document.getElementById('bookCancelled');

            if (elTotal) elTotal.textContent = total;
            if (elConfirmed) elConfirmed.textContent = confirmed;
            if (elPending) elPending.textContent = pending;
            if (elCancelled) elCancelled.textContent = cancelled;
        },

        async refresh() {
            const list = document.getElementById('bookingsList');
            showSkeleton('bookingsList', 'table');

            if (!list.innerHTML.trim() || list.innerHTML.includes('Loading bookings')) {
                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">Loading bookings...</div>';
            }

            try {
                // Fetch Stats and List in parallel
                const user = adminAuth.getUser();
                const adminId = user ? user.id : '';

                const [statsRes, listRes] = await Promise.all([
                    fetch(`${API_URL}/admin/stats?admin_id=${adminId}&period=all`),
                    fetch(`${API_URL}/bookings?admin_id=${adminId}`)
                ]);

                let statsData = null;
                if (statsRes.ok) {
                    try { statsData = await statsRes.json(); } catch(e) {}
                }

                if (!listRes.ok) throw new Error(`Server error: ${listRes.status}`);
                this.data = await listRes.json();

                // Always update the overview count cards from the actual bookings list
                this.updateOverviewCounts(this.data, statsData);



                this.render();



                this.renderNew();



                ActiveNow.render(this.data);



                if (typeof Extensions !== 'undefined') Extensions.load();



            } catch (err) {



                console.error('Bookings Error:', err);



                list.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--danger);">Error: ${err.message}<br><button onclick="Bookings.refresh()" style="margin-top:10px; color:white; background:var(--primary); border:none; padding:8px 15px; border-radius:5px;">Retry</button></div>`;



            }



        },



        setFilter(filter, btn) {



            this._filter = filter;



            document.querySelectorAll('.bk-chip').forEach(b => {



                const active = b.dataset.filter === filter;



                b.style.background  = active ? 'var(--primary)' : 'var(--surface-container)';



                b.style.borderColor = active ? 'var(--primary)' : 'var(--border)';



                b.style.color       = active ? 'white' : 'var(--text-main)';



                b.classList.toggle('bk-chip-active', active);



            });



            this.render();



        },



        _newFilter: 'all',



        setNewFilter(filter, btn) {



            this._newFilter = filter;



            document.querySelectorAll('.nb-chip').forEach(b => {



                const active = b.dataset.filter === filter;



                b.style.background  = active ? 'var(--primary)' : 'var(--surface-container)';



                b.style.borderColor = active ? 'var(--primary)' : 'var(--border)';



                b.style.color       = active ? 'white' : 'var(--text-main)';



            });



            this.renderNew();



        },



        renderNew() {



            const list = document.getElementById('newBookingsList');



            if (!list) return;



            // Show pending + confirmed + approved + picked up



            const activeStatuses = ['pending', 'confirmed', 'approved', 'picked up', 'ongoing'];



            const statusMap = { pending: 'Pending', confirmed: 'Confirmed', approved: 'Approved', picked_up: 'Picked Up' };



            const allActive = (this.data || []).filter(b => activeStatuses.includes((b.status||'').toLowerCase()));
            let filtered = allActive;

            if (this._newFilter === 'pickup_soon') {
                const pickupStatuses = ['confirmed', 'approved', 'pending'];
                filtered = filtered.filter(b => pickupStatuses.includes((b.status || '').toLowerCase()));
                const sortKey = (this._newSortBy && this._newSortBy !== 'date_desc') ? this._newSortBy : 'pickup_asc';
                filtered = this.sortBookings(filtered, sortKey);
            } else if (this._newFilter === 'return_soon') {
                const returnStatuses = ['picked up', 'ongoing'];
                filtered = filtered.filter(b => returnStatuses.includes((b.status || '').toLowerCase()));
                const sortKey = (this._newSortBy && this._newSortBy !== 'date_desc') ? this._newSortBy : 'return_asc';
                filtered = this.sortBookings(filtered, sortKey);
            } else if (this._newFilter !== 'all') {
                filtered = filtered.filter(b => {
                    const s = (b.status||'').toLowerCase().replace(' ', '_');
                    return s === this._newFilter || (b.status||'') === statusMap[this._newFilter];
                });
                filtered = this.sortBookings(filtered, this._newSortBy || 'date_desc');
            } else {
                filtered = this.sortBookings(filtered, this._newSortBy || 'date_desc');
            }

            // Update chip counter labels dynamically so admin sees exact breakdown
            const chipCounts = {
                all: allActive.length,
                pickup_soon: allActive.filter(b => ['confirmed', 'approved', 'pending'].includes((b.status || '').toLowerCase())).length,
                return_soon: allActive.filter(b => ['picked up', 'ongoing'].includes((b.status || '').toLowerCase())).length,
                confirmed: allActive.filter(b => (b.status || '').toLowerCase() === 'confirmed').length,
                approved: allActive.filter(b => (b.status || '').toLowerCase() === 'approved').length,
                picked_up: allActive.filter(b => ['picked up', 'ongoing'].includes((b.status || '').toLowerCase())).length,
                pending: allActive.filter(b => (b.status || '').toLowerCase() === 'pending').length
            };

            const chipLabels = {
                all: `All New (${chipCounts.all})`,
                pickup_soon: `<i class="fas fa-calendar-check" style="margin-right:5px;color:var(--primary);"></i>Pickup Soon (${chipCounts.pickup_soon})`,
                return_soon: `<i class="fas fa-undo-alt" style="margin-right:5px;color:#d97706;"></i>Return Soon (${chipCounts.return_soon})`,
                confirmed: `Confirmed (${chipCounts.confirmed})`,
                approved: `Approved (${chipCounts.approved})`,
                picked_up: `Picked Up (${chipCounts.picked_up})`,
                pending: `Pending Review (${chipCounts.pending})`
            };

            document.querySelectorAll('.nb-chip').forEach(chip => {
                const f = chip.dataset.filter;
                if (chipLabels[f]) {
                    chip.innerHTML = chipLabels[f];
                }
            });

            // Update badge count



            const pendingCount = this.data.filter(b => (b.status||'').toLowerCase() === 'pending').length;



            const badge = document.getElementById('newBookingsBadge');



            if (badge) {



                badge.textContent = pendingCount;



                badge.style.display = pendingCount > 0 ? 'inline-flex' : 'none';



            }



            if (filtered.length === 0) {



                list.innerHTML = `<div style="text-align:center;padding:60px 20px;color:var(--text-muted);">



                    <i class="fas fa-inbox" style="font-size:2.5rem;opacity:0.3;margin-bottom:12px;display:block;"></i>



                    <p style="font-weight:600;">No bookings in this queue.</p></div>`;



                return;



            }



            list.innerHTML = filtered.map(b => `



                <div class="stat-card" style="padding: 20px; margin-bottom: 16px;">



                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">



                        <div>



                            <span style="font-size: 0.7rem; color: var(--text-muted); font-weight: 800; letter-spacing: 0.5px;">#${b.id}</span>



                            <h4 style="font-size: 1.1rem; font-weight: 800; margin-top: 2px;">${b.customer_name || 'Guest User'}</h4>



                        </div>



                        <div style="display:flex;align-items:center;flex-wrap:wrap;justify-content:flex-end;gap:5px;">
                            ${(() => {
                                const now = Date.now();
                                const pTime = Bookings.getPickupTime(b);
                                const rTime = Bookings.getReturnTime(b);
                                const st = (b.status || '').toLowerCase();
                                if (['picked up', 'ongoing'].includes(st)) {
                                    if (rTime < now) {
                                        return `<span style="background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.35);padding:2px 8px;border-radius:12px;font-size:0.62rem;font-weight:800;display:inline-flex;align-items:center;gap:4px;"><i class="fas fa-exclamation-circle"></i> RETURN OVERDUE</span>`;
                                    } else if (rTime - now <= 36 * 3600 * 1000) {
                                        return `<span style="background:rgba(245,158,11,0.15);color:#d97706;border:1px solid rgba(245,158,11,0.35);padding:2px 8px;border-radius:12px;font-size:0.62rem;font-weight:800;display:inline-flex;align-items:center;gap:4px;"><i class="fas fa-undo-alt"></i> RETURN SOON</span>`;
                                    }
                                } else if (['confirmed', 'approved', 'pending'].includes(st)) {
                                    if (pTime >= now - 12 * 3600 * 1000 && pTime - now <= 36 * 3600 * 1000) {
                                        return `<span style="background:rgba(0,177,79,0.15);color:#00B14F;border:1px solid rgba(0,177,79,0.35);padding:2px 8px;border-radius:12px;font-size:0.62rem;font-weight:800;display:inline-flex;align-items:center;gap:4px;"><i class="fas fa-clock"></i> PICKUP SOON</span>`;
                                    }
                                }
                                return '';
                            })()}
                            <span class="pill ${this.getPillClass(b.status)}">${b.status || 'PENDING'}</span>
                        </div>



                    </div>



                    <div style="display: flex; gap: 14px; margin-bottom: 20px; background: rgba(255,255,255,0.03); padding: 12px; border-radius: 12px;">



                        <div style="width: 44px; height: 44px; background: rgba(99,102,241,0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center;">



                            <i class="fas fa-car" style="font-size: 1.2rem; color: var(--primary);"></i>



                        </div>



                        <div style="flex: 1;">



                            <p style="font-size: 0.9rem; font-weight: 700; color: var(--text-main);">${b.car || 'Unknown Vehicle'}</p>



                            <p style="font-size: 0.75rem; color: var(--text-muted);">



                                <i class="far fa-calendar-alt" style="margin-right:4px;"></i>



                                ${b.start_date ? new Date(b.start_date).toLocaleDateString() : 'N/A'} - ${b.end_date ? new Date(b.end_date).toLocaleDateString() : 'N/A'}



                            </p>



                        </div>



                    </div>



                    <div style="padding-top: 16px; border-top: 1px solid var(--border);">



                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">



                            <div style="font-size: 1.2rem; font-weight: 900; color: var(--success);">₱${parseFloat(b.total_price||0).toLocaleString()}</div>



                            <button onclick="Bookings.view(${b.id})" class="btn-outline" style="padding: 8px 14px; font-size: 0.72rem; font-weight: 700; border-radius: 10px;">



                                <i class="fas fa-eye" style="margin-right:4px;"></i>Details



                            </button>



                        </div>



                        <div style="display:flex; gap:8px; flex-wrap:wrap;">



                            ${(b.payment_status === 'Pending Payment' && b.status?.toLowerCase() === 'pending') ? `



                                <button onclick="Bookings.markCashReceived(${b.id})" style="flex:1; min-width:120px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;">



                                    <i class="fas fa-money-bill-wave" style="margin-right:4px;"></i>Cash Received



                                </button>



                                <button onclick="Bookings.reject(${b.id})" style="flex:1; min-width:100px; padding:10px 8px; background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;">



                                    <i class="fas fa-times" style="margin-right:4px;"></i>Reject



                                </button>



                            ` : ''}



                            ${(b.status?.toLowerCase() === 'confirmed' || b.status?.toLowerCase() === 'approved') ? (() => {
                                const act = Bookings.getPickupInspectAction(b);
                                return `
                                    <button onclick="${act.onClick}" style="flex:1; min-width:110px; padding:10px 8px; background:${act.active ? 'var(--amber,#f59e0b)' : '#94a3b8'}; color:white; border:none; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:${act.active ? 'pointer' : 'not-allowed'}; opacity:${act.active ? '1' : '0.6'};">
                                        <i class="fas fa-search-plus" style="margin-right:4px;"></i>Pickup Inspect
                                    </button>
                                    ${Bookings.isPickupPast(b) ? `<button onclick="Bookings.markNoShow(${b.id})" style="flex:1; min-width:110px; padding:10px 8px; background:#ef4444; color:#fff; border:none; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;"><i class="fas fa-user-slash" style="margin-right:4px;"></i>No Show</button>` : ''}
                                `;
                            })() : ''}
                            ${(b.status?.toLowerCase() === 'picked up' || b.status?.toLowerCase() === 'ongoing') ? `
                                <button onclick="Inspections.openModal(${b.id}, 'return')" style="flex:1; min-width:110px; padding:10px 8px; background:var(--amber,#f59e0b); color:white; border:none; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;">
                                    <i class="fas fa-clipboard-check" style="margin-right:4px;"></i>Return Inspect
                                </button>
                            ` : ''}
                            ${['completed', 'cancelled', 'rejected', 'no show', 'no-show'].includes((b.status||'').toLowerCase()) && !b.is_archived ? `
                                <button onclick="ArchivedBookings.archiveSingle(${b.id})" style="flex:1; min-width:100px; padding:10px 8px; background:rgba(139,92,246,0.12); color:#8b5cf6; border:1px solid rgba(139,92,246,0.3); border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;" title="Archive Booking">
                                    <i class="fas fa-archive" style="margin-right:4px;"></i>Archive
                                </button>
                            ` : ''}



                        </div>



                    </div>



                </div>



            `).join('');



        },



        render() {



            const list = document.getElementById('bookingsList');



            // Apply status filter



            // Apply status filter
            const statusMap = { pending: 'Pending', confirmed: 'Confirmed', approved: 'Approved', picked_up: 'Picked Up', completed: 'Completed', cancelled: 'Cancelled' };
            let filteredList = this.data;
            let activeSortKey = this._sortBy || 'date_desc';

            if (this._filter === 'pickup_soon') {
                const pickupStatuses = ['confirmed', 'approved', 'pending'];
                filteredList = this.data.filter(b => pickupStatuses.includes((b.status || '').toLowerCase()));
                if (!this._sortBy || this._sortBy === 'date_desc') activeSortKey = 'pickup_asc';
            } else if (this._filter === 'return_soon') {
                const returnStatuses = ['picked up', 'ongoing'];
                filteredList = this.data.filter(b => returnStatuses.includes((b.status || '').toLowerCase()));
                if (!this._sortBy || this._sortBy === 'date_desc') activeSortKey = 'return_asc';
            } else if (this._filter !== 'all') {
                filteredList = this.data.filter(b => {
                    const s = (b.status||'').toLowerCase().replace(' ', '_');
                    return s === this._filter || (b.status||'') === statusMap[this._filter];
                });
            }

            // Apply selected sorting to all bookings
            const sorted = this.sortBookings(filteredList, activeSortKey);
            if (sorted.length === 0) {



                list.innerHTML = `



                    <div style="text-align: center; padding: 60px 20px; background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border);">



                        <i class="fas fa-calendar-times" style="font-size: 3rem; color: var(--text-muted); opacity: 0.3; margin-bottom: 15px;"></i>



                        <p style="color: var(--text-muted); font-weight: 600;">No bookings found.</p>



                    </div>`;



                return;



            }



            list.innerHTML = sorted.map(b => `



                <div class="stat-card" style="padding: 20px; margin-bottom: 16px;">



                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">



                        <div>



                            <span style="font-size: 0.7rem; color: var(--text-muted); font-weight: 800; letter-spacing: 0.5px;">#${b.id}</span>



                            <h4 style="font-size: 1.1rem; font-weight: 800; margin-top: 2px;">${b.customer_name || 'Guest User'}</h4>



                        </div>



                        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">



                        <div style="display:flex;align-items:center;flex-wrap:wrap;justify-content:flex-end;gap:5px;">
                            ${(() => {
                                const now = Date.now();
                                const pTime = Bookings.getPickupTime(b);
                                const rTime = Bookings.getReturnTime(b);
                                const st = (b.status || '').toLowerCase();
                                if (['picked up', 'ongoing'].includes(st)) {
                                    if (rTime < now) {
                                        return `<span style="background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.35);padding:2px 8px;border-radius:12px;font-size:0.62rem;font-weight:800;display:inline-flex;align-items:center;gap:4px;"><i class="fas fa-exclamation-circle"></i> RETURN OVERDUE</span>`;
                                    } else if (rTime - now <= 36 * 3600 * 1000) {
                                        return `<span style="background:rgba(245,158,11,0.15);color:#d97706;border:1px solid rgba(245,158,11,0.35);padding:2px 8px;border-radius:12px;font-size:0.62rem;font-weight:800;display:inline-flex;align-items:center;gap:4px;"><i class="fas fa-undo-alt"></i> RETURN SOON</span>`;
                                    }
                                } else if (['confirmed', 'approved', 'pending'].includes(st)) {
                                    if (pTime >= now - 12 * 3600 * 1000 && pTime - now <= 36 * 3600 * 1000) {
                                        return `<span style="background:rgba(0,177,79,0.15);color:#00B14F;border:1px solid rgba(0,177,79,0.35);padding:2px 8px;border-radius:12px;font-size:0.62rem;font-weight:800;display:inline-flex;align-items:center;gap:4px;"><i class="fas fa-clock"></i> PICKUP SOON</span>`;
                                    }
                                }
                                return '';
                            })()}
                            <span class="pill ${this.getPillClass(b.status)}">${b.status || 'PENDING'}</span>
                        </div>



                            ${b.payment_status === 'Refund Pending' ? 



                                `<span class="pill danger" style="font-size: 0.55rem; padding: 2px 8px;">REFUND NEEDED</span>` : 



                                ((['paid', 'fully paid'].includes((b.payment_status || '').toLowerCase().trim())) ? `<span class="pill success" style="font-size: 0.55rem; padding: 2px 8px;">PAID</span>` : '')



                            }



                        </div>



                    </div>



                    



                    <div style="display: flex; gap: 14px; margin-bottom: 20px; background: rgba(255,255,255,0.03); padding: 12px; border-radius: 14px; border: 1px solid var(--border);">



                        <div style="width: 44px; height: 44px; background: rgba(99, 102, 241, 0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(99, 102, 241, 0.2);">



                            <i class="fas fa-car" style="font-size: 1.2rem; color: var(--primary);"></i>



                        </div>



                        <div style="flex: 1;">



                            <p style="font-size: 0.9rem; font-weight: 700; color: var(--text-main);">${b.car || 'Unknown Vehicle'}</p>



                            <p style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">



                                <i class="far fa-calendar-alt" style="margin-right: 4px;"></i>



                                ${b.start_date ? new Date(b.start_date).toLocaleDateString() : 'N/A'} - ${b.end_date ? new Date(b.end_date).toLocaleDateString() : 'N/A'}



                            </p>



                        </div>



                    </div>



 



                    <div style="padding-top: 16px; border-top: 1px solid var(--border);">



                        <!-- Price row -->



                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">



                            <div style="font-size: 1.2rem; font-weight: 900; color: var(--success); letter-spacing: -0.5px;">₱${parseFloat(b.total_price || 0).toLocaleString()}</div>



                            <button onclick="Bookings.view(${b.id})" class="btn-outline" style="padding: 8px 14px; font-size: 0.72rem; border-radius: 10px; font-weight: 700;">



                                <i class="fas fa-eye" style="margin-right:4px;"></i>Details



                            </button>



                        </div>







                        <!-- Contextual action buttons -->



                        <div style="display:flex; gap:8px; flex-wrap:wrap;">







                            ${(b.payment_status === 'Pending Payment' && b.status?.toLowerCase() === 'pending') ? `



                                <button onclick="Bookings.markCashReceived(${b.id})"



                                    style="flex:1; min-width:120px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;">



                                    <i class="fas fa-money-bill-wave" style="margin-right:4px;"></i>Cash Received



                                </button>



                                <button onclick="Bookings.reject(${b.id})"



                                    style="flex:1; min-width:100px; padding:10px 8px; background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;">



                                    <i class="fas fa-times" style="margin-right:4px;"></i>Reject



                                </button>



                            ` : ''}







                            ${(b.status?.toLowerCase() === 'confirmed' || b.status?.toLowerCase() === 'approved') ? (() => {
                                const act = Bookings.getPickupInspectAction(b);
                                return `
                                    <button onclick="${act.onClick}"
                                        style="flex:1; min-width:110px; padding:10px 8px; background:${act.active ? 'var(--amber,#f59e0b)' : '#94a3b8'}; color:white; border:none; border-radius:10px; font-size:0.75rem; font-weight:800; cursor:${act.active ? 'pointer' : 'not-allowed'}; opacity:${act.active ? '1' : '0.6'};">
                                        <i class="fas fa-search-plus" style="margin-right:4px;"></i>Pickup Inspect
                                    </button>
                                    ${Bookings.isPickupPast(b) ? `<button onclick="Bookings.markNoShow(${b.id})" style="flex:1; min-width:110px; padding:10px 8px; background:#ef4444; color:#fff; border:none; border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;"><i class="fas fa-user-slash" style="margin-right:4px;"></i>No Show</button>` : ''}
                                `;
                            })() : ''}







                            ${(b.status?.toLowerCase() === 'picked up' || b.status?.toLowerCase() === 'ongoing') ? `
                                <button onclick="Inspections.openModal(${b.id}, 'return')"
                                    style="flex:1; min-width:110px; padding:10px 8px; background:var(--amber,#f59e0b); color:white; border:none; border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;">
                                    <i class="fas fa-clipboard-check" style="margin-right:4px;"></i>Return Inspect


                            ` : ''}







                            ${b.payment_status === 'Partially Paid' ? `



                                <button onclick="Bookings.markPaid(${b.id})"



                                    style="flex:1; min-width:110px; padding:10px 8px; background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3); border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;">



                                    <i class="fas fa-money-bill-wave" style="margin-right:4px;"></i>Mark Fully Paid



                                </button>



                            ` : ''}







                        </div>



                    </div>



                </div>



            `).join('');



        },



        async view(id) {
            let b = (this.data && this.data.find(x => x.id == id || x.booking_id == id)) 
                 || (typeof FleetCalendar !== 'undefined' && FleetCalendar.bookings && FleetCalendar.bookings.find(x => x.id == id || x.booking_id == id)) 
                 || (typeof PastBookings !== "undefined" && PastBookings.data && PastBookings.data.find(x => x.id == id || x.booking_id == id)) 
                 || (typeof ArchivedBookings !== "undefined" && ArchivedBookings.data && ArchivedBookings.data.find(x => x.id == id || x.booking_id == id));

            if (!b) {
                const modal = document.getElementById('bookingDetailsModal');
                const content = document.getElementById('bookingDetailContent');
                if (modal && content) {
                    content.innerHTML = `
                        <div style="text-align:center;padding:45px 20px;">
                            <i class="fas fa-circle-notch fa-spin" style="font-size:2.2rem;color:#00B14F;margin-bottom:12px;"></i>
                            <div style="font-size:0.95rem;font-weight:800;color:#0f172a;">Loading Booking Details...</div>
                            <div style="font-size:0.75rem;color:#64748b;margin-top:4px;">Retrieving Booking #${id}</div>
                        </div>`;
                    modal.style.display = 'flex';
                    if (typeof modalOpen === 'function') modalOpen();
                }

                try {
                    const token = localStorage.getItem('token') || (typeof currentUser !== 'undefined' && currentUser ? currentUser.token : null);
                    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
                    const res = await fetch(`${API_BASE}/api/admin/bookings/${id}`, { credentials: 'omit', headers });
                    if (res.ok) {
                        const data = await res.json();
                        b = (data && data.booking) ? data.booking : data;
                    }
                } catch(e) {
                    console.warn('Single booking fetch error:', e);
                }

                if (!b) {
                    try {
                        const token = localStorage.getItem('token') || (typeof currentUser !== 'undefined' && currentUser ? currentUser.token : null);
                        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
                        const res = await fetch(`${API_BASE}/api/admin/bookings`, { credentials: 'omit', headers });
                        if (res.ok) {
                            const all = await res.json();
                            if (Array.isArray(all)) {
                                this.data = all;
                                b = all.find(x => x.id == id || x.booking_id == id);
                            }
                        }
                    } catch(e) {
                        console.warn('All bookings fallback fetch error:', e);
                    }
                }
            }

            if (!b) { 
                console.error('Booking not found:', id); 
                const content = document.getElementById('bookingDetailContent');
                if (content) {
                    content.innerHTML = `
                        <div style="text-align:center;padding:30px 20px;color:#ef4444;">
                            <i class="fas fa-exclamation-triangle" style="font-size:2rem;margin-bottom:10px;"></i>
                            <div style="font-size:0.95rem;font-weight:800;">Booking #${id} Not Found</div>
                            <div style="font-size:0.78rem;color:#64748b;margin-top:4px;">This booking record could not be loaded or may have been removed.</div>
                            <button onclick="document.getElementById('bookingDetailsModal').style.display='none';if(typeof modalClose==='function')modalClose();" style="margin-top:16px;padding:8px 16px;background:#f1f5f9;border:1px solid #cbd5e1;border-radius:8px;font-weight:700;font-size:0.8rem;cursor:pointer;color:#334155;">Close</button>
                        </div>`;
                }
                return; 
            }

            if (!b.id && b.booking_id) b.id = b.booking_id;
            this.currentBooking = b;

            // Normalize vehicle/car string
            if (!b.car) {
                b.car = (b.brand || b.model) ? `${b.brand || ''} ${b.model || ''} (${b.plate_number || 'N/A'})`.trim() : (b.vehicle || 'N/A');
            }

            const fmtDate = d => d ? new Date(d).toLocaleDateString('en-PH', {year:'numeric',month:'short',day:'numeric'}) : 'N/A';
            const fmtMoney = v => '₱' + parseFloat(v||0).toLocaleString('en-PH',{minimumFractionDigits:2,maximumFractionDigits:2});

            const statusStyles = {
                'pending':   { bg:'#fef9c3', color:'#854d0e', border:'#fde047' },
                'confirmed': { bg:'#dbeafe', color:'#1e40af', border:'#93c5fd' },
                'approved':  { bg:'#dbeafe', color:'#1e40af', border:'#93c5fd' },
                'picked up': { bg:'#dcfce7', color:'#166534', border:'#86efac' },
                'ongoing':   { bg:'#dcfce7', color:'#166534', border:'#86efac' },
                'completed': { bg:'#d1fae5', color:'#065f46', border:'#6ee7b7' },
                'cancelled': { bg:'#fee2e2', color:'#991b1b', border:'#fca5a5' },
                'rejected':  { bg:'#fee2e2', color:'#991b1b', border:'#fca5a5' },
            };
            const ss = statusStyles[(b.status||'').toLowerCase()] || { bg:'#f1f5f9', color:'#475569', border:'#cbd5e1' };

            let addonRows = '';
            if (parseFloat(b.addon_price||0) > 0 && b.addons) {
                try {
                    const addons = typeof b.addons === 'string' ? JSON.parse(b.addons) : b.addons;
                    if (Array.isArray(addons) && addons.length) {
                        const perAddon = parseFloat(b.addon_price||0) / addons.length;
                        addonRows = addons.map(a => `
                            <div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f1f5f9;">
                                <span style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:#374151;"><i class="fas fa-plus-circle" style="color:#00B14F;font-size:0.7rem;"></i>${a}</span>
                                <span style="font-size:0.82rem;font-weight:600;color:#374151;">${fmtMoney(perAddon)}</span>
                            </div>`).join('');
                    }
                } catch(e) {}
            }

            const st = (b.status||'').toLowerCase();
            let actionBtns = '';
            if (b.payment_status === 'Pending Payment' && st === 'pending') {
                actionBtns += `<button onclick="Bookings.markCashReceived(${b.id})" style="flex:1;min-width:130px;padding:11px 10px;background:#00B14F;color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-money-bill-wave"></i>Cash Received</button>`;
                actionBtns += `<button onclick="Bookings.reject(${b.id})" style="flex:1;min-width:100px;padding:11px 10px;background:#fff;color:#ef4444;border:1.5px solid #fca5a5;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-times"></i>Reject</button>`;
            }
            if (st === 'confirmed' || st === 'approved') {
                const act = Bookings.getPickupInspectAction(b);
                actionBtns += `<button onclick="${act.onClick}" style="flex:1;min-width:120px;padding:11px 10px;background:${act.active ? '#f59e0b' : '#94a3b8'};color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:${act.active ? 'pointer' : 'not-allowed'};opacity:${act.active ? '1' : '0.6'};display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-search-plus"></i>Pickup Inspect</button>`;
                if (Bookings.isPickupPast(b)) {
                    actionBtns += `<button onclick="Bookings.markNoShow(${b.id})" style="flex:1;min-width:120px;padding:11px 10px;background:#ef4444;color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-user-slash"></i>No Show</button>`;
                }
            }
            if (st === 'picked up' || st === 'ongoing') {
                actionBtns += `<button onclick="Inspections.openModal(${b.id},'return')" style="flex:1;min-width:120px;padding:11px 10px;background:#f59e0b;color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-clipboard-check"></i>Return Inspect</button>`;
            }
            if (b.payment_status === 'Partially Paid') {
                actionBtns += `<button onclick="Bookings.markPaid(${b.id})" style="flex:1;min-width:120px;padding:11px 10px;background:#10b981;color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-check-circle"></i>Mark Fully Paid</button>`;
            }
            if (st !== 'cancelled' && st !== 'rejected' && st !== 'completed') {
                actionBtns += `<button onclick="Bookings.cancel(${b.id})" style="flex:1;min-width:100px;padding:11px 10px;background:#fff;color:#ef4444;border:1.5px solid #fca5a5;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-ban"></i>Cancel</button>`;
            }
            // Trigger Refund button for cancelled bookings with paid status
            if (st === 'cancelled' && ['paid', 'fully paid'].includes((b.payment_status || '').toLowerCase().trim())) {
                actionBtns += `<button onclick="Bookings.triggerRefund(${b.id})" style="flex:1;min-width:130px;padding:11px 10px;background:#f59e0b;color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-undo"></i>Trigger Refund</button>`;
            }

            // Archive / Restore action buttons
            if (b.is_archived) {
                actionBtns += `<button onclick="ArchivedBookings.unarchiveSingle(${b.id})" style="flex:1;min-width:130px;padding:11px 10px;background:#8b5cf6;color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-box-open"></i>Restore to Active</button>`;
                actionBtns += `<button onclick="ArchivedBookings.deleteSinglePermanent(${b.id})" style="flex:1;min-width:100px;padding:11px 10px;background:#fff;color:#ef4444;border:1.5px solid #fca5a5;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-trash-alt"></i>Purge</button>`;
            } else if (['completed', 'cancelled', 'rejected', 'no show', 'no-show'].includes(st)) {
                actionBtns += `<button onclick="ArchivedBookings.archiveSingle(${b.id})" style="flex:1;min-width:120px;padding:11px 10px;background:rgba(139,92,246,0.12);color:#8b5cf6;border:1.5px solid rgba(139,92,246,0.3);border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-archive"></i>Archive Booking</button>`;
            }


            
            let adminReturnBanner = '';
            const isOngoingAdmin = ['picked up', 'ongoing', 'confirmed', 'approved'].includes((b.status || '').toLowerCase());
            if (isOngoingAdmin && b.end_date) {
                try {
                    const eD = (b.end_date || '').split('T')[0];
                    let eT = b.end_time || '18:00';
                    if (eT.length === 5) eT += ':00';
                    const rMs = new Date(eD + 'T' + eT).getTime();
                    if (!isNaN(rMs)) {
                        const diffMs = rMs - Date.now();
                        const diffH = diffMs / 3600000;
                        const diffM = Math.floor(diffMs / 60000);
                        const sD = (b.start_date || '').split('T')[0];
                        let sT = b.start_time || '06:00';
                        if (sT.length === 5) sT += ':00';
                        const durD = (rMs - new Date(sD + 'T' + sT).getTime()) / 86400000;

                        if (diffMs <= 0) {
                            adminReturnBanner = `
                            <div style="background:rgba(239,68,68,0.12);border:1.5px solid #ef4444;border-radius:12px;padding:12px 14px;margin-bottom:14px;display:flex;align-items:center;gap:10px;">
                                <i class="fas fa-ban" style="color:#dc2626;font-size:1.1rem;"></i>
                                <div style="flex:1;">
                                    <div style="font-size:0.82rem;font-weight:800;color:#dc2626;">⛔ OVERDUE RETURN</div>
                                    <div style="font-size:0.75rem;color:#64748b;">Return was due at ${fmtDate(b.end_date)} ${b.end_time||''}. Customer is incurring late penalties.</div>
                                </div>
                            </div>`;
                        } else if (diffH <= 0.5) {
                            adminReturnBanner = `
                            <div style="background:rgba(220,38,38,0.1);border:1.5px solid #dc2626;border-radius:12px;padding:12px 14px;margin-bottom:14px;display:flex;align-items:center;gap:10px;">
                                <i class="fas fa-bell" style="color:#dc2626;font-size:1.1rem;animation:pulse 1.5s infinite;"></i>
                                <div style="flex:1;">
                                    <div style="font-size:0.82rem;font-weight:800;color:#dc2626;">🚨 FINAL RETURN ALERT — ${Math.max(1, diffM)}m REMAINING</div>
                                    <div style="font-size:0.75rem;color:#64748b;">Vehicle is due in ${Math.max(1, diffM)} mins. Prepare for return inspection.</div>
                                </div>
                            </div>`;
                        } else if (diffH <= 1.0) {
                            adminReturnBanner = `
                            <div style="background:rgba(239,68,68,0.08);border:1.5px solid #ef4444;border-radius:12px;padding:12px 14px;margin-bottom:14px;display:flex;align-items:center;gap:10px;">
                                <i class="fas fa-hourglass-half" style="color:#dc2626;font-size:1.1rem;"></i>
                                <div style="flex:1;">
                                    <div style="font-size:0.82rem;font-weight:800;color:#dc2626;">🚨 RETURN DUE IN 1 HOUR (${Math.max(1, diffM)}m left)</div>
                                    <div style="font-size:0.75rem;color:#64748b;">Due at ${b.end_time||'scheduled time'}. Customer warned of hourly penalties.</div>
                                </div>
                            </div>`;
                        } else if (diffH <= 5.0) {
                            adminReturnBanner = `
                            <div style="background:rgba(249,115,22,0.08);border:1.5px solid #f97316;border-radius:12px;padding:12px 14px;margin-bottom:14px;display:flex;align-items:center;gap:10px;">
                                <i class="fas fa-exclamation-triangle" style="color:#ea580c;font-size:1.1rem;"></i>
                                <div style="flex:1;">
                                    <div style="font-size:0.82rem;font-weight:800;color:#ea580c;">⚠️ RETURN DUE IN 5 HOURS (~${Math.round(diffH)}h left)</div>
                                    <div style="font-size:0.75rem;color:#64748b;">Customer has received late return penalty warning.</div>
                                </div>
                            </div>`;
                        } else if (diffH <= 24.0) {
                            adminReturnBanner = `
                            <div style="background:rgba(245,158,11,0.08);border:1.5px solid #f59e0b;border-radius:12px;padding:12px 14px;margin-bottom:14px;display:flex;align-items:center;gap:10px;">
                                <i class="fas fa-business-time" style="color:#d97706;font-size:1.1rem;"></i>
                                <div style="flex:1;">
                                    <div style="font-size:0.82rem;font-weight:800;color:#d97706;">⏰ RETURN DUE TOMORROW (~${Math.round(diffH)}h left)</div>
                                    <div style="font-size:0.75rem;color:#64748b;">Return scheduled for tomorrow at ${b.end_time||''}.</div>
                                </div>
                            </div>`;
                        } else if (diffH <= 72.0 && durD > 3) {
                            adminReturnBanner = `
                            <div style="background:rgba(59,130,246,0.08);border:1.5px solid #3b82f6;border-radius:12px;padding:12px 14px;margin-bottom:14px;display:flex;align-items:center;gap:10px;">
                                <i class="fas fa-calendar-day" style="color:#2563eb;font-size:1.1rem;"></i>
                                <div style="flex:1;">
                                    <div style="font-size:0.82rem;font-weight:800;color:#2563eb;">🕒 3 DAYS REMAINING</div>
                                    <div style="font-size:0.75rem;color:#64748b;">Return scheduled on ${fmtDate(b.end_date)} ${b.end_time||''}.</div>
                                </div>
                            </div>`;
                        }
                    }
                } catch(e) {}
            }

            document.getElementById('bookingDetailContent').innerHTML = `
            <div style="color:#0f172a;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;">
                    <div>
                        <div style="font-size:0.65rem;color:#94a3b8;font-weight:800;letter-spacing:1px;text-transform:uppercase;">Booking</div>
                        <div style="font-size:1.3rem;font-weight:900;color:#0f172a;letter-spacing:-0.5px;">#${b.id}</div>
                    </div>
                    <span style="padding:6px 14px;border-radius:20px;font-size:0.72rem;font-weight:800;letter-spacing:0.3px;background:${ss.bg};color:${ss.color};border:1.5px solid ${ss.border};">${(b.status||'PENDING').toUpperCase()}</span>
                </div>
                ${adminReturnBanner}
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;">
                    <div style="background:#f8fafc;border-radius:12px;padding:12px;border:1px solid #e2e8f0;">
                        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                            <div style="display:flex;align-items:center;gap:6px;">
                                <div style="width:28px;height:28px;background:#dbeafe;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="fas fa-user" style="color:#3b82f6;font-size:0.7rem;"></i></div>
                                <span style="font-size:0.62rem;color:#94a3b8;font-weight:800;text-transform:uppercase;">Customer</span>
                            </div>
                            <button onclick="document.getElementById('bookingDetailsModal').style.display='none';if(typeof modalClose==='function')modalClose();AdminChatWithUser(${b.id})" style="padding:3px 8px;background:rgba(0,177,79,0.1);color:#00B14F;border:1px solid rgba(0,177,79,0.25);border-radius:6px;font-size:0.68rem;font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:4px;">
                                <i class="fas fa-comments"></i> Chat
                            </button>
                        </div>
                        <div style="font-weight:800;font-size:0.88rem;color:#0f172a;margin-bottom:2px;">${b.customer_name||'N/A'}</div>
                        ${(b.customer_phone || b.phone) ? `
                        <div style="font-size:0.75rem;color:#475569;margin-top:2px;">
                            <i class="fas fa-phone-alt" style="color:#00B14F;font-size:0.65rem;margin-right:4px;"></i>${b.customer_phone || b.phone}
                        </div>` : ''}
                        ${(b.customer_address && b.customer_address !== 'N/A') ? `
                        <div style="font-size:0.72rem;color:#64748b;margin-top:2px;line-height:1.3;">
                            <i class="fas fa-map-marker-alt" style="color:#ef4444;font-size:0.65rem;margin-right:4px;"></i>${b.customer_address}
                        </div>` : ''}
                        ${(b.emergency_contact_name || b.emergency_name) ? `
                        <div style="font-size:0.72rem;color:#8b5cf6;margin-top:3px;font-weight:600;">
                            <i class="fas fa-user-shield" style="font-size:0.65rem;margin-right:4px;"></i>ICE: ${b.emergency_contact_name || b.emergency_name} ${(b.emergency_contact_phone || b.emergency_phone) ? '(' + (b.emergency_contact_phone || b.emergency_phone) + ')' : ''}
                        </div>` : ''}
                        ${(b.customer_email || b.email) ? `
                        <div style="font-size:0.72rem;color:#64748b;word-break:break-all;display:inline-flex;align-items:center;gap:4px;margin-top:3px;">
                            <i class="fas fa-user-shield" style="color:#00B14F;font-size:0.65rem;" title="Data Privacy Act (RA 10173) Protected"></i>
                            <span>${maskEmail(b.customer_email || b.email)}</span>
                        </div>` : ''}
                    </div>
                    <div style="background:#f8fafc;border-radius:12px;padding:12px;border:1px solid #e2e8f0;">
                        <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
                            <div style="width:28px;height:28px;background:#dcfce7;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="fas fa-car" style="color:#16a34a;font-size:0.7rem;"></i></div>
                            <span style="font-size:0.62rem;color:#94a3b8;font-weight:800;text-transform:uppercase;">Vehicle</span>
                        </div>
                        <div style="font-weight:800;font-size:0.85rem;color:#0f172a;line-height:1.3;">${b.car||'N/A'}</div>
                        <div style="font-size:0.7rem;font-weight:700;color:${b.rental_type === 'With Driver' ? '#2563eb' : '#64748b'};margin-top:2px;">
                            ${b.rental_type === 'With Driver' ? '<i class="fas fa-user-tie"></i> With Driver (₱755/day)' : 'Self-Drive'}
                        </div>
                    </div>
                </div>
                <div style="background:#f8fafc;border-radius:12px;padding:14px;margin-bottom:14px;border:1px solid #e2e8f0;">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:${b.pickup_location ? '10px' : '0'};">
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:3px;display:flex;align-items:center;gap:4px;"><i class="fas fa-calendar-check" style="color:#00B14F;"></i>Pickup</div><div style="font-weight:700;font-size:0.9rem;color:#0f172a;">${fmtDate(b.start_date)} ${b.start_time || '06:00'}</div></div>
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:3px;display:flex;align-items:center;gap:4px;"><i class="fas fa-calendar-times" style="color:#ef4444;"></i>Return</div><div style="font-weight:700;font-size:0.9rem;color:#0f172a;">${fmtDate(b.end_date)} ${b.end_time || '06:00'}</div></div>
                    </div>
                    ${b.pickup_location ? `<div style="padding-top:10px;border-top:1px solid #e2e8f0;display:flex;align-items:flex-start;gap:6px;"><i class="fas fa-map-marker-alt" style="color:#ef4444;margin-top:2px;font-size:0.8rem;"></i><div style="font-size:0.82rem;color:#374151;">${b.pickup_location}</div></div>` : ''}
                    ${b.destination ? `<div style="padding-top:8px;border-top:1px dashed #e2e8f0;margin-top:8px;display:flex;align-items:flex-start;gap:6px;"><i class="fas fa-location-arrow" style="color:#2563eb;margin-top:2px;font-size:0.8rem;"></i><div style="font-size:0.82rem;color:#374151;"><b>Destination:</b> ${b.destination}</div></div>` : ''}
                    ${b.rental_purpose ? `<div style="padding-top:6px;display:flex;align-items:flex-start;gap:6px;"><i class="fas fa-bullseye" style="color:#8b5cf6;margin-top:2px;font-size:0.8rem;"></i><div style="font-size:0.82rem;color:#374151;"><b>Purpose:</b> ${b.rental_purpose}</div></div>` : ''}
                </div>
                <div style="background:#f8fafc;border-radius:12px;padding:14px;margin-bottom:14px;border:1px solid #e2e8f0;">
                    <div style="font-size:0.65rem;color:#94a3b8;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:12px;display:flex;align-items:center;gap:5px;"><i class="fas fa-receipt" style="color:#00B14F;"></i>Price Breakdown</div>
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f1f5f9;"><span style="font-size:0.82rem;color:#374151;">Base Rental</span><span style="font-size:0.82rem;font-weight:600;color:#374151;">${fmtMoney(b.base_price)}</span></div>
                    ${addonRows}
                    ${parseFloat(b.insurance_price||0)>0 ? `<div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f1f5f9;"><span style="font-size:0.82rem;color:#374151;">Insurance${b.insurance_type ? ' ('+b.insurance_type+')' : ''}</span><span style="font-size:0.82rem;font-weight:600;color:#374151;">${fmtMoney(b.insurance_price)}</span></div>` : ''}
                    ${b.rental_type === 'With Driver' || parseFloat(b.driver_fee||0)>0 ? `<div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f1f5f9;"><span style="font-size:0.82rem;color:#374151;"><i class="fas fa-user-tie" style="color:#2563eb;margin-right:4px;"></i>Professional Driver</span><span style="font-size:0.82rem;font-weight:600;color:#374151;">${fmtMoney(b.driver_fee || 755)}</span></div>` : ''}
                    ${parseFloat(b.driver_ot_hours||0)>0 ? `<div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f1f5f9;"><span style="font-size:0.82rem;color:#d97706;"><i class="fas fa-business-time" style="margin-right:4px;"></i>Driver OT (${b.driver_ot_hours} hrs @ ₱${parseFloat(b.driver_ot_rate)||95}/hr) <small>(${b.driver_ot_collection_method === 'company_charge' ? 'Charged' : 'Direct Cash'})</small></span><span style="font-size:0.82rem;font-weight:600;color:#d97706;">+${fmtMoney(b.driver_ot_amount || (parseFloat(b.driver_ot_hours)*(parseFloat(b.driver_ot_rate)||95)))}</span></div>` : ''}
                    ${parseFloat(b.discount_amount||0)>0 ? `<div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f1f5f9;"><span style="font-size:0.82rem;color:#16a34a;"><i class="fas fa-tag" style="margin-right:4px;"></i>Discount</span><span style="font-size:0.82rem;font-weight:600;color:#16a34a;">-${fmtMoney(b.discount_amount)}</span></div>` : ''}

                    ${parseFloat(b.payment_fee||0)>0 ? `<div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f1f5f9;"><span style="font-size:0.82rem;color:#d97706;"><i class="fas fa-percentage" style="margin-right:4px;"></i>${b.payment_method || 'Payment'} Fee (${b.payment_fee_percent || 3.5}%)</span><span style="font-size:0.82rem;font-weight:600;color:#d97706;">+${fmtMoney(b.payment_fee)}</span></div>` : ''}

                    ${parseFloat(b.penalty_amount||0)>0 ? `<div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f1f5f9;"><span style="font-size:0.82rem;color:#ef4444;"><i class="fas fa-exclamation-triangle" style="margin-right:4px;"></i>Penalties</span><span style="font-size:0.82rem;font-weight:600;color:#ef4444;">${fmtMoney(b.penalty_amount)}</span></div>` : ''}

                    <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0 0;"><span style="font-size:0.92rem;font-weight:800;color:#0f172a;">TOTAL</span><span style="font-size:1.1rem;font-weight:900;color:#00B14F;">${fmtMoney(b.total_price)}</span></div>
                </div>
                <div style="background:#f8fafc;border-radius:12px;padding:14px;margin-bottom:${actionBtns ? '14px' : '0'};border:1px solid #e2e8f0;">
                    <div style="font-size:0.65rem;color:#94a3b8;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;">
                        <span style="display:flex;align-items:center;gap:5px;"><i class="fas fa-credit-card" style="color:#3b82f6;"></i>Payment &amp; Official Receipt</span>
                        <span style="font-size:0.68rem;color:#00B14F;font-weight:800;background:#f0fdf4;padding:2px 8px;border-radius:6px;border:1px solid #bbf7d0;">RECEIPT #${String(b.id).padStart(6,'0')}</span>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;">
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Method</div><div style="font-size:0.85rem;font-weight:700;color:#0f172a;">${b.payment_method||'N/A'}</div></div>
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Status</div><div style="font-size:0.82rem;font-weight:700;color:${['paid','fully paid'].includes((b.payment_status||'').toLowerCase().trim())?'#16a34a':b.payment_status==='Refund Pending'?'#d97706':b.payment_status==='Partially Paid'?'#2563eb':'#374151'};">${b.payment_status||'N/A'}</div></div>
                    </div>
                    ${parseFloat(b.amount_paid||0)>0 ? `<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;"><div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Amount Paid</div><div style="font-size:0.85rem;font-weight:700;color:#16a34a;">${fmtMoney(b.amount_paid)}</div></div>${parseFloat(b.balance_amount||0)>0?`<div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Balance Due</div><div style="font-size:0.85rem;font-weight:700;color:#ef4444;">${fmtMoney(b.balance_amount)}</div></div>`:`<div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Date Issued</div><div style="font-size:0.78rem;font-weight:700;color:#0f172a;">${b.created_at ? new Date(b.created_at).toLocaleString('en-PH', {timeZone:'Asia/Manila', month:'short', day:'numeric', year:'numeric', hour:'numeric', minute:'2-digit'}) : fmtDate(b.start_date)}</div></div>`}</div>` : ''}
                    ${b.reference_number ? `<div style="padding-top:8px;border-top:1px solid #f1f5f9;"><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:3px;">Reference #</div><div style="font-size:0.78rem;font-weight:600;color:#0f172a;word-break:break-all;background:#fff;padding:6px 8px;border-radius:6px;border:1px solid #e2e8f0;font-family:monospace;">${b.reference_number}</div></div>` : ''}
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px;padding-top:10px;border-top:1px dashed #cbd5e1;">
                        <button type="button" onclick="Inspections.showReceiptModal(${b.id})" style="background:#0f172a;color:#ffffff;border:none;padding:9px 10px;border-radius:8px;font-size:0.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;gap:6px;cursor:pointer;"><i class="fas fa-receipt" style="color:#00B14F;"></i>View Receipt</button>
                        <button type="button" onclick="window.open(API_URL + '/bookings/${b.id}/receipt', '_blank')" style="background:#00B14F;color:#ffffff;border:none;padding:9px 10px;border-radius:8px;font-size:0.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;gap:6px;cursor:pointer;"><i class="fas fa-file-pdf"></i>Download PDF</button>
                    </div>
                </div>

                <div style="background:#fff5f5;border-radius:12px;padding:14px;margin-bottom:14px;border:1px solid #feb2b2;">
                    <div style="font-size:0.65rem;color:#c53030;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:12px;display:flex;align-items:center;gap:5px;"><i class="fas fa-gavel" style="color:#ef4444;"></i>Penalties & Damage Charges</div>
                    <div id="bookingPenaltiesContainer_${b.id}">Loading penalties...</div>
                    <div style="margin-top:10px;padding-top:10px;border-top:1px dashed #feb2b2;">
                        <button onclick="Bookings.toggleAddPenaltyForm(${b.id}, true)" style="background:#ef4444;color:white;border:none;width:100%;padding:8px;font-size:0.75rem;border-radius:8px;font-weight:700;display:flex;align-items:center;justify-content:center;gap:5px;cursor:pointer;"><i class="fas fa-plus"></i>Add Penalty Charge</button>
                        <div id="addPenaltyForm_${b.id}" style="display:none;flex-direction:column;gap:8px;margin-top:10px;">
                            <select id="penaltyType_${b.id}" style="width:100%;padding:6px;border-radius:6px;border:1px solid #feb2b2;font-size:0.78rem;color:#0f172a !important;background:#ffffff !important;">
                                <option value="late_return">Late Return</option>
                                <option value="damage">Vehicle Damage</option>
                                <option value="excess_mileage">Excess Mileage</option>
                                <option value="other">Other Charge</option>
                            </select>
                            <input type="number" id="penaltyAmount_${b.id}" min="0" max="100000" placeholder="Amount (PHP)" style="width:100%;padding:6px;border-radius:6px;border:1px solid #feb2b2;font-size:0.78rem;box-sizing:border-box;color:#0f172a !important;background:#ffffff !important;">
                            <textarea id="penaltyNotes_${b.id}" maxlength="250" placeholder="Reason/Details" style="width:100%;padding:6px;border-radius:6px;border:1px solid #feb2b2;font-size:0.78rem;box-sizing:border-box;font-family:inherit;color:#0f172a !important;background:#ffffff !important;"></textarea>
                            <div style="display:flex;gap:6px;">
                                <button onclick="Bookings.submitPenalty(${b.id})" style="flex:1;padding:6px;background:#10b981;color:white;border:none;border-radius:6px;font-size:0.75rem;font-weight:700;cursor:pointer;">Save</button>
                                <button onclick="Bookings.toggleAddPenaltyForm(${b.id}, false)" style="flex:1;padding:6px;background:#94a3b8;color:white;border:none;border-radius:6px;font-size:0.75rem;font-weight:700;cursor:pointer;">Cancel</button>
                            </div>
                        </div>
                    </div>
                </div>

                ${b.payment_status === 'Refund Pending' ? `
                <div style="background:#fffbeb;border-radius:12px;padding:14px;margin-bottom:14px;border:1.5px solid #fde68a;">
                    <div style="font-size:0.65rem;color:#d97706;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;display:flex;align-items:center;gap:5px;">
                        <i class="fas fa-clock"></i> Refund Pending &#8212; Action Required
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;">
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Refund Amount</div><div style="font-size:0.95rem;font-weight:800;color:#d97706;">${fmtMoney(b.refund_amount)}</div></div>
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Channel</div><div style="font-size:0.88rem;font-weight:700;color:#0f172a;">${b.refund_channel || '&#8212;'}</div></div>
                    </div>
                    ${b.refund_account_name ? `
                    <div style="background:#fff;border-radius:8px;padding:10px;border:1px solid #fde68a;margin-bottom:10px;">
                        <div style="font-size:0.72rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:6px;">Customer Refund Account</div>
                        <div style="font-size:0.88rem;font-weight:700;color:#0f172a;margin-bottom:2px;">${b.refund_account_name}</div>
                        <div style="font-size:0.85rem;color:#374151;font-weight:600;">${b.refund_account_number || ''}</div>
                    </div>
                    <div style="background:#fff;border-radius:8px;padding:10px;border:1px solid #fde68a;margin-bottom:10px;">
                        <div style="font-size:0.72rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:8px;">Step 1 &#8212; Upload Transfer Proof</div>
                        <input type="file" id="refundProofFile_${b.id}" accept="image/*" onchange="Bookings._onProofSelected(${b.id}, this)"
                            style="display:none;">
                        <button onclick="document.getElementById('refundProofFile_${b.id}').click()"
                            style="width:100%;padding:9px;background:#f8fafc;border:1.5px dashed #94a3b8;border-radius:8px;color:#374151;font-size:0.8rem;font-weight:600;cursor:pointer;margin-bottom:6px;">
                            <i class="fas fa-upload" style="margin-right:6px;color:#d97706;"></i><span id="refundProofLabel_${b.id}">Choose proof image</span>
                        </button>
                        <div style="font-size:0.72rem;color:#94a3b8;margin-bottom:8px;">Step 2 &#8212; Reference / Transaction No. (optional)</div>
                        <input type="text" id="refundRefInput_${b.id}" maxlength="50" placeholder="e.g. TXN123456789"
                            style="width:100%;padding:8px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:0.82rem;color:#0f172a;background:#f8fafc;box-sizing:border-box;margin-bottom:10px;">
                        <button id="markRefundedBtn_${b.id}" onclick="Bookings.markRefunded(${b.id})" disabled
                            style="width:100%;padding:10px;background:#d1d5db;border:none;border-radius:10px;color:#fff;font-size:0.82rem;font-weight:700;cursor:not-allowed;">
                            <i class="fas fa-check-circle" style="margin-right:6px;"></i>Mark as Refunded
                        </button>
                    </div>` : `
                    <div style="font-size:0.78rem;color:#92400e;padding:8px;background:#fef3c7;border-radius:8px;">
                        <i class="fas fa-exclamation-circle" style="margin-right:4px;"></i>Customer has not yet submitted refund account details.
                    </div>`}
                </div>` : ''}
                ${actionBtns ? `<div style="display:flex;gap:8px;flex-wrap:wrap;">${actionBtns}</div>` : ''}
            </div>`;

            const modal = document.getElementById('bookingDetailsModal');
            modal.style.display = 'flex';
            if (typeof modalOpen === 'function') modalOpen();
            setTimeout(() => { Bookings.loadPenalties(b.id); }, 50);
        },
        async triggerRefund(id) {
            const b = (this.data && this.data.find(x => x.id == id || x.booking_id == id)) 
                 || (typeof FleetCalendar !== 'undefined' && FleetCalendar.bookings && FleetCalendar.bookings.find(x => x.id == id || x.booking_id == id)) 
                 || (typeof PastBookings !== "undefined" && PastBookings.data && PastBookings.data.find(x => x.id == id || x.booking_id == id)) 
                 || (typeof ArchivedBookings !== "undefined" && ArchivedBookings.data && ArchivedBookings.data.find(x => x.id == id || x.booking_id == id))
                 || this.currentBooking;
            const ps = b ? b.payment_status : 'Paid';
            if (!confirm(`Trigger refund for Booking #${id}?\n\nThis will calculate the refund based on cancellation time vs pickup date (cancellation policy).\n\nCurrent status: ${ps}`)) return;
            try {
                const res = await fetch(`${API_BASE}/api/bookings/${id}/trigger-refund`, { method: 'POST', headers: {'Content-Type':'application/json'} });
                const data = await res.json();
                if (res.ok) {
                    alert(`Refund triggered!\nRefund: ${data.refund_amount}\nNon-refundable: ${data.non_refundable_fee||0}\nHours before pickup: ${data.hours_before_pickup}h\nCancelled: ${data.cancellation_time}\nPickup was: ${data.pickup_time}`);
                    document.getElementById('bookingDetailsModal').style.display = 'none';
                    if (typeof modalClose === 'function') modalClose();
                    this.refresh();
                } else {
                    alert(data.error || 'Failed to trigger refund');
                }
            } catch(e) {
                alert('Connection error');
            }
        },


        _onProofSelected(bookingId, input) {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                const isImg = (file.type || "").toLowerCase().startsWith("image/") || /\.(jpe?g|png|webp|gif|heic)$/i.test(file.name || "");
                if (!isImg) {
                    showNotification("Only image files are allowed for transfer proof.", "error");
                    input.value = "";
                    return;
                }
                if (file.size > 5 * 1024 * 1024) {
                    showNotification("Transfer proof must be 5 MB or smaller.", "error");
                    input.value = "";
                    return;
                }
                const label = document.getElementById('refundProofLabel_' + bookingId);
                if (label) label.textContent = input.files[0].name;
                const btn = document.getElementById('markRefundedBtn_' + bookingId);
                if (btn) {
                    btn.disabled = false;
                    btn.style.background = '#00B14F';
                    btn.style.cursor = 'pointer';
                }
            }
        },

        async markRefunded(bookingId) {
            const proofInput = document.getElementById('refundProofFile_' + bookingId);
            const refInput = document.getElementById('refundRefInput_' + bookingId);
            if (!proofInput || !proofInput.files.length) {
                showNotification('Please upload transfer proof first.', 'error');
                return;
            }
            const user = adminAuth.getUser();
            const fd = new FormData();
            fd.append('booking_id', bookingId);
            fd.append('admin_id', user ? user.id : 1);
            fd.append('proof', proofInput.files[0]);
            if (refInput && refInput.value.trim()) fd.append('refund_ref', refInput.value.trim());
            const btn = document.getElementById('markRefundedBtn_' + bookingId);
            if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...'; }
            try {
                const res = await fetch(`${API_BASE}/api/admin/upload-refund-proof`, { method: 'POST', body: fd });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed');
                showNotification('Refund marked as completed! Customer has been notified.', 'success');
                document.getElementById('bookingDetailsModal').style.display = 'none';
                if (typeof modalClose === 'function') modalClose();
                this.refresh();
            } catch (e) {
                showNotification(e.message, 'error');
                if (btn) { btn.disabled = false; btn.style.background = '#00B14F'; btn.innerHTML = '<i class="fas fa-check-circle" style="margin-right:6px;"></i>Mark as Refunded'; }
            }
        },


        _onProofSelected(bookingId, input) {
            if (!input.files || !input.files[0]) return;
            const label = document.getElementById('refundProofLabel_' + bookingId);
            if (label) label.textContent = input.files[0].name;
            const btn = document.getElementById('markRefundedBtn_' + bookingId);
            if (btn) {
                btn.disabled = false;
                btn.style.background = '#10b981';
                btn.style.cursor = 'pointer';
            }
        },

        
        async loadPenalties(bookingId) {
            const container = document.getElementById(`bookingPenaltiesContainer_${bookingId}`);
            if (!container) return;
            try {
                const res = await fetch(`${API_BASE}/api/admin/bookings/${bookingId}/penalties`);
                const penalties = await res.json();
                if (!res.ok || !Array.isArray(penalties)) {
                    container.innerHTML = '<div style="font-size:0.75rem;color:#64748b;text-align:center;padding:5px 0;">No penalties added.</div>';
                    return;
                }
                let html = "";
                penalties.forEach(p => {
                    const typeKey = p.charge_type || p.penalty_type || 'other';
                    const label = {
                        'late_return': 'Late Return',
                        'damage': 'Damage',
                        'excess_mileage': 'Excess Mileage',
                        'other': 'Other'
                    }[typeKey] || typeKey;
                    
                    const notesText = p.notes || p.description || '';
                    
                    html += `
                        <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px dashed #fcd34d;">
                            <div>
                                <span style="font-weight:700;font-size:0.78rem;color:#374151;">${label}</span>
                                ${notesText ? `<br><span style="font-size:0.68rem;color:#64748b;">${notesText}</span>` : ''}
                            </div>
                            <div style="display:flex;align-items:center;gap:6px;">
                                <span style="font-weight:700;font-size:0.78rem;color:#ef4444;">₱${parseFloat(p.amount || 0).toLocaleString('en-PH',{minimumFractionDigits:2,maximumFractionDigits:2})}</span>
                                <button onclick="Bookings.promptEditPenalty(${bookingId}, ${p.id}, ${parseFloat(p.amount||0)}, '${(notesText).replace(/'/g, "\\'")}', '${typeKey}')" title="Edit / Waive Penalty" style="background:none;border:none;color:#f59e0b;cursor:pointer;padding:2px;margin-right:4px;"><i class="fas fa-edit" style="font-size:0.75rem;"></i></button>
                                <button onclick="Bookings.deletePenalty(${bookingId}, ${p.id})" title="Delete Penalty" style="background:none;border:none;color:#ef4444;cursor:pointer;padding:2px;"><i class="fas fa-trash-alt" style="font-size:0.75rem;"></i></button>
                            </div>
                        </div>`;
                });
                if (penalties.length === 0) {
                    html = '<div style="font-size:0.75rem;color:#64748b;text-align:center;padding:5px 0;">No penalties added.</div>';
                }
                container.innerHTML = html;
            } catch(e) {
                container.innerHTML = '<div style="font-size:0.75rem;color:#64748b;text-align:center;padding:5px 0;">No penalties added.</div>';
            }
        },
        
        toggleAddPenaltyForm(bookingId, show) {
            const form = document.getElementById(`addPenaltyForm_${bookingId}`);
            if (form) form.style.display = show ? 'flex' : 'none';
        },
        
        async submitPenalty(bookingId) {
            const charge_type = document.getElementById(`penaltyType_${bookingId}`).value;
            const amount = parseFloat(document.getElementById(`penaltyAmount_${bookingId}`).value || 0);
            const notes = document.getElementById(`penaltyNotes_${bookingId}`).value;
            
            if (amount <= 0) {
                showNotification("Please enter a valid amount", "error");
                return;
            }
            
            try {
                const res = await fetch(`${API_BASE}/api/admin/bookings/${bookingId}/penalties`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ charge_type, amount, notes })
                });
                const data = await res.json();
                if (res.ok) {
                    showNotification("Penalty charge added successfully", "success");
                    this.loadPenalties(bookingId);
                    this.toggleAddPenaltyForm(bookingId, false);
                    document.getElementById(`penaltyAmount_${bookingId}`).value = "";
                    document.getElementById(`penaltyNotes_${bookingId}`).value = "";
                    
                    // Refresh parent booking detail view
                    this.refresh();
                    setTimeout(() => { this.view(bookingId); }, 200);
                } else {
                    showNotification(data.error || "Failed to add penalty", "error");
                }
            } catch(e) {
                showNotification("Connection error", "error");
            }
        },
        
        async deletePenalty(bookingId, penaltyId) {
            if (!confirm("Are you sure you want to delete this penalty charge?")) return;
            try {
                const res = await fetch(`${API_BASE}/api/admin/penalties/${penaltyId}`, { method: 'DELETE' });
                if (res.ok) {
                    showNotification("Penalty deleted", "success");
                    this.loadPenalties(bookingId);
                    
                    // Refresh parent booking detail view
                    this.refresh();
                    setTimeout(() => { this.view(bookingId); }, 200);
                } else {
                    showNotification("Failed to delete penalty", "error");
                }
            } catch(e) {
                showNotification("Connection error", "error");
            }
        },

        getPillClass(s) {



            const status = s?.toLowerCase();



            if (status === 'confirmed') return 'confirmed';



            if (status === 'pending') return 'pending';



            if (status === 'cancelled' || status === 'rejected') return 'cancelled';



            if (status === 'ongoing' || status === 'picked up') return 'success';



            return '';



        },







        async markPaid(id) {
            if (typeof anime !== 'undefined') {
                const btn = (window.event && (window.event.currentTarget || window.event.target));
                if (btn) anime({ targets: btn, scale: [1, 0.92, 1], duration: 250, easing: 'easeOutBack' });
            }
            const b = (this.data || []).find(x => x.id == id);
            if (!b) return;

            if (b && b.start_date) {
                try {
                    const dStr = String(b.start_date).split('T')[0];
                    const [pYr, pMo, pDay] = dStr.split('-').map(Number);
                    const pickupDate = new Date(pYr, pMo - 1, pDay);
                    pickupDate.setHours(0,0,0,0);
                    const today = new Date();
                    today.setHours(0,0,0,0);

                    if (today < pickupDate) {
                        const dateFormatted = pickupDate.toLocaleDateString('en-PH', {month:'short', day:'numeric', year:'numeric'});
                        showNotification(`🚫 Cannot Mark as Fully Paid before pickup date (${dateFormatted}). Remaining balance must be collected when customer physically arrives at counter.`, 'error');
                        return;
                    }
                } catch(e) {}
            }

            const total = parseFloat(b.total_price || 0);
            const paid = parseFloat(b.amount_paid || 0);
            const balance = Math.max(0, total - paid);
            const custName = b.full_name || b.client_name || b.customer_name || 'Customer';

            // Get card terminal fee setting (default 3.5%)
            let cardFeePct = 3.5;
            try {
                if (typeof Settings !== 'undefined' && Settings._allData) {
                    const found = Settings._allData.find(s => s.key === 'payment_fee_card_percent');
                    if (found && found.value) cardFeePct = parseFloat(found.value) || 3.5;
                }
            } catch(e) {}

            const body = document.getElementById('markPaidModalBody');
            if (!body) return;

            window._currentMarkPaidBooking = { id: id, balance: balance, cardFeePct: cardFeePct, baseTotal: total };

            body.innerHTML = `
                <div style="background:#f8fafc;padding:12px;border-radius:12px;border:1px solid #e2e8f0;margin-bottom:14px;font-size:0.85rem;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                        <span style="color:#64748b;">Booking:</span>
                        <strong style="color:#0f172a;">#${b.id} - ${b.car || 'Vehicle'}</strong>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                        <span style="color:#64748b;">Customer:</span>
                        <strong style="color:#0f172a;">${custName}</strong>
                    </div>
                    <div style="display:flex;justify-content:space-between;">
                        <span style="color:#64748b;">Current Balance:</span>
                        <strong style="color:#ef4444;font-size:0.95rem;">${fmtMoney(balance)}</strong>
                    </div>
                </div>

                <div style="margin-bottom:14px;">
                    <label style="font-size:0.75rem;font-weight:800;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;display:block;margin-bottom:6px;">Select Payment Method</label>
                    <div style="display:grid;grid-template-columns:1fr;gap:8px;">
                        <label style="display:flex;align-items:center;gap:10px;padding:10px 12px;border:1.5px solid #00B14F;border-radius:10px;background:rgba(0,177,79,0.05);cursor:pointer;" id="labelMethod_cash">
                            <input type="radio" name="markPaidMethod" value="Cash (Over the counter)" checked onchange="Bookings.updateMarkPaidCalc()" style="accent-color:#00B14F;">
                            <div style="flex:1;">
                                <div style="font-weight:700;font-size:0.85rem;color:#0f172a;">💵 Cash (Over the counter)</div>
                                <div style="font-size:0.7rem;color:#64748b;">Standard counter settlement (0% fee)</div>
                            </div>
                        </label>

                        <label style="display:flex;align-items:center;gap:10px;padding:10px 12px;border:1.5px solid #e2e8f0;border-radius:10px;background:#ffffff;cursor:pointer;" id="labelMethod_card">
                            <input type="radio" name="markPaidMethod" value="Card Terminal" onchange="Bookings.updateMarkPaidCalc()" style="accent-color:#00B14F;">
                            <div style="flex:1;">
                                <div style="font-weight:700;font-size:0.85rem;color:#0f172a;">💳 Card Terminal / POS Terminal</div>
                                <div style="font-size:0.7rem;color:#64748b;">Includes <b>${cardFeePct}%</b> card terminal fee</div>
                            </div>
                        </label>

                        <label style="display:flex;align-items:center;gap:10px;padding:10px 12px;border:1.5px solid #e2e8f0;border-radius:10px;background:#ffffff;cursor:pointer;" id="labelMethod_online">
                            <input type="radio" name="markPaidMethod" value="GCash / Maya (Counter QR)" onchange="Bookings.updateMarkPaidCalc()" style="accent-color:#00B14F;">
                            <div style="flex:1;">
                                <div style="font-weight:700;font-size:0.85rem;color:#0f172a;">📱 E-Wallet / Counter QR</div>
                                <div style="font-size:0.7rem;color:#64748b;">GCash or Maya QR settlement (0% fee)</div>
                            </div>
                        </label>
                    </div>
                </div>

                <div style="background:#f1f5f9;padding:12px;border-radius:12px;margin-bottom:16px;font-size:0.85rem;" id="markPaidCalcContainer">
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                        <span style="color:#475569;">Remaining Balance:</span>
                        <span style="font-weight:600;color:#0f172a;">${fmtMoney(balance)}</span>
                    </div>
                    <div id="markPaidFeeRow" style="display:none;justify-content:space-between;margin-bottom:4px;color:#d97706;">
                        <span>Card Terminal Fee (${cardFeePct}%):</span>
                        <span id="markPaidFeeAmount" style="font-weight:700;">+₱0.00</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding-top:8px;border-top:1px solid #cbd5e1;font-weight:800;font-size:1rem;color:#0f172a;">
                        <span>Total Amount to Collect:</span>
                        <span id="markPaidTotalCollect" style="color:#10b981;font-weight:900;">${fmtMoney(balance)}</span>
                    </div>
                </div>

                <div style="display:flex;gap:10px;">
                    <button onclick="Bookings.submitMarkPaid()" class="btn-premium" style="flex:1;padding:12px;background:#10b981;color:white;border:none;border-radius:10px;font-weight:800;font-size:0.85rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;">
                        <i class="fas fa-check-circle"></i> Confirm & Mark Paid
                    </button>
                    <button onclick="document.getElementById('bookingMarkPaidModal').style.display='none';modalClose();" class="btn-outline" style="padding:12px 18px;border:1px solid #cbd5e1;background:white;color:#475569;border-radius:10px;font-weight:700;cursor:pointer;">
                        Cancel
                    </button>
                </div>
            `;

            const m = document.getElementById('bookingMarkPaidModal');
            m.style.display = 'flex';
            if (typeof modalOpen === 'function') modalOpen();
        },

        updateMarkPaidCalc() {
            const cur = window._currentMarkPaidBooking;
            if (!cur) return;
            const radios = document.querySelectorAll('input[name="markPaidMethod"]');
            let selectedMethod = 'Cash (Over the counter)';
            radios.forEach(r => { if (r.checked) selectedMethod = r.value; });

            const isCard = selectedMethod === 'Card Terminal';
            const fee = isCard ? Math.round(cur.balance * (cur.cardFeePct / 100) * 100) / 100 : 0;
            const total = cur.balance + fee;

            const feeRow = document.getElementById('markPaidFeeRow');
            const feeAmount = document.getElementById('markPaidFeeAmount');
            const totalCollect = document.getElementById('markPaidTotalCollect');

            if (feeRow && feeAmount && totalCollect) {
                if (isCard) {
                    feeRow.style.display = 'flex';
                    feeAmount.textContent = '+' + fmtMoney(fee);
                } else {
                    feeRow.style.display = 'none';
                }
                totalCollect.textContent = fmtMoney(total);
            }
        },

        async submitMarkPaid() {
            const cur = window._currentMarkPaidBooking;
            if (!cur) return;

            const radios = document.querySelectorAll('input[name="markPaidMethod"]');
            let selectedMethod = 'Cash (Over the counter)';
            radios.forEach(r => { if (r.checked) selectedMethod = r.value; });

            const isCard = selectedMethod === 'Card Terminal';
            const fee = isCard ? Math.round(cur.balance * (cur.cardFeePct / 100) * 100) / 100 : 0;
            const feePct = isCard ? cur.cardFeePct : 0;

            try {
                const res = await fetch(`${API_BASE}/api/admin/bookings/${cur.id}/mark-paid`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        payment_method: selectedMethod,
                        payment_fee: fee,
                        payment_fee_percent: feePct
                    })
                });
                const data = await res.json();
                if (res.ok) {
                    showNotification('Booking marked as Fully Paid!', 'success');
                    document.getElementById('bookingMarkPaidModal').style.display = 'none';
                    document.getElementById('bookingDetailsModal').style.display = 'none';
                    if (typeof modalClose === 'function') modalClose();
                    this.refresh();
                } else {
                    showNotification(data.error || 'Failed to record payment', 'error');
                }
            } catch(err) {
                showNotification('Network error recording payment', 'error');
            }
        },







        // Returns the Date object for scheduled pickup datetime
        getPickupDateTime(b) {
            if (!b || !b.start_date) return null;
            const dStr = String(b.start_date).split('T')[0];
            const parts = dStr.split('-').map(Number);
            if (parts.length < 3 || isNaN(parts[0])) return null;
            let pt = String(b.start_time || b.pickup_time || '06:00').trim().toLowerCase();
            const isPM = pt.includes('pm');
            const isAM = pt.includes('am');
            pt = pt.replace(/[apm\s]/g, '');
            const timeParts = pt.split(':').map(Number);
            let h = isNaN(timeParts[0]) ? 6 : timeParts[0];
            let m = isNaN(timeParts[1]) ? 0 : timeParts[1];
            if (isPM && h < 12) h += 12;
            if (isAM && h === 12) h = 0;
            return new Date(parts[0], parts[1] - 1, parts[2], h, m, 0);
        },

        // Returns true if pickup inspection is ready (1 hour before scheduled pickup or at/after pickup time)
        isPickupInspectReady(b) {
            const dt = this.getPickupDateTime(b);
            if (!dt) return false;
            const allowFrom = new Date(dt.getTime() - 60 * 60 * 1000);
            return new Date() >= allowFrom;
        },

        // Returns true if the booking's pickup datetime has already passed (for No Show)
        isPickupPast(b) {
            const dt = this.getPickupDateTime(b);
            if (!dt) return false;
            return new Date() >= dt;
        },

        getPickupInspectAction(b) {
            const ps = (b && b.payment_status ? String(b.payment_status).trim().toLowerCase() : '');
            const bal = parseFloat((b && b.balance_amount) || 0);
            const amtPaid = parseFloat((b && b.amount_paid) || 0);
            const tot = parseFloat((b && b.total_price) || 0);
            const isPaid = ['paid', 'fully paid', 'fully-paid', 'completed'].includes(ps) ||
                           (amtPaid >= tot && tot > 0) ||
                           (bal <= 0 && amtPaid > 0);
            const isReady = this.isPickupInspectReady(b);
            const pDt = this.getPickupDateTime(b);
            const allowFrom = pDt ? new Date(pDt.getTime() - 60 * 60 * 1000) : null;
            const fmtAllow = allowFrom ? allowFrom.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
            const fmtPickup = pDt ? pDt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : (b.start_time || '06:00');

            if (!isPaid) {
                return {
                    active: false,
                    onClick: `showNotification('Booking must be fully paid before starting inspection', 'error')`
                };
            }
            if (!isReady) {
                return {
                    active: false,
                    onClick: `showNotification('Pickup inspection cannot be started yet. Scheduled pickup is at ${fmtPickup}${fmtAllow ? ` (available starting at ${fmtAllow})` : ''}.', 'warning')`
                };
            }
            return {
                active: true,
                onClick: `Inspections.openModal(${b.id}, 'pickup')`
            };
        },

        async markNoShow(bookingId) {
            if (!confirm('Mark this booking as No Show?\n\n⚠️ If the booking is PAID, the payment will be forfeited (0% refund).\nIf UNPAID, the booking will simply be cancelled.\n\nThis action cannot be undone.')) return;
            try {
                const user = adminAuth.getUser();
                if (!user || user.role !== 'super_admin') {
                    showNotification('Unauthorized', 'error');
                    return;
                }
                const res = await fetch(`${API_BASE}/admin/bookings/${bookingId}/mark-no-show`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ admin_id: user.id })
                });
                const data = await res.json();
                if (!res.ok) {
                    showNotification(data.error || 'Failed to mark No Show', 'error');
                    return;
                }
                showNotification('Booking marked as No Show.', 'success');
                document.getElementById('bookingDetailsModal').style.display = 'none'; modalClose();
                this.refresh();
            } catch (err) { showNotification('Network error', 'error'); }
        },

        async cancel(id) {
        if (typeof anime !== 'undefined') {
            const btn = (window.event && (window.event.currentTarget || window.event.target));
            if (btn) anime({ targets: btn, scale: [1, 0.92, 1], duration: 250, easing: 'easeOutBack' });
        }
        const reason = prompt('Enter cancellation reason (optional):') || 'Cancelled by admin';



            try {



                const res = await fetch(`${API_URL}/bookings/${id}/cancel`, {



                    method: 'PUT',



                    headers: { 'Content-Type': 'application/json' },



                    body: JSON.stringify({ reason: reason })



                });



                if (res.ok) {



                    showNotification('Booking Cancelled!', 'success');



                    document.getElementById('bookingDetailsModal').style.display = 'none'; modalClose();



                    this.refresh();



                } else {



                    const data = await res.json();



                    showNotification(data.error || 'Failed to cancel', 'error');



                }



            } catch (err) { showNotification('Network error', 'error'); }



        },







        async approve(id) {
        if (typeof anime !== 'undefined') {
            const btn = (window.event && (window.event.currentTarget || window.event.target));
            if (btn) anime({ targets: btn, scale: [1, 0.92, 1], duration: 250, easing: 'easeOutBack' });
        }
        if (!confirm('Approve this booking?')) return;



            showAdminBlockingUI(true);
            try {



                const res = await fetch(`${API_URL}/bookings/${id}/approve`, { method: 'PUT' });



                if (res.ok) {



                    showNotification('Booking Approved!', 'success');



                    document.getElementById('bookingDetailsModal').style.display = 'none'; modalClose();



                    this.refresh();



                } else {



                    const data = await res.json();



                    showNotification(data.error || 'Failed to approve', 'error');



                }



            } catch (err) {
                showAdminBlockingUI(false); showNotification('Network error', 'error'); }



        },







        async markCashReceived(id) {



            if (!confirm('Confirm cash payment received for this booking?\n\nThis will confirm the booking and mark it as paid.')) return;



            try {



                const res = await fetch(`${API_URL}/bookings/${id}/approve`, { method: 'PUT' });



                if (res.ok) {



                    showNotification('Cash received! Booking confirmed.', 'success');



                    document.getElementById('bookingDetailsModal').style.display = 'none'; modalClose();



                    this.refresh();



                } else {



                    const data = await res.json();



                    showNotification(data.error || 'Failed to confirm', 'error');



                }



            } catch (err) { showNotification('Network error', 'error'); }



        },







        async reject(id) {
        if (typeof anime !== 'undefined') {
            const btn = (window.event && (window.event.currentTarget || window.event.target));
            if (btn) anime({ targets: btn, scale: [1, 0.92, 1], duration: 250, easing: 'easeOutBack' });
        }
        const reason = prompt('Enter rejection reason:');



            if (!reason) return;



            showAdminBlockingUI(true);
            try {



                const res = await fetch(`${API_URL}/bookings/${id}/reject`, {



                    method: 'PUT',



                    headers: { 'Content-Type': 'application/json' },



                    body: JSON.stringify({ reason: reason })



                });



                if (res.ok) {



                    showNotification('Booking Rejected!', 'success');



                    document.getElementById('bookingDetailsModal').style.display = 'none'; modalClose();



                    this.refresh();



                } else {



                    const data = await res.json();



                    showNotification(data.error || 'Failed to reject', 'error');



                }



            } catch (err) {
                showAdminBlockingUI(false); showNotification('Network error', 'error'); }



        },







        async pickup(id) {
            const b = (this.data && this.data.find(x => x.id == id)) || (this.currentBooking);
            let collectCash = false;
            let overrideUnpaid = false;

            if (b && !['paid', 'fully paid'].includes((b.payment_status || '').toLowerCase().trim()) && parseFloat(b.balance_amount || b.total_price || 0) > 0) {
                const bal = parseFloat(b.balance_amount || (b.total_price - (b.amount_paid || 0)));
                const ans = confirm(
                    `⚠️ PAYMENT REQUIRED BEFORE PICKUP\n\n` +
                    `Booking #${id} has an unsettled balance of PHP ${bal.toLocaleString('en-US', { minimumFractionDigits: 2 })}.\n\n` +
                    `Vehicles cannot be released without full payment.\n\n` +
                    `• Click "OK" if the customer is paying the remaining balance in CASH right now.\n` +
                    `• Click "Cancel" if payment is NOT yet collected.`
                );
                if (!ans) return;
                collectCash = true;
            } else {
                if (!confirm('Confirm vehicle has been picked up?')) return;
            }

            if (typeof showAdminBlockingUI === 'function') showAdminBlockingUI(true);
            try {
                const adminUser = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
                const adminId = adminUser ? adminUser.id : 0;
                const res = await fetch(`${API_URL}/bookings/${id}/pickup`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        admin_id: adminId,
                        collect_balance_cash: collectCash,
                        override_unpaid: overrideUnpaid
                    })
                });
                const resData = await res.json().catch(() => ({}));
                if (typeof showAdminBlockingUI === 'function') showAdminBlockingUI(false);

                if (res.ok) {
                    showNotification(collectCash ? 'Balance collected in cash & vehicle marked as Picked Up!' : 'Marked as Picked Up!', 'success');
                    const bdm = document.getElementById('bookingDetailsModal');
                    if (bdm) bdm.style.display = 'none';
                    if (typeof modalClose === 'function') modalClose();
                    this.refresh();
                } else {
                    showNotification(resData.error || 'Failed to mark vehicle as picked up', 'error');
                }
            } catch (err) {
                if (typeof showAdminBlockingUI === 'function') showAdminBlockingUI(false);
                showNotification('Network error: ' + err.message, 'error');
            }
        },

        async complete(id) {



            if (!confirm('Confirm vehicle has been returned?')) return;



            showAdminBlockingUI(true);
            try {



                const res = await fetch(`${API_URL}/bookings/${id}/complete`, { method: 'PUT' });



                if (res.ok) {



                    showNotification('Booking Completed!', 'success');



                    document.getElementById('bookingDetailsModal').style.display = 'none'; modalClose();



                    this.refresh();



                } else {



                    const data = await res.json();



                    showNotification(data.error || 'Failed', 'error');



                }



            } catch (err) {
                showAdminBlockingUI(false); showNotification('Network error', 'error'); }



        },














        async uploadRefundProof(bookingId) {



            const fileInput = document.getElementById('mRefundProofFile');



            if (!fileInput.files.length) {



                alert('Please select an image first');



                return;



            }







            const user = adminAuth.getUser();



            const formData = new FormData();



            formData.append('booking_id', bookingId);



            formData.append('admin_id', user ? user.id : 1);



            formData.append('proof', fileInput.files[0]);







            const btn = event.target;



            btn.disabled = true;



            btn.textContent = 'Uploading...';







            try {



                const res = await fetch(`${API_BASE}/api/admin/upload-refund-proof`, {



                    method: 'POST',



                    body: formData



                });



                const data = await res.json();



                if (!res.ok) throw new Error(data.error || 'Upload failed');







                showNotification('Refund proof uploaded!', 'success');



                this.refresh();



                this.view(bookingId);



            } catch (err) {



                alert(err.message);



            } finally {



                btn.disabled = false;



                btn.textContent = 'Submit Proof';



            }



        },







        async processRefund(bookingId, extensionId = null) {



            const user = adminAuth.getUser();



            const amount  = (document.getElementById(`rfAmount_${bookingId}`) || {}).value;



            const method  = (document.getElementById(`rfMethod_${bookingId}`) || {}).value || 'GCash';



            const ref     = (document.getElementById(`rfRef_${bookingId}`)    || {}).value || '';



            const note    = (document.getElementById(`rfNote_${bookingId}`)   || {}).value || '';



            const proofEl = document.getElementById(`rfProof_${bookingId}`);







            if (!amount || parseFloat(amount) <= 0) {



                showNotification('Please enter a valid refund amount.', 'error');



                return;



            }







            const btn = event.target;



            btn.disabled = true;



            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';







            try {



                const fd = new FormData();



                fd.append('booking_id', bookingId);



                fd.append('admin_id', user ? user.id : 1);



                fd.append('refund_amount', amount);



                fd.append('refund_method', method);



                fd.append('refund_ref', ref);



                fd.append('refund_note', note);



                if (extensionId) fd.append('extension_id', extensionId);



                if (proofEl && proofEl.files && proofEl.files[0]) {



                    fd.append('proof', proofEl.files[0]);



                }







                const res = await fetch(`${API_URL}/admin/process-refund`, { method: 'POST', body: fd });



                const data = await res.json();



                if (!res.ok) throw new Error(data.error || 'Refund failed');







                showNotification(`Refund of ?${parseFloat(amount).toLocaleString()} recorded. Customer notified.`, 'success');



                document.getElementById('bookingDetailsModal').style.display = 'none';



                modalClose();



                this.refresh();



                if (typeof Extensions !== 'undefined') Extensions.load();



            } catch (err) {



                showNotification(err.message, 'error');



                btn.disabled = false;



                btn.innerHTML = '<i class="fas fa-paper-plane" style="margin-right:6px;"></i>Confirm Refund Sent';



            }



        },







        async fetchInspections(bookingId) {



            const list = document.getElementById('mInspList');



            list.innerHTML = '<div style="font-size:0.7rem; opacity:0.5;">Loading...</div>';



            try {



                const res = await fetch(`${API_BASE}/api/inspections/${bookingId}`);



                const data = await res.json();



                this.renderInspections(data);



            } catch (err) {



                list.innerHTML = '<div style="font-size:0.7rem; color:var(--danger);">Error loading inspections.</div>';



            }



        },







        renderInspections(inspections) {



            const list = document.getElementById('mInspList');



            if (!inspections || inspections.length === 0) {



                list.innerHTML = '<div style="font-size:0.7rem; opacity:0.5;">No inspections yet.</div>';



                return;



            }







            list.innerHTML = inspections.map(insp => `



                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 10px; padding: 10px;">



                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">



                        <strong style="text-transform: uppercase; color: #60a5fa; font-size: 0.7rem;">${insp.type}</strong>



                        <span style="font-size: 0.6rem; opacity: 0.5;">${new Date(insp.created_at).toLocaleDateString()}</span>



                    </div>



                    <div style="display: flex; gap: 15px; font-size: 0.7rem; margin-bottom: 8px;">



                        <span>Mileage: <strong>${insp.mileage}km</strong></span>



                        <span>Fuel: <strong>${insp.fuel_level}</strong></span>



                    </div>



                    ${insp.photos && Array.isArray(insp.photos) ? `



                        <div style="display: flex; gap: 5px; overflow-x: auto; padding-bottom: 5px; margin-bottom: 5px;">



                            ${insp.photos.map(p => `<img src="${API_BASE}${p}" style="height: 45px; border-radius: 6px;" onclick="window.open('${API_BASE}${p}', '_blank')">`).join('')}



                        </div>



                    ` : ''}



                    ${insp.notes ? `<p style="font-size: 0.65rem; color: var(--text-muted); border-top: 1px solid rgba(255,255,255,0.05); padding-top: 5px; margin: 0;">${insp.notes}</p>` : ''}



                </div>



            `).join('');



        },







        async saveInspection(bookingId) {



            const user = adminAuth.getUser();



            const mileage = document.getElementById('mfInspMileage').value;



            const photoInput = document.getElementById('mfInspPhotos');







            if (!mileage) { alert('Enter mileage'); return; }







            const formData = new FormData();



            formData.append('booking_id', bookingId);



            formData.append('admin_id', (user && user.id) ? user.id : 1);



            formData.append('type', document.getElementById('mfInspType').value);



            formData.append('mileage', mileage);



            formData.append('fuel_level', document.getElementById('mfInspFuel').value);



            formData.append('notes', document.getElementById('mfInspNotes').value);







            if (photoInput.files.length > 0) {



                for (let i = 0; i < photoInput.files.length; i++) {



                    formData.append('photos', photoInput.files[i]);



                }



            }







            const saveBtn = document.getElementById('mBtnSaveInsp');



            saveBtn.disabled = true;



            saveBtn.textContent = 'Saving...';







            try {



                const res = await fetch(`${API_BASE}/api/inspections/submit`, {



                    method: 'POST',



                    body: formData



                });







                if (res.ok) {



                    showNotification('Inspection saved!', 'success');



                    this.fetchInspections(bookingId);



                } else {



                    alert('Failed to save inspection');



                }



            } catch (err) { alert('Error saving'); }



            finally {



                saveBtn.disabled = false;



                saveBtn.textContent = 'Save';



            }



        },



        async pickup(id) {



            if (!confirm('Mark this vehicle as picked up?')) return;



            try {



                const res = await apiFetch(`bookings/${id}/pickup`, { method: 'PUT' });



                if (res.ok) { showNotification('Vehicle picked up!', 'success'); this.refresh(); }



                else { showNotification('Failed: ' + res.status, 'error'); }



            } catch (err) { showNotification('Action failed: ' + err.message, 'error'); }



        },



        async complete(id) {



            if (!confirm('Mark this vehicle as returned?')) return;



            try {



                const res = await apiFetch(`bookings/${id}/complete`, { method: 'PUT' });



                if (res.ok) { showNotification('Vehicle returned successfully!', 'success'); this.refresh(); }



                else { showNotification('Failed: ' + res.status, 'error'); }



            } catch (err) { showNotification('Action failed: ' + err.message, 'error'); }



        },



        /*



        async assign(id) {



            this.currentBookingId = id;



            const select = document.getElementById('assignDriverSelect');



            select.innerHTML = '<option value="">Loading drivers...</option>';



            document.getElementById('assignDriverModal').style.display = 'flex';







            try {



                const res = await fetch(`${API_BASE}/drivers`);



                const drivers = await res.json();



                const approved = drivers.filter(d => d.status === 'Approved');







                if (approved.length === 0) {



                    select.innerHTML = '<option value="">No approved drivers found</option>';



                } else {



                    select.innerHTML = '<option value="">Select a driver...</option>' + 



                        approved.map(d => `<option value="${d.id}">${d.full_name}</option>`).join('');



                }



            } catch (err) {



                select.innerHTML = '<option value="">Failed to load drivers</option>';



            }



        },



        async saveAssign() {



            const driverId = document.getElementById('assignDriverSelect').value;



            if (!driverId) { alert('Please select a driver'); return; }







            try {



                const res = await fetch(`${API_BASE}/admin/bookings/${this.currentBookingId}/assign_driver`, {



                    method: 'PUT',



                    headers: { 'Content-Type': 'application/json' },



                    body: JSON.stringify({ driver_id: parseInt(driverId) })



                });







                if (res.ok) {



                    alert('Driver assigned successfully!');



                    document.getElementById('assignDriverModal').style.display = 'none';



                    this.refresh();



                } else {



                    const data = await res.json();



                    alert(data.error || 'Failed to assign driver');



                }



            } catch (err) { alert('Network error'); }



        }



        */



    };







    // --- DRIVERS MODULE (FULL SYNC) ---



    const Drivers = {



        data: [],



        async refresh() {



            const list = document.getElementById('driversList');
            showSkeleton('driversList', 'list');



            try {



                this.fetchWage();



                const res = await fetch(`${API_BASE}/drivers`);



                this.data = await res.json();



                this.applyFilters();



            } catch (err) {



                list.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--danger);">Error loading drivers.</div>`;



            }



        },



        async fetchWage() {



            try {



                const res = await fetch(`${API_BASE}/settings/driver_wage`);



                if (res.ok) {



                    const data = await res.json();



                    if (data.value) document.getElementById('driverWageInput').value = data.value;



                }



            } catch (err) {}



        },



        async saveWage() {



            const val = document.getElementById('driverWageInput').value;



            try {



                const res = await fetch(`${API_BASE}/settings/driver_wage`, {



                    method: 'POST',



                    headers: { 'Content-Type': 'application/json' },



                    body: JSON.stringify({ value: val })



                });



                if (res.ok) alert('Wage setting saved!');



            } catch (err) { alert('Failed to save wage'); }



        },



        applyFilters() {



            const query = document.getElementById('driverSearchInput').value.toLowerCase().trim();



            const status = document.getElementById('driverStatusFilter').value;



            let filtered = this.data;



            if (status !== 'all') filtered = filtered.filter(d => d.status === status);



            if (query) {



                filtered = filtered.filter(d => 



                    (d.full_name && d.full_name.toLowerCase().includes(query)) ||



                    (d.license_number && d.license_number.toLowerCase().includes(query))



                );



            }



            this.render(filtered);



        },



        render(drivers) {



            const list = document.getElementById('driversList');



            if (drivers.length === 0) {



                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">No drivers found.</div>';



                return;



            }



            list.innerHTML = drivers.map(d => `



                <div class="stat-card" style="padding: 18px; margin-bottom: 12px; border: 1px solid var(--border);">



                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">



                        <div>



                            <h4 style="font-size: 1rem;">${d.full_name}</h4>



                            <p style="font-size: 0.75rem; color: var(--text-muted);">${d.license_number}</p>



                        </div>



                        <span style="font-size: 0.6rem; padding: 4px 8px; border-radius: 10px; background: ${this.getStatusBg(d.status)}; color: ${this.getStatusColor(d.status)}; font-weight: 800; text-transform: uppercase;">



                            ${d.status || 'PENDING'}



                        </span>



                    </div>



                    <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.05);">



                        <div style="font-size: 0.8rem; color: var(--text-muted);"><i class="fas fa-phone" style="margin-right: 5px;"></i> ${d.contact_info}</div>



                        <div style="display: flex; gap: 8px;">



                            ${d.license_document ? `<button onclick="window.open('${API_BASE}/uploads/${d.license_document}')" style="background: rgba(0,177,79,0.1); border: 1px solid var(--primary); color: var(--primary); padding: 5px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 600;">License</button>` : ''}



                            ${d.status === 'Pending' ? `



                                <button onclick="Drivers.approve(${d.id})" style="background: var(--success); border: none; color: white; padding: 5px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 600;">Approve</button>



                                <button onclick="Drivers.reject(${d.id})" style="background: var(--danger); border: none; color: white; padding: 5px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 600;">Reject</button>



                            ` : ''}



                        </div>



                    </div>



                </div>



            `).join('');



        },



        getStatusBg(s) {



            if (s === 'Approved') return 'rgba(16, 185, 129, 0.1)';



            if (s === 'Pending') return 'rgba(251, 191, 36, 0.1)';



            return 'rgba(239, 68, 68, 0.1)';



        },



        getStatusColor(s) {



            if (s === 'Approved') return 'var(--success)';



            if (s === 'Pending') return '#f59e0b';



            return 'var(--danger)';



        },



        async approve(id) {



            if (!confirm('Approve this driver?')) return;



            try {



                const res = await fetch(`${API_BASE}/drivers/${id}/approve`, { method: 'PUT' });



                if (res.ok) { alert('Driver approved!'); this.refresh(); }



            } catch (err) { alert('Action failed'); }



        },



        async reject(id) {



            const reason = prompt("Reason for rejection:");



            if (!reason) return;



            try {



                const res = await fetch(`${API_BASE}/drivers/${id}/reject`, {



                    method: 'PUT',



                    headers: { 'Content-Type': 'application/json' },



                    body: JSON.stringify({ reason })



                });



                if (res.ok) { alert('Driver rejected'); this.refresh(); }



            } catch (err) { alert('Action failed'); }



        }



    };







    // --- VERIFICATIONS MODULE ---



    const Verifications = {



        data: [],
        _searchQuery: '',
        _sortBy: 'date_desc',

        onSearch(query) {
            this._searchQuery = (query || '').toLowerCase().trim();
            this.render();
        },

        setSort(sortKey) {
            this._sortBy = sortKey;
            const el = document.getElementById('verificationsSort');
            if (el && el.value !== sortKey) el.value = sortKey;
            this.render();
        },

        sortList(list, sortKey) {
            const copy = [...list];
            switch (sortKey) {
                case 'date_asc':
                    return copy.sort((a, b) => {
                        const da = a.created_at ? new Date(a.created_at).getTime() : 0;
                        const db = b.created_at ? new Date(b.created_at).getTime() : 0;
                        return (da && db) ? da - db : (a.id || 0) - (b.id || 0);
                    });
                case 'name_asc':
                    return copy.sort((a, b) => (a.full_name || '').localeCompare(b.full_name || ''));
                case 'name_desc':
                    return copy.sort((a, b) => (b.full_name || '').localeCompare(a.full_name || ''));
                case 'expiry_asc':
                    return copy.sort((a, b) => {
                        const ea = a.license_expiry ? new Date(a.license_expiry).getTime() : Infinity;
                        const eb = b.license_expiry ? new Date(b.license_expiry).getTime() : Infinity;
                        return (isNaN(ea) ? Infinity : ea) - (isNaN(eb) ? Infinity : eb);
                    });
                case 'expiry_desc':
                    return copy.sort((a, b) => {
                        const ea = a.license_expiry ? new Date(a.license_expiry).getTime() : 0;
                        const eb = b.license_expiry ? new Date(b.license_expiry).getTime() : 0;
                        return (isNaN(eb) ? 0 : eb) - (isNaN(ea) ? 0 : ea);
                    });
                case 'date_desc':
                default:
                    return copy.sort((a, b) => {
                        const da = a.created_at ? new Date(a.created_at).getTime() : 0;
                        const db = b.created_at ? new Date(b.created_at).getTime() : 0;
                        return (da && db) ? db - da : (b.id || 0) - (a.id || 0);
                    });
            }
        },



        async refresh() {



            const list = document.getElementById('verificationsList');
            showSkeleton('verificationsList', 'list');



            if (!list) return;



            if (!list.innerHTML.trim() || list.innerHTML.includes('Fetching')) {



                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">Loading verifications...</div>';



            }



            



            try {



                const url = `${API_URL}/admin/pending-verifications`;



                const res = await fetch(url);



                



                if (!res.ok) {



                    const errTxt = await res.text();



                    alert('API Error: ' + res.status + '\n' + errTxt);



                    list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--danger);">Server Error ' + res.status + '</div>';



                    return;



                }



                



                this.data = await res.json();



                this.render();



            } catch (err) {



                console.error('Refresh Error:', err);



                console.error('Connection Error:', err.message);



                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--danger);"><i class="fas fa-wifi" style="font-size:2rem; margin-bottom:10px;"></i><br>Connection Error. Please retry.</div>';



            }



        },



        render() {



            const list = document.getElementById('verificationsList');



            let displayData = Array.isArray(this.data) ? this.data : [];

            // Apply search filter
            if (this._searchQuery) {
                const q = this._searchQuery;
                displayData = displayData.filter(v =>
                    (v.full_name || '').toLowerCase().includes(q) ||
                    (v.email || '').toLowerCase().includes(q) ||
                    (v.phone || '').toLowerCase().includes(q) ||
                    (v.license_number || '').toLowerCase().includes(q)
                );
            }

            // Apply sorting
            displayData = this.sortList(displayData, this._sortBy || 'date_desc');

            if (!displayData || displayData.length === 0) {
                list.innerHTML = `
                    <div style="text-align: center; padding: 60px 20px; background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border);">
                        <i class="fas fa-user-shield" style="font-size: 3rem; color: var(--text-muted); opacity: 0.3; margin-bottom: 15px;"></i>
                        <p style="color: var(--text-muted); font-weight: 600;">${this._searchQuery ? 'No verifications match your search.' : 'No pending verifications.'}</p>
                    </div>`;
                return;
            }

            list.innerHTML = displayData.map(v => {



                const name = v.full_name || 'Unnamed User';



                const initial = name[0] ? name[0].toUpperCase() : '?';



                const licenseUrl = v.license_image || v.license_image_url || '';







                // License detail rows



                const hasDetails = v.license_number || v.license_type || v.license_expiry;



                const detailsHtml = `



                    <div style="background:rgba(0,177,79,0.06);border:1px solid rgba(0,177,79,0.15);border-radius:12px;padding:12px 14px;margin-bottom:14px;">



                        <div style="font-size:0.65rem;font-weight:800;color:var(--primary);text-transform:uppercase;letter-spacing:0.6px;margin-bottom:10px;"><i class="fas fa-id-card" style="margin-right:5px;"></i>Declared License Details</div>



                        



                        <div style="display:flex;gap:8px;margin-bottom:12px;overflow-x:auto;padding-bottom:4px;">
                            ${v.profile_picture ? `
                                <div style="flex:1;min-width:90px;">
                                    <div style="font-size:0.6rem;color:#00B14F;font-weight:800;text-transform:uppercase;margin-bottom:4px;"><i class="fas fa-camera"></i> Live Selfie</div>
                                    <img src="${v.profile_picture}" style="width:100%;height:85px;object-fit:cover;border-radius:8px;border:2px solid #00B14F;cursor:pointer;" onclick="Verifications.viewLicense('${v.profile_picture}', 'Live Selfie Profile Photo')">
                                </div>` : `
                                <div style="flex:1;min-width:90px;background:#f8fafc;border:1px dashed #cbd5e1;border-radius:8px;display:flex;flex-direction:column;align-items:center;justify-content:center;height:85px;">
                                    <i class="fas fa-user-slash" style="color:#94a3b8;font-size:1.2rem;margin-bottom:4px;"></i>
                                    <span style="font-size:0.6rem;color:#94a3b8;font-weight:700;">No Selfie</span>
                                </div>`}

                            ${licenseUrl ? `
                                <div style="flex:1;min-width:90px;">
                                    <div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:4px;">License Front</div>
                                    <img src="${licenseUrl}" style="width:100%;height:85px;object-fit:cover;border-radius:8px;border:1px solid #cbd5e1;cursor:pointer;" onclick="Verifications.viewLicense('${licenseUrl}', 'License Front')">
                                </div>` : ''}

                            ${v.license_back_url ? `
                                <div style="flex:1;min-width:90px;">
                                    <div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:4px;">License Back</div>
                                    <img src="${v.license_back_url}" style="width:100%;height:85px;object-fit:cover;border-radius:8px;border:1px solid #cbd5e1;cursor:pointer;" onclick="Verifications.viewLicense('${v.license_back_url}', 'License Back')">
                                </div>` : ''}
                        </div>







                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">



                            <div>



                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">License No.</div>



                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.license_number || '-'}</div>



                            </div>



                            <div>



                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Expiry Date</div>



                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.license_expiry || '-'}</div>



                            </div>



                            <div>



                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Class / Category</div>



                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.license_type || '-'}</div>



                            </div>



                            <div style="grid-column: span 2;">



                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Complete Residential Address</div>



                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);line-height:1.4;word-break:break-word;">${v.address || v.issuing_country_state || '-'}</div>



                            </div>



                        </div>



                        



                        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:12px 0;">



                        <div style="font-size:0.75rem;font-weight:800;color:var(--text-main);margin-bottom:8px;">Personal Info</div>



                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">



                            <div>



                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Full Name</div>



                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${name || '-'}</div>



                            </div>



                            <div>



                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Date of Birth</div>



                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.date_of_birth || '-'}</div>



                            </div>



                        </div>







                        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:12px 0;">



                        <div style="font-size:0.75rem;font-weight:800;color:var(--text-main);margin-bottom:8px;">IV. IN CASE OF EMERGENCY NOTIFY:</div>



                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">



                            <div style="grid-column: span 2;">



                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Contact Name</div>



                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.emergency_contact_name || '-'}</div>



                            </div>



                            <div>



                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Phone Number</div>



                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.emergency_contact_phone || '-'}</div>



                            </div>



                            <div>



                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Relationship</div>



                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.emergency_contact_relationship || '-'}</div>



                            </div>



                        </div>



                    </div>`;







                const actionButtons = licenseUrl



                    ? `<button onclick="Verifications.process(${v.id}, 2)" class="btn-premium" style="flex: 1; padding: 12px; font-size: 0.8rem; border-radius: 14px; background: var(--success); box-shadow: 0 8px 16px rgba(16, 185, 129, 0.3);">Approve</button>



                       <button onclick="Verifications.process(${v.id}, 0)" class="btn-premium" style="flex: 0.7; padding: 12px; font-size: 0.8rem; border-radius: 14px; background: var(--danger); box-shadow: 0 8px 16px rgba(239, 68, 68, 0.3);">Reject</button>`



                    : `<div style="flex: 1; text-align: center; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 12px; color: var(--text-muted); font-size: 0.75rem; font-weight: 600; border: 1px dashed var(--border);">



                            <i class="fas fa-clock" style="margin-right: 5px;"></i> Waiting for Upload



                       </div>`;







                return `



                <div class="stat-card" style="padding: 20px; margin-bottom: 16px;">



                    <div style="display: flex; gap: 16px; align-items: center; margin-bottom: 14px;">
                        ${v.profile_picture ? `
                            <img src="${v.profile_picture}" style="width: 54px; height: 54px; border-radius: 16px; object-fit: cover; border: 2px solid #00B14F; box-shadow: 0 4px 12px var(--primary-glow); flex-shrink:0; cursor:pointer;" onclick="Verifications.viewLicense('${v.profile_picture}', '${name}')">` : `
                            <div style="width: 54px; height: 54px; background: linear-gradient(135deg, #00B14F, #005339); border-radius: 16px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: white; font-size: 1.2rem; box-shadow: 0 4px 12px var(--primary-glow); flex-shrink:0;">
                                ${initial}
                            </div>`}



                        <div style="flex: 1; min-width:0;">



                            <h4 style="font-size: 1.05rem; font-weight: 800; color: var(--text-main); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${name}</h4>



                            <p style="font-size: 0.8rem; color: var(--text-muted); font-weight: 500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${v.email ? `<i class="fas fa-user-shield" style="color: #00B14F; font-size: 0.65rem; margin-right: 4px;" title="RA 10173 Protected"></i>${maskEmail(v.email)}` : 'No Email'}</p>



                        </div>



                    </div>



                    ${detailsHtml}



                    <div style="display: flex; gap: 12px;">



                        ${actionButtons}



                    </div>



                </div>



                `;



            }).join('');



        },



        viewLicense(url) {



            if (!url) return alert('No license image uploaded');



            const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;



            



            // Show in-app preview instead of window.open which fails in Capacitor



            const modal = document.getElementById('licensePreviewModal');



            const img = document.getElementById('licensePreviewImg');



            if (modal && img) {



                img.src = fullUrl;



                modal.style.display = 'flex';



            } else {



                window.open(fullUrl, '_blank');



            }



        },



        async process(userId, status) {



            const admin = adminAuth.getUser();



            if (!confirm(`Are you sure you want to ${status === 2 ? 'APPROVE' : 'REJECT'} this user?`)) return;



            try {



                const res = await fetch(`${API_BASE}/api/admin/verify-action`, {



                    method: 'POST',



                    headers: { 'Content-Type': 'application/json' },



                    body: JSON.stringify({ 



                        user_id: userId, 



                        status: status,



                        admin_id: admin ? admin.id : 1



                    })



                });



                if (res.ok) {



                    alert('Action successful!');



                    this.refresh();



                } else {



                    const d = await res.json();



                    alert(d.error || 'Failed to update');



                }



            } catch (err) { alert('Network error: ' + err.message); }



        }



    };







    // --- INSTRUCTIONS MODULE ---



    const Instructions = {



        data: [],



        async refresh() {



            const list = document.getElementById('instructionsList');
            showSkeleton('instructionsList', 'list');



            try {



                const res = await fetch(`${API_BASE}/api/admin/instructions`);



                this.data = await res.json();



                this.render();



            } catch (err) {



                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">No instructions found.</div>';



            }



        },



        render() {



            const list = document.getElementById('instructionsList');



            if (this.data.length === 0) {



                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">No active instructions.</div>';



                return;



            }



            list.innerHTML = this.data.map(inst => `
                <div class="stat-card" style="padding: 14px 18px; margin-bottom: 10px; border: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; gap: 14px; border-radius: 12px;">
                    <div style="flex: 1; min-width: 0;">
                        <p style="font-size: 0.88rem; line-height: 1.4; margin: 0; word-break: break-word;">${inst.instruction_text}</p>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; flex-shrink: 0;">
                        <span style="font-size: 0.65rem; padding: 4px 8px; border-radius: 6px; background: ${inst.is_active ? 'rgba(0,177,79,0.12)' : 'rgba(255,255,255,0.05)'}; color: ${inst.is_active ? '#00b14f' : 'var(--text-muted)'}; font-weight: 700; text-transform: uppercase;">
                            ${inst.is_active ? 'Active' : 'Inactive'}
                        </span>
                        <button onclick="Instructions.delete(${inst.id})" style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.25); color: #ef4444; width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s;" title="Delete Instruction" onmouseover="this.style.background='rgba(239,68,68,0.2)'" onmouseout="this.style.background='rgba(239,68,68,0.1)'">
                            <i class="fas fa-trash-alt" style="font-size: 0.85rem;"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        },
        async delete(id) {
            if (!id) return;
            if (!confirm('Are you sure you want to delete this instruction?')) return;
            try {
                const res = await fetch(`${API_BASE}/api/admin/instructions/${id}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    if (typeof showToast === 'function') showToast('Instruction deleted successfully', 'success');
                    this.refresh();
                } else {
                    const err = await res.json().catch(() => ({}));
                    if (typeof showToast === 'function') showToast(err.error || 'Failed to delete instruction', 'error');
                }
            } catch (err) {
                if (typeof showToast === 'function') showToast('Failed to delete instruction', 'error');
            }
        },
        async add() {
            const text = document.getElementById('newInstructionInput').value;
            if (!text) return;
            try {
                const res = await fetch(`${API_BASE}/api/admin/instructions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ instruction: text, is_active: true })
                });
                if (res.ok) {
                    document.getElementById('newInstructionInput').value = '';
                    if (typeof showToast === 'function') showToast('Instruction added successfully', 'success');
                    this.refresh();
                } else {
                    const err = await res.json().catch(() => ({}));
                    if (typeof showToast === 'function') showToast(err.error || 'Failed to add instruction', 'error');
                }
            } catch (err) {
                if (typeof showToast === 'function') showToast('Failed to add instruction', 'error');
            }
        }
    };







    // --- STAFF MODULE ---



    const Staff = {



        data: [],



        editingId: null,



        async refresh() {



            const user = adminAuth.getUser();



            if (!user) return;



            try {



                const res = await fetch(`${API_BASE}/api/admin/list?requester_id=${user.id}`);



                this.data = await res.json();



                this.render();



            } catch (err) {



                console.error(err);



            }



        },



        render() {



            const list = document.getElementById('staffList');



            const currentUser = adminAuth.getUser();



            if (this.data.length === 0) {



                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">No staff accounts.</div>';



                return;



            }



            list.innerHTML = this.data.map(s => `
                <div style="padding: 16px 20px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-solid); margin-bottom: 12px; display: flex; flex-direction: column; gap: 14px; box-shadow: var(--shadow-card);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px;">
                        <div>
                            <h4 style="font-size: 0.95rem; color: var(--text-main); font-weight: 600; margin: 0; display: flex; align-items: center; gap: 8px;">
                                ${s.full_name} 
                                ${s.id === currentUser.id ? '<span style="color:var(--primary); font-size:0.75rem; background: var(--primary-glow); padding: 2px 6px; border-radius: 4px; font-weight: 500;">You</span>' : ''}
                            </h4>
                            <p style="font-size: 0.8rem; color: var(--text-secondary); margin: 4px 0 0 0;">${s.email}</p>
                        </div>
                        <span style="font-size: 0.65rem; padding: 4px 10px; border-radius: 20px; background: ${s.role === 'super_admin' ? 'var(--primary-glow)' : 'rgba(251,191,36,0.12)'}; color: ${s.role === 'super_admin' ? 'var(--primary)' : '#f59e0b'}; font-weight: 700; text-transform: uppercase; border: 1px solid ${s.role === 'super_admin' ? 'rgba(0,177,79,0.2)' : 'rgba(251,191,36,0.2)'};">
                            ${s.role.replace('_', ' ')}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; border-top: 1px solid var(--border); padding-top: 12px;">
                        <span style="font-size: 0.8rem; color: ${s.is_verified === 1 ? 'var(--success)' : 'var(--danger)'}; font-weight: 600; display: flex; align-items: center; gap: 6px;">
                            <span style="width: 8px; height: 8px; border-radius: 50%; background: ${s.is_verified === 1 ? 'var(--success)' : 'var(--danger)'}; display: inline-block;"></span>
                            ${s.is_verified === 1 ? 'Enabled' : 'Disabled'}
                        </span>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                            ${s.role !== 'super_admin' ? `
                            <button onclick="Staff.openModal(${s.id})" style="padding: 6px 12px; background: var(--surface-container); border: 1px solid var(--border); border-radius: 8px; color: var(--text-main); font-size: 0.75rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px;">
                                <i class="fas fa-pen-to-square" style="font-size: 0.75rem; color: var(--primary);"></i> Edit
                            </button>
                            ` : `
                            <span style="font-size: 0.7rem; color: var(--text-muted); font-style: italic; padding: 6px 12px;"><i class="fas fa-shield-halved" style="color: var(--primary); margin-right: 4px;"></i>Protected</span>
                            `}
                            ${s.id !== currentUser.id && s.role !== 'super_admin' ? `
                                <button onclick="Staff.toggleStatus(${s.id}, ${s.is_verified})" style="padding: 6px 12px; background: ${s.is_verified === 1 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(0, 177, 79, 0.1)'}; border: 1px solid ${s.is_verified === 1 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(0, 177, 79, 0.2)'}; border-radius: 8px; color: ${s.is_verified === 1 ? 'var(--danger)' : 'var(--success)'}; font-size: 0.75rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px;">
                                    <i class="fas ${s.is_verified === 1 ? 'fa-ban' : 'fa-check'}" style="font-size: 0.75rem;"></i> ${s.is_verified === 1 ? 'Disable' : 'Enable'}
                                </button>
                                <button onclick="Staff.delete(${s.id})" style="padding: 6px 12px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 8px; color: var(--danger); font-size: 0.75rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px;">
                                    <i class="fas fa-trash-can" style="font-size: 0.75rem;"></i> Delete
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `).join('');



        },



        openModal(id = null) {



            this.editingId = id;



            const modal = document.getElementById('staffModal');



            const hint = document.getElementById('staffPassHint');



            const pass = document.getElementById('staffPass');



            



            document.getElementById('staffForm').reset();



            if (id) {



                const s = this.data.find(x => x.id == id);

                // Block editing super_admin accounts
                if (s && s.role === 'super_admin') {
                    alert('Super Admin accounts cannot be edited.');
                    return;
                }


                document.getElementById('staffFormTitle').textContent = 'Edit Staff Account';



                document.getElementById('staffName').value = s.full_name;



                document.getElementById('staffEmail').value = s.email;



                document.getElementById('staffRole').value = s.role;



                pass.required = false;



                hint.style.display = 'block';



            } else {



                document.getElementById('staffFormTitle').textContent = 'Add New Staff';



                pass.required = true;



                hint.style.display = 'none';



            }



            modal.style.display = 'flex';



        },



        closeModal() {



            document.getElementById('staffModal').style.display = 'none';



        },



                async toggleStatus(id, current) {
            const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
            if (!user || !user.id) {
                alert('Session expired. Please log in again.');
                const overlay = document.getElementById('adminLoginOverlay');
                if (overlay) overlay.style.display = 'flex';
                return;
            }

            try {
                const res = await fetch(`${API_BASE}/api/admin/status/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ requester_id: user.id, status: current === 1 ? 0 : 1 })
                });
                if (res.ok) {
                    this.refresh();
                } else {
                    const data = await res.json().catch(() => ({}));
                    alert(data.error || 'Failed to update status');
                }
            } catch (err) {
                alert('Failed to update status');
            }
        },

        async delete(id) {
            if (!confirm('Are you sure?')) return;
            const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
            if (!user || !user.id) {
                alert('Session expired. Please log in again.');
                const overlay = document.getElementById('adminLoginOverlay');
                if (overlay) overlay.style.display = 'flex';
                return;
            }

            try {
                const res = await fetch(`${API_BASE}/api/admin/delete/${id}?requester_id=${user.id}`, { method: 'DELETE' });
                if (res.ok) {
                    this.refresh();
                } else {
                    const data = await res.json().catch(() => ({}));
                    alert(data.error || 'Failed to delete');
                }
            } catch (err) {
                alert('Failed to delete');
            }
        },

        async submit(e) {
            e.preventDefault();
            const id = this.editingId;
            const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;

            const nameEl = document.getElementById('staffName');
            const emailEl = document.getElementById('staffEmail');
            const passEl = document.getElementById('staffPass');
            const roleEl = document.getElementById('staffRole');

            [nameEl, emailEl, passEl, roleEl].forEach(el => clearInlineError(el));
            let hasError = false;

            const name = nameEl.value.trim();
            if (!name) { showInlineError(nameEl, 'Name is required'); hasError = true; }

            const email = emailEl.value.trim();
            if (!email) { showInlineError(emailEl, 'Email is required'); hasError = true; }
            else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { showInlineError(emailEl, 'Please enter a valid email address'); hasError = true; }

            const password = passEl.value;
            if (!id && !password) { showInlineError(passEl, 'Password is required for new staff'); hasError = true; }
            else if (password && password.length < 6) { showInlineError(passEl, 'Password must be at least 6 characters long'); hasError = true; }

            const role = roleEl.value;
            if (!role) { showInlineError(roleEl, 'Role is required'); hasError = true; }

            if (hasError) return;

            const submitBtn = document.getElementById('staffSubmitBtn');
            let origText = 'Save Account';
            if (submitBtn) {
                origText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            }

            if (!user || !user.id) {
                alert('Session expired or unauthorized. Please log in again.');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = origText;
                }
                const overlay = document.getElementById('adminLoginOverlay');
                if (overlay) overlay.style.display = 'flex';
                return;
            }

            const method = id ? 'PUT' : 'POST';
            const url = id ? `${API_BASE}/api/admin/update/${id}` : `${API_BASE}/api/admin/create`;

            try {
                const payload = {
                    requester_id: user.id,
                    name: name,
                    email: email,
                    password: password,
                    role: role
                };

                const res = await fetch(url, {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    this.closeModal();
                    this.refresh();
                    if (typeof showNotification === 'function') {
                        showNotification(id ? 'Staff updated successfully!' : 'Staff created successfully!', 'success');
                    }
                } else {
                    const data = await res.json().catch(() => ({}));
                    alert('Error: ' + (data.error || data.message || 'Operation failed'));
                }
            } catch (err) {
                console.error('Staff submit error:', err);
                alert('Connection error. Please try again.');
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = origText;
                }
            }
        }
    };















        // --- GPS MODULE (Blynk IoT + Multi-Device Fleet Assignment + Persistent DB Recording) ---
    const GPS = {
        lat: null,
        lng: null,
        currentAddress: '',
        lastActive: 0,
        timer: null,
        selectedVehicleId: null,
        fleetVehicles: [],
        _lastGeoLookupTime: 0,
        _lastSavedCoords: null,

        toggleMapInteractive(enable) {
            const frame = document.getElementById('blynkMapFrame');
            const overlay = document.getElementById('gpsMapTouchOverlay');
            const lockBtn = document.getElementById('gpsMapLockBtn');
            if (frame) frame.style.pointerEvents = enable ? 'auto' : 'none';
            if (overlay) overlay.style.display = enable ? 'none' : 'flex';
            if (lockBtn) lockBtn.style.display = enable ? 'inline-flex' : 'none';
        },

        async init() {
            this.toggleMapInteractive(false);
            const frame = document.getElementById('blynkMapFrame');
            if (frame && (!frame.src || frame.src === 'about:blank' || frame.src.endsWith('about:blank'))) {
                frame.src = frame.getAttribute('data-src') || 'https://car-rental-inlaguna.vercel.app/';
            }
            await this.loadFleetVehicles();
            await this.loadLastKnownLocationFromDB();
        },

        async loadFleetVehicles() {
            try {
                let res = await fetch(`${API_BASE}/api/admin/gps-locations`);
                if (!res.ok) res = await fetch(`${API_BASE}/admin/gps-locations`);
                if (res.ok) {
                    const data = await res.json();
                    this.fleetVehicles = data || [];
                }
            } catch (e) {
                console.error('[GPS] loadFleetVehicles error:', e);
            }

            // Fallback: If fleetVehicles has fewer than 2 vehicles, fetch from /api/vehicles to guarantee full fleet
            if (!this.fleetVehicles || this.fleetVehicles.length <= 1) {
                try {
                    let vRes = await fetch(`${API_BASE}/api/vehicles`);
                    if (!vRes.ok) vRes = await fetch(`${API_BASE}/vehicles`);
                    if (vRes.ok) {
                        const vList = await vRes.json();
                        if (vList && vList.length > (this.fleetVehicles ? this.fleetVehicles.length : 0)) {
                            const existingMap = new Map((this.fleetVehicles || []).map(x => [x.id, x]));
                            this.fleetVehicles = vList.map(v => {
                                const exist = existingMap.get(v.id) || {};
                                return {
                                    id: v.id,
                                    name: v.name || `${v.brand || ''} ${v.model || ''}`.trim() || `Vehicle #${v.id}`,
                                    plate_number: v.plate_number,
                                    latitude: exist.latitude || v.latitude,
                                    longitude: exist.longitude || v.longitude,
                                    last_address: exist.last_address || v.last_address,
                                    last_gps_update: exist.last_gps_update || v.last_gps_update,
                                    gps_status: exist.gps_status || v.gps_status,
                                    gps_device_token: exist.gps_device_token || v.gps_device_token,
                                    gps_device_name: exist.gps_device_name || v.gps_device_name,
                                    gps_server: exist.gps_server || v.gps_server || 'sgp1.blynk.cloud'
                                };
                            });
                        }
                    }
                } catch (e) {}
            }

            const select = document.getElementById('gpsVehicleSelect');
            if (select && this.fleetVehicles.length > 0) {
                const curVal = this.selectedVehicleId;
                select.innerHTML = this.fleetVehicles.map(v => `
                    <option value="${v.id}" style="background-color:#0f172a !important; color:#ffffff !important; padding:8px 10px;" ${v.id === curVal ? 'selected' : ''}>
                        ${v.name || 'Vehicle'} (${v.plate_number || 'No Plate'})
                    </option>
                `).join('');
                if (!this.selectedVehicleId || !this.fleetVehicles.some(v => v.id === this.selectedVehicleId)) {
                    this.selectedVehicleId = this.fleetVehicles[0].id;
                }
                select.value = this.selectedVehicleId;
            }
            this._updateHeaderDeviceLabel();
        },

        _updateHeaderDeviceLabel() {
            const currentVeh = this.fleetVehicles.find(v => v.id === this.selectedVehicleId) || this.fleetVehicles[0];
            const labelEl = document.getElementById('gpsDeviceLabel');
            if (labelEl && currentVeh) {
                const isCar2 = (
                    (currentVeh.gps_device_name && (currentVeh.gps_device_name.includes('2') || currentVeh.gps_device_name.toLowerCase().includes('vios'))) ||
                    (currentVeh.plate_number && currentVeh.plate_number.toUpperCase().includes('DBJ')) ||
                    currentVeh.id === 18 ||
                    currentVeh.id === 35
                );
                const isCar1 = (
                    (currentVeh.gps_device_name && (currentVeh.gps_device_name.includes('1') || currentVeh.gps_device_name.toLowerCase().includes('montero'))) ||
                    (currentVeh.plate_number && currentVeh.plate_number.toUpperCase().includes('DUY')) ||
                    currentVeh.id === 12
                );

                if (!currentVeh.gps_device_token && (isCar1 || isCar2)) {
                    currentVeh.gps_device_token = '6fub_AeSZfywBab9j-d7KRXWKFPMwIxz';
                    currentVeh.gps_device_name = isCar2 ? 'Tracker Unit 2 (ESP32 - Vios)' : 'Tracker Unit 1 (ESP32 - Montero)';
                    currentVeh.gps_server = 'sgp1.blynk.cloud';
                }

                if (currentVeh.gps_device_name) {
                    labelEl.textContent = `Tracker: ${currentVeh.gps_device_name}`;
                    labelEl.style.color = 'var(--text-main)';
                    labelEl.style.borderColor = 'var(--border)';
                } else if (currentVeh.gps_device_token) {
                    labelEl.textContent = isCar2 ? 'Tracker: Unit 2 Linked' : 'Tracker: Unit 1 Linked';
                    labelEl.style.color = 'var(--primary)';
                    labelEl.style.borderColor = 'rgba(0,177,79,0.3)';
                } else {
                    labelEl.textContent = 'Tracker: Unassigned';
                    labelEl.style.color = '#f59e0b';
                    labelEl.style.borderColor = 'rgba(245,158,11,0.3)';
                }
            }
        },

        onVehicleSelect(vehicleId) {
            this.selectedVehicleId = parseInt(vehicleId, 10);
            this._updateHeaderDeviceLabel();
            this.refresh();

            // Notify map iframe to center on selected car
            try {
                const frame = document.getElementById('blynkMapFrame');
                if (frame && frame.contentWindow) {
                    const currentVeh = this.fleetVehicles.find(v => v.id === this.selectedVehicleId);
                    const isCar2 = (
                        (currentVeh?.gps_device_name && (currentVeh.gps_device_name.includes('2') || currentVeh.gps_device_name.toLowerCase().includes('vios'))) ||
                        (currentVeh?.plate_number && currentVeh.plate_number.toUpperCase().includes('DBJ')) ||
                        this.selectedVehicleId === 18 ||
                        this.selectedVehicleId === 35
                    );
                    frame.contentWindow.postMessage({
                        type: 'AUTORIDE_GPS_SELECT_CAR',
                        car: isCar2 ? 2 : 1,
                        vehicleId: this.selectedVehicleId
                    }, '*');
                }
            } catch(e) {}
        },

        async loadLastKnownLocationFromDB() {
            if (!this.selectedVehicleId && this.fleetVehicles.length > 0) {
                this.selectedVehicleId = this.fleetVehicles[0].id;
            }
            if (!this.selectedVehicleId) return;

            try {
                const res = await fetch(`${API_BASE}/api/admin/gps-locations`);
                if (res.ok) {
                    const list = await res.json();
                    this.fleetVehicles = list || [];
                    this._updateHeaderDeviceLabel();
                    const veh = this.fleetVehicles.find(v => v.id === this.selectedVehicleId);
                    if (veh) {
                        this._updateCardWithData(veh);
                    }
                }
            } catch (e) {
                console.error('[GPS] loadLastKnownLocationFromDB error:', e);
            }
        },

        _updateCardWithData(veh) {
            const addrEl = document.getElementById('gpsLastAddressText');
            const coordsEl = document.getElementById('gpsCoordsText');
            const elapsedEl = document.getElementById('gpsLastTimeElapsed');
            const exactEl = document.getElementById('gpsLastTimeExact');
            const pill = document.getElementById('gpsStatusPill');
            const pillDot = document.getElementById('gpsPillDot');
            const pillText = document.getElementById('gpsPillText');

            if (veh.latitude && veh.longitude) {
                this.lat = parseFloat(veh.latitude);
                this.lng = parseFloat(veh.longitude);
                this.currentAddress = veh.last_address || 'Recorded Location';

                if (addrEl) addrEl.textContent = veh.last_address || 'Recorded Location Coordinates Available';
                if (coordsEl) coordsEl.textContent = `Lat: ${this.lat.toFixed(6)}, Lng: ${this.lng.toFixed(6)}`;
            } else {
                if (addrEl) addrEl.textContent = 'No GPS coordinates recorded yet for this vehicle.';
                if (coordsEl) coordsEl.textContent = 'Lat: --, Lng: --';
            }

            if (veh.last_gps_update) {
                const dt = new Date(veh.last_gps_update);
                const elapsedMin = Math.round((Date.now() - dt.getTime()) / 60000);
                let elapsedStr = '';
                if (elapsedMin < 2) elapsedStr = 'Just now';
                else if (elapsedMin < 60) elapsedStr = `${elapsedMin} minutes ago`;
                else if (elapsedMin < 1440) elapsedStr = `${Math.floor(elapsedMin / 60)} hour(s) ago`;
                else elapsedStr = `${Math.floor(elapsedMin / 1440)} day(s) ago`;

                if (elapsedEl) elapsedEl.textContent = elapsedStr;
                if (exactEl) exactEl.textContent = dt.toLocaleString();

                const isRecentlyOnline = elapsedMin < 5;
                if (pill && pillDot && pillText) {
                    if (isRecentlyOnline) {
                        pill.style.background = 'rgba(0, 177, 79, 0.12)';
                        pill.style.borderColor = 'rgba(0, 177, 79, 0.3)';
                        pill.style.color = 'var(--primary)';
                        pillDot.style.background = '#00B14F';
                        pillText.textContent = 'LIVE • MOVING / IDLE';
                    } else {
                        pill.style.background = 'rgba(245, 158, 11, 0.12)';
                        pill.style.borderColor = 'rgba(245, 158, 11, 0.3)';
                        pill.style.color = '#f59e0b';
                        pillDot.style.background = '#f59e0b';
                        pillText.textContent = 'LAST KNOWN • PARKED / OFFLINE';
                    }
                }
            } else {
                if (elapsedEl) elapsedEl.textContent = 'Never active';
                if (exactEl) exactEl.textContent = 'No signal recorded';
                if (pill && pillDot && pillText) {
                    pill.style.background = 'rgba(148, 163, 184, 0.12)';
                    pill.style.borderColor = 'rgba(148, 163, 184, 0.3)';
                    pill.style.color = '#94a3b8';
                    pillDot.style.background = '#94a3b8';
                    pillText.textContent = 'NO SIGNAL';
                }
            }
        },

        async reverseGeocode(lat, lng) {
            try {
                const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`, {
                    headers: { 'Accept-Language': 'en' }
                });
                if (res.ok) {
                    const data = await res.json();
                    if (data && data.display_name) {
                        const a = data.address || {};
                        const parts = [
                            a.road || a.street,
                            a.suburb || a.village || a.neighbourhood,
                            a.city || a.municipality || a.town,
                            a.state || a.province
                        ].filter(Boolean);
                        return parts.length > 0 ? parts.join(', ') : data.display_name;
                    }
                }
            } catch (e) {}
            return '';
        },

        async refresh() {
            if (!this.fleetVehicles || this.fleetVehicles.length === 0) {
                await this.loadFleetVehicles();
            }
            const currentVeh = this.fleetVehicles.find(v => v.id === this.selectedVehicleId) || this.fleetVehicles[0];
            if (!currentVeh) return;

            const isCar2 = (
                (currentVeh.gps_device_name && (currentVeh.gps_device_name.includes('2') || currentVeh.gps_device_name.toLowerCase().includes('vios'))) ||
                (currentVeh.plate_number && currentVeh.plate_number.toUpperCase().includes('DBJ')) ||
                currentVeh.id === 18 ||
                currentVeh.id === 35
            );
            const isCar1 = (
                (currentVeh.gps_device_name && (currentVeh.gps_device_name.includes('1') || currentVeh.gps_device_name.toLowerCase().includes('montero'))) ||
                (currentVeh.plate_number && currentVeh.plate_number.toUpperCase().includes('DUY')) ||
                currentVeh.id === 12
            );

            if (!currentVeh.gps_device_token && (isCar1 || isCar2)) {
                currentVeh.gps_device_token = '6fub_AeSZfywBab9j-d7KRXWKFPMwIxz';
                currentVeh.gps_device_name = isCar2 ? 'Tracker Unit 2 (ESP32 - Vios)' : 'Tracker Unit 1 (ESP32 - Montero)';
                currentVeh.gps_server = 'sgp1.blynk.cloud';
            }

            const token = currentVeh?.gps_device_token || '6fub_AeSZfywBab9j-d7KRXWKFPMwIxz';
            const server = currentVeh?.gps_server || 'sgp1.blynk.cloud';

            this._updateHeaderDeviceLabel();

            const latPin = isCar2 ? 'v5' : 'v1';
            const lngPin = isCar2 ? 'v6' : 'v2';
            const satPin = isCar2 ? 'v7' : 'v3';
            const pingPin = isCar2 ? 'v8' : 'v4';

            try {
                const res = await fetch(
                    `https://${server}/external/api/get?token=${token}&v1&v2&v3&v4&v5&v6&v7&v8&_=${Date.now()}`
                );
                if (!res.ok) {
                    this._showOffline('Device offline');
                    this.loadLastKnownLocationFromDB();
                    return;
                }

                const data = await res.json();
                const now = Date.now();

                // 1. Concurrently record Car 1 (Unit 1 / Montero DUY 6527 -> vehicle 12)
                const rawLat1 = String(data.v1 || '');
                const rawLng1 = String(data.v2 || '');
                const isOnline1 = data.v4 !== undefined || (rawLat1 !== '' && rawLat1 !== '0');
                if (rawLat1 && rawLat1 !== '0' && !rawLat1.includes('ENCRYPTED')) {
                    const lat1 = parseFloat(rawLat1);
                    const lng1 = parseFloat(rawLng1);
                    if (!isNaN(lat1) && !isNaN(lng1) && lat1 !== 0 && lng1 !== 0) {
                        const car1 = this.fleetVehicles.find(v => v.id === 12 || (v.plate_number && v.plate_number.toUpperCase().includes('DUY')));
                        const c1Id = car1 ? car1.id : 12;
                        fetch(`${API_BASE}/api/vehicles/${c1Id}/location`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                latitude: lat1,
                                longitude: lng1,
                                speed: 0,
                                gps_status: isOnline1 ? 'online' : 'offline'
                            })
                        }).catch(() => {});
                    }
                }

                // 2. Concurrently record Car 2 (Unit 2 / Vios DBJ 9483 -> vehicle 18 & 35)
                const rawLat2 = String(data.v5 || '');
                const rawLng2 = String(data.v6 || '');
                const isOnline2 = data.v8 !== undefined || (rawLat2 !== '' && rawLat2 !== '0');
                if (rawLat2 && rawLat2 !== '0' && !rawLat2.includes('ENCRYPTED')) {
                    const lat2 = parseFloat(rawLat2);
                    const lng2 = parseFloat(rawLng2);
                    if (!isNaN(lat2) && !isNaN(lng2) && lat2 !== 0 && lng2 !== 0) {
                        const car2 = this.fleetVehicles.find(v => v.id === 18 || v.id === 35 || (v.plate_number && v.plate_number.toUpperCase().includes('DBJ')));
                        const c2Id = car2 ? car2.id : 18;
                        fetch(`${API_BASE}/api/vehicles/${c2Id}/location`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                latitude: lat2,
                                longitude: lng2,
                                speed: 0,
                                gps_status: isOnline2 ? 'online' : 'offline'
                            })
                        }).catch(() => {});
                    }
                }

                // 3. Update UI telemetry for the SELECTED vehicle
                if (data[pingPin] !== undefined) this.lastActive = now;
                const isOnline = (now - this.lastActive) < 30000;

                const rawLat = String(data[latPin] || '');
                const rawLng = String(data[lngPin] || '');
                const isEncrypted = rawLat.includes('ENCRYPTED') || rawLat === '' || rawLat === '0';

                const badge = document.getElementById('gpsStatusBadge');
                if (isOnline && !isEncrypted) {
                    if (badge) { badge.textContent = 'LIVE'; badge.style.color = 'var(--success)'; }
                } else {
                    if (badge) { badge.textContent = 'OFFLINE'; badge.style.color = '#f59e0b'; }
                }

                if (!isEncrypted) {
                    const lat = parseFloat(rawLat);
                    const lng = parseFloat(rawLng);
                    if (!isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0) {
                        this.lat = lat;
                        this.lng = lng;

                        // Reverse geocode if 60s elapsed
                        if (now - this._lastGeoLookupTime > 60000 || !this.currentAddress) {
                            this._lastGeoLookupTime = now;
                            const addr = await this.reverseGeocode(lat, lng);
                            if (addr) this.currentAddress = addr;
                        }

                        const vehId = this.selectedVehicleId || currentVeh.id;

                        // Update UI Card
                        this._updateCardWithData({
                            id: vehId,
                            latitude: lat,
                            longitude: lng,
                            last_address: this.currentAddress,
                            last_gps_update: new Date().toISOString(),
                            gps_status: isOnline ? 'online' : 'offline'
                        });
                        return;
                    }
                }

                this.loadLastKnownLocationFromDB();

            } catch (e) {
                this._showOffline('Connection error');
                this.loadLastKnownLocationFromDB();
            }
        },

        _showNoDevice() {
            const badge = document.getElementById('gpsStatusBadge');
            if (badge) {
                badge.textContent = 'NO TRACKER LINKED';
                badge.style.color = '#94a3b8';
            }
            const pill = document.getElementById('gpsStatusPill');
            const pillDot = document.getElementById('gpsPillDot');
            const pillText = document.getElementById('gpsPillText');
            if (pill && pillDot && pillText) {
                pill.style.background = 'rgba(148, 163, 184, 0.12)';
                pill.style.borderColor = 'rgba(148, 163, 184, 0.3)';
                pill.style.color = '#94a3b8';
                pillDot.style.background = '#94a3b8';
                pillText.innerHTML = 'NO TRACKER LINKED &bull; <a href="javascript:void(0)" onclick="GPS.openConfigModal()" style="color:var(--primary);font-weight:700;text-decoration:underline;">+ Assign</a>';
            }
        },

        _showOffline(reason) {
            const badge = document.getElementById('gpsStatusBadge');
            if (badge) { badge.textContent = 'OFFLINE'; badge.style.color = 'var(--text-muted)'; }
        },

        openMap() {
            window.open('https://car-rental-inlaguna.vercel.app/', '_blank');
        },

        openGoogleMaps() {
            if (this.lat && this.lng) {
                window.open(`https://www.google.com/maps?q=${this.lat},${this.lng}`, '_blank');
            } else {
                alert('No recorded GPS coordinates available yet.');
            }
        },

        async openTripHistoryModal() {
            const vehId = this.selectedVehicleId || (this.fleetVehicles[0] ? this.fleetVehicles[0].id : 12);
            if (!vehId) return;

            const modal = document.getElementById('gpsTripHistoryModal');
            if (modal) modal.style.display = 'flex';

            const veh = this.fleetVehicles.find(v => v.id === vehId);
            const sub = document.getElementById('gpsHistSubtitle');
            if (sub && veh) {
                sub.textContent = `${veh.name || 'Vehicle'} (${veh.plate_number || ''}) • Recent breadcrumb trail logs`;
            }

            const container = document.getElementById('gpsHistoryListContainer');
            if (!container) return;
            container.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Loading trail logs...</div>';

            // Auto-refresh freshest GPS telemetry before loading history
            try {
                await this.refresh();
            } catch (e) {}

            try {
                const res = await fetch(`${API_BASE}/api/vehicles/${vehId}/gps-history?limit=50`);
                if (res.ok) {
                    const data = await res.json();
                    const logs = data.logs || [];
                    if (logs.length === 0) {
                        container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><i class="fas fa-map-marked-alt" style="font-size:2rem;opacity:0.3;margin-bottom:8px;display:block;"></i>No trip logs recorded yet for this vehicle. Logs are recorded automatically while moving.</div>';
                        return;
                    }

                    container.innerHTML = logs.map(l => `
                        <div style="background:var(--surface-card);border:1px solid var(--border);border-radius:12px;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;box-shadow:0 2px 6px rgba(0,0,0,0.04);">
                            <div style="display:flex;align-items:center;gap:14px;">
                                <div style="width:38px;height:38px;border-radius:10px;background:rgba(0,177,79,0.12);display:flex;align-items:center;justify-content:center;color:var(--primary);font-size:1rem;flex-shrink:0;">
                                    <i class="fas fa-map-pin"></i>
                                </div>
                                <div>
                                    <div style="font-size:0.92rem;font-weight:800;color:var(--text-main);line-height:1.35;">${escapeHtml(l.address || 'Recorded Coordinate Point')}</div>
                                    <div style="font-family:monospace;font-size:0.76rem;color:var(--text-muted);margin-top:3px;">
                                        ${parseFloat(l.latitude).toFixed(6)}, ${parseFloat(l.longitude).toFixed(6)}
                                        ${l.speed ? ` • <span style="color:var(--primary);font-weight:700;">${l.speed} km/h</span>` : ''}
                                    </div>
                                </div>
                            </div>
                            <div style="text-align:right;margin-left:auto;">
                                <div style="font-size:0.8rem;font-weight:800;color:var(--primary);">${new Date(l.created_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'})}</div>
                                <div style="font-size:0.7rem;color:var(--text-muted);margin-top:2px;">${new Date(l.created_at).toLocaleDateString([], {month:'short', day:'numeric', year:'numeric'})}</div>
                            </div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<div style="text-align:center;padding:24px;color:#ef4444;">Failed to load trip history logs.</div>';
                }
            } catch (err) {
                console.error("GPS trip history error:", err);
                container.innerHTML = `<div style="text-align:center;padding:24px;color:#ef4444;">Failed to load trip history: ${escapeHtml(err.message || String(err))}</div>`;
            }
        },

        closeTripHistoryModal() {
            const modal = document.getElementById('gpsTripHistoryModal');
            if (modal) modal.style.display = 'none';
        },

        async openConfigModal(vehicleId = null) {
            const modal = document.getElementById('gpsConfigModal');
            if (!modal) return;

            if (!this.fleetVehicles || this.fleetVehicles.length <= 1) {
                await this.loadFleetVehicles();
            }

            const sel = document.getElementById('gpsConfigVehicleSelect');
            if (sel && this.fleetVehicles.length > 0) {
                const targetId = vehicleId || this.selectedVehicleId || this.fleetVehicles[0].id;
                sel.innerHTML = this.fleetVehicles.map(v => `
                    <option value="${v.id}" style="background-color:#0f172a !important; color:#ffffff !important; padding:8px 10px;" ${v.id == targetId ? 'selected' : ''}>
                        ${v.name || 'Vehicle'} (${v.plate_number || 'No Plate'})
                    </option>
                `).join('');
                sel.value = targetId;
                this.onConfigVehicleChange(targetId);
            }

            const statusBox = document.getElementById('gpsTestStatusBox');
            if (statusBox) statusBox.style.display = 'none';

            modal.style.display = 'flex';
        },

        closeConfigModal() {
            const modal = document.getElementById('gpsConfigModal');
            if (modal) modal.style.display = 'none';
        },

        toggleTokenVisibility() {
            const input = document.getElementById('gpsConfigToken');
            if (input) {
                input.type = input.type === 'password' ? 'text' : 'password';
            }
        },

        async onConfigVehicleChange(vehicleId) {
            if (!vehicleId) return;
            const veh = this.fleetVehicles.find(v => v.id == vehicleId);
            const tokenInput = document.getElementById('gpsConfigToken');
            const nameInput = document.getElementById('gpsConfigDeviceName');
            const serverInput = document.getElementById('gpsConfigServer');
            const statusBox = document.getElementById('gpsTestStatusBox');
            if (statusBox) statusBox.style.display = 'none';

            if (veh) {
                if (tokenInput) tokenInput.value = veh.gps_device_token || '';
                if (nameInput) nameInput.value = veh.gps_device_name || '';
                if (serverInput) serverInput.value = veh.gps_server || 'sgp1.blynk.cloud';
            }

            try {
                const res = await fetch(`${API_BASE}/api/admin/vehicles/${vehicleId}/gps-config`);
                if (res.ok) {
                    const data = await res.json();
                    if (tokenInput) tokenInput.value = data.gps_device_token || '';
                    if (nameInput) nameInput.value = data.gps_device_name || '';
                    if (serverInput) serverInput.value = data.gps_server || 'sgp1.blynk.cloud';
                }
            } catch (e) {}
        },

        async testDeviceConnection() {
            const token = (document.getElementById('gpsConfigToken')?.value || '').trim();
            const server = (document.getElementById('gpsConfigServer')?.value || 'sgp1.blynk.cloud').trim();
            const statusBox = document.getElementById('gpsTestStatusBox');
            const btn = document.getElementById('gpsTestBtn');

            if (!token) {
                if (statusBox) {
                    statusBox.style.display = 'block';
                    statusBox.style.background = 'rgba(239, 68, 68, 0.12)';
                    statusBox.style.border = '1px solid rgba(239, 68, 68, 0.3)';
                    statusBox.style.color = '#ef4444';
                    statusBox.innerHTML = '<i class="fas fa-exclamation-circle"></i> Please enter a Blynk Auth Token to test.';
                }
                return;
            }

            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
            }

            try {
                const res = await fetch(`https://${server}/external/api/get?token=${token}&v1&v2&v3&v4&v5&v6&v7&v8&_=${Date.now()}`);
                if (res.ok) {
                    const data = await res.json();
                    const sel = document.getElementById('gpsConfigVehicleSelect');
                    const vehId = sel ? parseInt(sel.value, 10) : null;
                    const veh = this.fleetVehicles.find(v => v.id === vehId);
                    const isCar2 = (
                        (veh?.gps_device_name && (veh.gps_device_name.includes('2') || veh.gps_device_name.toLowerCase().includes('vios'))) ||
                        (veh?.plate_number && veh.plate_number.toUpperCase().includes('DBJ')) ||
                        vehId === 18 || vehId === 35
                    );

                    const latPin = isCar2 ? 'v5' : 'v1';
                    const lngPin = isCar2 ? 'v6' : 'v2';
                    const satPin = isCar2 ? 'v7' : 'v3';
                    const pingPin = isCar2 ? 'v8' : 'v4';

                    const hasSelectedSignal = data[pingPin] !== undefined || (data[latPin] && data[latPin] !== '0');
                    const hasAnySignal = data.v4 !== undefined || data.v8 !== undefined || (data.v1 && data.v1 !== '0') || (data.v5 && data.v5 !== '0');

                    if (statusBox) {
                        statusBox.style.display = 'block';
                        statusBox.style.background = 'rgba(0, 177, 79, 0.12)';
                        statusBox.style.border = '1px solid rgba(0, 177, 79, 0.3)';
                        statusBox.style.color = 'var(--primary)';

                        let details = '';
                        if (data[latPin] && data[lngPin]) {
                            details += `<div style="font-size:0.75rem;font-family:monospace;margin-top:4px;color:var(--text-main);font-weight:600;">` +
                                       `${isCar2 ? 'Unit 2 (Vios DBJ)' : 'Unit 1 (Montero DUY)'}: Lat ${data[latPin]}, Lng ${data[lngPin]} (Sats: ${data[satPin] || 'N/A'})</div>`;
                        }
                        const otherLat = isCar2 ? data.v1 : data.v5;
                        const otherLng = isCar2 ? data.v2 : data.v6;
                        if (otherLat && otherLng) {
                            details += `<div style="font-size:0.70rem;font-family:monospace;margin-top:2px;color:var(--text-secondary);">` +
                                       `Also active: ${isCar2 ? 'Unit 1' : 'Unit 2'} (Lat ${otherLat}, Lng ${otherLng})</div>`;
                        }

                        statusBox.innerHTML = `
                            <div style="display:flex;align-items:center;gap:6px;">
                                <i class="fas fa-check-circle"></i>
                                <span>Token Valid &amp; Connected! ${hasSelectedSignal ? '(Online / Signal Received)' : (hasAnySignal ? '(Token OK, other unit active)' : '(Token OK, waiting for GPS fix)')}</span>
                            </div>
                            ${details}
                        `;
                    }
                } else {
                    if (statusBox) {
                        statusBox.style.display = 'block';
                        statusBox.style.background = 'rgba(239, 68, 68, 0.12)';
                        statusBox.style.border = '1px solid rgba(239, 68, 68, 0.3)';
                        statusBox.style.color = '#ef4444';
                        statusBox.innerHTML = `<i class="fas fa-times-circle"></i> Connection Failed (HTTP ${res.status}). Verify the Blynk Token and Server.`;
                    }
                }
            } catch (err) {
                if (statusBox) {
                    statusBox.style.display = 'block';
                    statusBox.style.background = 'rgba(239, 68, 68, 0.12)';
                    statusBox.style.border = '1px solid rgba(239, 68, 68, 0.3)';
                    statusBox.style.color = '#ef4444';
                    statusBox.innerHTML = `<i class="fas fa-times-circle"></i> Connection error: ${err.message || err}`;
                }
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-plug"></i> Test Connection';
                }
            }
        },

        async saveDeviceConfig() {
            const sel = document.getElementById('gpsConfigVehicleSelect');
            const vehId = sel ? parseInt(sel.value, 10) : null;
            if (!vehId) {
                alert('Please select a vehicle.');
                return;
            }

            const token = (document.getElementById('gpsConfigToken')?.value || '').trim();
            const name = (document.getElementById('gpsConfigDeviceName')?.value || '').trim();
            const server = (document.getElementById('gpsConfigServer')?.value || 'sgp1.blynk.cloud').trim();
            const btn = document.getElementById('gpsSaveConfigBtn');

            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            }

            try {
                const res = await fetch(`${API_BASE}/api/admin/vehicles/${vehId}/gps-config`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        gps_device_token: token,
                        gps_device_name: name,
                        gps_server: server
                    })
                });

                if (res.ok) {
                    const veh = this.fleetVehicles.find(v => v.id === vehId);
                    if (veh) {
                        veh.gps_device_token = token;
                        veh.gps_device_name = name;
                        veh.gps_server = server;
                    }

                    this._updateHeaderDeviceLabel();

                    if (this.selectedVehicleId === vehId) {
                        this.refresh();
                    }

                    this.closeConfigModal();
                    if (typeof showToast === 'function') {
                        showToast('GPS device configuration saved successfully!', 'success');
                    } else {
                        alert('GPS device configuration saved successfully!');
                    }
                } else {
                    const data = await res.json().catch(() => ({}));
                    alert(data.error || 'Failed to save GPS configuration.');
                }
            } catch (err) {
                alert('Save failed: ' + (err.message || err));
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-check"></i> Save Device';
                }
            }
        },

        async startLive() {
            await this.init();
            await this.refresh();
            if (this.timer) clearInterval(this.timer);
            this.timer = setInterval(() => this.refresh(), 10000);
        },

        stopLive() {
            if (this.timer) { clearInterval(this.timer); this.timer = null; }
        }
    };

    // --- ACTIVITY MODULE ---



    const Activity = {



        data: [],
        page: 1,
        limit: 50,
        totalPages: 1,
        totalLogs: 0,
        _filter: 'all',







        _colors: { login:'#00B14F', logout:'#94a3b8', approve:'#00B14F', reject:'#ef4444', create:'#00B14F', update:'#f59e0b', delete:'#ef4444', view:'#5FDBE2' },







        _color(action) {



            const k = Object.keys(this._colors).find(k => action.toLowerCase().includes(k));



            return k ? this._colors[k] : '#00B14F';



        },







        _icon(action) {



            const a = action.toLowerCase();



            if (a.includes('login'))  return 'fa-sign-in-alt';



            if (a.includes('logout')) return 'fa-sign-out-alt';



            if (a.includes('approve')) return 'fa-check';



            if (a.includes('reject')) return 'fa-times';



            if (a.includes('delete')) return 'fa-trash';



            if (a.includes('create') || a.includes('add')) return 'fa-plus';



            if (a.includes('update') || a.includes('edit')) return 'fa-pen';



            return 'fa-history';



        },







        setFilter(filter, btn) {



            this._filter = filter;



            document.querySelectorAll('.act-chip').forEach(b => {



                const active = b.dataset.filter === filter;



                b.style.background   = active ? 'var(--primary)' : 'var(--surface-container)';



                b.style.borderColor  = active ? 'var(--primary)' : 'var(--border)';



                b.style.color        = active ? '#fff' : 'var(--text-secondary)';



            });



            this.page = 1;
            this.refresh(true);
        },

        applyFilters() {
            clearTimeout(this._searchTimer);
            this._searchTimer = setTimeout(() => {
                this.page = 1;
                this.refresh(true);
            }, 300);
        },







        _render(logs) {



            const list = document.getElementById('activityList');



            if (!list) return;



            if (!logs.length) {



                list.innerHTML = '<div style="text-align:center;padding:50px;color:var(--text-muted);">No matching logs found.</div>';



                return;



            }



            const now = new Date();



            list.innerHTML = `<ul style="list-style:none;margin:0;padding:0;background:var(--surface-card,var(--surface));border-radius:16px;overflow:hidden;">` +



                logs.map((l, i) => {



                    const color = this._color(l.action);



                    const icon  = this._icon(l.action);



                    const dt    = new Date(l.created_at);



                    const isToday = dt.toDateString() === now.toDateString();



                    const dateStr = isToday



                        ? dt.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})



                        : dt.toLocaleDateString([], {month:'numeric', day:'numeric', year:'2-digit'});



                    return `



                    <li style="display:flex;align-items:center;gap:14px;padding:13px 16px;${i > 0 ? 'border-top:1px solid var(--border);' : ''}">



                        <div style="flex-shrink:0;width:46px;height:46px;border-radius:50%;background:${color}22;display:flex;align-items:center;justify-content:center;color:${color};font-size:1rem;">



                            <i class="fas ${icon}"></i>



                        </div>



                        <div style="flex:1;min-width:0;">



                            <div style="font-size:0.88rem;font-weight:700;color:var(--text-main);margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${l.admin_name || 'System'}</div>



                            <div style="font-size:0.78rem;color:var(--text-secondary);margin-bottom:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${l.action.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</div>



                            <div style="font-size:0.73rem;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${l.details || '-'}</div>



                        </div>



                        <div style="flex-shrink:0;display:flex;align-items:center;gap:4px;">



                            <span style="font-size:0.72rem;color:${color};font-weight:600;">${dateStr}</span>



                            <i class="fas fa-chevron-right" style="font-size:0.6rem;color:var(--text-muted);"></i>



                        </div>



                    </li>`;



                }).join('') + `</ul>`;



        },







        async prevPage() {
            if (this.page > 1) {
                this.page--;
                await this.refresh(true);
            }
        },

        async nextPage() {
            if (this.page < this.totalPages) {
                this.page++;
                await this.refresh(true);
            }
        },

        async refresh(keepPage = false) {
            const list = document.getElementById('activityList');
            showSkeleton('activityList', 'list');

            if (!list) return;

            if (!keepPage) {
                this.page = 1;
            }

            // Show export button only for super_admin
            const exportBtn = document.getElementById('activityExportBtn');
            if (exportBtn) {
                const user = adminAuth.getUser();
                const isSuperAdmin = user && (user.role === 'super_admin' || user.role === 'superadmin');
                exportBtn.style.display = isSuperAdmin ? 'flex' : 'none';
            }

            list.innerHTML = '<div style="text-align:center;padding:50px;color:var(--text-muted);">Loading activity logs...</div>';

            try {
                let url = `admin/activity-logs?page=${this.page}&limit=${this.limit}`;
                if (this._filter && this._filter !== 'all') {
                    url += `&filter=${encodeURIComponent(this._filter)}`;
                }
                const q = (document.getElementById('activitySearch')?.value || '').trim();
                if (q) {
                    url += `&q=${encodeURIComponent(q)}`;
                }
                const res = await apiFetch(url);
                const responseData = await res.json();
                
                // Check if response is paginated dictionary or legacy array
                if (responseData && responseData.logs) {
                    this.data = responseData.logs || [];
                    this.totalPages = responseData.pages || 1;
                    this.totalLogs = responseData.total || 0;
                } else {
                    this.data = responseData || [];
                    this.totalPages = 1;
                    this.totalLogs = this.data.length;
                }

                // If this is a fresh reload and not page navigation, reset UI values
                if (!keepPage) {
                    const s = document.getElementById('activitySearch');
                    if (s) s.value = '';
                    this._filter = 'all';
                    document.querySelectorAll('.act-chip').forEach(b => {
                        const active = b.dataset.filter === 'all';
                        b.style.background  = active ? 'var(--primary)' : 'var(--surface-container)';
                        b.style.borderColor = active ? 'var(--primary)' : 'var(--border)';
                        b.style.color       = active ? '#fff' : 'var(--text-secondary)';
                    });
                }

                // Update pagination controls UI
                const prevBtn = document.getElementById('btnPrevActivity');
                const nextBtn = document.getElementById('btnNextActivity');
                const pageNum = document.getElementById('activityPageNum');
                const paginationDiv = document.getElementById('activityPagination');

                if (paginationDiv) {
                    paginationDiv.style.display = this.totalPages > 1 ? 'flex' : 'none';
                }
                if (pageNum) {
                    pageNum.innerText = `Page ${this.page} of ${this.totalPages} (${this.totalLogs} logs)`;
                }
                if (prevBtn) prevBtn.disabled = this.page <= 1;
                if (nextBtn) nextBtn.disabled = this.page >= this.totalPages;

                if (!this.data.length) {
                    list.innerHTML = '<div style="text-align:center;padding:50px;color:var(--text-muted);">No activity logs found.</div>';
                    return;
                }

                this._render(this.data);

            } catch (err) {
                console.error('Activity logs fetch error:', err);
                list.innerHTML = '<div style="text-align:center;padding:50px;color:var(--danger);">Failed to load logs.</div>';
            }
        },







        async exportExcel() {
            if (typeof anime !== 'undefined') {
                const _btn = document.getElementById('activityExportBtn') || (window.event && (window.event.currentTarget || window.event.target));
                if (_btn) {
                    anime({
                        targets: (_btn.querySelector && _btn.querySelector('i')) || _btn,
                        translateY: [0, -6, 2, 0],
                        duration: 450,
                        easing: 'easeOutBack'
                    });
                }
            }
            // Double-check role before exporting



            const user = adminAuth.getUser();



            if (!user || (user.role !== 'super_admin' && user.role !== 'superadmin')) {



                showNotification('Only Super Admins can export activity logs.', 'error');



                return;



            }







            const data = this.data || [];



            if (!data.length) {



                showNotification('No activity logs to export.', 'error');



                return;



            }







            if (typeof XLSX === 'undefined') {



                showNotification('Excel library not loaded. Please refresh.', 'error');



                return;



            }







            // Build rows



            const headers = ['#', 'Admin', 'Action', 'Target Type', 'Target ID', 'Details', 'IP Address', 'Timestamp'];



            const rows = [headers];



            data.forEach((log, i) => {



                rows.push([



                    i + 1,



                    log.admin_name || '-',



                    log.action || '-',



                    log.target_type || '-',



                    log.target_id || '-',



                    log.details || '-',



                    log.ip_address || '-',



                    log.created_at ? new Date(log.created_at).toLocaleString() : '-'



                ]);



            });







            try {



                const wb = XLSX.utils.book_new();



                const ws = XLSX.utils.aoa_to_sheet(rows);



                // Auto-width columns



                const colWidths = headers.map((h, i) => ({



                    wch: Math.max(h.length, ...rows.slice(1).map(r => String(r[i] || '').length))



                }));



                ws['!cols'] = colWidths;



                XLSX.utils.book_append_sheet(wb, ws, 'Activity Log');







                const filename = 'autoride_activity_log_' + new Date().toISOString().split('T')[0] + '.xlsx';



                const wboutBase64 = XLSX.write(wb, { bookType: 'xlsx', type: 'base64' });







                // ?? Try Capacitor Filesystem (save to Downloads) ??



                const { Filesystem } = window.Capacitor?.Plugins || {};



                if (Filesystem) {



                    try {



                        const result = await Filesystem.writeFile({



                            path: filename,



                            data: wboutBase64,



                            directory: 'DOWNLOADS',



                            recursive: true



                        });



                        showNotification('Activity log saved to Downloads: ' + filename, 'success');



                        try {



                            const { FileOpener } = window.Capacitor?.Plugins || {};



                            if (FileOpener) await FileOpener.open({ filePath: result.uri, contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });



                        } catch(e) {}



                        return;



                    } catch (fsErr) {



                        try {



                            await Filesystem.writeFile({ path: filename, data: wboutBase64, directory: 'DOCUMENTS', recursive: true });



                            showNotification('Activity log saved to Documents: ' + filename, 'success');



                            return;



                        } catch(e) {}



                    }



                }







                // Browser fallback



                const wboutArray = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });



                const blob = new Blob([wboutArray], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });



                const url = URL.createObjectURL(blob);



                const a = document.createElement('a');



                a.href = url; a.download = filename;



                document.body.appendChild(a); a.click(); document.body.removeChild(a);



                setTimeout(() => URL.revokeObjectURL(url), 5000);



                showNotification('Activity log downloaded!', 'success');







            } catch (err) {



                showNotification('Export failed: ' + err.message, 'error');



            }



        }



    };







    // --- ACTIVE NOW MODULE ---



    const ActiveNow = {



        _timer: null,



        _countdown: {},







        render(allBookings) {



            const active = (allBookings || []).filter(b =>
                b.status === 'Picked Up' || b.status === 'Ongoing'
            );

            // Prioritize due returns (closest return date & time first)
            active.sort((a, b) => {
                const getRet = (x) => {
                    if (!x.end_date) return Infinity;
                    const t = x.end_time ? String(x.end_time).substring(0, 5) : '23:59';
                    const ds = String(x.end_date).split('T')[0];
                    const ts = new Date(`${ds}T${t}:00`).getTime();
                    return isNaN(ts) ? new Date(x.end_date).getTime() : ts;
                };
                return getRet(a) - getRet(b);
            });



            const countEl = document.getElementById('activeNowCount');



            if (countEl) countEl.textContent = active.length;







            const list = document.getElementById('activeNowList');



            if (!list) return;







            if (active.length === 0) {



                list.innerHTML = '<div style="text-align:center;padding:16px;color:var(--text-muted);font-size:0.8rem;background:var(--surface-container);border-radius:14px;">No active rentals right now.</div>';



                return;



            }







            list.innerHTML = active.map((b, i) => {



                const endDate = b.end_date ? new Date(b.end_date) : null;
                const endTimeStr = b.end_time ? String(b.end_time).substring(0, 5) : '';
                let endStr = 'N/A';
                if (endDate) {
                    const dStr = endDate.toLocaleDateString('en-PH', {month:'short',day:'numeric',year:'numeric'});
                    endStr = endTimeStr ? `${dStr} ${endTimeStr}` : dStr;
                }



                const cdId    = 'anCountdown_' + b.id;



                



                // Location handling



                const pickupLoc = b.pickup_location || b.location || 'N/A';



                const dropoffLoc = b.dropoff_location || b.pickup_location || b.location || 'N/A';



                const showBothLocations = pickupLoc !== dropoffLoc && dropoffLoc !== 'N/A';



                



                // Truncate location for display (max 30 chars)



                const truncateLocation = (loc) => {



                    if (!loc || loc === 'N/A') return 'N/A';



                    return loc.length > 30 ? loc.substring(0, 30) + '...' : loc;



                };



                



                const pickupDisplay = truncateLocation(pickupLoc);



                const dropoffDisplay = truncateLocation(dropoffLoc);



                



                return `



                <div style="background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:14px;margin-bottom:10px;border-left:3px solid #00B14F;">



                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">



                        <div style="width:40px;height:40px;border-radius:12px;background:rgba(0,177,79,0.1);display:flex;align-items:center;justify-content:center;flex-shrink:0;">



                            <i class="fas fa-car" style="color:#00B14F;font-size:1rem;"></i>



                        </div>



                        <div style="flex:1;min-width:0;">



                            <div style="font-size:0.88rem;font-weight:800;color:var(--text-main);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${b.car || (b.brand||'') + ' ' + (b.model||'')}</div>



                            <div style="font-size:0.72rem;color:var(--text-muted);">${b.customer_name || 'Customer'} &bull; #${b.id}</div>



                        </div>



                        <span style="background:rgba(0,177,79,0.1);color:#00B14F;border:1px solid rgba(0,177,79,0.25);padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;flex-shrink:0;">ACTIVE</span>



                    </div>



                    



                    <!-- Location Information -->



                    <div style="background:var(--surface-container);border-radius:10px;padding:10px;margin-bottom:8px;">



                        <div style="display:flex;align-items:flex-start;gap:8px;">



                            <i class="fas fa-map-marker-alt" style="color:var(--primary);font-size:1.1rem;flex-shrink:0;margin-top:2px;"></i>



                            <div style="flex:1;min-width:0;">



                                <div style="font-size:0.58rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:4px;">Location</div>



                                <div style="display:flex;flex-direction:column;gap:4px;">



                                    <div title="${pickupLoc}" style="font-size:0.78rem;font-weight:700;color:var(--text-main);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">



                                        <span style="font-size:0.65rem;color:var(--text-muted);font-weight:600;">Pickup:</span> ${pickupDisplay}



                                    </div>



                                    ${showBothLocations ? `



                                    <div style="display:flex;align-items:center;gap:4px;margin:2px 0;">



                                        <i class="fas fa-arrow-down" style="color:var(--text-muted);font-size:0.65rem;"></i>



                                    </div>



                                    <div title="${dropoffLoc}" style="font-size:0.78rem;font-weight:600;color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">



                                        <span style="font-size:0.65rem;color:var(--text-muted);font-weight:600;">Dropoff:</span> ${dropoffDisplay}



                                    </div>



                                    ` : ''}



                                </div>



                            </div>



                        </div>



                    </div>



                    



                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;">



                        <div style="background:var(--surface-container);border-radius:10px;padding:8px 10px;">



                            <div style="font-size:0.58rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:2px;">Return By</div>



                            <div style="font-size:0.78rem;font-weight:700;color:var(--text-main);">${endStr}</div>



                        </div>



                        <div style="background:var(--surface-container);border-radius:10px;padding:8px 10px;">



                            <div style="font-size:0.58rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:2px;">Time Left</div>



                            <div id="${cdId}" style="font-size:0.78rem;font-weight:800;color:#00B14F;">-</div>



                        </div>



                    </div>



                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">



                        <button onclick="Bookings.view(${b.id})" style="padding:9px 8px;background:rgba(99,102,241,0.12);color:#818cf8;border:1px solid rgba(99,102,241,0.25);border-radius:10px;font-size:0.72rem;font-weight:700;cursor:pointer;">



                            <i class="fas fa-eye" style="margin-right:4px;"></i>View Details



                        </button>



                        <button onclick="AdminChatWithUser(${b.id})" style="padding:9px 8px;background:rgba(0,177,79,0.1);color:#00B14F;border:1px solid rgba(0,177,79,0.25);border-radius:10px;font-size:0.72rem;font-weight:700;cursor:pointer;">



                            <i class="fas fa-comments" style="margin-right:4px;"></i>Chat



                        </button>



                    </div>



                </div>`;



            }).join('');







            // Start countdowns



            this._stopCountdowns();



            active.forEach(b => {



                if (!b.end_date) return;



                const endParts = this._normDate(b.end_date).split('-');
                let endH = 23, endM = 59, endS = 59;
                if (b.end_time) {
                    const tp = String(b.end_time).substring(0, 5).split(':');
                    if (tp.length >= 2) {
                        endH = parseInt(tp[0], 10) || 0;
                        endM = parseInt(tp[1], 10) || 0;
                        endS = 0;
                    }
                }
                const endDt = new Date(parseInt(endParts[0], 10), parseInt(endParts[1], 10)-1, parseInt(endParts[2], 10), endH, endM, endS);
                const cdId = 'anCountdown_' + b.id;
                const updateCountdown = () => {
                    const el = document.getElementById(cdId);
                    if (!el) { clearInterval(this._countdown[b.id]); return; }
                    const ms = endDt - new Date();
                    if (ms <= 0) { el.textContent = 'Ended'; el.style.color = '#ef4444'; return; }
                    const d = Math.floor(ms/86400000);
                    const h = Math.floor((ms%86400000)/3600000);
                    const m = Math.floor((ms%3600000)/60000);
                    const s = Math.floor((ms%60000)/1000);
                    el.textContent = d > 0
                        ? `${d}d ${h}h ${String(m).padStart(2,'0')}m ${String(s).padStart(2,'0')}s`
                        : `${h}h ${String(m).padStart(2,'0')}m ${String(s).padStart(2,'0')}s`;
                    el.style.color = ms < 86400000 ? '#ef4444' : '#00B14F';
                };
                updateCountdown();
                this._countdown[b.id] = setInterval(updateCountdown, 1000);



            });







            // Auto-refresh every 30s



            if (this._timer) clearInterval(this._timer);



            this._timer = setInterval(() => {



                const label = document.getElementById('activeNowRefreshLabel');



                if (label) label.textContent = 'refreshing...';



                Bookings.refresh().then(() => {



                    if (label) label.textContent = 'auto-refresh 30s';



                }).catch(() => {



                    if (label) label.textContent = 'auto-refresh 30s';



                });



            }, 30000);



        },







        _normDate(d) {



            if (!d) return '';



            if (/^\d{4}-\d{2}-\d{2}$/.test(String(d))) return String(d);



            const dt = new Date(d);



            if (isNaN(dt.getTime())) return String(d);



            return dt.getFullYear() + '-' + String(dt.getMonth()+1).padStart(2,'0') + '-' + String(dt.getDate()).padStart(2,'0');



        },







        _stopCountdowns() {



            Object.values(this._countdown).forEach(t => clearInterval(t));



            this._countdown = {};



        },







        stop() {



            this._stopCountdowns();



            if (this._timer) { clearInterval(this._timer); this._timer = null; }



        }



    };







    // --- PAST BOOKINGS MODULE ---



    const PastBookings = {



        data: [],



        filteredData: [],



        currentPage: 1,



        pageSize: 10,



        sortBy: 'completion_date_desc',



        totalPages: 1,







        async load() {



            const loadingEl = document.getElementById('pastBookingsLoading');



            const emptyEl = document.getElementById('pastBookingsEmpty');



            const tableEl = document.getElementById('pastBookingsTable');



            



            // Show loading state



            if (loadingEl) loadingEl.style.display = 'block';



            if (emptyEl) emptyEl.classList.add('hidden');



            if (tableEl) tableEl.style.display = 'none';







            try {



                // Fetch past bookings from API



                const res = await fetch(`${API_BASE}/api/bookings/past?page=${this.currentPage}&page_size=${this.pageSize}&sort_by=${this.sortBy}`);



                



                if (!res.ok) {



                    throw new Error(`Server error: ${res.status}`);



                }



                



                const responseData = await res.json();



                



                // Handle response format - could be array or object with pagination



                if (Array.isArray(responseData)) {



                    this.data = responseData;



                    this.filteredData = [...responseData];



                    this.totalPages = Math.ceil(responseData.length / this.pageSize);



                } else if (responseData.bookings) {



                    this.data = responseData.bookings;



                    this.filteredData = [...responseData.bookings];



                    this.totalPages = responseData.total_pages || 1;



                } else {



                    this.data = [];



                    this.filteredData = [];



                    this.totalPages = 1;



                }



                



                this.renderTable();



                this.updatePaginationControls();



                



            } catch (err) {



                console.error('Failed to load past bookings:', err);



                



                // Hide loading, show empty state with error



                if (loadingEl) loadingEl.style.display = 'none';



                if (emptyEl) {



                    emptyEl.classList.remove('hidden');



                    emptyEl.innerHTML = `



                        <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 16px; opacity: 0.3; color: var(--danger);"></i>



                        <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; color: var(--text-main);">Failed to Load</h3>



                        <p style="font-size: 0.85rem; margin-bottom: 16px;">${err.message}</p>



                        <button onclick="PastBookings.load()" style="padding: 10px 20px; background: var(--primary); border: none; color: white; border-radius: 8px; font-size: 0.85rem; font-weight: 700; cursor: pointer;">Retry</button>



                    `;



                }



                if (tableEl) tableEl.style.display = 'none';



            }



        },







        renderTable() {



            const tbody = document.getElementById('pastBookingsTableBody');



            const loadingEl = document.getElementById('pastBookingsLoading');



            const emptyEl = document.getElementById('pastBookingsEmpty');



            const tableEl = document.getElementById('pastBookingsTable');



            



            // Hide loading



            if (loadingEl) loadingEl.style.display = 'none';



            



            if (!tbody) return;



            



            if (this.filteredData.length === 0) {



                // Show empty state



                if (emptyEl) emptyEl.classList.remove('hidden');



                if (tableEl) tableEl.style.display = 'none';



                return;



            }



            



            // Show table, hide empty state



            if (emptyEl) emptyEl.classList.add('hidden');



            if (tableEl) tableEl.style.display = 'table';



            



            // Render table rows



            tbody.innerHTML = this.filteredData.map(b => {



                const completionDate = b.completion_date || b.updated_at || b.end_date;



                const completionDateStr = completionDate ? new Date(completionDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A';



                const startDateStr = b.start_date ? new Date(b.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'N/A';



                const endDateStr = b.end_date ? new Date(b.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'N/A';



                const rentalDates = `${startDateStr} - ${endDateStr}`;



                const totalPrice = b.total_price ? parseFloat(b.total_price).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00';



                



                return `



                    <tr style="border-bottom: 1px solid var(--border); transition: background 0.2s;">



                        <td style="padding: 12px 10px; font-size: 0.8rem; font-weight: 700; color: var(--text-secondary);">#${b.id}</td>



                        <td style="padding: 12px 10px; font-size: 0.85rem; font-weight: 600; color: var(--text-main);">${b.customer_name || 'N/A'}</td>



                        <td style="padding: 12px 10px; font-size: 0.85rem; color: var(--text-secondary);">${b.car || b.vehicle || 'N/A'}</td>



                        <td style="padding: 12px 10px; font-size: 0.8rem; color: var(--text-secondary);">${rentalDates}</td>



                        <td style="padding: 12px 10px; font-size: 0.8rem; color: var(--text-secondary);">${completionDateStr}</td>



                        <td style="padding: 12px 10px; text-align: right; font-size: 0.9rem; font-weight: 700; color: var(--success);">₱${totalPrice}</td>



                        <td style="padding: 12px 10px; text-align: center;">



                            <button onclick="Bookings.view(${b.id})" style="padding: 6px 12px; background: var(--primary); border: none; color: white; border-radius: 6px; font-size: 0.75rem; font-weight: 600; cursor: pointer; transition: all 0.2s;">



                                <i class="fas fa-eye" style="margin-right: 4px;"></i> View



                            </button>
                                <button onclick="ArchivedBookings.archiveSingle(${b.id})" style="padding: 6px 10px; background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.3); color: #8b5cf6; border-radius: 6px; font-size: 0.75rem; font-weight: 700; cursor: pointer; margin-left: 6px;" title="Archive Booking">
                                    <i class="fas fa-archive"></i> Archive
                                </button>



                        </td>



                    </tr>



                `;



            }).join('');



        },







        updatePaginationControls() {



            const pageInfo = document.getElementById('pastBookingsPageInfo');



            const prevBtn = document.getElementById('pastBookingsPrevBtn');



            const nextBtn = document.getElementById('pastBookingsNextBtn');



            



            if (pageInfo) {



                pageInfo.textContent = `Page ${this.currentPage} of ${this.totalPages}`;



            }



            



            if (prevBtn) {



                prevBtn.disabled = this.currentPage <= 1;



                prevBtn.style.opacity = this.currentPage <= 1 ? '0.5' : '1';



                prevBtn.style.cursor = this.currentPage <= 1 ? 'not-allowed' : 'pointer';



            }



            



            if (nextBtn) {



                nextBtn.disabled = this.currentPage >= this.totalPages;



                nextBtn.style.opacity = this.currentPage >= this.totalPages ? '0.5' : '1';



                nextBtn.style.cursor = this.currentPage >= this.totalPages ? 'not-allowed' : 'pointer';



            }



        }



    };







    // Global functions for past bookings



    window.loadPastBookings = function() {



        PastBookings.load();



    };







    window.filterPastBookings = function() {



        const searchInput = document.getElementById('pastBookingsSearch');



        if (!searchInput) return;



        



        const query = searchInput.value.toLowerCase().trim();



        



        if (!query) {



            PastBookings.filteredData = [...PastBookings.data];



        } else {



            PastBookings.filteredData = PastBookings.data.filter(b => {



                const customerName = (b.customer_name || '').toLowerCase();



                const bookingId = String(b.id || '');



                const vehicle = (b.car || b.vehicle || '').toLowerCase();



                



                return customerName.includes(query) || 



                       bookingId.includes(query) || 



                       vehicle.includes(query);



            });



        }



        



        PastBookings.currentPage = 1;



        PastBookings.renderTable();



        PastBookings.updatePaginationControls();



    };







    window.sortPastBookings = function() {



        const sortSelect = document.getElementById('pastBookingsSort');



        if (!sortSelect) return;



        



        PastBookings.sortBy = sortSelect.value;



        PastBookings.currentPage = 1;



        PastBookings.load();



    };







    window.changePastBookingsPageSize = function() {



        const pageSizeSelect = document.getElementById('pastBookingsPageSize');



        if (!pageSizeSelect) return;



        



        PastBookings.pageSize = parseInt(pageSizeSelect.value);



        PastBookings.currentPage = 1;



        PastBookings.load();



    };







    window.previousPastBookingsPage = function() {



        if (PastBookings.currentPage > 1) {



            PastBookings.currentPage--;



            PastBookings.load();



        }



    };







    window.nextPastBookingsPage = function() {



        if (PastBookings.currentPage < PastBookings.totalPages) {



            PastBookings.currentPage++;



            PastBookings.load();



        }



    };







    // --- EXTENSIONS MODULE ---



    window.AdminChatWithUser = async function(bookingId, directUserId, directUserName) {
        // Find user info from Bookings.data, FleetCalendar.bookings, PastBookings.data, or ArchivedBookings.data
        const b = (typeof Bookings !== 'undefined' && Bookings.data ? Bookings.data.find(x => x.id == bookingId) : null)
            || (typeof FleetCalendar !== 'undefined' && FleetCalendar.bookings ? FleetCalendar.bookings.find(x => x.id == bookingId) : null)
            || (typeof PastBookings !== 'undefined' && PastBookings.data ? PastBookings.data.find(x => x.id == bookingId) : null)
            || (typeof ArchivedBookings !== 'undefined' && ArchivedBookings.data ? ArchivedBookings.data.find(x => x.id == bookingId) : null)
            || (typeof Bookings !== 'undefined' && Bookings.currentBooking ? Bookings.currentBooking : null);

        let userId = directUserId || (b ? (b.user_id || b.customer_id) : null);
        let name = directUserName || (b ? (b.customer_name || b.user_name || "Customer") : "Customer");

        // If not found in memory, attempt resolution via API
        if (!userId) {
            try {
                const res = await fetch(`${API_BASE}/api/admin/bookings/${bookingId}/license-details`);
                if (res.ok) {
                    const d = await res.json();
                    if (d && d.user_id) {
                        userId = d.user_id;
                        name = d.full_name || name;
                    }
                }
            } catch(e) {}
        }

        if (!userId) {
            try {
                const res = await fetch(`${API_URL}/bookings/${bookingId}`);
                if (res.ok) {
                    const bk = await res.json();
                    if (bk && bk.user_id) {
                        userId = bk.user_id;
                        name = bk.customer_name || bk.user_name || name;
                    }
                }
            } catch(e) {}
        }

        if (!userId && name && name !== "Customer") {
            try {
                const res = await fetch(`${API_URL}/users/search?q=${encodeURIComponent(name)}&limit=1`);
                if (res.ok) {
                    const users = await res.json();
                    if (Array.isArray(users) && users.length > 0) {
                        userId = users[0].id;
                        name = users[0].full_name || name;
                    }
                }
            } catch(e) {}
        }

        // Open chat tab directly into user's chat box
        if (userId && typeof AdminChat !== 'undefined' && typeof AdminChat.openConversation === 'function') {
            window._suppressChatInbox = true;
            if (typeof switchTab === 'function') switchTab("chat");
            if (typeof navTo === 'function') navTo("chat");
            AdminChat.openConversation(userId, name);
        } else {
            if (typeof switchTab === 'function') switchTab("chat");
            if (typeof navTo === 'function') navTo("chat");
            setTimeout(() => {
                if (typeof AdminChat !== 'undefined' && typeof AdminChat.showUserSearch === 'function') {
                    AdminChat.showUserSearch();
                    const inp = document.getElementById("acUserSearchInput");
                    if (inp) {
                        inp.value = name;
                        AdminChat.searchUsers(name);
                    }
                }
            }, 300);
        }
    };







    const Extensions = {



        async load() {



            const list = document.getElementById('extensionRequestsList');



            if (!list) return;



            list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin"></i></div>';



            try {



                const res = await fetch(`${API_URL}/admin/extensions`);



                const data = res.ok ? await res.json() : [];



                const badge = document.getElementById('extReqBadge');



                if (badge) { badge.textContent = data.length; badge.style.display = data.length > 0 ? 'inline-flex' : 'none'; }



                // Also update the tab button badge



                const tabBadge = document.getElementById('extTabBadge');



                if (tabBadge) { tabBadge.textContent = data.length; tabBadge.style.display = data.length > 0 ? 'inline-flex' : 'none'; }



                if (!data.length) { list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);font-size:0.8rem;">No pending extension requests.</div>'; return; }



                list.innerHTML = data.map(e => `



                    <div data-ext-id="${e.id}" style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:14px;margin-bottom:10px;border-left:3px solid #f59e0b;">



                        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">



                            <div>



                                <div style="font-size:0.7rem;color:var(--text-muted);font-weight:700;">Booking #${e.booking_id}</div>



                                <div style="font-size:0.88rem;font-weight:800;color:var(--text-main);">${e.customer_name || 'Customer'}</div>



                                <div style="font-size:0.75rem;color:var(--text-muted);">${e.car || ''}</div>



                            </div>



                            <span style="background:rgba(245,158,11,0.15);color:#f59e0b;border:1px solid rgba(245,158,11,0.3);padding:3px 8px;border-radius:20px;font-size:0.62rem;font-weight:800;">PENDING</span>



                        </div>



                        <div style="background:var(--surface-container);border-radius:10px;padding:10px;margin-bottom:10px;font-size:0.8rem;">



                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">



                                <div><div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Current End</div><div style="font-weight:700;color:var(--text-main);">${e.original_end_date}</div></div>



                                <div><div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Requested End</div><div style="font-weight:700;color:#f59e0b;">${e.new_end_date}</div></div>



                                <div><div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Extension</div><div style="font-weight:700;color:var(--text-main);">${e.extension_days} day${e.extension_days !== 1 ? 's' : ''}</div></div>



                                <div><div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Amount Paid</div><div style="font-weight:800;color:#00B14F;">₱${parseFloat(e.extension_price||0).toLocaleString()}</div></div>



                            </div>



                            <div style="margin-top:8px;font-size:0.75rem;color:var(--text-muted);">Method: <span style="color:var(--text-main);font-weight:600;">${e.payment_method || 'N/A'}</span>${e.reference_number ? ' &bull; Ref: ' + e.reference_number : ''}</div>



                            ${e.payment_proof_url ? `<img src="${e.payment_proof_url}" style="width:100%;border-radius:8px;margin-top:8px;max-height:150px;object-fit:contain;background:rgba(0,0,0,0.2);">` : ''}



                        </div>



                        <div class="ext-action-btns" style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">



                            <button onclick="Extensions.approve(${e.id})" style="padding:10px;background:var(--primary);color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;">



                                <i class="fas fa-check" style="margin-right:4px;"></i>Approve



                            </button>



                            <button onclick="Extensions.reject(${e.id})" style="padding:10px;background:rgba(239,68,68,0.12);color:#ef4444;border:1px solid rgba(239,68,68,0.3);border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;">



                                <i class="fas fa-times" style="margin-right:4px;"></i>Reject



                            </button>



                        </div>



                    </div>



                `).join('');



            } catch(err) {



                if (list) list.innerHTML = '<div style="color:var(--danger);text-align:center;padding:12px;">Failed to load extensions.</div>';



            }



        },







        async approve(extId) {



            if (!confirm('Approve this extension request?\n\nThis will update the booking end date.')) return;



            try {



                const res = await fetch(`${API_URL}/admin/extensions/${extId}/approve`, { method: 'PUT' });



                const data = await res.json();



                if (res.ok) {



                    showNotification('Extension approved! Booking end date updated.', 'success');



                    this.load();



                    Bookings.refresh();



                } else { showNotification(data.error || 'Failed to approve', 'error'); }



            } catch(err) { showNotification('Network error', 'error'); }



        },







        async reject(extId) {



            const note = prompt('Reason for rejection (customer will be notified):');



            if (note === null) return;



            try {



                const res = await fetch(`${API_URL}/admin/extensions/${extId}/reject`, {



                    method: 'PUT',



                    headers: { 'Content-Type': 'application/json' },



                    body: JSON.stringify({ note: note || 'Extension rejected. Refund will be processed.' })



                });



                const data = await res.json();



                if (!res.ok) { showNotification(data.error || 'Failed to reject', 'error'); return; }







                showNotification('Extension rejected. Customer notified.', 'success');







                // Show inline refund form for this extension



                const refundAmount = data.refund_amount || 0;



                const bookingId    = data.booking_id;



                const extensionId  = data.extension_id || extId;







                // Find the card and replace action buttons with refund panel



                const card = document.querySelector(`[data-ext-id="${extId}"]`);



                if (card) {



                    const actionDiv = card.querySelector('.ext-action-btns');



                    if (actionDiv) {



                        actionDiv.innerHTML = `



                            <div style="border:1.5px solid #f59e0b;border-radius:12px;padding:14px;background:rgba(245,158,11,0.06);margin-top:4px;">



                                <div style="display:flex;align-items:center;gap:6px;margin-bottom:12px;">



                                    <i class="fas fa-undo-alt" style="color:#f59e0b;"></i>



                                    <span style="font-size:0.85rem;font-weight:800;color:#f59e0b;">Process Refund � ?${parseFloat(refundAmount).toLocaleString()}</span>



                                </div>



                                <div style="display:flex;flex-direction:column;gap:8px;">



                                    <input id="extRfAmt_${extensionId}" type="number" step="0.01" min="0" max="500000" value="${parseFloat(refundAmount).toFixed(2)}"



                                        placeholder="Amount (PHP)"



                                        style="width:100%;padding:9px;border:1px solid #e2e8f0;border-radius:8px;font-size:0.85rem;">



                                    <select id="extRfMethod_${extensionId}" style="width:100%;padding:9px;border:1px solid #e2e8f0;border-radius:8px;font-size:0.85rem;">



                                        <option value="GCash">GCash</option>



                                        <option value="Maya">Maya</option>



                                        <option value="Bank Transfer">Bank Transfer</option>



                                        <option value="Cash">Cash</option>



                                    </select>



                                    <input id="extRfRef_${extensionId}" type="text" maxlength="50" placeholder="Reference # (optional)"



                                        style="width:100%;padding:9px;border:1px solid #e2e8f0;border-radius:8px;font-size:0.85rem;">



                                    <input id="extRfProof_${extensionId}" type="file" accept="image/*" style="font-size:0.75rem;color:#64748b;">



                                    <button onclick="Extensions.processExtRefund(${extensionId}, ${bookingId})"



                                        style="width:100%;padding:11px;background:#f59e0b;color:white;border:none;border-radius:10px;font-size:0.85rem;font-weight:800;cursor:pointer;">



                                        <i class="fas fa-paper-plane" style="margin-right:5px;"></i>Confirm Refund Sent



                                    </button>



                                </div>



                            </div>`;



                    }



                } else {



                    // Fallback: reload the list



                    this.load();



                }



                Bookings.refresh();



            } catch(err) { showNotification('Network error', 'error'); }



        },







        async processExtRefund(extensionId, bookingId) {



            const user   = adminAuth.getUser();



            const amount = (document.getElementById(`extRfAmt_${extensionId}`)    || {}).value;



            const method = (document.getElementById(`extRfMethod_${extensionId}`) || {}).value || 'GCash';



            const ref    = (document.getElementById(`extRfRef_${extensionId}`)    || {}).value || '';



            const proofEl = document.getElementById(`extRfProof_${extensionId}`);







            if (!amount || parseFloat(amount) <= 0) {



                showNotification('Please enter a valid amount.', 'error');



                return;



            }







            const btn = event.target;



            btn.disabled = true;



            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';







            try {



                const fd = new FormData();



                fd.append('booking_id', bookingId);



                fd.append('extension_id', extensionId);



                fd.append('admin_id', user ? user.id : 1);



                fd.append('refund_amount', amount);



                fd.append('refund_method', method);



                fd.append('refund_ref', ref);



                fd.append('refund_note', `Extension #${extensionId} refund`);



                if (proofEl && proofEl.files && proofEl.files[0]) fd.append('proof', proofEl.files[0]);







                const res  = await fetch(`${API_URL}/admin/process-refund`, { method: 'POST', body: fd });



                const data = await res.json();



                if (!res.ok) throw new Error(data.error || 'Refund failed');







                showNotification(`Refund of ?${parseFloat(amount).toLocaleString()} confirmed. Customer notified.`, 'success');



                this.load();



                Bookings.refresh();



            } catch(err) {



                showNotification(err.message, 'error');



                btn.disabled = false;



                btn.innerHTML = '<i class="fas fa-paper-plane" style="margin-right:5px;"></i>Confirm Refund Sent';



            }



        }



    };







    window.switchBookingTab = function(tab) {



        // Hide all tab contents



        const tabContents = document.querySelectorAll('.booking-tab-content');



        tabContents.forEach(content => {



            content.style.display = 'none';



        });



        



        // Remove active class from all tab buttons



        const tabButtons = document.querySelectorAll('.booking-tab-btn');



        tabButtons.forEach(btn => {



            btn.style.border = '1px solid var(--border)';



            btn.style.background = 'var(--surface-container)';



            btn.style.color = 'var(--text-secondary)';



        });



        



        // Show selected tab content



        if (tab === 'active') {



            const activeTab = document.getElementById('tabActive');



            if (activeTab) activeTab.style.display = 'block';



            const activeBtn = document.getElementById('tabBtnActive');



            if (activeBtn) {



                activeBtn.style.border = '1px solid var(--primary)';



                activeBtn.style.background = 'var(--primary)';



                activeBtn.style.color = 'white';



            }



            // Refresh active bookings



            if (typeof ActiveNow !== 'undefined' && typeof Bookings !== 'undefined') {



                ActiveNow.render(Bookings.data);



            }



        } else if (tab === 'past') {



            const pastTab = document.getElementById('tabPast');



            if (pastTab) pastTab.style.display = 'block';



            const pastBtn = document.getElementById('tabBtnPast');



            if (pastBtn) {



                pastBtn.style.border = '1px solid var(--primary)';



                pastBtn.style.background = 'var(--primary)';



                pastBtn.style.color = 'white';



            }



            // Load past bookings



            PastBookings.load();



        } else if (tab === 'new') {



            const newTab = document.getElementById('tabNew');



            if (newTab) newTab.style.display = 'block';



            const newBtn = document.getElementById('tabBtnNew');



            if (newBtn) {



                newBtn.style.border = '1px solid var(--primary)';



                newBtn.style.background = 'var(--primary)';



                newBtn.style.color = 'white';



            }



            if (typeof Bookings !== 'undefined') {



                Bookings.renderNew();



            }



            if (typeof Extensions !== 'undefined') {



                Extensions.load();



            }



        } else if (tab === 'all') {



            const allTab = document.getElementById('tabAll');



            if (allTab) allTab.style.display = 'block';



            const allBtn = document.getElementById('tabBtnAll');



            if (allBtn) {



                allBtn.style.border = '1px solid var(--primary)';



                allBtn.style.background = 'var(--primary)';



                allBtn.style.color = 'white';



            }



            if (typeof Bookings !== 'undefined') {



                Bookings.render();



            }



        } else if (tab === 'extensions') {



            const extTab = document.getElementById('tabExtensions');



            if (extTab) extTab.style.display = 'block';



            const extBtn = document.getElementById('tabBtnExtensions');



            if (extBtn) {



                extBtn.style.border = '1px solid var(--primary)';



                extBtn.style.background = 'var(--primary)';



                extBtn.style.color = 'white';



            }



            if (typeof Extensions !== 'undefined') {



                Extensions.load();



            }



        } else if (tab === 'refunds') {
            const refTab = document.getElementById('tabRefunds');
            if (refTab) refTab.style.display = 'block';
            const refBtn = document.getElementById('tabBtnRefunds');
            if (refBtn) {
                refBtn.style.border = '1px solid var(--primary)';
                refBtn.style.background = 'var(--primary)';
                refBtn.style.color = 'white';
            }
            if (typeof Refunds !== 'undefined') {
                Refunds.load();
            } else if (tab === 'archived') {
            const archTab = document.getElementById('tabArchived');
            if (archTab) archTab.style.display = 'block';
            const archBtn = document.getElementById('tabBtnArchived');
            if (archBtn) {
                archBtn.style.border = '1px solid #8b5cf6';
                archBtn.style.background = '#8b5cf6';
                archBtn.style.color = 'white';
            }
            if (typeof ArchivedBookings !== 'undefined') {
                ArchivedBookings.load();
            }
        }
        }



    };







    // --- REFUNDS MODULE ---
    const Refunds = {
        _filter: 'needs',
        _all: [],

        async load() {
            try {
                const list = document.getElementById('refundsList');
                if (list) {
                    list.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-muted);font-size:0.8rem;">Loading...</div>';
                }
                const token = localStorage.getItem('admin_token') || localStorage.getItem('token');
                const user = adminAuth.getUser();
                const adminId = user ? user.id : '';
                const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
                const res = await fetch(`${API_URL}/bookings?admin_id=${adminId}`, { headers });
                if (!res.ok) throw new Error('Failed to fetch bookings');
                const data = await res.json();
                this._all = data.bookings || data || [];
                this.render(this._all);
            } catch(e) {
                console.error('Refunds.load error:', e);
                const list = document.getElementById('refundsList');
                if (list) {
                    list.innerHTML = `<div style="text-align:center;padding:24px;color:#ef4444;font-size:0.8rem;">Failed to load. <a href="#" onclick="Refunds.load()" style="color:var(--primary);">Retry</a></div>`;
                }
            }
        },

        setFilter(filter, btn) {
            this._filter = filter;
            document.querySelectorAll('.rf-chip').forEach(b => {
                const active = b.dataset.filter === filter;
                b.style.background  = active ? 'var(--primary)' : 'var(--surface-container)';
                b.style.borderColor = active ? 'var(--primary)' : 'var(--border)';
                b.style.color       = active ? 'white' : 'var(--text-main)';
                b.classList.toggle('rf-chip-active', active);
                
                const badge = b.querySelector('span');
                if (badge) {
                    if (active) {
                        badge.style.background = 'rgba(255,255,255,0.2)';
                        badge.style.color = 'white';
                    } else {
                        badge.style.background = 'rgba(0,0,0,0.08)';
                        badge.style.color = 'var(--text-secondary)';
                    }
                }
            });
            this._renderFiltered();
        },

        render(bookings) {
            this._all = bookings;
            
            const needsRefund = this._all.filter(b =>
                b.status === 'Cancelled' &&
                ['Paid', 'Partially Paid'].includes(b.payment_status)
            );
            const refundPending = this._all.filter(b =>
                b.payment_status === 'Refund Pending'
            );
            const refunded = this._all.filter(b =>
                b.payment_status === 'Refunded'
            );

            // Update counts
            const setCount = (id, count) => { const el = document.getElementById(id); if (el) el.textContent = count; };
            setCount('needsRefundCount', needsRefund.length);
            setCount('refundPendingCount', refundPending.length);
            setCount('refundedCount', refunded.length);

            // Badge on tab button
            const urgentCount = needsRefund.length + refundPending.length;
            const badge = document.getElementById('refundTabBadge');
            if (badge) { badge.textContent = urgentCount; badge.style.display = urgentCount > 0 ? 'flex' : 'none'; }

            this._renderFiltered();
        },

        _renderFiltered() {
            const list = document.getElementById('refundsList');
            if (!list) return;

            let filteredList = [];
            let type = 'needs';
            if (this._filter === 'needs') {
                filteredList = this._all.filter(b =>
                    b.status === 'Cancelled' &&
                    ['Paid', 'Partially Paid'].includes(b.payment_status)
                );
                type = 'needs';
            } else if (this._filter === 'pending') {
                filteredList = this._all.filter(b =>
                    b.payment_status === 'Refund Pending'
                );
                type = 'pending';
            } else if (this._filter === 'refunded') {
                filteredList = this._all.filter(b =>
                    b.payment_status === 'Refunded'
                );
                type = 'done';
            }

            if (!filteredList.length) {
                const emptyMsgs = { needs: 'No cancelled bookings needing refund.', pending: 'No refunds pending.', refunded: 'No completed refunds yet.' };
                list.innerHTML = `<div style="text-align:center;padding:24px;color:var(--text-muted);font-size:0.8rem;">${emptyMsgs[this._filter]}</div>`;
                return;
            }

            list.innerHTML = filteredList.map(b => {
                const accentColor = type === 'needs' ? '#ef4444' : type === 'pending' ? '#f59e0b' : '#10b981';
                const amount = parseFloat(b.refund_amount || b.amount_paid || 0).toLocaleString('en-PH', {minimumFractionDigits:2});
                const refundAmt = parseFloat(b.amount_paid || 0).toLocaleString('en-PH', {minimumFractionDigits:2});
                return `
                <div style="background:var(--surface);border:1px solid var(--border);border-left:3px solid ${accentColor};border-radius:12px;padding:14px 16px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                        <div>
                            <span style="font-size:0.7rem;font-weight:800;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;">Booking #${b.id}</span>
                            <div style="font-size:0.95rem;font-weight:800;color:var(--text-main);margin-top:2px;">${b.full_name || b.customer_name || 'Customer'}</div>
                            <div style="font-size:0.78rem;color:var(--text-muted);">${b.brand || ''} ${b.model || ''} &bull; ${b.start_date || ''} &ndash; ${b.end_date || ''}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:0.72rem;color:var(--text-muted);font-weight:700;">Amount Paid</div>
                            <div style="font-size:1rem;font-weight:900;color:${accentColor};">₱${type === 'done' ? amount : refundAmt}</div>
                        </div>
                    </div>
                    <div style="display:flex;gap:8px;flex-wrap:wrap;">
                        <span style="font-size:0.68rem;font-weight:700;padding:3px 10px;border-radius:20px;background:rgba(0,0,0,0.06);color:var(--text-secondary);">Status: ${b.status}</span>
                        <span style="font-size:0.68rem;font-weight:700;padding:3px 10px;border-radius:20px;background:rgba(0,0,0,0.06);color:var(--text-secondary);">Payment: ${b.payment_status}</span>
                        ${type === 'needs' ? `<button onclick="Bookings.triggerRefund(${b.id})" style="margin-left:auto;padding:6px 14px;background:#ef4444;color:white;border:none;border-radius:8px;font-size:0.72rem;font-weight:800;cursor:pointer;"><i class='fas fa-bolt' style='margin-right:4px;'></i>Trigger Refund</button>` : ''}
                        ${type === 'pending' ? `<button onclick="Bookings.openDetail(${b.id})" style="margin-left:auto;padding:6px 14px;background:#f59e0b;color:white;border:none;border-radius:8px;font-size:0.72rem;font-weight:800;cursor:pointer;"><i class='fas fa-eye' style='margin-right:4px;'></i>View & Process</button>` : ''}
                        ${type === 'done' ? `<span style="margin-left:auto;font-size:0.68rem;font-weight:800;color:#10b981;"><i class='fas fa-check-circle' style='margin-right:4px;'></i>Refund Completed</span>` : ''}
                    </div>
                </div>`;
            }).join('');
        }
    };
    window.Refunds = Refunds;



    // --- REPORTS MODULE -->



    const Reports = {



        chart: null,



        chartBookings: null,



        chartPie: null,



        _loaded: false,



        _filter: 'year',



        _rawData: null,







        setFilter(period, btn) {



            this._filter = period;



            document.querySelectorAll('.rpt-filter-btn').forEach(b => {



                b.style.background = 'var(--surface-container)';



                b.style.borderColor = 'var(--border)';



                b.style.color = 'var(--text-secondary)';



            });



            btn.style.background = 'var(--primary)';



            btn.style.borderColor = 'var(--primary)';



            btn.style.color = 'white';



            // Set default date range based on period



            const now = new Date();
            const y = now.getFullYear();
            const m = String(now.getMonth() + 1).padStart(2, '0');
            const d = String(now.getDate()).padStart(2, '0');
            let from, to;
            if (period === 'day') {
                from = to = `${y}-${m}-${d}`;
            } else if (period === 'month') {
                const lastDay = new Date(y, now.getMonth() + 1, 0).getDate();
                from = `${y}-${m}-01`;
                to = `${y}-${m}-${String(lastDay).padStart(2, '0')}`;
            } else {
                from = `${y}-01-01`;
                to = `${y}-12-31`;
            }



            document.getElementById('rptDateFrom').value = from;



            document.getElementById('rptDateTo').value = to;



            this.refresh();



        },







        async refresh() {
            this._loaded = true;
            try {
                const from = document.getElementById('rptDateFrom').value;
                const to = document.getElementById('rptDateTo').value;
                const params = from && to ? `&date_from=${from}&date_to=${to}` : '';
                const res = await fetch(`${API_BASE}/api/admin/detailed-stats?filter=${this._filter}${params}`);
                const data = await res.json();
                this._rawData = data;

                const totalRev = data.totalRevenue || 0;
                const totalBook = data.totalBookings || 0;
                const totalExp = data.totalExpenses || 0;
                const netProf = data.netProfit || 0;

                document.getElementById('repAvgRev').textContent = '\u20B1' + Math.floor(totalRev / (totalBook || 1)).toLocaleString();
                document.getElementById('repActive').textContent = totalBook;
                document.getElementById('repTotalRev').textContent = '\u20B1' + totalRev.toLocaleString();
                document.getElementById('repTotalExpenses').textContent = '\u20B1' + totalExp.toLocaleString();
                document.getElementById('repNetProfit').textContent = '\u20B1' + netProf.toLocaleString();
                const activeFleetCount = (data.fleetDistribution || []).reduce((sum, item) => sum + (item.count || 0), 0);
                document.getElementById('repFleet').textContent = activeFleetCount;

                this.renderRevenueChart(data.revenueTrend || []);
                this.renderBookingsChart(data.bookingsTrend || data.revenueTrend || []);
                this.renderPieChart(data.topVehicles || []);
                this.renderTop(data.topVehicles || []);
                
                // Load expenses
                this.fetchExpenses();
            } catch (err) { console.error(err); }
        },







        renderRevenueChart(trend) {



            const ctx = document.getElementById('reportsRevenueChart').getContext('2d');



            if (this.chart) this.chart.destroy();



            this.chart = new Chart(ctx, {



                type: 'line',



                data: {



                    labels: trend.map(t => t.label || (t.day ? (t.day.length === 7 ? t.day : t.day.split('-').slice(1).join('/')) : '')),



                    datasets: [{



                        label: 'Revenue',



                        data: trend.map(t => t.amount || t.revenue || 0),



                        borderColor: '#00B14F',



                        borderWidth: 2,



                        backgroundColor: 'rgba(0,177,79,0.1)',



                        fill: true,



                        tension: 0.4,



                        pointRadius: 3,



                        pointBackgroundColor: '#00B14F'



                    }]



                },



                options: { responsive: true, maintainAspectRatio: false,
                    animation: { duration: 1000, easing: 'easeOutQuart' },



                    plugins: { legend: { display: false } },



                    scales: {



                        x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 9 } } },



                        y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#94a3b8', font: { size: 9 } } }



                    }



                }



            });



            makeChartClickable('reportsRevenueChart', this.chart, 'revenue');



        },







        renderBookingsChart(trend) {



            const ctx = document.getElementById('reportsBookingsChart').getContext('2d');



            if (this.chartBookings) this.chartBookings.destroy();



            const barPalette = ['#00B14F','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#ec4899','#14b8a6','#f97316','#06b6d4','#a855f7','#84cc16','#e11d48'];



            this.chartBookings = new Chart(ctx, {



                type: 'bar',



                data: {



                    labels: trend.map(t => t.label || (t.day ? (t.day.length === 7 ? t.day : t.day.split('-').slice(1).join('/')) : '')),



                    datasets: [{



                        label: 'Bookings',



                        data: trend.map(t => t.booking_count || t.count || t.bookings || 0),



                        backgroundColor: trend.map((_, i) => barPalette[i % barPalette.length]),



                        borderRadius: 4



                    }]



                },



                options: { responsive: true, maintainAspectRatio: false,
                    animation: { duration: 1000, easing: 'easeOutQuart' },



                    plugins: { legend: { display: false } },



                    scales: {



                        x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 9 } } },



                        y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#94a3b8', font: { size: 9 } } }



                    }



                }



            });



            makeChartClickable('reportsBookingsChart', this.chartBookings, 'bookings');



        },







        renderPieChart(cars) {



            const ctx = document.getElementById('reportsTopPieChart').getContext('2d');



            if (this.chartPie) this.chartPie.destroy();



            // Deduplicate by vehicle name, summing booking counts



            const seen = {};



            cars.forEach(c => {



                const key = `${c.brand} ${c.model}`;



                if (seen[key]) {



                    seen[key].booking_count += (c.booking_count || 0);



                } else {



                    seen[key] = { label: key, booking_count: c.booking_count || 0 };



                }



            });



            const deduped = Object.values(seen).sort((a, b) => b.booking_count - a.booking_count).slice(0, 5);



            this.chartPie = new Chart(ctx, {



                type: 'pie',



                data: {



                    labels: deduped.map(c => c.label),



                    datasets: [{



                        data: deduped.map(c => c.booking_count),



                        backgroundColor: ['#00B14F','#3b82f6','#f59e0b','#ef4444','#8b5cf6'],



                        borderWidth: 0



                    }]



                },



                options: {



                    responsive: true,



                    maintainAspectRatio: false,
                    animation: { duration: 1000, easing: 'easeOutCirc' },



                    plugins: {



                        legend: {



                            position: 'bottom',



                            labels: {



                                color: '#6b7080',



                                font: { size: 9 },



                                padding: 6,



                                usePointStyle: true,



                                pointStyleWidth: 8,



                                boxHeight: 8



                            }



                        }



                    }



                }



            });



            makeChartClickable('reportsTopPieChart', this.chartPie, 'topveh');



        },







        renderTop(cars) {



            const container = document.getElementById('reportsTopVehicles');



            if (!cars.length) { container.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:20px;">No data</p>'; return; }



            container.innerHTML = cars.slice(0, 5).map((c, i) => `



                <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 15px;background:var(--surface-container);border-radius:10px;margin-bottom:8px;border:1px solid var(--border);">



                    <div style="display:flex;align-items:center;gap:10px;">



                        <span style="width:22px;height:22px;border-radius:50%;background:var(--primary);color:white;font-size:0.65rem;font-weight:800;display:flex;align-items:center;justify-content:center;">${i+1}</span>



                        <div>



                            <div style="font-size:0.85rem;font-weight:700;color:var(--text-main);">${c.brand} ${c.model} ${c.plate_number ? '('+c.plate_number+')' : ''}</div>



                            <div style="font-size:0.65rem;color:var(--text-muted);">${c.booking_count} bookings</div>



                        </div>



                    </div>



                    <span style="font-size:0.9rem;font-weight:900;color:var(--success);">₱${(c.revenue||0).toLocaleString()}</span>



                </div>



            `).join('');



        },



        openRecordExpenseModal() {
            document.getElementById('recordExpenseModal').style.display = 'flex';
            document.getElementById('recordExpenseForm').reset();
            document.getElementById('expDate').value = new Date().toISOString().split('T')[0];
            this.loadVehiclesDropdown();
        },



        closeRecordExpenseModal() {
            document.getElementById('recordExpenseModal').style.display = 'none';
        },



        closeRecordExpenseModalBackdrop(event) {
            if (event.target.id === 'recordExpenseModal') {
                this.closeRecordExpenseModal();
            }
        },



        async loadVehiclesDropdown() {
            try {
                const res = await fetch(`${API_URL}/vehicles`);
                const vehicles = await res.json();
                const select = document.getElementById('expVehicleId');
                select.innerHTML = '<option value="">-- Select a Vehicle --</option>' + 
                    vehicles.map(v => `<option value="${v.id}">${v.brand} ${v.model} (${v.plate_number || 'No Plate'})</option>`).join('');
            } catch (err) {
                console.error('Failed to load vehicles dropdown', err);
                document.getElementById('expVehicleId').innerHTML = '<option value="">Error loading vehicles</option>';
            }
        },



        async saveExpense(event) {
            event.preventDefault();
            const user = adminAuth.getUser();
            if (!user) return;

            const vehicleId = document.getElementById('expVehicleId').value;
            const type = document.getElementById('expType').value;
            const amount = document.getElementById('expAmount').value;
            const date = document.getElementById('expDate').value;
            const desc = document.getElementById('expDesc').value;
            const fileInput = document.getElementById('expProofFile');

            if (!fileInput.files[0]) {
                showNotification('Proof of expense image is required', 'error');
                return;
            }
            const expFile = fileInput.files[0];
            const isExpImg = (expFile.type || "").toLowerCase().startsWith("image/") || /\.(jpe?g|png|webp|gif|heic)$/i.test(expFile.name || "");
            if (!isExpImg) {
                showNotification("Only image files are allowed for expense proof.", "error");
                return;
            }
            if (expFile.size > 5 * 1024 * 1024) {
                showNotification("Expense proof must be 5 MB or smaller.", "error");
                return;
            }

            const formData = new FormData();
            formData.append('vehicle_id', vehicleId);
            formData.append('expense_type', type);
            formData.append('amount', amount);
            formData.append('expense_date', date);
            formData.append('description', desc);
            formData.append('recorded_by', user.id);
            formData.append('proof_image', fileInput.files[0]);

            try {
                showAdminLoading(true);
                const res = await fetch(`${API_BASE}/admin/expenses`, {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                showAdminLoading(false);

                if (res.ok) {
                    showNotification('Expense recorded successfully', 'success');
                    this.closeRecordExpenseModal();
                    this.refresh();
                } else {
                    showNotification(data.error || 'Failed to record expense', 'error');
                }
            } catch (err) {
                showAdminLoading(false);
                console.error(err);
                showNotification('Error saving expense record', 'error');
            }
        },



        async fetchExpenses() {
            const user = adminAuth.getUser();
            if (!user) return;
            const from = document.getElementById('rptDateFrom').value;
            const to = document.getElementById('rptDateTo').value;
            const params = `?admin_id=${user.id}` + (from && to ? `&date_from=${from}&date_to=${to}` : '');
            
            try {
                const res = await fetch(`${API_BASE}/admin/expenses${params}`);
                const data = await res.json();
                this._expensesData = data;
                this.renderExpensesTable(data);
            } catch (err) {
                console.error(err);
                document.getElementById('reportsExpensesList').innerHTML = '<tr><td colspan="8" style="text-align:center;color:red;">Error loading expenses log.</td></tr>';
            }
        },



        renderExpensesTable(expenses) {
            const container = document.getElementById('reportsExpensesList');
            if (!container) return;
            const user = adminAuth.getUser();
            const isSuperAdmin = user && (user.role === 'super_admin' || user.role === 'superadmin');

            if (!expenses.length) {
                container.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--text-muted);">No expenses logged for this range.</td></tr>';
                return;
            }

            container.innerHTML = expenses.map(e => `
                <tr style="border-bottom:1px solid var(--border);">
                    <td style="padding:10px 8px;">${e.expense_date}</td>
                    <td style="padding:10px 8px;font-weight:700;">${e.brand} ${e.model} <span style="font-size:0.7rem;color:var(--text-muted);display:block;">${e.plate_number}</span></td>
                    <td style="padding:10px 8px;"><span class="badge" style="background:var(--surface-container);color:var(--text-main);padding:4px 8px;border-radius:6px;font-size:0.7rem;">${e.expense_type}</span></td>
                    <td style="padding:10px 8px;font-weight:700;color:var(--danger);">₱${e.amount.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    <td style="padding:10px 8px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${e.description}">${e.description}</td>
                    <td style="padding:10px 8px;text-align:center;">
                        ${e.proof_image_url ? `<a href="${e.proof_image_url}" target="_blank" class="btn-primary" style="padding:4px 8px;font-size:0.7rem;border-radius:6px;display:inline-flex;align-items:center;gap:4px;"><i class="fas fa-image"></i> View Receipt</a>` : `<span style="color:var(--text-muted);font-size:0.7rem;">No Image</span>`}
                    </td>
                    <td style="padding:10px 8px;font-size:0.75rem;">${e.recorder_name}</td>
                    <td style="padding:10px 8px;text-align:center;">
                        ${isSuperAdmin ? `<button onclick="Reports.deleteExpense(${e.id})" style="background:transparent;border:none;color:var(--danger);cursor:pointer;font-size:0.95rem;padding:4px;" title="Delete expense record"><i class="fas fa-trash-alt"></i></button>` : `<span style="color:var(--text-muted);font-size:0.7rem;">-</span>`}
                    </td>
                </tr>
            `).join('');
        },



        async deleteExpense(expenseId) {
            if (!confirm('Are you sure you want to delete this expense record?')) return;
            const user = adminAuth.getUser();
            if (!user) return;

            try {
                showAdminLoading(true);
                const res = await fetch(`${API_BASE}/admin/expenses/${expenseId}?admin_id=${user.id}`, {
                    method: 'DELETE'
                });
                const data = await res.json();
                showAdminLoading(false);

                if (res.ok) {
                    showNotification('Expense record deleted successfully', 'success');
                    this.refresh();
                } else {
                    showNotification(data.error || 'Failed to delete record', 'error');
                }
            } catch (err) {
                showAdminLoading(false);
                console.error(err);
                showNotification('Error deleting expense record', 'error');
            }
        },







        async exportExcel() {
            if (typeof anime !== 'undefined') {
                const _btn = (window.event && (window.event.currentTarget || window.event.target));
                if (_btn) {
                    anime({
                        targets: (_btn.querySelector && _btn.querySelector('i')) || _btn,
                        translateY: [0, -6, 2, 0],
                        duration: 450,
                        easing: 'easeOutBack'
                    });
                }
            }

            try {
                showNotification('Generating Executive Excel report with interactive charts...', 'success');
                const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser()) || {};
                const from = document.getElementById('rptDateFrom') ? document.getElementById('rptDateFrom').value : '';
                const to = document.getElementById('rptDateTo') ? document.getElementById('rptDateTo').value : '';
                const filter = this._filter || 'year';
                const adminId = user.id || '';

                // Determine clean indicator filename
                let filename = 'AutoRide_Report.xlsx';
                const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];
                if (from && to) {
                    if (from === to) {
                        filename = `AutoRide_DAILY_Report_${from}.xlsx`;
                    } else {
                        const pFrom = from.split('-').map(Number);
                        const pTo = to.split('-').map(Number);
                        if (filter === 'month' || (pFrom[0] === pTo[0] && pFrom[1] === pTo[1] && pFrom[2] === 1 && pTo[2] >= 28)) {
                            const mName = monthNames[pFrom[1] - 1] || 'Month';
                            const mm = String(pFrom[1]).padStart(2, '0');
                            filename = `AutoRide_MONTHLY_Report_${pFrom[0]}_${mm}_${mName}.xlsx`;
                        } else if (filter === 'year' || (pFrom[0] === pTo[0] && pFrom[1] === 1 && pFrom[2] === 1 && pTo[1] === 12 && pTo[2] === 31)) {
                            filename = `AutoRide_ANNUAL_Report_${pFrom[0]}.xlsx`;
                        } else {
                            filename = `AutoRide_CUSTOM_Report_${from}_to_${to}.xlsx`;
                        }
                    }
                } else if (filter === 'year') {
                    filename = `AutoRide_ANNUAL_Report_${new Date().getFullYear()}.xlsx`;
                } else if (filter === 'month') {
                    const d = new Date();
                    const mm = String(d.getMonth() + 1).padStart(2, '0');
                    filename = `AutoRide_MONTHLY_Report_${d.getFullYear()}_${mm}_${monthNames[d.getMonth()]}.xlsx`;
                } else if (filter === 'day') {
                    const d = new Date();
                    const todayStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
                    filename = `AutoRide_DAILY_Report_${todayStr}.xlsx`;
                } else {
                    filename = `AutoRide_ALL_TIME_Report.xlsx`;
                }

                const url = `${API_BASE}/api/admin/reports/export-excel?filter=${filter}&date_from=${from}&date_to=${to}&admin_id=${adminId}`;
                const res = await fetch(url);
                if (!res.ok) {
                    throw new Error(`Server returned status ${res.status}`);
                }

                // If backend provided filename in Content-Disposition header, use it
                try {
                    const cd = res.headers && res.headers.get('content-disposition');
                    if (cd) {
                        const match = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                        if (match && match[1]) {
                            filename = match[1].replace(/['"]/g, '').trim();
                        }
                    }
                } catch (_) {}
                const blob = await res.blob();

                // Check for Capacitor Mobile download
                const { Filesystem } = window.Capacitor?.Plugins || {};
                if (Filesystem) {
                    try {
                        const reader = new FileReader();
                        reader.readAsDataURL(blob);
                        reader.onloadend = async () => {
                            const base64data = reader.result.split(',')[1];
                            const result = await Filesystem.writeFile({
                                path: filename,
                                data: base64data,
                                directory: 'DOWNLOADS',
                                recursive: true
                            });
                            showNotification('Excel saved to Downloads: ' + filename, 'success');
                        };
                        return;
                    } catch (mErr) {
                        console.warn('Mobile download failed, falling back to browser download:', mErr);
                    }
                }

                // Standard Web Browser download
                const downloadUrl = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                setTimeout(() => URL.revokeObjectURL(downloadUrl), 5000);
                showNotification('Executive Excel report with charts downloaded!', 'success');

            } catch (err) {
                console.error('Excel export failed:', err);
                showNotification('Export failed: ' + err.message, 'error');
            }
        },
    };















    // --- SETTINGS MODULE ---

    const SETTINGS_NUM_CONFIG = {
        'long_term_discount_percent':        { min: 0,    max: 100,   step: 1,    suffix: '%' },
        'loyalty_max_discount_percent':      { min: 0,    max: 100,   step: 1,    suffix: '%' },
        'cancellation_penalty_percent':      { min: 0,    max: 100,   step: 1,    suffix: '%' },
        'cancellation_deadline_hours':       { min: 1,    max: 168,   step: 1,    suffix: 'hrs' },
        'loyalty_points_spend_ratio':        { min: 1,    max: 9999,  step: 1,    suffix: 'PHP' },
        'loyalty_points_value':              { min: 0.01, max: 100,   step: 0.01, suffix: 'PHP' },
        'mileage_limit':                     { min: 10,   max: 9999,  step: 10,   suffix: 'km/day' },
        'refuel_full_tank_price':            { min: 500,  max: 10000, step: 100,  suffix: 'PHP' },
        'long_term_discount_days':           { min: 1,    max: 365,   step: 1,    suffix: 'days' },
        'extension_conflict_deadline_hours': { min: 1,    max: 720,   step: 1,    suffix: 'hrs' },
        'max_booking_duration_days':         { min: 1,    max: 3650,  step: 1,    suffix: 'days' },
        'violation_max_strikes':             { min: 1,    max: 10,    step: 1,    suffix: 'strikes' },
        'violation_1st_suspension_hours':    { min: 1,    max: 168,   step: 1,    suffix: 'hrs' },
        'violation_2nd_suspension_days':     { min: 1,    max: 60,    step: 1,    suffix: 'days' },
        'violation_commitment_fee_amount':   { min: 0,    max: 5000,  step: 20,   suffix: 'PHP' },
        'violation_auto_reset_clean_days':   { min: 1,    max: 365,   step: 1,    suffix: 'days' },
        'late_return_grace_period_mins':     { min: 0,    max: 1440,  step: 5,    suffix: 'mins' },
        'late_return_hourly_rate':           { min: 0,    max: 10000, step: 50,   suffix: 'PHP/hr' },
        'late_return_fixed_base_fee':        { min: 0,    max: 10000, step: 50,   suffix: 'PHP' },
        'late_return_max_penalty_cap':       { min: 0,    max: 50000, step: 100,  suffix: 'PHP' },
        'cleaning_fee_standard':             { min: 0,    max: 10000, step: 50,   suffix: 'PHP' },
        'refuel_price_per_liter':            { min: 1,    max: 300,   step: 1,    suffix: 'PHP/L' },
        'regular_customer_min_bookings':     { min: 1,    max: 100,   step: 1,    suffix: 'bookings' },
        'payment_fee_card_percent':          { min: 0,    max: 50,    step: 0.1,  suffix: '%' },
        'payment_fee_ewallet_percent':       { min: 0,    max: 50,    step: 0.1,  suffix: '%' },
        'payment_fee_cash_percent':          { min: 0,    max: 50,    step: 0.1,  suffix: '%' },
        'driver_daily_wage':                 { min: 100,  max: 10000, step: 5,    suffix: 'PHP/day' },
        'driver_shift_hours':                { min: 1,    max: 24,    step: 1,    suffix: 'hrs/day' },
        'driver_overtime_rate':              { min: 0,    max: 1000,  step: 5,    suffix: 'PHP/hr' },
    };
    window.SETTINGS_NUM_CONFIG = SETTINGS_NUM_CONFIG;

    window.handleSettingNumberKeydown = function(e, min) {
        if (['e', 'E', '+'].includes(e.key)) {
            e.preventDefault();
            return false;
        }
        if (min >= 0 && e.key === '-') {
            e.preventDefault();
            return false;
        }
    };

    window.handleSettingNumberInput = function(input, min, max, step) {
        if (!input) return;
        let raw = input.value;
        if (raw === '') return;

        if (min >= 0 && raw.includes('-')) {
            raw = raw.replace(/-/g, '');
        }

        const isDec = String(step).includes('.') || (min < 1 && min > 0);
        const maxDigits = String(Math.floor(max)).length;
        const parts = raw.split('.');

        if (parts[0].length > maxDigits) {
            parts[0] = parts[0].slice(0, maxDigits);
            raw = parts.length > 1 && isDec ? parts[0] + '.' + parts[1].slice(0, 2) : parts[0];
        }
        if (parts.length > 1 && isDec && parts[1].length > 2) {
            raw = parts[0] + '.' + parts[1].slice(0, 2);
        }

        const num = Number(raw);
        if (!isNaN(num)) {
            if (num > max) {
                raw = String(max);
            }
        }
        input.value = raw;
    };

    window.handleSettingNumberBlur = function(input, min, max, step) {
        if (!input) return;
        let raw = input.value.trim();
        if (raw === '' || isNaN(Number(raw))) {
            input.value = min;
            return;
        }
        let num = Number(raw);
        if (num > max) num = max;
        if (num < min) num = min;

        const isDec = String(step).includes('.') || (min < 1 && min > 0);
        if (isDec) {
            const decimals = (String(step).split('.')[1] || '0').length;
            input.value = num.toFixed(decimals);
        } else {
            input.value = Math.round(num);
        }
    };

    const Settings = {
        _allData: [],
        _groups: {},
        _activeCat: 'all',
        _searchQuery: '',

        async fetch() {
            const list = document.getElementById('mobileSettingsList');
            try {
                let res = await fetch(`${API_BASE}/admin/settings`);
                if (res.status === 404 || res.status === 405) {
                    res = await fetch(`${API_BASE}/api/admin/settings`);
                }
                const data = await res.json();
                this._allData = Array.isArray(data) ? data : [];
                this.render();
            } catch (err) {
                if (list) list.innerHTML = `<p style="color: var(--danger); text-align: center; padding: 20px;">Failed to load settings.</p>`;
            }
        },

        render() {
            const list = document.getElementById('mobileSettingsList');
            const tabsContainer = document.getElementById('settingsCategoryTabs');
            if (!list) return;

            // Define modular categories
            const groups = {
                safety: {
                    title: 'Customer Safety & Verification',
                    shortTitle: 'Safety',
                    icon: 'fa-user-shield',
                    color: '#8b5cf6',
                    desc: 'Driver license verification, emergency contact, and live selfie rules',
                    keys: ['require_license_verification', 'require_emergency_contact', 'require_live_selfie'],
                    settings: []
                },
                                penalties: {
                    title: 'Penalties & Late Return Fees',
                    shortTitle: 'Penalties',
                    icon: 'fa-file-invoice-dollar',
                    color: '#dc2626',
                    desc: 'Late return hourly fines, grace period, auto-charge policy, and damage fees',
                    keys: [
                        'late_return_auto_apply_enabled',
                        'late_return_grace_period_mins',
                        'late_return_hourly_rate',
                        'late_return_fixed_base_fee',
                        'late_return_max_penalty_cap',
                        'block_booking_on_unpaid_penalty',
                        'cleaning_fee_standard',
                        'refuel_price_per_liter'
                    ],
                    settings: []
                },
                violations: {
                    title: 'Violations & Strike System',
                    shortTitle: 'Violations',
                    icon: 'fa-gavel',
                    color: '#f43f5e',
                    desc: 'Deposit cancellation penalties, suspension times, and warning notifications',
                    keys: [
                        'violation_max_strikes',
                        'violation_1st_suspension_hours',
                        'violation_2nd_suspension_days',
                        'violation_commitment_fee_amount',
                        'violation_auto_reset_clean_days',
                        'violation_warning_15min_enabled',
                        'violation_warning_5min_enabled'
                    ],
                    settings: []
                },
                rentals: {
                    title: 'Rental & Fleet Policies',
                    shortTitle: 'Rentals',
                    icon: 'fa-car-side',
                    color: '#10b981',
                    desc: 'Mileage allowances, max rental duration, low fuel alert, rental terms, and regular customer VIP downpayment exemption',
                    keys: [
                        'mileage_limit', 'max_booking_duration_days', 'low_fuel_alert_threshold', 'refuel_full_tank_price', 'rental_terms',
                        'regular_customer_min_bookings', 'regular_customer_auto_qualify', 'regular_customer_downpayment_exempt'
                    ],
                    settings: []
                },
                driver_policy: {
                    title: 'Driver Wage & Overtime (OT) Policy',
                    shortTitle: 'Driver & OT',
                    icon: 'fa-user-tie',
                    color: '#0d9488',
                    desc: 'Chauffeur daily wage, standard duty shift hours, hourly overtime rate, service availability, and meals & lodging notice',
                    keys: [
                        'driver_service_enabled',
                        'driver_daily_wage',
                        'driver_shift_hours',
                        'driver_overtime_rate',
                        'driver_meals_lodging_policy'
                    ],
                    settings: []
                },
                cancellation: {
                    title: 'Cancellations & Refunds',
                    shortTitle: 'Cancellations',
                    icon: 'fa-calendar-times',
                    color: '#ef4444',
                    desc: 'Cutoff deadlines and non-refundable penalty fee percentages',
                    keys: ['cancellation_deadline_hours', 'cancellation_penalty_percent'],
                    settings: []
                },
                discounts: {
                    title: 'Discounts & Booking Extensions',
                    shortTitle: 'Discounts',
                    icon: 'fa-tags',
                    color: '#f59e0b',
                    desc: 'Long-term rental discounts and extension overlap conflict deadlines',
                    keys: ['long_term_discount_days', 'long_term_discount_percent', 'extension_conflict_deadline_hours'],
                    settings: []
                },
                loyalty: {
                    title: 'Loyalty Points System',
                    shortTitle: 'Loyalty',
                    icon: 'fa-coins',
                    color: '#3b82f6',
                    desc: 'Point accumulation rates, peso conversion, and max discount redemption',
                    keys: ['loyalty_points_spend_ratio', 'loyalty_points_value', 'loyalty_max_discount_percent'],
                    settings: []
                },
                ai_chat: {
                    title: 'AI Assistant & Live Chat',
                    shortTitle: 'AI & Chat',
                    icon: 'fa-robot',
                    color: '#6366f1',
                    desc: 'Floating AI chatbot, automated FAQ responses, and greeting messages',
                    keys: [
                        'ai_assistant_enabled',
                        'ai_assistant_autoreply_enabled',
                        'ai_assistant_greeting',
                        'ai_assistant_fallback',
                        'chat_faq_enabled',
                        'chat_faq_autoreply_enabled'
                    ],
                    settings: []
                },
                payment: {
                    title: 'Payment Gateway & Payment Fees',
                    shortTitle: 'Payment',
                    icon: 'fa-credit-card',
                    color: '#00c389',
                    desc: 'PayMongo mode, API keys, webhook secret, and terminal/POS payment surcharge fee rates',
                    keys: [
                        'paymongo_mode',
                        'paymongo_test_public_key',
                        'paymongo_test_secret_key',
                        'paymongo_live_public_key',
                        'paymongo_live_secret_key',
                        'paymongo_webhook_secret',
                        'payment_fee_card_percent',
                        'payment_fee_card_label',
                        'payment_fee_ewallet_percent',
                        'payment_fee_cash_percent'
                    ],
                    settings: []
                },
                email_smtp: {
                    title: 'Email & Notification Integration',
                    shortTitle: 'Email & SMTP',
                    icon: 'fa-envelope-open-text',
                    color: '#0284c7',
                    desc: 'Gmail OAuth credentials and notification delivery settings',
                    keys: [
                        'smtp_oauth_email',
                        'smtp_oauth_access_token',
                        'smtp_oauth_refresh_token',
                        'smtp_oauth_token_expiry'
                    ],
                    settings: []
                },
                general: {
                    title: 'General & Regional Preferences',
                    shortTitle: 'General',
                    icon: 'fa-sliders-h',
                    color: '#64748b',
                    desc: 'System currency symbol, local timezone, and marketing newsletter feature',
                    keys: ['currency', 'time_zone', 'enable_newsletter'],
                    settings: []
                }
            };

            // Distribute settings into categories
            this._allData.forEach(s => {
                let grouped = false;
                for (const cat in groups) {
                    if (groups[cat].keys.includes(s.key)) {
                        groups[cat].settings.push(s);
                        grouped = true;
                        break;
                    }
                }
                if (!grouped) {
                    groups.general.settings.push(s);
                }
            });

            this._groups = groups;

            // Render category navigation tabs
            if (tabsContainer) {
                const totalCount = this._allData.length;
                let tabsHtml = `
                    <button type="button" onclick="Settings.selectCategory('all')" id="tab_all" class="settings-tab-btn" style="display: flex; align-items: center; gap: 6px; padding: 7px 14px; font-size: 0.78rem; font-weight: 700; border-radius: 20px; border: 1px solid ${this._activeCat === 'all' ? 'var(--primary)' : 'var(--border)'}; background: ${this._activeCat === 'all' ? 'rgba(59,130,246,0.15)' : 'var(--surface-solid)'}; color: ${this._activeCat === 'all' ? 'var(--primary)' : 'var(--text-muted)'}; cursor: pointer; white-space: nowrap; transition: all 0.2s;">
                        <i class="fas fa-layer-group"></i> All <span style="font-size: 0.7rem; opacity: 0.85; padding: 1px 6px; border-radius: 10px; background: rgba(255,255,255,0.08);">${totalCount}</span>
                    </button>
                `;

                for (const cat in groups) {
                    const g = groups[cat];
                    if (g.settings.length === 0) continue;
                    const isActive = this._activeCat === cat;
                    tabsHtml += `
                        <button type="button" onclick="Settings.selectCategory('${cat}')" id="tab_${cat}" class="settings-tab-btn" style="display: flex; align-items: center; gap: 6px; padding: 7px 14px; font-size: 0.78rem; font-weight: 700; border-radius: 20px; border: 1px solid ${isActive ? g.color : 'var(--border)'}; background: ${isActive ? g.color + '22' : 'var(--surface-solid)'}; color: ${isActive ? g.color : 'var(--text-muted)'}; cursor: pointer; white-space: nowrap; transition: all 0.2s;">
                            <i class="fas ${g.icon}" style="color: ${g.color};"></i> ${g.shortTitle} <span style="font-size: 0.7rem; opacity: 0.85; padding: 1px 6px; border-radius: 10px; background: rgba(255,255,255,0.08);">${g.settings.length}</span>
                        </button>
                    `;
                }
                tabsContainer.innerHTML = tabsHtml;
            }

            // Build all category cards into DOM
            let html = '';
            for (const cat in groups) {
                const g = groups[cat];
                if (g.settings.length === 0) continue;

                html += `
                    <div class="settings-group-card" data-cat="${cat}" style="background: var(--surface-container); border: 1px solid var(--border); border-radius: 16px; padding: 16px; width: 100%; max-width: 100%; min-width: 0; box-sizing: border-box; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); transition: all 0.2s;">
                        <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px; border-bottom: 1px solid var(--border); padding-bottom: 12px;">
                            <div style="display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0;">
                                <div style="width: 34px; height: 34px; flex-shrink: 0; background: ${g.color}15; border: 1px solid ${g.color}33; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                                    <i class="fas ${g.icon}" style="color: ${g.color}; font-size: 0.95rem;"></i>
                                </div>
                                <div style="flex: 1; min-width: 0;">
                                    <div style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); word-break: break-word;">${g.title}</div>
                                    <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 1px; word-break: break-word;">${g.desc}</div>
                                </div>
                            </div>
                            <span style="font-size: 0.7rem; font-weight: 700; color: ${g.color}; background: ${g.color}15; padding: 3px 8px; border-radius: 12px; border: 1px solid ${g.color}33; white-space: nowrap; flex-shrink: 0;">
                                ${g.settings.length} ${g.settings.length === 1 ? 'setting' : 'settings'}
                            </span>
                        </div>
                        <div class="settings-fields-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 230px), 1fr)); gap: 14px; margin-top: 14px; width: 100%; max-width: 100%; min-width: 0; box-sizing: border-box;">
                `;

                if (cat === 'email_smtp') {
                    html += `
                        <div style="grid-column: 1 / -1; margin-bottom: 8px; padding: 14px 16px; background: rgba(2, 132, 199, 0.08); border: 1px solid rgba(2, 132, 199, 0.25); border-radius: 12px; display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap;">
                            <div>
                                <div style="font-size: 0.88rem; font-weight: 700; color: var(--text-main); display: flex; align-items: center; gap: 8px;">
                                    <i class="fas fa-satellite-dish" style="color: #0284c7;"></i> System Email Connector & Diagnostics
                                </div>
                                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 3px;">
                                    Connect or re-authorize Gmail with 1-click, configure a permanent App Password, and test live email delivery.
                                </div>
                            </div>
                            <button type="button" onclick="toggleSmtpConfigModal()" class="btn-premium" style="padding: 10px 14px; font-size: 0.82rem; font-weight: 700; background: var(--primary); color: white; border-radius: 10px; cursor: pointer; max-width: 100%; white-space: normal; text-align: center; display: inline-flex; align-items: center; justify-content: center; gap: 8px; box-sizing: border-box;">
                                <i class="fas fa-plug"></i> Open Re-Authorize &amp; Email Tools
                            </button>
                        </div>
                    `;
                }

                g.settings.forEach(s => {
                    html += this.renderField(s);
                });

                html += `
                        </div>
                    </div>
                `;
            }

            list.innerHTML = html;
            this.applyFilters();
            this.snapshotInitialValues();
        },

        renderField(s) {
            const isTextarea = ['rental_terms', 'ai_assistant_greeting', 'ai_assistant_fallback', 'driver_meals_lodging_policy'].includes(s.key);
            const booleanKeys = [
                'require_license_verification',
                'require_emergency_contact',
                'require_live_selfie',
                'ai_assistant_enabled',
                'ai_assistant_autoreply_enabled',
                'chat_faq_enabled',
                'chat_faq_autoreply_enabled',
                'enable_newsletter',
                'violation_warning_15min_enabled',
                'violation_warning_5min_enabled',
                'late_return_auto_apply_enabled',
                'block_booking_on_unpaid_penalty',
                'regular_customer_auto_qualify',
                'regular_customer_downpayment_exempt',
                'driver_service_enabled'
            ];
            const isBool = booleanKeys.includes(s.key);

            const numericKeys = [
                'mileage_limit', 'long_term_discount_days', 'long_term_discount_percent', 'extension_conflict_deadline_hours',
                'loyalty_points_spend_ratio', 'loyalty_points_value', 'loyalty_max_discount_percent',
                'cancellation_deadline_hours', 'cancellation_penalty_percent', 'max_booking_duration_days',
                'violation_max_strikes', 'violation_1st_suspension_hours', 'violation_2nd_suspension_days',
                'violation_commitment_fee_amount', 'violation_auto_reset_clean_days',
                'late_return_grace_period_mins', 'late_return_hourly_rate', 'late_return_fixed_base_fee',
                'late_return_max_penalty_cap', 'cleaning_fee_standard', 'refuel_price_per_liter', 'refuel_full_tank_price',
                'regular_customer_min_bookings', 'payment_fee_card_percent', 'payment_fee_ewallet_percent', 'payment_fee_cash_percent',
                'driver_daily_wage', 'driver_shift_hours', 'driver_overtime_rate'
            ];
            const isNumeric = numericKeys.includes(s.key);

            const secretKeys = [
                'paymongo_test_secret_key', 'paymongo_live_secret_key', 'paymongo_webhook_secret',
                'smtp_oauth_access_token', 'smtp_oauth_refresh_token'
            ];
            const isSecret = secretKeys.includes(s.key);

            const val = s.value !== null && s.value !== undefined ? String(s.value) : '';

            // 1. License verification dropdown
            if (s.key === 'require_license_verification') {
                const isStrict = val === 'true';
                return `
                    <div class="settings-field-item" data-key="${s.key}" style="display: flex; flex-direction: column; gap: 6px;">
                        <label style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">${s.description || s.key}</label>
                        <select data-key="${s.key}" style="width: 100%; box-sizing: border-box; padding: 10px 12px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.82rem; font-weight: 600; outline: none; cursor: pointer;">
                            <option value="true" ${isStrict ? 'selected' : ''}>🛡️ Strict (Require Approved License)</option>
                            <option value="false" ${!isStrict ? 'selected' : ''}>⚠️ Relaxed (Allow Booking Pending Verification)</option>
                        </select>
                    </div>
                `;
            }

            // 2. Emergency contact dropdown
            if (s.key === 'require_emergency_contact') {
                const isReq = val === 'true';
                return `
                    <div class="settings-field-item" data-key="${s.key}" style="display: flex; flex-direction: column; gap: 6px;">
                        <label style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">${s.description || s.key}</label>
                        <select data-key="${s.key}" style="width: 100%; box-sizing: border-box; padding: 10px 12px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.82rem; font-weight: 600; outline: none; cursor: pointer;">
                            <option value="true" ${isReq ? 'selected' : ''}>✅ Required (Before Booking)</option>
                            <option value="false" ${!isReq ? 'selected' : ''}>⚪ Optional</option>
                        </select>
                    </div>
                `;
            }

            // 2b. Live Selfie requirement dropdown
            if (s.key === 'require_live_selfie') {
                const isReq = val === 'true';
                return `
                    <div class="settings-field-item" data-key="${s.key}" style="display: flex; flex-direction: column; gap: 6px;">
                        <label style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">${s.description || 'Require Live Selfie / Profile Picture'}</label>
                        <select data-key="${s.key}" style="width: 100%; box-sizing: border-box; padding: 10px 12px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.82rem; font-weight: 600; outline: none; cursor: pointer;">
                            <option value="true" ${isReq ? 'selected' : ''}>📸 Mandatory (Selfie / ID Photo)</option>
                            <option value="false" ${!isReq ? 'selected' : ''}>📝 Info Only (No Selfie Required)</option>
                        </select>
                    </div>
                `;
            }

            // 3. Generic Booleans (AI, FAQ, Newsletter, Violation Warnings)
            if (isBool) {
                const isEnabled = val === 'true';
                return `
                    <div class="settings-field-item" data-key="${s.key}" style="display: flex; flex-direction: column; gap: 6px;">
                        <label style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">${s.description || s.key}</label>
                        <select data-key="${s.key}" style="width: 100%; box-sizing: border-box; padding: 10px 12px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.82rem; font-weight: 600; outline: none; cursor: pointer;">
                            <option value="true" ${isEnabled ? 'selected' : ''}>🟢 Enabled</option>
                            <option value="false" ${!isEnabled ? 'selected' : ''}>⚪ Disabled</option>
                        </select>
                    </div>
                `;
            }

            // 4. Low Fuel Alert Threshold
            if (s.key === 'low_fuel_alert_threshold') {
                const curVal = val || '1/4';
                const options = ['Off', 'Empty', 'Reserve', '1/4', '1/2', '3/4', 'Full'];
                const optHtml = options.map(o => `<option value="${o}" ${curVal === o ? 'selected' : ''}>${o}</option>`).join('');
                return `
                    <div class="settings-field-item" data-key="${s.key}" style="display: flex; flex-direction: column; gap: 6px;">
                        <label style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">${s.description || s.key}</label>
                        <select data-key="${s.key}" style="width: 100%; box-sizing: border-box; padding: 10px 12px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.82rem; font-weight: 600; outline: none; cursor: pointer;">${optHtml}</select>
                    </div>
                `;
            }

            // 5. PayMongo Environment Mode
            if (s.key === 'paymongo_mode') {
                const isLive = val === 'live';
                const badgeBg = isLive ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)';
                const badgeColor = isLive ? '#ef4444' : '#10b981';
                const badgeText = isLive ? '🔴 LIVE (Real Money / Production)' : '🧪 TEST (Sandbox / Safe Mode)';
                return `
                    <div class="settings-field-item" data-key="${s.key}" style="display: flex; flex-direction: column; gap: 6px; grid-column: 1 / -1; margin-bottom: 4px; background: rgba(0,195,137,0.05); padding: 14px; border-radius: 12px; border: 1px dashed rgba(0,195,137,0.3);">
                        <label style="font-size: 0.72rem; color: #00c389; text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">${s.description || s.key}</label>
                        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                            <select data-key="${s.key}" onchange="updatePaymongoModeBadge(this)" style="flex: 1; min-width: 200px; padding: 12px 14px; background: var(--surface-solid); border: 2px solid ${isLive ? '#ef4444' : '#10b981'}; border-radius: 10px; color: var(--text-main); font-size: 0.92rem; font-weight: 700; outline: none; cursor: pointer;">
                                <option value="test" ${!isLive ? 'selected' : ''}>🧪 Test Mode (Sandbox)</option>
                                <option value="live" ${isLive ? 'selected' : ''}>🔴 Live Mode (Real Payments)</option>
                            </select>
                            <span id="pmModeBadge" style="padding: 6px 14px; background: ${badgeBg}; color: ${badgeColor}; border: 1px solid ${badgeColor}; border-radius: 20px; font-size: 0.78rem; font-weight: 800; text-transform: uppercase;">
                                ${badgeText}
                            </span>
                            <button type="button" onclick="testPaymongoCredentials()" style="padding: 10px 16px; font-size: 0.8rem; font-weight: 700; border-radius: 10px; background: #00c389; color: white; border: none; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                                <i class="fas fa-plug"></i> Test Connection
                            </button>
                        </div>
                    </div>
                `;
            }

            // 6. Passwords / Secrets / OAuth Tokens
            if (isSecret) {
                const inputId = 'input_' + s.key;
                const isLiveKey = s.key.includes('live');
                const placeholder = s.key.includes('live') ? 'sk_live_...' : s.key.includes('webhook') ? 'whsec_...' : s.key.includes('refresh') ? 'OAuth Refresh Token' : s.key.includes('access') ? 'OAuth Access Token' : 'sk_test_...';
                return `
                    <div class="settings-field-item" data-key="${s.key}" style="display: flex; flex-direction: column; gap: 6px;">
                        <label style="font-size: 0.68rem; color: ${isLiveKey ? '#ef4444' : 'var(--text-muted)'}; text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">${s.description || s.key}</label>
                        <div style="position: relative; display: flex; align-items: center; width: 100%;">
                            <input type="password" id="${inputId}" data-key="${s.key}" maxlength="255" autocomplete="new-password" value="${val}" placeholder="${placeholder}" style="width: 100%; box-sizing: border-box; padding: 12px 42px 12px 14px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.86rem; font-family: monospace; font-weight: 600; outline: none;">
                            <button type="button" onclick="togglePasswordVisibility('${inputId}', this)" style="position: absolute; right: 10px; background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 6px; font-size: 0.9rem;">
                                <i class="fas fa-eye"></i>
                            </button>
                        </div>
                    </div>
                `;
            }

            // 7. Public Keys
            if (s.key.includes('public_key')) {
                const isLiveKey = s.key.includes('live');
                const placeholder = isLiveKey ? 'pk_live_...' : 'pk_test_...';
                return `
                    <div class="settings-field-item" data-key="${s.key}" style="display: flex; flex-direction: column; gap: 6px;">
                        <label style="font-size: 0.68rem; color: ${isLiveKey ? '#ef4444' : 'var(--text-muted)'}; text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">${s.description || s.key}</label>
                        <input type="text" data-key="${s.key}" maxlength="255" value="${val}" placeholder="${placeholder}" style="width: 100%; box-sizing: border-box; padding: 12px 14px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.86rem; font-family: monospace; font-weight: 600; outline: none;">
                    </div>
                `;
            }

            // 8. Numeric Fields
            if (isNumeric) {
                const nc = (typeof SETTINGS_NUM_CONFIG !== 'undefined' && SETTINGS_NUM_CONFIG[s.key]) ? SETTINGS_NUM_CONFIG[s.key] : { min: 0, max: 9999, step: 1, suffix: '' };
                return `
                    <div class="settings-field-item" data-key="${s.key}" style="display: flex; flex-direction: column; gap: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <label style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">${s.description || s.key}</label>
                            <span style="font-size: 0.65rem; color: var(--text-muted); font-weight: 600;">Limit: ${nc.min} – ${nc.max}</span>
                        </div>
                        <div style="position: relative; display: flex; align-items: center; width: 100%;">
                            <input type="number" data-key="${s.key}" value="${val}" min="${nc.min}" max="${nc.max}" step="${nc.step}"
                                autocomplete="off"
                                onkeydown="handleSettingNumberKeydown(event, ${nc.min})"
                                oninput="handleSettingNumberInput(this, ${nc.min}, ${nc.max}, ${nc.step})"
                                onblur="handleSettingNumberBlur(this, ${nc.min}, ${nc.max}, ${nc.step})"
                                style="width: 100%; box-sizing: border-box; padding: 12px 65px 12px 14px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.88rem; font-weight: 700; outline: none; transition: border-color 0.2s;">
                            <span style="position: absolute; right: 12px; font-size: 0.72rem; color: var(--text-muted); font-weight: 800; text-transform: uppercase; pointer-events: none;">${nc.suffix}</span>
                        </div>
                    </div>
                `;
            }

            // 9. Textareas
            if (isTextarea) {
                const height = s.key === 'rental_terms' ? '120px' : '75px';
                return `
                    <div class="settings-field-item" data-key="${s.key}" style="display: flex; flex-direction: column; gap: 6px; grid-column: 1 / -1;">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <label style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">${s.description || s.key}</label>
                            <span style="font-size: 0.65rem; color: var(--text-muted);">Max 5,000 characters</span>
                        </div>
                        <textarea data-key="${s.key}" maxlength="5000" style="width: 100%; box-sizing: border-box; height: ${height}; padding: 12px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.85rem; font-weight: 600; font-family: inherit; resize: vertical; outline: none; line-height: 1.5;">${val}</textarea>
                    </div>
                `;
            }

            // 10. Default Text Input
            const isExpiry = s.key === 'smtp_oauth_token_expiry';
            const isEmail = s.key === 'smtp_oauth_email';
            const isCurrency = s.key === 'currency';
            const isTimezone = s.key === 'time_zone';
            const isCardLabel = s.key === 'payment_fee_card_label';
            const maxLen = isCurrency ? 10 : isTimezone ? 50 : isCardLabel ? 60 : isEmail ? 100 : isExpiry ? 50 : 255;
            const inputType = isEmail ? 'email' : 'text';
            const readonlyAttr = isExpiry ? 'readonly style="width: 100%; box-sizing: border-box; padding: 12px 14px; background: var(--surface-container); opacity: 0.8; border: 1px solid var(--border); border-radius: 10px; color: var(--text-muted); font-size: 0.88rem; font-weight: 600; outline: none; cursor: not-allowed;"' : 'style="width: 100%; box-sizing: border-box; padding: 12px 14px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.88rem; font-weight: 600; outline: none; transition: border-color 0.2s;"';
            const helperNote = isExpiry ? '<span style="font-size: 0.65rem; color: #0284c7; margin-top: 2px;"><i class="fas fa-info-circle"></i> Auto-managed by Gmail OAuth</span>' : `<span style="font-size: 0.62rem; color: var(--text-muted); margin-top: 2px;">Max ${maxLen} characters</span>`;
            return `
                <div class="settings-field-item" data-key="${s.key}" style="display: flex; flex-direction: column; gap: 6px;">
                    <label style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">${s.description || s.key}</label>
                    <input type="${inputType}" data-key="${s.key}" maxlength="${maxLen}" value="${val}" ${readonlyAttr}>
                    ${helperNote}
                </div>
            `;
        },

        selectCategory(catKey) {
            this._activeCat = catKey;
            this.updateTabStyles();
            this.applyFilters();
        },

        updateTabStyles() {
            const tabs = document.querySelectorAll('.settings-tab-btn');
            tabs.forEach(tab => {
                const isCurrent = (tab.id === `tab_${this._activeCat}`);
                if (isCurrent) {
                    tab.style.background = 'rgba(59,130,246,0.18)';
                    tab.style.borderColor = 'var(--primary)';
                    tab.style.color = 'var(--primary)';
                } else {
                    tab.style.background = 'var(--surface-solid)';
                    tab.style.borderColor = 'var(--border)';
                    tab.style.color = 'var(--text-muted)';
                }
            });
        },

        onSearchInput(val) {
            this._searchQuery = (val || '').trim().toLowerCase();
            const clearBtn = document.getElementById('settingsSearchClearBtn');
            if (clearBtn) clearBtn.style.display = this._searchQuery ? 'block' : 'none';
            this.applyFilters();
        },

        clearSearch() {
            this._searchQuery = '';
            const input = document.getElementById('settingsSearchInput');
            if (input) input.value = '';
            const clearBtn = document.getElementById('settingsSearchClearBtn');
            if (clearBtn) clearBtn.style.display = 'none';
            this.applyFilters();
        },

        applyFilters() {
            const list = document.getElementById('mobileSettingsList');
            if (!list) return;

            const cards = list.querySelectorAll('.settings-group-card');
            const q = this._searchQuery;
            let visibleCards = 0;

            cards.forEach(card => {
                const cat = card.dataset.cat;
                const matchesCategory = (this._activeCat === 'all' || this._activeCat === cat);

                if (!matchesCategory && !q) {
                    card.style.display = 'none';
                    return;
                }

                if (!q) {
                    card.style.display = 'block';
                    card.querySelectorAll('.settings-field-item').forEach(item => item.style.display = 'flex');
                    visibleCards++;
                    return;
                }

                // We have a search query: filter field items inside the card
                let matchingFields = 0;
                card.querySelectorAll('.settings-field-item').forEach(item => {
                    const key = (item.dataset.key || '').toLowerCase();
                    const label = (item.querySelector('label') ? item.querySelector('label').innerText : '').toLowerCase();
                    const input = item.querySelector('input, select, textarea');
                    const val = (input ? input.value : '').toLowerCase();
                    const cardTitle = (card.innerText || '').toLowerCase();

                    if (key.includes(q) || label.includes(q) || val.includes(q) || cardTitle.includes(q)) {
                        item.style.display = 'flex';
                        matchingFields++;
                    } else {
                        item.style.display = 'none';
                    }
                });

                if (matchingFields > 0 && (this._activeCat === 'all' || this._activeCat === cat)) {
                    card.style.display = 'block';
                    visibleCards++;
                } else {
                    card.style.display = 'none';
                }
            });

            let emptyNotice = document.getElementById('settingsEmptyNotice');
            if (visibleCards === 0) {
                if (!emptyNotice) {
                    emptyNotice = document.createElement('div');
                    emptyNotice.id = 'settingsEmptyNotice';
                    emptyNotice.style.cssText = 'text-align: center; padding: 36px 20px; color: var(--text-muted);';
                    list.appendChild(emptyNotice);
                }
                emptyNotice.innerHTML = `
                    <i class="fas fa-search" style="font-size: 2rem; margin-bottom: 10px; opacity: 0.5;"></i>
                    <p style="font-size: 0.95rem; font-weight: 700; color: var(--text-main); margin: 0 0 6px 0;">No matching settings</p>
                    <p style="font-size: 0.8rem; margin: 0 0 12px 0;">No settings found matching "${q}".</p>
                    <button type="button" onclick="Settings.clearSearch(); Settings.selectCategory('all');" style="padding: 8px 16px; background: var(--surface-solid); border: 1px solid var(--border); border-radius: 10px; color: var(--text-main); font-size: 0.8rem; font-weight: 600; cursor: pointer;">Reset Filters</button>
                `;
                emptyNotice.style.display = 'block';
            } else if (emptyNotice) {
                emptyNotice.style.display = 'none';
            }
        },

        snapshotInitialValues() {
            this._initialValues = {};
            const curInputs = document.querySelectorAll('#mobileSettingsList input, #mobileSettingsList textarea, #mobileSettingsList select');
            curInputs.forEach(i => {
                if (i.dataset && i.dataset.key) {
                    this._initialValues[i.dataset.key] = String(i.value !== undefined ? i.value : '');
                }
            });
        },

        getChanges() {
            const inputs = document.querySelectorAll('#mobileSettingsList input, #mobileSettingsList textarea, #mobileSettingsList select');
            const changes = [];
            const secretKeys = ['paymongo_test_secret_key', 'paymongo_live_secret_key', 'paymongo_webhook_secret', 'smtp_oauth_access_token', 'smtp_oauth_refresh_token'];
            const numConfig = (typeof SETTINGS_NUM_CONFIG !== 'undefined') ? SETTINGS_NUM_CONFIG : {};

            inputs.forEach(i => {
                if (!i.dataset || !i.dataset.key) return;
                const key = i.dataset.key;
                const initialVal = (this._initialValues && this._initialValues[key] !== undefined) ? String(this._initialValues[key]) : '';
                let currentVal = String(i.value !== undefined ? i.value : '');

                if (numConfig[key]) {
                    const nc = numConfig[key];
                    let n = Number(currentVal.trim());
                    if (isNaN(n) || currentVal.trim() === '') {
                        currentVal = String(nc.min);
                    } else {
                        if (n > nc.max) n = nc.max;
                        if (n < nc.min) n = nc.min;
                        const isDec = String(nc.step).includes('.');
                        currentVal = isDec ? n.toFixed((String(nc.step).split('.')[1] || '0').length) : String(Math.round(n));
                    }
                } else if (i.tagName === 'TEXTAREA') {
                    currentVal = currentVal.slice(0, 5000);
                } else if (i.tagName === 'INPUT') {
                    currentVal = currentVal.slice(0, 255);
                }

                if (initialVal !== currentVal) {
                    let label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                    const item = i.closest('.settings-field-item');
                    if (item) {
                        const lbl = item.querySelector('label');
                        if (lbl && lbl.childNodes && lbl.childNodes[0]) {
                            const txt = lbl.childNodes[0].textContent.trim();
                            if (txt) label = txt;
                        }
                    }

                    const formatVal = (v) => {
                        if (secretKeys.includes(key) && v) return '••••••••';
                        if (v === 'true') return 'Enabled';
                        if (v === 'false') return 'Disabled';
                        if (v === '') return '(Empty)';
                        return v;
                    };

                    changes.push({
                        key: key,
                        label: label,
                        oldValue: formatVal(initialVal),
                        newValue: formatVal(currentVal),
                        rawOld: initialVal,
                        rawNew: currentVal
                    });
                }
            });
            return changes;
        },

        discardChanges() {
            if (!this._initialValues) return;
            const inputs = document.querySelectorAll('#mobileSettingsList input, #mobileSettingsList textarea, #mobileSettingsList select');
            inputs.forEach(i => {
                if (i.dataset && i.dataset.key && this._initialValues[i.dataset.key] !== undefined) {
                    i.value = this._initialValues[i.dataset.key];
                    i.dispatchEvent(new Event('input', { bubbles: true }));
                    i.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        },

        async save() {
            const inputs = document.querySelectorAll('#mobileSettingsList input, #mobileSettingsList textarea, #mobileSettingsList select');
            const numConfig = (typeof SETTINGS_NUM_CONFIG !== 'undefined') ? SETTINGS_NUM_CONFIG : {};
            const updates = [];

            inputs.forEach(i => {
                if (!i.dataset || !i.dataset.key) return;
                const k = i.dataset.key;
                let v = String(i.value !== undefined ? i.value : '');

                if (numConfig[k]) {
                    const nc = numConfig[k];
                    let n = Number(v.trim());
                    if (isNaN(n) || v.trim() === '') {
                        n = nc.min;
                    } else {
                        if (n > nc.max) n = nc.max;
                        if (n < nc.min) n = nc.min;
                    }
                    const isDec = String(nc.step).includes('.');
                    v = isDec ? n.toFixed((String(nc.step).split('.')[1] || '0').length) : String(Math.round(n));
                    i.value = v; // sync input box in DOM
                } else if (i.tagName === 'TEXTAREA') {
                    v = v.slice(0, 5000);
                } else {
                    v = v.trim().slice(0, 255);
                }

                updates.push({ key: k, value: v });
            });
            const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;

            try {
                let res = await fetch(`${API_BASE}/admin/settings`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ requester_id: (user && user.id) ? user.id : 20, settings: updates })
                });
                if (res.status === 404 || res.status === 405) {
                    res = await fetch(`${API_BASE}/api/admin/settings`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ requester_id: (user && user.id) ? user.id : 20, settings: updates })
                    });
                }
                const data = await res.json().catch(() => ({ error: 'HTTP ' + res.status }));

                if (res.ok) {
                    showNotification('✅ Settings saved successfully!', 'success');
                    await this.fetch();
                    return true;
                } else {
                    showNotification('❌ Save failed: ' + (data.error || data.message || 'Unauthorized'), 'error');
                    return false;
                }
            } catch (err) {
                showNotification('❌ Network error: ' + err.message, 'error');
                return false;
            }
        }
    };

    window.saveSystemSettingsBtn = async function(btn) {
        if (!btn) btn = document.getElementById('btnSaveSystemSettings');
        const origHtml = btn ? btn.innerHTML : '';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        }
        try {
            const success = await Settings.save();
            if (success) {
                setTimeout(() => {
                    if (typeof closeSystemConfigModal === 'function') closeSystemConfigModal();
                }, 500);
            }
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = origHtml || 'Save Settings';
            }
        }
    };

    window.updatePaymongoModeBadge = function(selectEl) {
        const badge = document.getElementById('pmModeBadge');
        if (!badge) return;
        const isLive = selectEl.value === 'live';
        selectEl.style.borderColor = isLive ? '#ef4444' : '#10b981';
        badge.style.background = isLive ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)';
        badge.style.color = isLive ? '#ef4444' : '#10b981';
        badge.style.borderColor = isLive ? '#ef4444' : '#10b981';
        badge.textContent = isLive ? '🔴 LIVE (Real Money / Production)' : '🧪 TEST (Sandbox / Safe Mode)';
    };

    window.togglePasswordVisibility = function(inputId, btn) {
        const input = document.getElementById(inputId);
        if (!input) return;
        const icon = btn.querySelector('i');
        if (input.type === 'password') {
            input.type = 'text';
            if (icon) { icon.classList.remove('fa-eye'); icon.classList.add('fa-eye-slash'); }
        } else {
            input.type = 'password';
            if (icon) { icon.classList.remove('fa-eye-slash'); icon.classList.add('fa-eye'); }
        }
    };

    window.testPaymongoCredentials = async function() {
        const modeSelect = document.querySelector('select[data-key="paymongo_mode"]');
        const mode = modeSelect ? modeSelect.value : 'test';
        const keyName = mode === 'live' ? 'paymongo_live_secret_key' : 'paymongo_test_secret_key';
        const secretKeyInput = document.querySelector(`input[data-key="${keyName}"]`);
        const secretKey = secretKeyInput ? secretKeyInput.value.trim() : '';

        const testBtn = document.querySelector('button[onclick*="testPaymongoCredentials"]');
        const originalBtnHtml = testBtn ? testBtn.innerHTML : '';
        if (testBtn) {
            testBtn.disabled = true;
            testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        }

        showNotification('Testing PayMongo connection...', 'info');
        try {
            let res = await fetch(`${API_BASE}/admin/paymongo/test-connection`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: mode, secret_key: secretKey })
            });
            if (res.status === 404 || res.status === 405) {
                res = await fetch(`${API_BASE}/api/admin/paymongo/test-connection`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode: mode, secret_key: secretKey })
                });
            }
            const data = await res.json().catch(() => ({ success: false, message: `Server error (${res.status})` }));
            if (res.ok && data.success) {
                showNotification('✅ ' + data.message, 'success');
            } else {
                showNotification('❌ ' + (data.message || data.error || 'Connection test failed'), 'error');
            }
        } catch (e) {
            showNotification('❌ Connection error: ' + e.message, 'error');
        } finally {
            if (testBtn) {
                testBtn.disabled = false;
                testBtn.innerHTML = originalBtnHtml || '<i class="fas fa-plug"></i> Test Connection';
            }
        }
    };



    var currentDashPeriod = 'today';

    function changeDashboardFilter(period, btn) {
        currentDashPeriod = period;
        document.querySelectorAll('.dash-filter-btn').forEach(b => {
            const active = b === btn;
            b.style.background = active ? 'var(--primary)' : 'var(--surface-container)';
            b.style.borderColor = active ? 'var(--primary)' : 'var(--border)';
            b.style.color = active ? 'white' : 'var(--text-secondary)';
        });
        // Clear custom range picker since preset chip was clicked
        const dateFromEl = document.getElementById('dashDateFrom');
        const dateToEl = document.getElementById('dashDateTo');
        if (dateFromEl) dateFromEl.value = '';
        if (dateToEl) dateToEl.value = '';

        refreshDashboard();
    }
    window.changeDashboardFilter = changeDashboardFilter;

    function syncAndRefreshDashboardDates() {
        const dateFromVal = document.getElementById('dashDateFrom')?.value || '';
        const dateToVal = document.getElementById('dashDateTo')?.value || '';
        
        if (dateFromVal || dateToVal) {
            currentDashPeriod = 'custom';
            // De-select all filter chips
            document.querySelectorAll('.dash-filter-btn').forEach(b => {
                b.style.background = 'var(--surface-container)';
                b.style.borderColor = 'var(--border)';
                b.style.color = 'var(--text-secondary)';
            });
        }
        refreshDashboard();
    }
    window.syncAndRefreshDashboardDates = syncAndRefreshDashboardDates;

    async function refreshDashboard(_retryCount) {

        _retryCount = _retryCount || 0;

        const user = adminAuth.getUser();

        if (!user) {

            if (_retryCount < 3) {

                setTimeout(function() { refreshDashboard(_retryCount + 1); }, 500);

            }

            return;

        }

        try {
            const dateFrom = document.getElementById('dashDateFrom')?.value || '';
            const dateTo = document.getElementById('dashDateTo')?.value || '';
            const res = await fetch(`${API_URL}/admin/stats?admin_id=${user.id}&period=${currentDashPeriod}&date_from=${dateFrom}&date_to=${dateTo}`);



            if (!res.ok) throw new Error(`HTTP ${res.status}`);



            const data = await res.json();



            



            // Store for potential re-use



            _dashData = data;







            // Dynamically update chart subtitles based on active filter
            const revSub = document.getElementById('dashRevenueSubtitle');
            const bookSub = document.getElementById('dashBookingsSubtitle');
            if (revSub) {
                if (currentDashPeriod === 'today') revSub.textContent = 'Today';
                else if (currentDashPeriod === 'thismonth') revSub.textContent = 'This Month (Daily)';
                else if (currentDashPeriod === 'thisyear') revSub.textContent = 'This Year (Monthly)';
                else if (dateFrom || dateTo) revSub.textContent = `${dateFrom || 'Start'} to ${dateTo || 'End'}`;
                else revSub.textContent = 'Filtered Period';
            }
            if (bookSub) {
                if (currentDashPeriod === 'today') bookSub.textContent = "Today's Status Volume";
                else if (currentDashPeriod === 'thismonth') bookSub.textContent = "This Month's Status Volume";
                else if (currentDashPeriod === 'thisyear') bookSub.textContent = "This Year's Status Volume";
                else bookSub.textContent = "Filtered Period Volume";
            }

            // Update stat cards
            var targetRev = Number(data.total_revenue || 0);
            var targetBookings = Number(data.total_bookings || 0);

            if (window.anime) {
                var revObj = { val: 0 };
                anime({
                    targets: revObj,
                    val: targetRev,
                    round: 1,
                    easing: 'easeOutExpo',
                    duration: 1200,
                    update: function() {
                        var el = document.getElementById('dashTotalRevenue');
                        if (el) el.textContent = '\u20B1' + Number(revObj.val).toLocaleString('en-PH', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                    }
                });

                var bookObj = { val: 0 };
                anime({
                    targets: bookObj,
                    val: targetBookings,
                    round: 1,
                    easing: 'easeOutExpo',
                    duration: 1000,
                    update: function() {
                        var el = document.getElementById('dashTotalBookings');
                        if (el) el.textContent = Math.round(bookObj.val);
                    }
                });

                anime({
                    targets: '#dashboard .stat-card',
                    opacity: [0, 1],
                    translateY: [12, 0],
                    delay: anime.stagger(40, { start: 20 }),
                    duration: 400,
                    easing: 'easeOutCubic'
                });
            } else {
                document.getElementById('dashTotalRevenue').textContent = '\u20B1' + targetRev.toLocaleString('en-PH', {minimumFractionDigits: 2});
                document.getElementById('dashTotalBookings').textContent = targetBookings;
            }



            



            // Top Performance: bookings by vehicle type (derived from topVehicles)



            const topPerf = document.getElementById('dashTopPerformance');



            if (topPerf && data.topVehicles && data.topVehicles.length) {



                // Group by vehicle type if available, else show top vehicles by booking count



                const top = data.topVehicles.slice(0, 4);



                topPerf.innerHTML = top.map(c => `



                    <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid var(--border-light);">



                        <span style="font-size:0.75rem;color:var(--text-secondary);">${c.brand} ${c.model}</span>



                        <span style="font-size:0.75rem;font-weight:800;color:var(--text-main);">${c.booking_count}</span>



                    </div>



                `).join('');
                if (typeof anime !== 'undefined') {
                    anime({
                        targets: '#dashTopPerformance > div',
                        opacity: [0, 1],
                        translateX: [-15, 0],
                        delay: anime.stagger(60),
                        duration: 400,
                        easing: 'easeOutQuad'
                    });
                }



            } else if (topPerf) {



                topPerf.innerHTML = '<div style="font-size:0.75rem;color:var(--text-muted);text-align:center;padding:10px 0;">No data.</div>';



            }







            // Top Grossing: revenue by vehicle



            const topGross = document.getElementById('dashTopGrossing');



            if (topGross && data.topVehicles && data.topVehicles.length) {



                const sorted = [...data.topVehicles].sort((a,b) => (b.revenue||0) - (a.revenue||0)).slice(0, 4);



                topGross.innerHTML = sorted.map(c => `



                    <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid var(--border-light);">



                        <span style="font-size:0.75rem;color:var(--text-secondary);">${c.brand} ${c.model}</span>



                        <span style="font-size:0.7rem;font-weight:800;color:var(--success);">\u20B1${(c.revenue||0).toLocaleString()}</span>



                    </div>



                `).join('');
                if (typeof anime !== 'undefined') {
                    anime({
                        targets: '#dashTopGrossing > div',
                        opacity: [0, 1],
                        translateX: [-15, 0],
                        delay: anime.stagger(60),
                        duration: 400,
                        easing: 'easeOutQuad'
                    });
                }



            } else if (topGross) {



                topGross.innerHTML = '<div style="font-size:0.75rem;color:var(--text-muted);text-align:center;padding:10px 0;">No data.</div>';



            }







            // Init charts (canvases are always visible now)



            if (typeof Chart !== 'undefined') initCharts(data);



        } catch (err) { 



            console.error('Dashboard Refresh Error:', err); 



            document.getElementById('dashTotalRevenue').textContent = '\u20B1-';
            var _dIds=['dashTotalRevenue','dashTotalBookings','dashActiveRentals','dashPendingBookings'];
            _dIds.forEach(function(id){var e=document.getElementById(id);if(e)e.innerHTML='<div style="height:28px;width:80%;border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;"></div>';});



            document.getElementById('dashTotalBookings').textContent = '-';



        }



    }







    function renderTopVehicles(cars) {



        const tbody = document.getElementById('topVehiclesBody');



        if (!cars || cars.length === 0) {



            tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 40px; color: var(--text-muted); font-weight: 600;">No active vehicles.</td></tr>';



            return;



        }



        tbody.innerHTML = cars.map(c => `



            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">



                <td style="padding: 16px 8px;">



                    <div style="font-weight: 800; color: var(--text-main); font-size: 0.9rem;">${c.brand}</div>



                    <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">${c.model}</div>



                </td>



                <td style="padding: 16px 8px; text-align: center;">



                    <span style="font-size: 0.85rem; font-weight: 700; color: var(--text-secondary);">${c.booking_count}</span>



                </td>



                <td style="padding: 16px 8px; text-align: right;">



                    <span style="font-size: 0.95rem; font-weight: 900; color: var(--success); letter-spacing: -0.5px;">₱${c.revenue.toLocaleString()}</span>



                </td>



            </tr>



        `).join('');



    }







    // --- CHART COLLAPSE TOGGLE ---



    let _dashData = null; // store last dashboard data for re-render on expand







    function toggleChart(id) {



        const body = document.getElementById('cc-body-' + id);



        const icon = document.getElementById('cc-icon-' + id);



        if (!body) return;



        const collapsed = body.style.display === 'none';



        body.style.display = collapsed ? '' : 'none';



        if (icon) icon.className = collapsed ? 'fas fa-chevron-up' : 'fas fa-chevron-down';



        // Re-render chart when expanding so Chart.js gets correct dimensions



        if (collapsed && _dashData) {



            setTimeout(function() {



                if (id === 'revenue' || id === 'bookings' || id === 'fleet' || id === 'topveh') {



                    initCharts(_dashData);



                }



                window.dispatchEvent(new Event('resize'));



            }, 100);



        }



    }







    let charts = {};



    function initCharts(data) {
        if (charts.revenue) { charts.revenue.destroy(); charts.revenue = null; }
        if (charts.bookings) { charts.bookings.destroy(); charts.bookings = null; }
        if (charts.health) { charts.health.destroy(); charts.health = null; }
        if (charts.topPie) { charts.topPie.destroy(); charts.topPie = null; }

        const defaultScales = {
            x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } },
            y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#94a3b8', font: { size: 10 } } }
        };

        // 1. Revenue Line Chart (Filtered by active period)
        const revTrend = data.revenueTrend || [];
        const revCtx = document.getElementById('revenueChart');
        if (revCtx) {
            const labels = revTrend.length > 0 ? revTrend.map(t => {
                if (!t.day) return '';
                if (t.day.includes('-')) return t.day.split('-').slice(1).join('/');
                return t.day;
            }) : (currentDashPeriod === 'today' ? ['Today'] : ['No Data']);
            const values = revTrend.length > 0 ? revTrend.map(t => t.amount) : [0];

            charts.revenue = new Chart(revCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        borderColor: '#00B14F',
                        borderWidth: 3,
                        backgroundColor: 'rgba(0, 177, 79, 0.12)',
                        fill: true,
                        tension: 0.35,
                        pointRadius: 4,
                        pointBackgroundColor: '#00B14F',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    animation: { duration: 1000, easing: 'easeOutQuart' },
                    plugins: { legend: { display: false } }, scales: defaultScales
                }
            });
        }

        // 2. Bookings Bar Chart (Filtered by active period)
        const bookCtx = document.getElementById('bookingsChart');
        if (bookCtx) {
            const bStatus = data.bookingsByStatus || {};
            const keys = Object.keys(bStatus);
            let bLabels = keys.map(k => k.charAt(0).toUpperCase() + k.slice(1));
            let bData = Object.values(bStatus);

            // When no bookings in active period, display baseline so admin sees 0 volume
            if (bLabels.length === 0) {
                bLabels = ['Cancelled', 'Completed', 'No Show', 'Picked Up'];
                bData = [0, 0, 0, 0];
            }

            const barPalette = ['#00B14F','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#ec4899','#14b8a6','#f97316'];
            const bColors = bLabels.map((_, i) => barPalette[i % barPalette.length]);

            charts.bookings = new Chart(bookCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: bLabels,
                    datasets: [{
                        label: 'Bookings',
                        data: bData,
                        backgroundColor: bColors,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    animation: { duration: 1000, easing: 'easeOutQuart' },
                    plugins: { legend: { display: false } }, scales: defaultScales
                }
            });
        }

        // 3. Fleet Health doughnut (only if canvas exists)
        const fleetCtxEl = document.getElementById('fleetHealthChart');
        if (fleetCtxEl) {
            const fleetDist = data.fleetDistribution || [];
            charts.health = new Chart(fleetCtxEl.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: fleetDist.map(f => f.status),
                    datasets: [{
                        data: fleetDist.map(f => f.count),
                        backgroundColor: ['#00B14F','#3b82f6','#f59e0b','#ef4444','#94a3b8'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false, cutout: '75%',
                    animation: { duration: 1000, easing: 'easeOutCirc' },
                    plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { weight: '600', size: 11 }, padding: 20, usePointStyle: true } } }
                }
            });
        }

        // 4. Top Vehicles Pie Chart (Filtered by active period)
        const topVehEl = document.getElementById('topVehiclesPieChart');
        if (topVehEl) {
            const topVeh = (data.topVehicles || []).slice(0, 6);
            const hasData = topVeh.length > 0 && topVeh.some(c => (c.booking_count > 0 || c.revenue > 0));
            if (hasData) {
                charts.topPie = new Chart(topVehEl.getContext('2d'), {
                    type: 'pie',
                    data: {
                        labels: topVeh.map(c => `${c.brand} ${c.model} ${c.plate_number ? '('+c.plate_number+')' : ''}`.trim()),
                        datasets: [{
                            data: topVeh.map(c => c.revenue > 0 ? c.revenue : (c.booking_count || 0)),
                            backgroundColor: ['#00B14F','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#ec4899'],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        animation: { duration: 1000, easing: 'easeOutCirc' },
                        plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 }, padding: 10, usePointStyle: true } } }
                    }
                });
            } else {
                const ctx = topVehEl.getContext('2d');
                ctx.clearRect(0, 0, topVehEl.width, topVehEl.height);
                ctx.font = 'bold 12px Arial';
                ctx.fillStyle = '#94a3b8';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('No booking data for this period', topVehEl.width / 2, topVehEl.height / 2);
            }
        }

        // Make dashboard charts clickable
        makeChartClickable('revenueChart', charts.revenue, 'revenue');
        makeChartClickable('bookingsChart', charts.bookings, 'bookings');
        if (charts.topPie) makeChartClickable('topVehiclesPieChart', charts.topPie, 'topveh');
        // Animate canvas elements smoothly on render / filter change
        if (window.anime) {
            anime({
                targets: ['#revenueChart', '#bookingsChart', '#topVehiclesPieChart'].filter(id => document.querySelector(id)),
                opacity: [0, 1],
                scale: [0.96, 1],
                translateY: [8, 0],
                duration: 650,
                easing: 'easeOutCubic'
            });
        }
    }







    // --- EXPANDABLE CHART POPUP LOGIC ---



    let currentPopupChart = null;



    let currentChartType = '';



    let originalChartInstance = null;



    let originalChartData = null;







    function makeChartClickable(canvasId, chartInstance, chartType) {



        const canvas = document.getElementById(canvasId);



        if (!canvas) return;



        canvas.style.cursor = 'pointer';



        canvas.onclick = function() {



            openChartPopup(chartInstance, chartType);



        };



    }







    function openChartPopup(chartInstance, chartType) {



        if (!chartInstance) return;



        originalChartInstance = chartInstance;



        currentChartType = chartType;



        originalChartData = JSON.parse(JSON.stringify(chartInstance.data));







        let titleText = 'Chart Details';



        if (chartType === 'revenue') titleText = 'Revenue Details';



        else if (chartType === 'bookings') titleText = 'Booking Details';



        else if (chartType === 'fleet') titleText = 'Fleet Health Details';



        else if (chartType === 'topveh') titleText = 'Vehicle Popularity Details';



        document.getElementById('popupChartTitle').textContent = titleText;







        // Reset filter inputs inheriting from dashboard range inputs if populated

        document.getElementById('popupDateFrom').value = document.getElementById('dashDateFrom')?.value || '';

        document.getElementById('popupDateTo').value = document.getElementById('dashDateTo')?.value || '';



        document.getElementById('popupStatusFilter').value = 'all';



        document.getElementById('popupVehicleFilter').value = 'all';







        // Adjust visibility of filters based on chart type



        const metricContainer = document.getElementById('popupMetricFilterContainer');



        const limitContainer = document.getElementById('popupLimitFilterContainer');



        if (chartType === 'fleet') {



            document.getElementById('popupStatusFilterContainer').style.display = 'none';



        } else {



            document.getElementById('popupStatusFilterContainer').style.display = '';



        }



        if (chartType === 'topveh') {



            metricContainer.style.display = '';



            limitContainer.style.display = '';



            document.getElementById('popupMetricFilter').value = 'bookings';



            document.getElementById('popupLimitFilter').value = '5';



            document.getElementById('popupStatusFilterContainer').style.display = 'none';



            document.getElementById('popupVehicleFilterContainer').style.display = 'none';



        } else {



            metricContainer.style.display = 'none';



            limitContainer.style.display = 'none';



            document.getElementById('popupVehicleFilterContainer').style.display = '';



        }







        const modal = document.getElementById('chartPopupModal');



        modal.style.display = 'flex';



        // Force reflow



        modal.offsetHeight;



        modal.classList.add('show');







        renderPopupChart();



    }







    function renderPopupChart() {



        const canvas = document.getElementById('popupChartCanvas');



        if (!canvas) return;



        const ctx = canvas.getContext('2d');



        if (currentPopupChart) {



            currentPopupChart.destroy();



        }







        const chartData = JSON.parse(JSON.stringify(originalChartData));



        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';



        const textColor = isDark ? '#ffffff' : '#0f1117';



        const gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';







        let chartConfig = {



            type: originalChartInstance.config.type,



            data: chartData,



            options: {



                responsive: true,



                maintainAspectRatio: false,



                plugins: {



                    legend: {



                        display: true,



                        position: 'bottom',



                        labels: {



                            color: textColor,



                            font: { family: 'Inter', size: 10, weight: 600 }



                        }



                    }



                }



            }



        };







        if (originalChartInstance.config.type !== 'doughnut' && originalChartInstance.config.type !== 'pie') {



            chartConfig.options.scales = {



                x: {



                    grid: { display: false },



                    ticks: { color: textColor, font: { size: 9 } }



                },



                y: {



                    grid: { color: gridColor },



                    ticks: { color: textColor, font: { size: 9 } }



                }



            };



            if (currentChartType === 'revenue') {



                chartConfig.options.scales.y.ticks.callback = function(value) {



                    return '₱' + value.toLocaleString();



                };



            }



        } else {



            if (currentChartType === 'fleet') {



                chartConfig.options.cutout = '68%';



            }



        }







                chartConfig.options.animation = {
            duration: 800,
            easing: 'easeOutQuart',
            animateRotate: true,
            animateScale: true
        };
        currentPopupChart = new Chart(ctx, chartConfig);



    }







    function closeChartPopup() {



        const modal = document.getElementById('chartPopupModal');



        if (!modal) return;



        modal.classList.remove('show');



        setTimeout(() => {



            modal.style.display = 'none';



            if (currentPopupChart) {



                currentPopupChart.destroy();



                currentPopupChart = null;



            }



        }, 300);



    }







    function closeChartPopupOverlay(event) {



        if (event.target.id === 'chartPopupModal') {



            closeChartPopup();



        }



    }







    async function applyPopupFilters() {
        const dateFrom = document.getElementById('popupDateFrom').value;

        const dateTo = document.getElementById('popupDateTo').value;

        const status = document.getElementById('popupStatusFilter').value;

        const vehicleType = document.getElementById('popupVehicleFilter').value;

        // Synchronize back to main dashboard inputs
        const dashDateFromEl = document.getElementById('dashDateFrom');
        const dashDateToEl = document.getElementById('dashDateTo');
        if (dashDateFromEl) dashDateFromEl.value = dateFrom;
        if (dashDateToEl) dashDateToEl.value = dateTo;

        if (dateFrom || dateTo) {
            currentDashPeriod = 'custom';
            document.querySelectorAll('.dash-filter-btn').forEach(b => {
                b.style.background = 'var(--surface-container)';
                b.style.borderColor = 'var(--border)';
                b.style.color = 'var(--text-secondary)';
            });
        }







        const user = adminAuth.getUser();



        if (!user) return;







        try {



            const url = `${API_URL}/admin/detailed-stats?admin_id=${user.id}&type=${currentChartType}&date_from=${dateFrom}&date_to=${dateTo}&status=${status}&vehicle_type=${vehicleType}`;



            const response = await fetch(url);



            if (!response.ok) throw new Error('Network response was not ok');



            const data = await response.json();







            if (currentChartType === 'revenue') {



                const trend = data.revenueTrend || [];



                originalChartData.labels = trend.map(t => t.day ? t.day.split('-').slice(1).join('/') : t.label || '');



                originalChartData.datasets[0].data = trend.map(t => t.amount || t.revenue || 0);



            } else if (currentChartType === 'bookings') {



                const trend = data.revenueTrend || [];



                originalChartData.labels = trend.map(t => t.day ? t.day.split('-').slice(1).join('/') : t.label || '');



                originalChartData.datasets[0].data = trend.map(t => t.booking_count || t.count || t.bookings || 0);



            } else if (currentChartType === 'fleet') {



                const fleetDist = data.fleetDistribution || [];



                originalChartData.labels = fleetDist.map(f => f.status);



                originalChartData.datasets[0].data = fleetDist.map(f => f.count);



            } else if (currentChartType === 'topveh') {



                const metric = document.getElementById('popupMetricFilter').value || 'bookings';



                const limitVal = document.getElementById('popupLimitFilter').value || '5';



                let topVeh = data.topVehicles || [];



                if (limitVal !== 'all') topVeh = topVeh.slice(0, parseInt(limitVal));



                originalChartData.labels = topVeh.map(c => `${c.brand} ${c.model} ${c.plate_number ? '('+c.plate_number+')' : ''}`.trim());



                if (metric === 'revenue') {



                    originalChartData.datasets[0].data = topVeh.map(c => c.revenue || 0);



                } else {



                    originalChartData.datasets[0].data = topVeh.map(c => c.booking_count || 0);



                }



                // Ensure enough colors



                const pieColors = ['#00B14F','#00B14F','#f59e0b','#ef4444','#00B14F','#5FDBE2','#ec4899','#14b8a6','#f97316','#84cc16','#06b6d4','#a855f7','#e11d48','#0ea5e9','#22d3ee'];



                originalChartData.datasets[0].backgroundColor = pieColors.slice(0, topVeh.length);



            }







            renderPopupChart();



        } catch (error) {



            console.error('Error applying popup filters:', error);



        }



    }







    function resetPopupFilters() {



        document.getElementById('popupDateFrom').value = '';

        document.getElementById('popupDateTo').value = '';

        // Reset main dashboard inputs as well
        const dashDateFromEl = document.getElementById('dashDateFrom');
        const dashDateToEl = document.getElementById('dashDateTo');
        if (dashDateFromEl) dashDateFromEl.value = '';
        if (dashDateToEl) dashDateToEl.value = '';



        document.getElementById('popupStatusFilter').value = 'all';



        document.getElementById('popupVehicleFilter').value = 'all';



        document.getElementById('popupMetricFilter').value = 'bookings';



        document.getElementById('popupLimitFilter').value = '5';



        applyPopupFilters();



    }







    // --- INSPECTIONS LOGIC ---



    const Inspections = {



        currentPhotos: [],



        async openModal(bookingId, type) {
            let b = (Bookings.data || []).find(x => String(x.id) === String(bookingId));
            if (!b) {
                try {
                    const bRes = await fetch(`${API_BASE}/api/bookings/${bookingId}`);
                    if (bRes.ok) b = await bRes.json();
                } catch(e) {}
            }
            if (!b) return;

            if (type === 'pickup' && typeof Bookings !== 'undefined' && Bookings.isPickupInspectReady && !Bookings.isPickupInspectReady(b)) {
                const dt = Bookings.getPickupDateTime(b);
                const allowFrom = dt ? new Date(dt.getTime() - 60 * 60 * 1000) : null;
                const fmtAllow = allowFrom ? allowFrom.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
                const fmtPickup = dt ? dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : (b.start_time || '06:00');
                showNotification(`Pickup inspection cannot be started yet. Scheduled pickup is at ${fmtPickup}${fmtAllow ? ` (available starting at ${fmtAllow})` : ''}.`, 'warning');
                return;
            }

            // Reset first, then set values (order matters!)
            document.getElementById('inspectionForm').reset();
            this.currentPhotos = [];
            document.getElementById('inspectPhotoPreview').innerHTML = '';
            document.getElementById('inspectProofImages').innerHTML = '';

            document.getElementById('inspectBookingId').value = bookingId;
            document.getElementById('inspectType').value = type;
            document.getElementById('inspectTitle').textContent = type === 'pickup' ? 'Pickup Inspection' : 'Return Inspection';
            document.getElementById('inspectSubtitle').textContent = `Car: ${b.car || b.vehicle_name || ''}`;

            // Pre-fill initial Odometer and Fuel Level from Vehicle Master with robust lookup
            let veh = null;
            if (typeof Vehicles !== 'undefined' && Array.isArray(Vehicles.data) && Vehicles.data.length > 0) {
                veh = Vehicles.data.find(v => 
                    (b.vehicle_id && String(v.id) === String(b.vehicle_id)) ||
                    (b.car_id && String(v.id) === String(b.car_id)) ||
                    (b.plate_number && v.plate_number && String(v.plate_number).toLowerCase().trim() === String(b.plate_number).toLowerCase().trim()) ||
                    (b.car && v.plate_number && String(b.car).toLowerCase().includes(String(v.plate_number).toLowerCase().trim())) ||
                    (b.car && (v.brand + ' ' + v.model).toLowerCase().trim() === String(b.car).toLowerCase().trim())
                );
            }

            // API fallback if vehicle not found in client cache
            if (!veh || veh.odometer === undefined || veh.odometer === null) {
                try {
                    const targetId = b.vehicle_id || b.car_id;
                    if (targetId) {
                        const vRes = await fetch(`${API_BASE}/api/vehicles/${targetId}`);
                        if (vRes.ok) veh = await vRes.json();
                    }
                    if (!veh) {
                        const vResAll = await fetch(`${API_BASE}/api/vehicles`);
                        if (vResAll.ok) {
                            const vData = await vResAll.json();
                            const allVeh = Array.isArray(vData) ? vData : (vData.vehicles || []);
                            veh = allVeh.find(v => 
                                (b.vehicle_id && String(v.id) === String(b.vehicle_id)) ||
                                (b.car_id && String(v.id) === String(b.car_id)) ||
                                (b.plate_number && v.plate_number && String(v.plate_number).toLowerCase().trim() === String(b.plate_number).toLowerCase().trim()) ||
                                (b.car && v.plate_number && String(b.car).toLowerCase().includes(String(v.plate_number).toLowerCase().trim()))
                            );
                        }
                    }
                } catch(e) { console.warn('Vehicle fetch fallback error:', e); }
            }

            const currentOdom = (veh && veh.odometer !== undefined && veh.odometer !== null) ? parseFloat(veh.odometer) : 0;
            const currentFuel = (veh && veh.fuel_level) ? veh.fuel_level : 'Full Tank';

            // Calculate minimum allowed mileage (cannot decrease on pickup or return)
            let minMileage = currentOdom;
            let minLabel = 'Current Vehicle Odometer';

            if (type === 'return') {
                try {
                    const iRes = await fetch(`${API_BASE}/api/inspections/${bookingId}`);
                    if (iRes.ok) {
                        const iList = await iRes.json();
                        const pInsp = (iList || []).find(x => x.inspection_type === 'pickup');
                        if (pInsp && pInsp.mileage !== undefined && pInsp.mileage !== null && String(pInsp.mileage).trim() !== '') {
                            const pm = parseFloat(pInsp.mileage);
                            if (!isNaN(pm)) {
                                minMileage = pm;
                                minLabel = 'Pickup Inspection Mileage';
                            }
                        }
                    }
                } catch(e) { console.warn('Pickup inspection lookup error:', e); }
            }

            const mileageEl = document.getElementById('inspectMileage');
            if (mileageEl) {
                mileageEl.value = minMileage;
                mileageEl.min = minMileage;
                mileageEl.dataset.minAllowed = minMileage;
                mileageEl.dataset.minLabel = minLabel;
                mileageEl.oninput = function() {
                    const val = parseFloat(this.value);
                    const min = parseFloat(this.dataset.minAllowed || 0);
                    const lbl = this.dataset.minLabel || 'minimum';
                    if (!isNaN(val) && val < min) {
                        showInlineError(this, `Mileage cannot be lower than ${lbl.toLowerCase()} (${min.toLocaleString()} km)`);
                    } else {
                        clearInlineError(this);
                    }
                };
            }

            let minNoticeEl = document.getElementById('inspectMileageMinNotice');
            if (!minNoticeEl && mileageEl && mileageEl.parentElement) {
                minNoticeEl = document.createElement('div');
                minNoticeEl.id = 'inspectMileageMinNotice';
                mileageEl.parentElement.appendChild(minNoticeEl);
            }
            if (minNoticeEl) {
                minNoticeEl.style.cssText = 'font-size: 0.72rem; color: #475569; margin-top: 5px; font-weight: 600; display: flex; align-items: center; gap: 4px;';
                minNoticeEl.innerHTML = `<i class="fas fa-tachometer-alt" style="color: #2563eb;"></i> Min required: <strong style="color: #0f172a;">${minMileage.toLocaleString()} KM</strong> <span style="font-size: 0.68rem; color: #64748b;">(${minLabel})</span>`;
            }

            const fuelEl = document.getElementById('inspectFuel');
            if (fuelEl) {
                // Rule: Both Pickup and Return Inspections default to Full Tank!
                fuelEl.value = 'Full';
                Inspections.onFuelChange();
            }

            // Set receipt button
            const receiptUrl = `${API_BASE}/api/bookings/${bookingId}/receipt`;
            document.getElementById('inspectReceiptBtn').onclick = () => {
                Inspections.showReceiptModal(bookingId);
            };

            // Load payment proof images asynchronously
            fetch(`${API_BASE}/api/admin/bookings/${bookingId}/payment-proof`)
                .then(r => r.json())
                .then(data => {
                    const proofs = Array.isArray(data) ? data.filter(p => p.payment_proof_url) : [];
                    const container = document.getElementById('inspectProofImages');
                    if (!container) return;
                    if (proofs.length === 0) { container.innerHTML = ''; return; }
                    container.innerHTML = proofs.map(p => `
                        <div style="margin-top:8px;">
                            <div style="font-size:0.72rem;color:rgba(255,255,255,0.5);margin-bottom:4px;">
                                ${p.method || 'Payment'}${p.reference_number ? ' &bull; ' + p.reference_number : ''}
                                <span style="float:right;color:#00B14F;font-weight:700;">₱${parseFloat(p.amount||0).toLocaleString()}</span>
                            </div>
                            <img src="${p.payment_proof_url}" onclick="window.open('${p.payment_proof_url}','_blank')"
                                style="width:100%;border-radius:8px;border:1px solid rgba(255,255,255,0.1);cursor:pointer;max-height:180px;object-fit:contain;background:rgba(0,0,0,0.3);">
                        </div>
                    `).join('');
                }).catch(() => {});

            // Driver Overtime Section (Shown on return inspection when rental_type is 'With Driver')
            const isWithDriver = (b.rental_type === 'With Driver');
            const driverSec = document.getElementById('inspectDriverOTSection');
            if (driverSec) {
                if (type === 'return' && isWithDriver) {
                    driverSec.style.display = 'block';
                    let s = new Date(b.start_date);
                    let e = new Date(b.end_date);
                    let days = Math.max(1, Math.round((e - s) / (1000 * 60 * 60 * 24)));
                    let sWage = 755, sShift = 8, sOt = 95;
                    if (typeof Settings !== 'undefined' && Settings._allData) {
                        const wItem = Settings._allData.find(x => x.key === 'driver_daily_wage');
                        if (wItem && !isNaN(parseFloat(wItem.value))) sWage = parseFloat(wItem.value);
                        const shItem = Settings._allData.find(x => x.key === 'driver_shift_hours');
                        if (shItem && !isNaN(parseFloat(shItem.value))) sShift = parseFloat(shItem.value);
                        const otItem = Settings._allData.find(x => x.key === 'driver_overtime_rate');
                        if (otItem && !isNaN(parseFloat(otItem.value))) sOt = parseFloat(otItem.value);
                    }
                    const baseDaily = document.getElementById('inspectDriverDailyWageText');
                    if (baseDaily) baseDaily.textContent = `₱${sWage.toLocaleString()} / day`;
                    const baseSumm = document.getElementById('inspectDriverBaseWageSummary');
                    if (baseSumm) baseSumm.textContent = `₱${sWage.toLocaleString()} × ${days} day${days > 1 ? 's' : ''} = ₱${(sWage * days).toLocaleString()}`;
                    const shiftBadge = document.getElementById('inspectDriverShiftBadge');
                    if (shiftBadge) shiftBadge.textContent = `Standard Duty: ${days * sShift} hrs (${days}d × ${sShift}h)`;
                    const shiftText = document.getElementById('inspectDriverShiftText');
                    if (shiftText) shiftText.textContent = `${sShift} hrs/day`;
                    const otRateSummary = document.getElementById('inspectDriverOTRateSummary');
                    if (otRateSummary) otRateSummary.textContent = `₱${sOt.toLocaleString()} / hour`;
                    const otRateLabel = document.getElementById('inspectDriverOTRateLabel');
                    if (otRateLabel) otRateLabel.textContent = `OT Amount (₱${sOt.toLocaleString()}/hr)`;
                    const otHoursInput = document.getElementById('inspectDriverOTHours');
                    if (otHoursInput) {
                        otHoursInput.value = b.driver_ot_hours || 0;
                    }
                    const otAmtInput = document.getElementById('inspectDriverOTAmount');
                    if (otAmtInput) {
                        otAmtInput.value = parseFloat(b.driver_ot_amount || 0).toLocaleString('en-PH', {minimumFractionDigits: 2});
                    }
                    const otNotes = document.getElementById('inspectDriverOTNotes');
                    if (otNotes) {
                        otNotes.value = b.driver_ot_notes || '';
                    }
                    if (b.driver_ot_collection_method === 'company_charge') {
                        const rCharge = document.getElementById('inspectDriverOTCharge');
                        if (rCharge) rCharge.checked = true;
                    } else {
                        const rCash = document.getElementById('inspectDriverOTCash');
                        if (rCash) rCash.checked = true;
                    }
                } else {
                    driverSec.style.display = 'none';
                }
            }

            document.getElementById('inspectionModal').style.display = 'flex'; modalOpen();
        },

        onDriverOTChange() {
            const hoursEl = document.getElementById('inspectDriverOTHours');
            const amtEl = document.getElementById('inspectDriverOTAmount');
            if (!hoursEl || !amtEl) return;
            const hrs = parseFloat(hoursEl.value) || 0;
            let sOt = 95;
            if (typeof Settings !== 'undefined' && Settings._allData) {
                const otItem = Settings._allData.find(x => x.key === 'driver_overtime_rate');
                if (otItem && !isNaN(parseFloat(otItem.value))) sOt = parseFloat(otItem.value);
            }
            const amt = Math.max(0, hrs * sOt);
            amtEl.value = amt.toLocaleString('en-PH', {minimumFractionDigits: 2});
        },

        onFuelChange() {
            const typeEl = document.getElementById('inspectType');
            const type = typeEl ? typeEl.value : 'pickup';
            const fuelEl = document.getElementById('inspectFuel');
            const refuelSec = document.getElementById('inspectRefuelSection');
            const fullBanner = document.getElementById('inspectFuelFullReturnedBanner');
            const amountInput = document.getElementById('inspectFuelChargeAmount');
            const notesInput = document.getElementById('inspectFuelChargeNotes');
            const deficitTag = document.getElementById('inspectFuelDeficitTag');
            const policyDesc = document.getElementById('inspectPolicyDesc');
            const policyTitle = document.getElementById('inspectPolicyTitle');

            if (!fuelEl) return;
            const val = fuelEl.value;

            if (type === 'pickup') {
                if (refuelSec) refuelSec.style.display = 'none';
                if (fullBanner) fullBanner.style.display = 'none';
                if (policyTitle) policyTitle.innerHTML = '⛽ Pickup Rule: Released 100% Full Tank';
                if (val !== 'Full') {
                    if (policyDesc) policyDesc.innerHTML = `<span style="color: #dc2626; font-weight: 700;">⚠️ Policy Warning: Selected '${val}'. Rules require vehicles to be released 100% FULL TANK before rental. Please top up before releasing to customer!</span>`;
                } else {
                    if (policyDesc) policyDesc.innerHTML = `Vehicle must be released with a <strong>100% Full Tank</strong>. Customer is required to return Full Tank.`;
                }
                return;
            }

            // type === 'return'
            if (policyTitle) policyTitle.innerHTML = '⛽ Return Rule: Must Return 100% Full Tank';
            if (val === 'Full') {
                if (refuelSec) refuelSec.style.display = 'none';
                if (fullBanner) fullBanner.style.display = 'flex';
                if (amountInput) { amountInput.value = '0'; delete amountInput.dataset.autoFilled; }
                if (policyDesc) policyDesc.innerHTML = `Vehicle returned with <strong>100% Full Tank</strong> ✅ No refuel fee required.`;
            } else {
                if (fullBanner) fullBanner.style.display = 'none';
                if (refuelSec) refuelSec.style.display = 'block';

                let suggestedFee = 650;
                let missingText = 'Missing 1/4 Tank (~10L)';
                if (val === '3/4') {
                    suggestedFee = 650;
                    missingText = 'Missing 1/4 Tank (~10L)';
                } else if (val === '1/2') {
                    suggestedFee = 1300;
                    missingText = 'Missing 1/2 Tank (~20L)';
                } else if (val === '1/4') {
                    suggestedFee = 1950;
                    missingText = 'Missing 3/4 Tank (~30L)';
                } else if (val === 'Reserve') {
                    suggestedFee = 2400;
                    missingText = 'Near Empty (Reserve Tank)';
                } else if (val === 'Empty') {
                    suggestedFee = 2600;
                    missingText = '100% Empty Tank';
                }

                if (deficitTag) deficitTag.textContent = missingText;
                if (amountInput) {
                    amountInput.value = suggestedFee;
                    amountInput.dataset.autoFilled = 'true';
                }
                if (notesInput) {
                    notesInput.value = `Refueling Fee: Returned at ${val} (Full Tank required, ${missingText})`;
                }
                if (policyDesc) {
                    policyDesc.innerHTML = `<span style="color:#e11d48; font-weight:700;">⚠️ Refuel Fee Required: Returned with ${val} fuel. Customer must pay ₱${suggestedFee.toLocaleString()} to refill tank back to Full.</span>`;
                }
            }
        },







        handlePhotoSelect(input) {



            if (!input.files) return;



            const preview = document.getElementById('inspectPhotoPreview');



            Array.from(input.files).forEach(file => {
                if (!file) return;
                const isImg = (file.type || "").toLowerCase().startsWith("image/") || /\.(jpe?g|png|webp|gif|heic)$/i.test(file.name || "");
                if (!isImg) {
                    showNotification("Only image files are allowed for inspection photos.", "error");
                    return;
                }
                if (file.size > 5 * 1024 * 1024) {
                    showNotification("Inspection photos must be 5 MB or smaller.", "error");
                    return;
                }
                this.currentPhotos.push(file);



                const reader = new FileReader();



                reader.onload = (e) => {



                    const div = document.createElement('div');



                    div.style.cssText = 'flex: 0 0 100px; height: 100px; border-radius: 12px; overflow: hidden; border: 1px solid var(--border); position: relative;';



                    div.innerHTML = `



                        <img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;">



                        <button type="button" onclick="this.parentElement.remove()" style="position: absolute; top: 5px; right: 5px; background: rgba(239, 68, 68, 0.8); border: none; color: white; width: 20px; height: 20px; border-radius: 50%; font-size: 0.6rem;"><i class="fas fa-times"></i></button>



                    `;



                    preview.appendChild(div);



                };



                reader.readAsDataURL(file);



            });



        },







        async submit(event) {
            event.preventDefault();

            const mileageEl = document.getElementById('inspectMileage');
            const fuelEl = document.getElementById('inspectFuel');

            if (mileageEl) clearInlineError(mileageEl);
            if (fuelEl) clearInlineError(fuelEl);
            let hasError = false;

            const enteredMileage = parseFloat(mileageEl ? mileageEl.value : NaN);
            const minAllowed = parseFloat(mileageEl ? (mileageEl.dataset.minAllowed || 0) : 0);
            const minLabel = mileageEl ? (mileageEl.dataset.minLabel || 'minimum reading') : 'minimum reading';

            if (mileageEl && (!mileageEl.value.trim() || isNaN(enteredMileage) || enteredMileage < 0)) {
                showInlineError(mileageEl, 'Valid positive mileage is required');
                hasError = true;
            } else if (mileageEl && enteredMileage < minAllowed) {
                showInlineError(mileageEl, `Mileage (${enteredMileage.toLocaleString()} km) cannot be lower than ${minLabel.toLowerCase()} (${minAllowed.toLocaleString()} km)`);
                showNotification(`Mileage cannot be lower than ${minLabel.toLowerCase()} (${minAllowed.toLocaleString()} km). Reading cannot decrease!`, 'error');
                hasError = true;
            }

            if (hasError) return;

            const btn = document.getElementById('inspectSubmitBtn');
            const originalText = btn.innerHTML;
            const bookingId = document.getElementById('inspectBookingId').value;
            const type = document.getElementById('inspectType').value;
            const user = adminAuth.getUser();

            const formData = new FormData();
            formData.append('booking_id', bookingId);
            formData.append('inspection_type', type);
            formData.append('mileage', mileageEl.value);
            formData.append('fuel_level', fuelEl ? fuelEl.value : 'Full');
            formData.append('notes', document.getElementById('inspectNotes').value);
            formData.append('inspector_id', user ? user.id : 1);
            this.currentPhotos.forEach(file => formData.append('photos', file));

            // Refueling charge if return inspection and fuel is not Full
            if (type === 'return' && fuelEl && fuelEl.value !== 'Full') {
                const chargeBox = document.getElementById('inspectChargeCustomerCheckbox');
                const chargeAmountEl = document.getElementById('inspectFuelChargeAmount');
                const chargeNotesEl = document.getElementById('inspectFuelChargeNotes');
                if (chargeBox && chargeBox.checked && chargeAmountEl && parseFloat(chargeAmountEl.value) > 0) {
                    formData.append('fuel_charge', parseFloat(chargeAmountEl.value));
                    formData.append('fuel_charge_notes', chargeNotesEl ? chargeNotesEl.value : `Refueling Fee: Returned at ${fuelEl.value}`);
                }
            }

            // Driver Overtime if return inspection and 'With Driver'
            const driverSec = document.getElementById('inspectDriverOTSection');
            if (type === 'return' && driverSec && driverSec.style.display !== 'none') {
                const otHoursEl = document.getElementById('inspectDriverOTHours');
                const otNotesEl = document.getElementById('inspectDriverOTNotes');
                const rCharge = document.getElementById('inspectDriverOTCharge');
                const collectionMethod = (rCharge && rCharge.checked) ? 'company_charge' : 'direct_cash';
                const otHrs = parseFloat(otHoursEl ? otHoursEl.value : 0) || 0;
                formData.append('driver_ot_hours', otHrs);
                formData.append('driver_ot_collection_method', collectionMethod);
                formData.append('driver_ot_notes', otNotesEl ? otNotesEl.value.trim() : '');
            }

            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Submitting...';

            try {
                const res = await fetch(`${API_URL}/inspections/submit`, { method: 'POST', body: formData });
                const data = await res.json();
                if (res.ok) {
                    let msg = 'Inspection report submitted!';
                    if (data.distance_driven !== undefined && data.distance_driven !== null) {
                        msg += ` Distance driven: ${data.distance_driven} km.`;
                    }
                    if (data.fuel_charge !== undefined && data.fuel_charge !== null) {
                        msg += ` Refueling fee of ₱${parseFloat(data.fuel_charge).toLocaleString()} added to booking.`;
                    }
                    if (data.driver_ot_amount !== undefined && data.driver_ot_amount !== null && parseFloat(data.driver_ot_amount) > 0) {
                        const methodLabel = data.driver_ot_collection_method === 'company_charge' ? 'charged to booking' : 'paid cash to driver';
                        msg += ` Driver OT fee: ₱${parseFloat(data.driver_ot_amount).toLocaleString()} (${methodLabel}).`;
                    }
                    showNotification(msg, 'success');
                    document.getElementById('inspectionModal').style.display = 'none';
                    const bdm = document.getElementById('bookingDetailsModal');
                    if (bdm) bdm.style.display = 'none';
                    modalClose();
                    Bookings.refresh();
                    if (typeof Vehicles !== 'undefined' && Vehicles.refresh) Vehicles.refresh();
                } else {
                    showNotification(data.error || 'Submission failed', 'error');
                }
            } catch (err) {
                showNotification('Network error', 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        },







        async showReceiptModal(bookingId) {



            const modal = document.getElementById('receiptPreviewModal');



            const body = document.getElementById('receiptBody');



            if (!modal || !body) return;







            // Use already-loaded booking data across active, past, and archived bookings
            const b = (Bookings.data || []).find(x => x.id === bookingId)
                   || (window.PastBookings && Array.isArray(PastBookings.data) ? PastBookings.data.find(x => x.id === bookingId) : null)
                   || (window.ArchivedBookings && Array.isArray(ArchivedBookings.data) ? ArchivedBookings.data.find(x => x.id === bookingId) : null)
                   || (Bookings.currentBooking && Bookings.currentBooking.id === bookingId ? Bookings.currentBooking : null);

            if (!b) {



                modal.style.display = 'flex';



                body.innerHTML = '<div style="text-align:center;color:#f87171;padding:20px;"><i class="fas fa-exclamation-circle"></i> Booking not found</div>';



                return;



            }







            modal.style.display = 'flex';



            body.innerHTML = '<div style="text-align:center;color:rgba(255,255,255,0.4);padding:30px;"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';







            // Fetch payment proofs using correct API_URL



            let proofs = [];



            try {



                const pRes = await fetch(`${API_URL}/admin/bookings/${bookingId}/payment-proof`);



                if (pRes.ok) proofs = await pRes.json();



                if (!Array.isArray(proofs)) proofs = [];



            } catch(e) { proofs = []; }

            if (proofs.length === 0 && (b.payment_method || b.reference_number)) {
                proofs = [{
                    method: b.payment_method || 'Payment',
                    amount: b.amount_paid || b.total_price || 0,
                    reference_number: b.reference_number || '',
                    status: b.payment_status || 'Completed'
                }];
            }

            const fmt = n => parseFloat(n||0).toLocaleString('en-PH', {minimumFractionDigits:2});



            const fmtD = d => {



                if (!d) return 'N/A';



                try { return new Date(d).toLocaleDateString('en-PH', {year:'numeric',month:'short',day:'numeric'}); }



                catch(e) { return String(d).split('T')[0]; }



            };
            const fmtDT = d => {
                if (!d) return fmtD(b.start_date);
                try { return new Date(d).toLocaleString('en-PH', {timeZone:'Asia/Manila', year:'numeric', month:'short', day:'numeric', hour:'numeric', minute:'2-digit'}); }
                catch(e) { return fmtD(d); }
            };







            // Build proof images HTML



            const proofItems = proofs.filter(p => p.payment_proof_url);

            const proofsHtml = proofItems.length ? `
                <div style="margin-top:16px;padding-top:16px;border-top:1px solid #e2e8f0;">
                    <div style="font-size:0.68rem;font-weight:700;color:#64748b;text-transform:uppercase;margin-bottom:10px;letter-spacing:0.04em;">Payment Proof</div>
                    ${proofItems.map(p => `
                        <div style="margin-bottom:10px;padding:8px;background:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;">
                            <div style="font-size:0.75rem;color:#475569;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;">
                                <span>${p.method||'Payment'}${p.reference_number?' &bull; <code style="color:#0284c7;background:#e0f2fe;padding:2px 6px;border-radius:4px;font-family:monospace;">'+p.reference_number+'</code>':''}</span>
                                <span style="color:#00B14F;font-weight:800;font-size:0.85rem;">₱${fmt(p.amount)}</span>
                            </div>
                            <img src="${p.payment_proof_url}" style="width:100%;border-radius:8px;max-height:200px;object-fit:contain;background:#f1f5f9;border:1px solid #e2e8f0;">
                        </div>
                    `).join('')}
                </div>` : '';

            body.innerHTML = `
                <div style="padding:4px 0 14px;border-bottom:1px solid #e2e8f0;margin-bottom:14px;display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <div style="font-size:1.05rem;font-weight:900;color:#0f172a;letter-spacing:0.02em;">RECEIPT #${String(b.id).padStart(6,'0')}</div>
                        <div style="font-size:0.72rem;color:#64748b;margin-top:3px;"><i class="far fa-clock" style="margin-right:4px;"></i>Date Issued: ${fmtDT(b.created_at)}</div>
                    </div>
                    <div style="font-size:0.75rem;color:#64748b;text-align:right;">
                        Status: <span style="color:#15803d;background:#dcfce7;border:1px solid #bbf7d0;font-weight:800;padding:2px 8px;border-radius:6px;font-size:0.72rem;">${(b.status||'').toUpperCase()}</span>
                    </div>
                </div>

                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px;">
                    <div>
                        <div style="font-size:0.68rem;color:#64748b;text-transform:uppercase;font-weight:700;letter-spacing:0.04em;margin-bottom:4px;">Billed To</div>
                        <div style="font-size:0.9rem;color:#0f172a;font-weight:700;">${b.customer_name||'N/A'}</div>
                    </div>
                    <div>
                        <div style="font-size:0.68rem;color:#64748b;text-transform:uppercase;font-weight:700;letter-spacing:0.04em;margin-bottom:4px;">Rental Period</div>
                        <div style="font-size:0.82rem;color:#0f172a;font-weight:600;">${fmtD(b.start_date)}</div>
                        <div style="font-size:0.78rem;color:#64748b;">to ${fmtD(b.end_date)}</div>
                    </div>
                </div>

                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:12px;margin-bottom:14px;">
                    <div style="font-size:0.68rem;color:#64748b;text-transform:uppercase;font-weight:700;letter-spacing:0.04em;margin-bottom:6px;">Vehicle</div>
                    <div style="font-size:0.9rem;color:#0f172a;font-weight:700;">${b.car||'N/A'}</div>
                    <div style="font-size:0.76rem;color:#64748b;margin-top:2px;">${b.rental_type||''}</div>
                    ${b.rental_type === 'With Driver' ? `
                        <div style="margin-top:8px;padding-top:8px;border-top:1px solid #e2e8f0;font-size:0.78rem;color:#166534;display:flex;justify-content:space-between;font-weight:600;">
                            <span>Chauffeur Driver Wage:</span>
                            <strong>₱${fmt(b.driver_fee || 755)}</strong>
                        </div>
                    ` : ''}
                    ${b.driver_ot_hours && parseFloat(b.driver_ot_hours) > 0 ? `
                        <div style="margin-top:6px;font-size:0.78rem;color:#854d0e;display:flex;justify-content:space-between;font-weight:600;">
                            <span>Driver OT (${b.driver_ot_hours} hrs @ ₱${parseFloat(b.driver_ot_rate)||95}/hr):</span>
                            <strong>₱${fmt(b.driver_ot_amount || (parseFloat(b.driver_ot_hours)*(parseFloat(b.driver_ot_rate)||95)))} <span style="font-size:0.68rem;opacity:0.8;">(${b.driver_ot_collection_method === 'company_charge' ? 'Charged' : 'Cash to Driver'})</span></strong>
                        </div>
                    ` : ''}
                </div>

                <div>
                    <div style="font-size:0.68rem;color:#64748b;text-transform:uppercase;font-weight:700;letter-spacing:0.04em;margin-bottom:8px;">Payment</div>
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 14px;background:#f0fdf4;border:1.5px solid #86efac;border-radius:12px;">
                        <span style="font-weight:800;color:#166534;font-size:0.9rem;">Total Amount</span>
                        <span style="font-weight:900;color:#00B14F;font-size:1.25rem;">₱${fmt(b.total_price)}</span>
                    </div>

                    <div style="font-size:0.76rem;color:#64748b;margin-top:8px;display:flex;justify-content:space-between;align-items:center;">
                        <span>Payment: <span style="color:${['paid','fully paid'].includes((b.payment_status||'').toLowerCase().trim())?'#16a34a':'#d97706'};background:${['paid','fully paid'].includes((b.payment_status||'').toLowerCase().trim())?'#dcfce7':'#fef3c7'};border:1px solid ${['paid','fully paid'].includes((b.payment_status||'').toLowerCase().trim())?'#bbf7d0':'#fde68a'};font-weight:800;padding:2px 8px;border-radius:6px;font-size:0.72rem;">${(b.payment_status||'pending').toUpperCase()}</span></span>
                    </div>

                    ${proofs.length > 0 ? proofs.map(p => `
                        <div style="margin-top:8px;padding:10px 12px;background:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                                <span style="font-size:0.75rem;color:#475569;font-weight:600;">${p.method||'Payment'}</span>
                                <span style="font-size:0.85rem;color:#00B14F;font-weight:800;">₱${fmt(p.amount)}</span>
                            </div>
                            ${p.reference_number ? `<div style="font-size:0.78rem;color:#334155;font-weight:600;">Ref #: <span style="color:#0284c7;background:#e0f2fe;padding:2px 6px;border-radius:4px;font-family:monospace;font-size:0.75rem;">${p.reference_number}</span></div>` : ''}
                            <div style="font-size:0.7rem;color:#64748b;margin-top:4px;">Status: ${(p.status||'completed').toUpperCase()}</div>
                        </div>
                    `).join('') : ''}
                </div>

                ${proofsHtml}

                <div style="margin-top:16px;padding-top:14px;border-top:1px solid #e2e8f0;">
                    <button type="button" onclick="window.open(API_URL + '/bookings/${b.id}/receipt', '_blank')" style="width:100%;background:#00B14F;color:#ffffff;border:none;padding:12px 16px;border-radius:12px;font-size:0.88rem;font-weight:800;display:flex;align-items:center;justify-content:center;gap:8px;cursor:pointer;box-shadow:0 4px 14px rgba(0,177,79,0.35);transition:transform 0.15s,box-shadow 0.15s;" onmouseover="this.style.boxShadow='0 6px 20px rgba(0,177,79,0.5)';" onmouseout="this.style.boxShadow='0 4px 14px rgba(0,177,79,0.35)';">
                        <i class="fas fa-file-pdf"></i> Download Official PDF Receipt
                    </button>
                </div>
            `;



        }







    };







    function openChangePasswordModal() {



        document.getElementById('changePasswordModal').style.display = 'flex';



    }







    async function submitChangePassword() {



        const newPass = document.getElementById('newMobilePassword').value;



        const confirmPass = document.getElementById('confirmMobilePassword').value;



        const user = adminAuth.getUser();







        if (!newPass || !confirmPass) {



            alert('Please fill in both fields');



            return;



        }



        if (newPass !== confirmPass) {



            alert('Passwords do not match');



            return;



        }



        if (newPass.length < 6) {



            alert('Password too short (min 6 chars)');



            return;



        }







        try {



            const res = await fetch(`${API_BASE}/api/admin/change-password`, {



                method: 'POST',



                headers: { 'Content-Type': 'application/json' },



                body: JSON.stringify({ user_id: user.id, new_password: newPass })



            });



            if (res.ok) {



                showNotification('Password updated successfully!', 'success');



                document.getElementById('changePasswordModal').style.display = 'none';



                document.getElementById('newMobilePassword').value = '';



                document.getElementById('confirmMobilePassword').value = '';



            } else {



                const data = await res.json();



                showNotification(data.error || 'Failed to update', 'error');



            }



        } catch (err) { showNotification('Network error', 'error'); }



    }

    function openSuperAdminProfileModal() {
        const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
        if (!user) {
            if (typeof showNotification === 'function') showNotification('Please log in first', 'error');
            return;
        }
        const userRole = (user.role || '').toLowerCase().replace(/_/g, ' ').trim();
        const isSuper = user.role === 'super_admin' || userRole.includes('super admin') || userRole.includes('superadmin');
        if (!isSuper) {
            if (typeof showNotification === 'function') showNotification('Only Super Admin can edit this profile.', 'error');
            return;
        }

        const emailInput = document.getElementById('superAdminEditEmail');
        if (emailInput) emailInput.value = user.email || '';

        const currPass = document.getElementById('superAdminCurrentPassword');
        if (currPass) currPass.value = '';

        const newPass = document.getElementById('superAdminNewPassword');
        if (newPass) newPass.value = '';

        const confPass = document.getElementById('superAdminConfirmPassword');
        if (confPass) confPass.value = '';

        const errDiv = document.getElementById('superAdminProfileError');
        if (errDiv) {
            errDiv.textContent = '';
            errDiv.style.display = 'none';
        }

        const modal = document.getElementById('superAdminProfileModal');
        if (modal) modal.style.display = 'flex';
    }

    function closeSuperAdminProfileModal() {
        const modal = document.getElementById('superAdminProfileModal');
        if (modal) modal.style.display = 'none';
        const currPass = document.getElementById('superAdminCurrentPassword');
        if (currPass) currPass.value = '';
        const newPass = document.getElementById('superAdminNewPassword');
        if (newPass) newPass.value = '';
        const confPass = document.getElementById('superAdminConfirmPassword');
        if (confPass) confPass.value = '';
    }

    async function submitSuperAdminProfileUpdate() {
        const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser) ? adminAuth.getUser() : null;
        if (!user) {
            if (typeof showNotification === 'function') showNotification('Please log in first', 'error');
            return;
        }
        const userRole = (user.role || '').toLowerCase().replace(/_/g, ' ').trim();
        const isSuper = user.role === 'super_admin' || userRole.includes('super admin') || userRole.includes('superadmin');
        if (!isSuper) {
            if (typeof showNotification === 'function') showNotification('Only Super Admin accounts can edit this profile.', 'error');
            return;
        }

        const errDiv = document.getElementById('superAdminProfileError');
        const showError = (msg) => {
            if (errDiv) {
                errDiv.textContent = msg;
                errDiv.style.display = 'block';
            } else if (typeof showNotification === 'function') {
                showNotification(msg, 'error');
            } else {
                alert(msg);
            }
        };

        if (errDiv) {
            errDiv.textContent = '';
            errDiv.style.display = 'none';
        }

        const email = (document.getElementById('superAdminEditEmail')?.value || '').trim();
        const currentPassword = (document.getElementById('superAdminCurrentPassword')?.value || '').trim();
        const newPassword = (document.getElementById('superAdminNewPassword')?.value || '').trim();
        const confirmPassword = (document.getElementById('superAdminConfirmPassword')?.value || '').trim();

        if (!email) {
            showError('Please enter a valid email address.');
            return;
        }
        if (!currentPassword) {
            showError('Please enter your current password to authorize changes.');
            return;
        }
        if (newPassword) {
            if (newPassword.length < 6) {
                showError('New password must be at least 6 characters long.');
                return;
            }
            if (newPassword !== confirmPassword) {
                showError('New passwords do not match.');
                return;
            }
        }

        const btn = document.getElementById('superAdminSaveProfileBtn');
        const origHtml = btn ? btn.innerHTML : '';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        }

        try {
            const payload = {
                admin_id: user.id,
                current_password: currentPassword,
                email: email
            };
            if (newPassword) {
                payload.new_password = newPassword;
            }

            const res = await fetch(`${API_BASE}/api/admin/super-admin/update-profile`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (res.ok && data.success) {
                try {
                    const raw = localStorage.getItem('admin_user');
                    if (raw) {
                        const parsed = JSON.parse(raw);
                        if (parsed.user) {
                            parsed.user.email = data.user.email;
                            localStorage.setItem('admin_user', JSON.stringify(parsed));
                        } else {
                            parsed.email = data.user.email;
                            localStorage.setItem('admin_user', JSON.stringify(parsed));
                        }
                    }
                } catch(e) {
                    console.error('Error updating cached admin user:', e);
                }

                const emailEl = document.getElementById('settingsEmail');
                if (emailEl) emailEl.textContent = data.user.email;

                closeSuperAdminProfileModal();

                if (typeof showNotification === 'function') {
                    showNotification(data.message || 'Super Admin profile updated successfully!', 'success');
                } else {
                    alert('Super Admin profile updated successfully!');
                }
            } else {
                showError(data.error || 'Failed to update profile. Please check your credentials.');
            }
        } catch (err) {
            console.error('Update profile error:', err);
            showError('Network error. Failed to reach server.');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = origHtml;
            }
        }
    }

    window.openSuperAdminProfileModal = openSuperAdminProfileModal;
    window.closeSuperAdminProfileModal = closeSuperAdminProfileModal;
    window.submitSuperAdminProfileUpdate = submitSuperAdminProfileUpdate;

    function showNotification(message, type = 'info') {



        const container = document.getElementById('notificationContainer');



        if (!container) return;







        const notification = document.createElement('div');



        notification.className = `notification ${type}`;



        



        let icon = 'info-circle';



        if (type === 'success') icon = 'check-circle';



        if (type === 'error') icon = 'exclamation-circle';







        notification.innerHTML = `



            <div class="notification-icon"><i class="fas fa-${icon}"></i></div>



            <div style="flex:1; font-size: 0.9rem; font-weight: 500;">${message}</div>



        `;







        container.appendChild(notification);



        setTimeout(() => notification.classList.add('show'), 10);



        setTimeout(() => {



            notification.classList.remove('show');



            setTimeout(() => notification.remove(), 400);



        }, 3500);



    }







    document.addEventListener('DOMContentLoaded', () => {



        adminAuth.initSession();







        // FCM token save function for admin (defined early in script, referenced here for completeness)



        // saveAdminFcmToken is defined at top of script block







        // Login Button Listener



        const loginBtn = document.getElementById('loginBtn');



        if (loginBtn) {



            loginBtn.addEventListener('click', () => {



                adminAuth.login();



            });



        }



        



        // Staff Form Listener



        const staffForm = document.getElementById('staffForm');



        if (staffForm) {



            staffForm.addEventListener('submit', (e) => Staff.submit(e));



        }







        setInterval(() => {



            const now = new Date();



            const headerTime = document.getElementById('headerTime');



            if (headerTime) {



                headerTime.textContent = now.toLocaleString('en-US', {



                    weekday: 'short', month: 'short', day: 'numeric',



                    hour: '2-digit', minute: '2-digit', second: '2-digit'



                });



            }



        }, 1000);







        // Auto-refresh dashboard stats every 60 seconds (silent, no loading flash)



        setInterval(() => {



            if (typeof currentTab !== 'undefined' && currentTab === 'dashboard') {



                refreshDashboard();



            }



        }, 60000);







        // ---- Android Back Button Handler ----



        // Uses custom modal instead of window.confirm() (which is blocked on Android WebView)



        window.showExitConfirm = function() {



            document.getElementById('exitConfirmModal').style.display = 'flex';



        };



        window.hideExitConfirm = function() {



            document.getElementById('exitConfirmModal').style.display = 'none';



        };



        window.confirmExit = function() {



            // Logout then exit



            adminAuth.logoutAndExit();



        };







        // Tab history stack for back navigation



        var _tabHistory = [];



        var _origSwitchTabForBack = window.switchTab;



        window.switchTab = function(tabId) {



            var current = typeof currentTab !== 'undefined' ? currentTab : null;



            if (current && current !== tabId) {



                _tabHistory.push(current);



                if (_tabHistory.length > 10) _tabHistory.shift();



            }



            _origSwitchTabForBack(tabId);



        };







        const handleBackButton = (e) => {



            if (e && e.preventDefault) e.preventDefault();







            // 1. If exit modal is open, close it



            const exitModal = document.getElementById('exitConfirmModal');



            if (exitModal && exitModal.style.display === 'flex') {



                hideExitConfirm();



                return;



            }







            // 2. Close any open modal/overlay



            const modals = document.querySelectorAll('.premium-modal, #inspectionModal, #licensePreviewModal, #changePasswordModal, #bookingDetailsModal, #vehicleModal, #driverModal');



            for (const m of modals) {



                if (m && (m.style.display === 'flex' || m.style.display === 'block')) {



                    m.style.display = 'none';



                    return;



                }



            }







            // 3. Close notification panel if open



            const notifPanel = document.getElementById('adminNotifPanel');



            if (notifPanel && notifPanel.style.display !== 'none') {



                notifPanel.style.display = 'none';



                return;



            }







            // 4. Close side drawer if open



            const drawer = document.getElementById('sideDrawer');



            if (drawer && (drawer.style.left === '0px' || drawer.classList.contains('open'))) {



                toggleDrawer(false);



                return;



            }







            // 5. If on login screen, exit app



            const loginOverlay = document.getElementById('adminLoginOverlay');



            if (loginOverlay && loginOverlay.style.display !== 'none') {



                if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App) {



                    window.Capacitor.Plugins.App.exitApp();



                }



                return;



            }







            // 6. Navigate back through tab history



            if (_tabHistory.length > 0) {



                var prevTab = _tabHistory.pop();



                _origSwitchTabForBack(prevTab);



                return;



            }







            // 7. On root tab - show exit confirmation



            showExitConfirm();



        };







        // Register for both Capacitor and Cordova back button events



        (function() {



            function _adminBackListener(e) {



                if (e && e.preventDefault) e.preventDefault();



                handleBackButton(e);



            }



            document.addEventListener('backbutton', _adminBackListener, false);



            document.addEventListener('deviceready', function() {



                document.removeEventListener('backbutton', _adminBackListener, false);



                document.addEventListener('backbutton', _adminBackListener, false);



                if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App) {



                    window.Capacitor.Plugins.App.addListener('backButton', function() {



                        handleBackButton();



                    });



                }



                



                // Initialize Push Notifications for Admin



                if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.PushNotifications) {



                    const PushNotifications = window.Capacitor.Plugins.PushNotifications;



                    



                    // Request permission



                    PushNotifications.requestPermissions().then(function(result) {



                        if (result.receive === 'granted') {



                            PushNotifications.register();



                        }



                    });



                    



                    // Listen for registration success



                    PushNotifications.addListener('registration', function(token) {



                        console.log('Admin FCM Token:', token.value);



                        window._adminFcmToken = token.value;



                        saveAdminFcmToken(token.value);



                    });



                    



                    // Listen for registration errors



                    PushNotifications.addListener('registrationError', function(error) {



                        console.error('Admin FCM Registration Error:', error);



                    });



                    



                    // Listen for push notifications received



                    PushNotifications.addListener('pushNotificationReceived', function(notification) {



                        console.log('Admin Push notification received:', notification);



                        // Show in-app notification



                        showNotification(notification.title || 'New Notification', 'info');



                        



                        // Refresh chat if on chat tab



                        const user = adminAuth.getUser();



                        if (user && typeof AdminChat !== 'undefined') {



                            AdminChat.updateNavBadge();



                        }



                    });



                    



                    // Listen for notification taps



                    PushNotifications.addListener('pushNotificationActionPerformed', function(action) {

                        console.log('Admin Push notification action performed:', action);

                        var data = (action.notification && action.notification.data) ? action.notification.data : {};
                        var type = data.type || '';

                        if (type === 'license' || type === 'admin_license_upload') {
                            switchTab('users');
                        } else if (type === 'admin_new_booking' || type === 'admin_booking_cancelled' || type === 'admin_payment_proof' || type === 'admin_extension_request') {
                            switchTab('bookings');
                        } else {
                            switchTab('chat');
                        }

                    });



                }



            }, false);



        })();



    });







    // Global Bindings for HTML Access



    window.adminAuth = adminAuth;



    window.toggleDarkMode = toggleDarkMode;



    window.toggleSystemConfigModal = toggleSystemConfigModal;



    window.closeSystemConfigModal = closeSystemConfigModal;



    window.closeSystemConfigModalBackdrop = closeSystemConfigModalBackdrop;
    window.toggleAddonsModal = toggleAddonsModal;
    window.closeAddonsModal = closeAddonsModal;
    window.closeAddonsModalBackdrop = closeAddonsModalBackdrop;
    window.editAddon = editAddon;
    window.deleteAddon = deleteAddon;
    window.saveAddon = saveAddon;
    window.resetAddonForm = resetAddonForm;
    window.toggleLocationsModal = toggleLocationsModal;
    window.closeLocationsModal = closeLocationsModal;
    window.closeLocationsModalBackdrop = closeLocationsModalBackdrop;
    window.editLocation = editLocation;
    window.deleteLocation = deleteLocation;
    window.saveLocation = saveLocation;
    window.resetLocationForm = resetLocationForm;
    window.Vehicles = Vehicles;
    window.FleetCalendar = FleetCalendar;
    window.Bookings = Bookings;

    // ==================== WALKIN BOOKING CONTROLLER ====================
    const WalkinBooking = {
        mode: 'guest', // 'guest' or 'registered'
        vehicles: [],
        customers: [],
        selectedCustomer: null,

        formatTime(date) {
            const h = String(date.getHours()).padStart(2, '0');
            const m = String(date.getMinutes()).padStart(2, '0');
            return `${h}:${m}`;
        },

        formatDate(date) {
            const y = date.getFullYear();
            const m = String(date.getMonth() + 1).padStart(2, '0');
            const d = String(date.getDate()).padStart(2, '0');
            return `${y}-${m}-${d}`;
        },

        async openModal(preselectedVehicleId = null) {
            const modal = document.getElementById('walkinBookingModal');
            if (!modal) return;

            // Reset form
            const form = document.getElementById('walkinBookingForm');
            if (form) form.reset();

            this.selectedCustomer = null;
            this.setMode('guest');

            // Default dates: today start time now
            const now = new Date();
            const todayStr = this.formatDate(now);
            const timeStr = this.formatTime(now);

            const tomorrow = new Date(now.getTime() + 86400000);
            const tomorrowStr = this.formatDate(tomorrow);

            const startD = document.getElementById('walkinStartDate');
            const startT = document.getElementById('walkinStartTime');
            const endD = document.getElementById('walkinEndDate');
            const endT = document.getElementById('walkinEndTime');

            if (startD) startD.value = todayStr;
            if (startT) startT.value = timeStr;
            if (endD) endD.value = tomorrowStr;
            if (endT) endT.value = timeStr;

            const extraFee = document.getElementById('walkinExtraFee');
            if (extraFee) extraFee.value = '0';
            const disc = document.getElementById('walkinDiscount');
            if (disc) disc.value = '0';

            modal.style.display = 'flex';
            if (typeof modalOpen === 'function') modalOpen();

            // Load vehicles & customers in background
            await Promise.all([
                this.loadVehicles(preselectedVehicleId),
                this.loadCustomers()
            ]);

            this.recalculate();
        },

        closeModal() {
            const modal = document.getElementById('walkinBookingModal');
            if (modal) modal.style.display = 'none';
            if (typeof modalClose === 'function') modalClose();
        },

        setMode(mode) {
            this.mode = mode;
            const guestBtn = document.getElementById('walkinModeGuestBtn');
            const regBtn = document.getElementById('walkinModeRegisteredBtn');
            const guestSec = document.getElementById('walkinGuestSection');
            const regSec = document.getElementById('walkinRegisteredSection');

            const nameInput = document.getElementById('walkinCustName');
            const phoneInput = document.getElementById('walkinCustPhone');

            if (mode === 'guest') {
                if (guestBtn) {
                    guestBtn.style.border = '2px solid #00B14F';
                    guestBtn.style.background = 'rgba(0, 177, 79, 0.08)';
                    guestBtn.style.color = '#00B14F';
                }
                if (regBtn) {
                    regBtn.style.border = '1px solid var(--border, #cbd5e1)';
                    regBtn.style.background = 'var(--surface-solid, #ffffff)';
                    regBtn.style.color = 'var(--text-muted, #64748b)';
                }
                if (guestSec) guestSec.style.display = 'block';
                if (regSec) regSec.style.display = 'none';

                if (nameInput) nameInput.required = true;
                if (phoneInput) phoneInput.required = true;
                const uid = document.getElementById('walkinCustUserId');
                if (uid) uid.value = '';
            } else {
                if (regBtn) {
                    regBtn.style.border = '2px solid #2563eb';
                    regBtn.style.background = 'rgba(37, 99, 235, 0.08)';
                    regBtn.style.color = '#2563eb';
                }
                if (guestBtn) {
                    guestBtn.style.border = '1px solid var(--border, #cbd5e1)';
                    guestBtn.style.background = 'var(--surface-solid, #ffffff)';
                    guestBtn.style.color = 'var(--text-muted, #64748b)';
                }
                if (guestSec) guestSec.style.display = 'none';
                if (regSec) regSec.style.display = 'block';

                if (nameInput) nameInput.required = false;
                if (phoneInput) phoneInput.required = false;
            }
        },

        setCurrentTime() {
            const now = new Date();
            const startD = document.getElementById('walkinStartDate');
            const startT = document.getElementById('walkinStartTime');
            if (startD) startD.value = this.formatDate(now);
            if (startT) startT.value = this.formatTime(now);
            this.recalculate();
        },

        addDays(num) {
            const startD = document.getElementById('walkinStartDate');
            const startVal = startD && startD.value ? new Date(startD.value) : new Date();
            const endD = document.getElementById('walkinEndDate');
            if (endD) {
                const target = new Date(startVal.getTime() + (num * 86400000));
                endD.value = this.formatDate(target);
            }
            this.recalculate();
        },

        async loadVehicles(preselectedId = null) {
            try {
                const res = await fetch(`${API_BASE}/api/vehicles`);
                if (!res.ok) throw new Error('Failed to load vehicles');
                const list = await res.json();
                this.vehicles = Array.isArray(list) ? list : (list.vehicles || []);

                const sel = document.getElementById('walkinVehicleSelect');
                if (!sel) return;

                sel.innerHTML = '<option value="">Select an available vehicle...</option>';
                this.vehicles.forEach(v => {
                    const statusStr = (v.status || 'Available');
                    const isOperational = !['maintenance', 'repair', 'sold'].includes(statusStr.toLowerCase());
                    if (isOperational) {
                        const opt = document.createElement('option');
                        opt.value = v.id;
                        opt.textContent = `${v.brand} ${v.model} (${v.plate_number || 'No Plate'}) - ₱${Number(v.daily_rate || 0).toLocaleString()}/day [${statusStr}]`;
                        opt.dataset.rate = v.daily_rate || 0;
                        if (preselectedId && String(v.id) === String(preselectedId)) {
                            opt.selected = true;
                        }
                        sel.appendChild(opt);
                    }
                });
            } catch (err) {
                console.error('Error loading vehicles for walk-in:', err);
            }
        },

        async loadCustomers() {
            try {
                const res = await fetch(`${API_BASE}/api/admin/users/list`);
                if (res.ok) {
                    const data = await res.json();
                    this.customers = Array.isArray(data) ? data : (data.users || []);
                }
            } catch (err) {
                console.warn('Could not preload customers list:', err);
            }
        },

        onCustomerSearch(query) {
            const dropdown = document.getElementById('walkinCustomerDropdown');
            if (!dropdown) return;

            const q = (query || '').toLowerCase().trim();
            if (q.length < 1) {
                dropdown.style.display = 'none';
                return;
            }

            const matches = this.customers.filter(c => {
                const name = (c.full_name || '').toLowerCase();
                const email = (c.email || '').toLowerCase();
                const phone = (c.phone || '').toLowerCase();
                return name.includes(q) || email.includes(q) || phone.includes(q);
            }).slice(0, 10);

            if (matches.length === 0) {
                dropdown.innerHTML = '<div style="padding: 10px 14px; font-size: 0.78rem; color: var(--text-muted);">No matching registered customers found.</div>';
                dropdown.style.display = 'block';
                return;
            }

            let html = '';
            matches.forEach(m => {
                const safeName = (m.full_name || 'Customer').replace(/"/g, '&quot;');
                const safeEmail = (m.email || '').replace(/"/g, '&quot;');
                const safePhone = (m.phone || '').replace(/"/g, '&quot;');
                html += `
                    <div onclick="WalkinBooking.selectCustomer(${m.id})" 
                         style="padding: 10px 14px; border-bottom: 1px solid var(--border, #e2e8f0); cursor: pointer; transition: background 0.15s;"
                         onmouseover="this.style.background='rgba(0,177,79,0.06)'" onmouseout="this.style.background='transparent'">
                        <div style="font-weight: 700; font-size: 0.82rem; color: var(--text-main, #0f172a);">${safeName}</div>
                        <div style="font-size: 0.72rem; color: var(--text-muted, #64748b);">${safeEmail} • ${safePhone}</div>
                    </div>
                `;
            });
            dropdown.innerHTML = html;
            dropdown.style.display = 'block';
        },

        selectCustomer(userId) {
            const cust = this.customers.find(c => Number(c.id) === Number(userId));
            if (!cust) return;

            this.selectedCustomer = cust;
            const uidInput = document.getElementById('walkinCustUserId');
            if (uidInput) uidInput.value = cust.id;

            const nameEl = document.getElementById('walkinSelectedCustName');
            if (nameEl) nameEl.textContent = cust.full_name || 'Customer';

            const metaEl = document.getElementById('walkinSelectedCustMeta');
            if (metaEl) metaEl.textContent = `${cust.email || 'No email'} • ${cust.phone || 'No phone'}`;
            
            const card = document.getElementById('walkinSelectedCustCard');
            if (card) card.style.display = 'flex';

            const searchInput = document.getElementById('walkinCustomerSearch');
            if (searchInput) searchInput.style.display = 'none';

            const dropdown = document.getElementById('walkinCustomerDropdown');
            if (dropdown) dropdown.style.display = 'none';
        },

        clearCustomerSelection() {
            this.selectedCustomer = null;
            const uidInput = document.getElementById('walkinCustUserId');
            if (uidInput) uidInput.value = '';

            const card = document.getElementById('walkinSelectedCustCard');
            if (card) card.style.display = 'none';

            const searchInput = document.getElementById('walkinCustomerSearch');
            if (searchInput) {
                searchInput.style.display = 'block';
                searchInput.value = '';
                searchInput.focus();
            }
        },

        onVehicleChange() {
            const sel = document.getElementById('walkinVehicleSelect');
            if (!sel) return;
            const opt = sel.options[sel.selectedIndex];
            const dailyRate = opt ? Number(opt.dataset.rate || 0) : 0;
            this.recalculate(dailyRate);
        },

        getDays() {
            const startD = document.getElementById('walkinStartDate');
            const endD = document.getElementById('walkinEndDate');
            if (!startD || !endD || !startD.value || !endD.value) return 1;

            const s = new Date(startD.value).getTime();
            const e = new Date(endD.value).getTime();
            if (isNaN(s) || isNaN(e) || e < s) return 1;
            return Math.max(1, Math.round((e - s) / 86400000));
        },

        recalculate(forcedDailyRate = null) {
            const days = this.getDays();
            const daysBadge = document.getElementById('walkinDurationDaysBadge');
            if (daysBadge) daysBadge.textContent = `${days} Day${days > 1 ? 's' : ''}`;

            const sel = document.getElementById('walkinVehicleSelect');
            let dailyRate = 0;
            if (forcedDailyRate !== null) {
                dailyRate = forcedDailyRate;
            } else if (sel && sel.selectedIndex >= 0) {
                const opt = sel.options[sel.selectedIndex];
                dailyRate = opt ? Number(opt.dataset.rate || 0) : 0;
            }

            const basePriceInput = document.getElementById('walkinBasePrice');
            if (basePriceInput) {
                basePriceInput.value = dailyRate * days;
            }

            // Driver fee calculation if With Driver selected
            const rType = document.getElementById('walkinRentalType');
            const extraFeeInput = document.getElementById('walkinExtraFee');
            if (rType && extraFeeInput) {
                if (rType.value === 'With Driver') {
                    extraFeeInput.value = 755 * days;
                } else if (Number(extraFeeInput.value) === 755 * days) {
                    extraFeeInput.value = '0';
                }
            }

            this.recalculateTotal();
        },

        recalculateTotal() {
            const baseInput = document.getElementById('walkinBasePrice');
            const extraInput = document.getElementById('walkinExtraFee');
            const discInput = document.getElementById('walkinDiscount');

            if (baseInput) {
                if (baseInput.value.length > 7) baseInput.value = baseInput.value.slice(0, 7);
                if (Number(baseInput.value) > 500000) baseInput.value = 500000;
                if (Number(baseInput.value) < 0) baseInput.value = 0;
            }
            if (extraInput) {
                if (extraInput.value.length > 6) extraInput.value = extraInput.value.slice(0, 6);
                if (Number(extraInput.value) > 50000) extraInput.value = 50000;
                if (Number(extraInput.value) < 0) extraInput.value = 0;
            }
            if (discInput) {
                if (discInput.value.length > 6) discInput.value = discInput.value.slice(0, 6);
                if (Number(discInput.value) > 50000) discInput.value = 50000;
                if (Number(discInput.value) < 0) discInput.value = 0;
            }

            const base = Math.min(500000, Math.max(0, Number(baseInput?.value || 0)));
            const extra = Math.min(50000, Math.max(0, Number(extraInput?.value || 0)));
            const disc = Math.min(50000, Math.max(0, Number(discInput?.value || 0)));
            const total = Math.min(550000, Math.max(0, (base + extra) - disc));

            const display = document.getElementById('walkinTotalDisplay');
            if (display) display.textContent = `₱${total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

            // Sync amount paid based on status
            const payStatus = document.getElementById('walkinPaymentStatus')?.value || 'Paid';
            const amountInput = document.getElementById('walkinAmountPaid');
            if (amountInput) {
                if (payStatus === 'Paid') {
                    amountInput.value = total;
                } else if (payStatus === 'Unpaid') {
                    amountInput.value = 0;
                }
            }
            this.recalculateBalance();
        },

        onPaymentStatusChange() {
            const payStatus = document.getElementById('walkinPaymentStatus')?.value || 'Paid';
            const base = Math.min(500000, Math.max(0, Number(document.getElementById('walkinBasePrice')?.value || 0)));
            const extra = Math.min(50000, Math.max(0, Number(document.getElementById('walkinExtraFee')?.value || 0)));
            const disc = Math.min(50000, Math.max(0, Number(document.getElementById('walkinDiscount')?.value || 0)));
            const total = Math.min(550000, Math.max(0, (base + extra) - disc));

            const amountInput = document.getElementById('walkinAmountPaid');
            if (amountInput) {
                if (payStatus === 'Paid') {
                    amountInput.value = total;
                } else if (payStatus === 'Unpaid') {
                    amountInput.value = 0;
                } else if (payStatus === 'Partial' && Number(amountInput.value) === 0) {
                    amountInput.value = Math.round(total / 2);
                }
            }
            this.recalculateBalance();
        },

        recalculateBalance() {
            const base = Math.min(500000, Math.max(0, Number(document.getElementById('walkinBasePrice')?.value || 0)));
            const extra = Math.min(50000, Math.max(0, Number(document.getElementById('walkinExtraFee')?.value || 0)));
            const disc = Math.min(50000, Math.max(0, Number(document.getElementById('walkinDiscount')?.value || 0)));
            const total = Math.min(550000, Math.max(0, (base + extra) - disc));

            const amountInput = document.getElementById('walkinAmountPaid');
            if (amountInput) {
                if (amountInput.value.length > 7) amountInput.value = amountInput.value.slice(0, 7);
                if (Number(amountInput.value) > 500000) amountInput.value = 500000;
                if (Number(amountInput.value) < 0) amountInput.value = 0;
            }

            const paid = Math.min(500000, Math.max(0, Number(amountInput?.value || 0)));
            const balance = Math.max(0, total - paid);

            const note = document.getElementById('walkinBalanceNote');
            if (note) {
                if (balance <= 0.01) {
                    note.textContent = 'Paid in Full (Balance: ₱0.00)';
                    note.style.color = '#10b981';
                } else {
                    note.textContent = `Balance to Collect: ₱${balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                    note.style.color = '#f59e0b';
                }
            }
        },

        async submit(e) {
            if (e && e.preventDefault) e.preventDefault();

            const submitBtn = document.getElementById('walkinSubmitBtn');
            const originalBtnHtml = submitBtn ? submitBtn.innerHTML : '';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }

            try {
                const vehicleId = document.getElementById('walkinVehicleSelect')?.value;
                if (!vehicleId) {
                    alert('Please select a vehicle unit.');
                    if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = originalBtnHtml; }
                    return;
                }

                const startDate = document.getElementById('walkinStartDate')?.value;
                const startTime = document.getElementById('walkinStartTime')?.value || '08:00';
                const endDate = document.getElementById('walkinEndDate')?.value;
                const endTime = document.getElementById('walkinEndTime')?.value || '08:00';

                if (!startDate || !endDate) {
                    alert('Please select both start date and end date.');
                    if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = originalBtnHtml; }
                    return;
                }

                const isExisting = (this.mode === 'registered');
                const userId = isExisting ? (document.getElementById('walkinCustUserId')?.value || null) : null;

                if (isExisting && !userId) {
                    alert('Please search and select a registered customer profile.');
                    if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = originalBtnHtml; }
                    return;
                }

                let custName = '';
                let custPhone = '';
                let custAddress = '';
                let emergName = '';
                let emergPhone = '';
                let emergRel = '';

                if (isExisting && this.selectedCustomer) {
                    custName = this.selectedCustomer.full_name || 'Customer';
                    custPhone = this.selectedCustomer.phone || '';
                } else {
                    custName = (document.getElementById('walkinCustName')?.value || '').trim();
                    custPhone = (document.getElementById('walkinCustPhone')?.value || '').trim();
                    custAddress = (document.getElementById('walkinCustAddress')?.value || '').trim();
                    emergName = (document.getElementById('walkinEmergName')?.value || '').trim();
                    emergPhone = (document.getElementById('walkinEmergPhone')?.value || '').trim();
                    emergRel = (document.getElementById('walkinEmergRel')?.value || '').trim();

                    if (!custName || !custPhone) {
                        alert('Customer Full Name and Phone Number are required.');
                        if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = originalBtnHtml; }
                        return;
                    }
                }

                const rawBasePrice = Number(document.getElementById('walkinBasePrice')?.value || 0);
                const rawExtraFee = Number(document.getElementById('walkinExtraFee')?.value || 0);
                const rawDiscount = Number(document.getElementById('walkinDiscount')?.value || 0);
                const rawAmountPaid = Number(document.getElementById('walkinAmountPaid')?.value || 0);

                if (isNaN(rawBasePrice) || rawBasePrice < 0 || rawBasePrice > 500000) {
                    alert('Base price must be between ₱0 and ₱500,000.');
                    if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = originalBtnHtml; }
                    return;
                }
                if (isNaN(rawExtraFee) || rawExtraFee < 0 || rawExtraFee > 50000) {
                    alert('Driver/Delivery fee must be between ₱0 and ₱50,000.');
                    if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = originalBtnHtml; }
                    return;
                }
                if (isNaN(rawDiscount) || rawDiscount < 0 || rawDiscount > 50000) {
                    alert('Discount must be between ₱0 and ₱50,000.');
                    if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = originalBtnHtml; }
                    return;
                }
                if (isNaN(rawAmountPaid) || rawAmountPaid < 0 || rawAmountPaid > 500000) {
                    alert('Amount collected must be between ₱0 and ₱500,000.');
                    if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = originalBtnHtml; }
                    return;
                }

                const basePrice = Math.min(500000, Math.max(0, rawBasePrice));
                const extraFee = Math.min(50000, Math.max(0, rawExtraFee));
                const discount = Math.min(50000, Math.max(0, rawDiscount));
                const totalPrice = Math.min(550000, Math.max(0, (basePrice + extraFee) - discount));
                const amountPaid = Math.min(500000, Math.max(0, rawAmountPaid));
                const balanceAmount = Math.max(0, totalPrice - amountPaid);

                const paymentMethod = document.getElementById('walkinPaymentMethod')?.value || 'Cash';
                const paymentStatus = document.getElementById('walkinPaymentStatus')?.value || 'Paid';
                const bookingStatus = document.getElementById('walkinBookingStatus')?.value || 'Confirmed';
                const rentalType = document.getElementById('walkinRentalType')?.value || 'Self Drive';
                const pickupLocation = document.getElementById('walkinPickupLocation')?.value || 'Main Office / Garage';

                // Auth credentials
                let adminUser = null;
                try {
                    adminUser = JSON.parse(localStorage.getItem('admin_user') || localStorage.getItem('autoride_user') || '{}');
                } catch (pe) {
                    adminUser = {};
                }
                const adminId = adminUser.id || 1;
                const token = localStorage.getItem('admin_token') || localStorage.getItem('token');

                const payload = {
                    vehicle_id: Number(vehicleId),
                    start_date: startDate,
                    start_time: startTime,
                    end_date: endDate,
                    end_time: endTime,
                    is_existing_account: isExisting,
                    user_id: userId ? Number(userId) : null,
                    customer_name: custName,
                    customer_phone: custPhone,
                    customer_address: custAddress,
                    emergency_name: emergName,
                    emergency_phone: emergPhone,
                    emergency_rel: emergRel,
                    base_price: basePrice,
                    driver_fee: (rentalType === 'With Driver' ? extraFee : 0),
                    delivery_fee: (rentalType !== 'With Driver' ? extraFee : 0),
                    discount_amount: discount,
                    total_price: totalPrice,
                    amount_paid: amountPaid,
                    balance_amount: balanceAmount,
                    payment_method: paymentMethod,
                    payment_status: paymentStatus,
                    status: bookingStatus,
                    rental_type: rentalType,
                    pickup_location: pickupLocation,
                    rental_purpose: 'Walk-in Counter Rental',
                    admin_id: adminId
                };

                const headers = {
                    'Content-Type': 'application/json',
                    'X-Admin-Id': String(adminId)
                };
                if (token) {
                    headers['Authorization'] = `Bearer ${token}`;
                }

                const res = await fetch(`${API_BASE}/api/admin/bookings/walkin`, {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify(payload)
                });

                const result = await res.json();
                if (!res.ok) {
                    throw new Error(result.error || 'Failed to create walk-in booking');
                }

                // Success!
                this.closeModal();

                if (typeof showNotification === 'function') {
                    showNotification('Walk-in booking created successfully!', 'success');
                } else {
                    alert('Walk-in booking created successfully!');
                }

                // Refresh views
                if (window.FleetCalendar && typeof window.FleetCalendar.refresh === 'function') {
                    window.FleetCalendar.refresh();
                }
                if (window.Bookings && typeof window.Bookings.refresh === 'function') {
                    window.Bookings.refresh();
                }
                if (typeof loadDashboardData === 'function') {
                    loadDashboardData();
                }

            } catch (err) {
                console.error('Error submitting walk-in booking:', err);
                alert(`Error: ${err.message}`);
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnHtml;
                }
            }
        }
    };
    window.WalkinBooking = WalkinBooking;



    window.Drivers = Drivers;



    window.Verifications = Verifications;



    window.Instructions = Instructions;



    window.Staff = Staff;



    window.GPS = GPS;



    window.Activity = Activity;



    window.Reports = Reports;



    window.Settings = Settings;



    window.switchTab = switchTab;



    window.toggleDrawer = toggleDrawer;



    window.showNotification = showNotification;



    window.refreshDashboard = refreshDashboard;



    window.openChangePasswordModal = openChangePasswordModal;



    window.submitChangePassword = submitChangePassword;



    window.navTo = navTo;







    // ??? USER MANAGEMENT MODULE ???????????????????????????????????????????



    /**
     * Data Privacy Act of 2012 (RA 10173) Dynamic Redaction
     * Automatically masks personal email addresses to protect customer PII.
     */
    function maskEmail(email) {
        if (!email || typeof email !== 'string' || !email.includes('@')) return email || '';
        if (email.includes('*')) return email;
        const parts = email.split('@');
        const u = parts[0], d = parts[1];
        if (u.length <= 2) return u[0] + '*@' + d;
        if (u.length <= 5) return u[0] + '*'.repeat(u.length - 2) + u[u.length - 1] + '@' + d;
        return u.substring(0, 2) + '*'.repeat(Math.max(3, u.length - 4)) + u.substring(u.length - 2) + '@' + d;
    }

    const UserMgmt = {



        _all: [],



        _filter: 'all',







        async refresh() {



            document.getElementById('umList').innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:1.5rem;"></i></div>';
            showSkeleton('umList', 'list');



            try {



                const res = await apiFetch('admin/users/list');



                const data = await res.json();



                if (!res.ok) throw new Error(data.error || 'Failed to load users');



                this._all = (data || []).filter(u => {
                    const r = (u.role || '').toLowerCase();
                    return !['admin', 'super_admin', 'superadmin', 'staff'].includes(r);
                });



                this._updateStats();



                this.applyFilters();



            } catch (e) {



                document.getElementById('umList').innerHTML = `<div style="text-align:center;padding:40px;color:var(--danger);">${e.message}</div>`;



            }



        },







        _updateStats() {



            const total = this._all.length;



            const verified = this._all.filter(u => u.is_verified === 2).length;



            const frozen = this._all.filter(u => u.is_frozen).length;



            document.getElementById('umTotalCount').textContent = total;



            document.getElementById('umVerifiedCount').textContent = verified;



            document.getElementById('umFrozenCount').textContent = frozen;



        },







        _sortBy: 'date_desc',

        setSort(key) {
            this._sortBy = key;
            const el = document.getElementById('umSort');
            if (el && el.value !== key) el.value = key;
            this.applyFilters();
        },

        sortUsers(list, sortKey) {
            const copy = [...list];
            switch (sortKey) {
                case 'date_asc':
                    return copy.sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));
                case 'name_asc':
                    return copy.sort((a, b) => (a.full_name || '').localeCompare(b.full_name || ''));
                case 'name_desc':
                    return copy.sort((a, b) => (b.full_name || '').localeCompare(a.full_name || ''));
                case 'bookings_desc':
                    return copy.sort((a, b) => (Number(b.total_bookings) || 0) - (Number(a.total_bookings) || 0));
                case 'bookings_asc':
                    return copy.sort((a, b) => (Number(a.total_bookings) || 0) - (Number(b.total_bookings) || 0));
                case 'loyalty_desc':
                    return copy.sort((a, b) => (Number(b.loyalty_points) || 0) - (Number(a.loyalty_points) || 0));
                case 'verified_first':
                    return copy.sort((a, b) => (b.is_verified === 2 ? 1 : 0) - (a.is_verified === 2 ? 1 : 0));
                case 'date_desc':
                default:
                    return copy.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
            }
        },
        setFilter(f, btn) {



            this._filter = f;



            document.querySelectorAll('.um-filter-btn').forEach(b => {
                b.classList.remove('active');
                b.style.background = '#ffffff';
                b.style.color = '#1e293b';
                b.style.borderColor = '#cbd5e1';
            });

            btn.classList.add('active');
            btn.style.background = '#00B14F';
            btn.style.color = '#ffffff';
            btn.style.borderColor = '#00B14F';

            this.applyFilters();



        },







        applyFilters() {



            const q = (document.getElementById('umSearch').value || '').toLowerCase();



            let list = this._all;



            if (this._filter === 'verified') list = list.filter(u => u.is_verified === 2);



            else if (this._filter === 'unverified') list = list.filter(u => u.is_verified !== 2);



            else if (this._filter === 'frozen') list = list.filter(u => u.is_frozen);
            else if (this._filter === 'violations') list = list.filter(u => (u.violation_strikes > 0 || u.booking_suspension_until || u.violation_permanently_restricted));



            if (q) list = list.filter(u =>



                (u.full_name || '').toLowerCase().includes(q) ||



                (u.email || '').toLowerCase().includes(q) ||



                (u.phone || '').toLowerCase().includes(q)



            );



            // Apply user management sort
            list = this.sortUsers(list, this._sortBy || 'date_desc');

            this._render(list);



        },







        _render(list) {



            const el = document.getElementById('umList');



            if (!list.length) {



                el.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">No renters found</div>';



                return;



            }



            el.innerHTML = list.map(u => {



                const verifiedBadge = u.is_verified === 2



                    ? `<span style="background:rgba(0,177,79,0.15);color:var(--success);padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;">VERIFIED</span>`



                    : u.is_verified === 1



                    ? `<span style="background:rgba(245,158,11,0.15);color:var(--amber);padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;">PENDING</span>`



                    : `<span style="background:rgba(148,163,184,0.1);color:var(--text-muted);padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;">UNVERIFIED</span>`;



                const frozenBadge = u.is_frozen



                    ? `<span style="background:rgba(239,68,68,0.15);color:var(--danger);padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;margin-left:4px;">FROZEN</span>`



                    : '';

                const violationBadge = u.violation_permanently_restricted
                    ? `<span style="background:rgba(220,38,38,0.2);color:#dc2626;padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;margin-left:4px;border:1px solid rgba(220,38,38,0.4);"><i class="fas fa-ban" style="font-size:0.55rem;margin-right:2px;"></i>BANNED</span>`
                    : (u.booking_suspension_until && new Date(u.booking_suspension_until) > new Date())
                    ? `<span style="background:rgba(245,158,11,0.15);color:#f59e0b;padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;margin-left:4px;border:1px solid rgba(245,158,11,0.3);"><i class="fas fa-clock" style="font-size:0.55rem;margin-right:2px;"></i>SUSPENDED</span>`
                    : (u.violation_strikes > 0)
                    ? `<span style="background:rgba(251,146,60,0.15);color:#fb923c;padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;margin-left:4px;border:1px solid rgba(251,146,60,0.3);"><i class="fas fa-exclamation-triangle" style="font-size:0.55rem;margin-right:2px;"></i>${u.violation_strikes} STRIKE${(u.violation_strikes || 0) !== 1 ? 'S' : ''}</span>`
                    : '';

                const regularBadge = u.is_regular_customer
                    ? `<span style="background:rgba(234,179,8,0.18);color:#eab308;padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;margin-left:4px;border:1px solid rgba(234,179,8,0.4);"><i class="fas fa-crown" style="font-size:0.55rem;margin-right:2px;"></i>REGULAR VIP</span>`
                    : '';

                const avatar = u.full_name ? u.full_name.charAt(0).toUpperCase() : '?';



                let joined = 'N/A';



                if (u.created_at) {



                    try {



                        const dStr = u.created_at.replace(' ', 'T');



                        const parsedDate = new Date(dStr);



                        if (!isNaN(parsedDate.getTime())) {



                            joined = parsedDate.toLocaleDateString('en-PH', {month:'short', day:'numeric', year:'numeric'});



                        } else {



                            joined = String(u.created_at).split(' ')[0] || 'N/A';



                        }



                    } catch(e) { joined = 'N/A'; }



                }



                return `
                <div onclick="UserMgmt.openModal(${u.id})" style="background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:14px 12px;margin-bottom:10px;cursor:pointer;display:flex;align-items:center;gap:12px;">
                    ${u.profile_picture ? `
                        <img src="${u.profile_picture}" style="width:44px;height:44px;border-radius:50%;object-fit:cover;border:2px solid #00B14F;flex-shrink:0;cursor:pointer;" onclick="event.stopPropagation();viewLicenseImage('${u.profile_picture}')" title="Click to enlarge">` : `
                        <div style="width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--primary),#005339);display:flex;align-items:center;justify-content:center;font-weight:900;font-size:1rem;flex-shrink:0;color:#fff;">${avatar}</div>`}



                    <div style="flex:1;min-width:0;">



                        <div style="font-weight:800;font-size:0.88rem;color:#0f172a;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${u.full_name || 'No Name'}</div>



                        <div style="font-size:0.72rem;color:#475569;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:flex;align-items:center;gap:5px;">
                            <i class="fas fa-user-shield" style="color:#00B14F;font-size:0.65rem;" title="Data Privacy Act (RA 10173) Protected"></i>
                            <span>${maskEmail(u.email)}</span>
                        </div>



                        <div style="margin-top:5px;display:flex;align-items:center;flex-wrap:wrap;gap:4px;">${verifiedBadge}${frozenBadge}${violationBadge}${regularBadge}</div>



                    </div>



                    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;flex-shrink:0;">



                        <div style="font-size:0.65rem;color:#64748b;font-weight:600;text-align:right;">${joined}</div>

                        <div style="font-size:0.68rem;color:var(--amber);font-weight:700;"><i class="fas fa-star" style="font-size:0.58rem;"></i> ${u.loyalty_points || 0} pts</div>
                        <div style="font-size:0.68rem;color:#00B14F;font-weight:800;"><i class="fas fa-wallet" style="font-size:0.58rem;"></i> ₱${(u.total_spent || 0).toLocaleString()}</div>

                        <button onclick="event.stopPropagation(); UserMgmt.openPushModal(${u.id}, '${(u.full_name || 'No Name').replace(/'/g, "\\'")}')" style="background:rgba(0,177,79,0.1);border:1px solid rgba(0,177,79,0.25);color:#00B14F;width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;cursor:pointer;" title="Send Notification">



                            <i class="fas fa-bell" style="font-size:0.8rem;"></i>



                        </button>



                    </div>



                </div>`;



            }).join('');



        },



        _pushTarget: null,



        openBroadcastModal() {



            this._pushTarget = null;



            document.getElementById('pushNotifRecipient').textContent = '📢 ALL REGISTERED RENTERS';



            document.getElementById('pushNotifTitle').value = '';



            document.getElementById('pushNotifBody').value = '';



            document.getElementById('pushNotifModal').style.display = 'block';



        },



        openPushModal(userId, userName) {



            this._pushTarget = userId;



            document.getElementById('pushNotifRecipient').textContent = `🔔 ${userName} (Renter ID: ${userId})`;



            document.getElementById('pushNotifTitle').value = '';



            document.getElementById('pushNotifBody').value = '';



            document.getElementById('pushNotifModal').style.display = 'block';



        },



        closePushModal() {



            document.getElementById('pushNotifModal').style.display = 'none';



        },



        async submitPushNotif() {



            const title = document.getElementById('pushNotifTitle').value.trim();



            const body = document.getElementById('pushNotifBody').value.trim();



            if (!title || !body) {



                alert('Please fill in both Title and Message Body');



                return;



            }



            



            const payload = {



                title: title,



                body: body



            };



            



            if (this._pushTarget === null) {



                payload.broadcast = true;



            } else {



                payload.user_id = this._pushTarget;



            }



            



            const btn = document.querySelector('#pushNotifModal button[onclick="UserMgmt.submitPushNotif()"]');



            const originalContent = btn.innerHTML;



            btn.disabled = true;



            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';



            



            try {



                const res = await apiFetch('admin/send-custom-push', {



                    method: 'POST',



                    headers: { 'Content-Type': 'application/json' },



                    body: JSON.stringify(payload)



                });



                const data = await res.json();



                if (!res.ok) throw new Error(data.error || 'Failed to send notification');



                



                showNotification(data.message || 'Notification sent successfully!', 'success');



                this.closePushModal();



            } catch (e) {



                alert('Error: ' + e.message);



            } finally {



                btn.disabled = false;



                btn.innerHTML = originalContent;



            }



        },







        closeModal() {
            const m = document.getElementById('umModal');
            if (m) m.style.display = 'none';
        },

        async openModal(userId) {



            document.getElementById('umModal').style.display = 'block';



            document.getElementById('umModalContent').innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:1.5rem;"></i></div>';



            try {



                const [res, licRes] = await Promise.all([



                    apiFetch(`admin/users/${userId}`),



                    fetch(`${API_BASE}/api/admin/users/${userId}/license-details`)



                ]);



                const u = await res.json();



                if (!res.ok) throw new Error(u.error || 'Failed to load user');



                



                let lData = null;



                if (licRes.ok) {



                    lData = await licRes.json();



                }



                this._renderModal(u, lData);



            } catch (e) {



                document.getElementById('umModalContent').innerHTML = `<div style="color:var(--danger);text-align:center;padding:20px;">${e.message}</div>`;



            }



        },







        _renderModal(u, lData) {



            const verifiedLabel = u.is_verified === 2 ? 'Verified' : u.is_verified === 1 ? 'Pending' : 'Unverified';



            const verifiedColor = u.is_verified === 2 ? 'var(--success)' : u.is_verified === 1 ? 'var(--amber)' : 'var(--text-muted)';



            const frozenLabel = u.is_frozen ? 'Frozen' : 'Active';



            const frozenColor = u.is_frozen ? 'var(--danger)' : 'var(--success)';



            let joined = 'N/A';
            if (u.created_at) {
                try {
                    const dStr = u.created_at.replace(' ', 'T');
                    const parsedDate = new Date(dStr);
                    if (!isNaN(parsedDate.getTime())) {
                        joined = parsedDate.toLocaleDateString('en-PH', {month:'long', day:'numeric', year:'numeric'});
                    } else {
                        joined = String(u.created_at).split(' ')[0] || 'N/A';
                    }
                } catch(e) { joined = 'N/A'; }
            }
            const avatar = u.full_name ? u.full_name.charAt(0).toUpperCase() : '?';





            document.getElementById('umModalContent').innerHTML = `



            <!-- Avatar & Name -->



            <div style="text-align:center;margin-bottom:20px;">
                ${u.profile_picture ? `
                    <img src="${u.profile_picture}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;border:3px solid #00B14F;margin:0 auto 12px;display:block;cursor:pointer;box-shadow:0 4px 14px rgba(0,177,79,0.35);" onclick="viewLicenseImage('${u.profile_picture}')" title="Click to enlarge profile picture">` : `
                    <div style="width:70px;height:70px;border-radius:50%;background:linear-gradient(135deg,var(--primary),#005339);display:flex;align-items:center;justify-content:center;font-weight:900;font-size:1.8rem;margin:0 auto 12px;color:#fff;">${avatar}</div>`}
                <div style="font-size:1.1rem;font-weight:900;">${u.full_name || 'No Name'}</div>



                <div style="font-size:0.8rem;color:var(--text-muted);display:flex;align-items:center;justify-content:center;gap:6px;margin-top:4px;">
                    <span style="display:inline-flex;align-items:center;gap:6px;background:rgba(0,177,79,0.1);color:#00B14F;padding:4px 10px;border-radius:12px;font-size:0.75rem;font-weight:700;border:1px solid rgba(0,177,79,0.2);"><i class="fas fa-user-shield"></i> ${maskEmail(u.email)} <span style="font-size:0.65rem;color:var(--text-muted);font-weight:600;">(RA 10173 Protected)</span></span>
                </div>



                <div style="display:flex;justify-content:center;gap:8px;margin-top:8px;">
                    <span style="color:${verifiedColor};font-size:0.72rem;font-weight:800;background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.25);padding:4px 10px;border-radius:20px;">${verifiedLabel}</span>
                    <span style="color:${frozenColor};font-size:0.72rem;font-weight:800;background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.25);padding:4px 10px;border-radius:20px;">${frozenLabel}</span>
                    ${u.is_regular_customer ? `<span style="color:#ca8a04;font-size:0.72rem;font-weight:800;background:rgba(234,179,8,0.15);border:1px solid rgba(234,179,8,0.35);padding:4px 10px;border-radius:20px;"><i class="fas fa-crown" style="margin-right:4px;"></i>VIP Regular</span>` : ''}
                </div>
            </div>

            <!-- Stats -->
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:20px;">
                <div style="background:var(--surface-card);border:1px solid var(--border);border-radius:14px;padding:14px 10px;text-align:center;">
                    <div style="font-size:1.3rem;font-weight:900;color:var(--primary);">${u.total_bookings || 0}</div>
                    <div style="font-size:0.65rem;color:var(--text-muted);font-weight:800;text-transform:uppercase;margin-top:3px;">Bookings</div>
                </div>
                <div style="background:var(--surface-card);border:1px solid var(--border);border-radius:14px;padding:14px 10px;text-align:center;">
                    <div style="font-size:1.3rem;font-weight:900;color:var(--success);">${u.completed_bookings || 0}</div>
                    <div style="font-size:0.65rem;color:var(--text-muted);font-weight:800;text-transform:uppercase;margin-top:3px;">Completed</div>
                </div>
                <div style="background:var(--surface-card);border:1px solid var(--border);border-radius:14px;padding:14px 10px;text-align:center;">
                    <div style="font-size:1.15rem;font-weight:900;color:var(--amber);">₱${(u.total_spent||0).toLocaleString()}</div>
                    <div style="font-size:0.65rem;color:var(--text-muted);font-weight:800;text-transform:uppercase;margin-top:3px;">Spent</div>
                </div>
            </div>







            <!-- License Details Section -->
            <div style="background: var(--surface-card); padding: 18px; border-radius: 16px; border: 1px solid var(--border); margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
                <h3 style="font-size: 0.95rem; color: #00B14F; font-weight: 800; margin: 0 0 14px 0; display:flex; align-items:center; gap:8px;">
                    <i class="fas fa-id-card"></i> Driver's License Details
                </h3>
                ${lData && lData.license_number ? `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 0.85rem;">
                        <div><span style="color:var(--text-muted); font-size:0.75rem; font-weight:600; display:block; margin-bottom:2px;">License #:</span> <span style="color:var(--text-main); font-weight:700;">${lData.license_number}</span></div>
                        <div><span style="color:var(--text-muted); font-size:0.75rem; font-weight:600; display:block; margin-bottom:2px;">Expiry:</span> <span style="color:var(--text-main); font-weight:700;">${lData.expiry_date || '-'}</span></div>
                        <div><span style="color:var(--text-muted); font-size:0.75rem; font-weight:600; display:block; margin-bottom:2px;">Class:</span> <span style="color:var(--text-main); font-weight:700;">${lData.license_class || '-'}</span></div>
                        <div><span style="color:var(--text-muted); font-size:0.75rem; font-weight:600; display:block; margin-bottom:2px;">Date of Birth:</span> <span style="color:var(--text-main); font-weight:700;">${lData.date_of_birth || '-'}</span></div>
                    </div>
                    <div style="margin-top: 12px; font-size: 0.85rem; border-top: 1px solid var(--border); padding-top: 12px; display: flex; flex-direction: column; gap: 10px;">
                        <div><span style="color:var(--text-muted); font-size:0.75rem; font-weight:600; display:block; margin-bottom:2px;">Full Name:</span> <span style="color:var(--text-main); font-weight:700;">${lData.full_name || '-'}</span></div>
                        <div><span style="color:var(--text-muted); font-size:0.75rem; font-weight:600; display:block; margin-bottom:2px;">Complete Residential Address:</span> <span style="color:var(--text-main); font-weight:700; line-height:1.45; word-break:break-word;">${lData.address || lData.issuing_country_state || '-'}</span></div>
                    </div>
                    <div style="margin-top: 12px; font-size: 0.85rem; padding-top: 12px; border-top: 1px solid var(--border);">
                        <p style="color:var(--text-main); font-weight:800; font-size:0.82rem; margin:0 0 8px 0; display:flex; align-items:center; gap:6px;">
                            <i class="fas fa-phone-alt" style="color:#3b82f6;"></i> Emergency Contact
                        </p>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px;">
                            <div><span style="color:var(--text-muted); font-size:0.72rem; display:block;">Name:</span> <span style="color:var(--text-main); font-weight:700; font-size:0.82rem;">${lData.emergency_contact_name || '-'}</span></div>
                            <div><span style="color:var(--text-muted); font-size:0.72rem; display:block;">Phone:</span> <span style="color:var(--text-main); font-weight:700; font-size:0.82rem;">${lData.emergency_contact_phone || '-'}</span></div>
                            <div><span style="color:var(--text-muted); font-size:0.72rem; display:block;">Rel:</span> <span style="color:var(--text-main); font-weight:700; font-size:0.82rem;">${lData.emergency_contact_relationship || '-'}</span></div>
                        </div>
                    </div>
                    <div style="display:flex; gap:10px; margin-top: 14px;">
                        ${lData.license_front_url ? `<button onclick="viewLicenseImage('${lData.license_front_url}')" class="btn-outline" style="flex:1; font-size:0.78rem; padding:8px 12px; border-radius:8px; font-weight:700; display:flex; align-items:center; justify-content:center; gap:6px;"><i class="fas fa-image"></i> Front Image</button>` : ''}
                        ${lData.license_back_url ? `<button onclick="viewLicenseImage('${lData.license_back_url}')" class="btn-outline" style="flex:1; font-size:0.78rem; padding:8px 12px; border-radius:8px; font-weight:700; display:flex; align-items:center; justify-content:center; gap:6px;"><i class="fas fa-image"></i> Back Image</button>` : ''}
                    </div>
                ` : `<p style="font-size: 0.85rem; color: var(--text-muted); margin:0;">No license details provided by user.</p>`}
            </div>







            <!-- Info -->
            <div style="background:var(--surface-card);border:1px solid var(--border);border-radius:14px;padding:14px 16px;margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:0.82rem;"><span style="color:var(--text-muted);">Phone</span><span style="font-weight:700;color:var(--text-main);">${u.phone || 'N/A'}</span></div>
                <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:0.82rem;"><span style="color:var(--text-muted);">Loyalty Points</span><span style="color:var(--amber);font-weight:800;">${u.loyalty_points || 0} pts</span></div>
                <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:0.82rem;"><span style="color:var(--text-muted);">Auth Provider</span><span style="font-weight:700;color:var(--text-main);">${u.auth_provider || 'Email'}</span></div>
                <div style="display:flex;justify-content:space-between;padding:8px 0;font-size:0.82rem;"><span style="color:var(--text-muted);">Joined</span><span style="font-weight:700;color:var(--text-main);">${joined}</span></div>
            </div>

            <!-- Edit Form -->
            <div style="background:var(--surface-card);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:16px;">
                <div style="font-size:0.72rem;color:var(--text-muted);font-weight:800;text-transform:uppercase;margin-bottom:12px;">Edit Info</div>
                <input id="umEditName" type="text" maxlength="50" value="${u.full_name || ''}" placeholder="Full Name" style="width:100%;padding:11px 14px;background:var(--surface-container, var(--surface-solid));border:1.5px solid var(--border);border-radius:10px;color:var(--text-main);font-size:0.88rem;margin-bottom:10px;box-sizing:border-box;outline:none;">
                <input id="umEditPhone" type="text" maxlength="11" value="${u.phone || ''}" placeholder="Phone Number" style="width:100%;padding:11px 14px;background:var(--surface-container, var(--surface-solid));border:1.5px solid var(--border);border-radius:10px;color:var(--text-main);font-size:0.88rem;margin-bottom:10px;box-sizing:border-box;outline:none;">
                <button onclick="UserMgmt.saveEdit(${u.id})" class="btn-primary" style="width:100%;padding:11px;border-radius:10px;font-weight:800;font-size:0.85rem;">Save Changes</button>
            </div>

            <!-- Loyalty Points -->
            <div style="background:var(--surface-card);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:16px;">
                <div style="font-size:0.72rem;color:var(--text-muted);font-weight:800;text-transform:uppercase;margin-bottom:12px;"><i class="fas fa-star" style="color:var(--amber);margin-right:6px;"></i>Loyalty Points</div>
                <input id="umLoyaltyInput" type="number" min="0" max="100000" value="${u.loyalty_points || 0}" placeholder="Points" style="width:100%;padding:11px 14px;background:var(--surface-container, var(--surface-solid));border:1.5px solid var(--border);border-radius:10px;color:var(--text-main);font-size:0.9rem;margin-bottom:10px;box-sizing:border-box;outline:none;">
                <button onclick="UserMgmt.setLoyalty(${u.id})" style="width:100%;padding:11px;background:rgba(245,158,11,0.12);border:1.5px solid var(--amber);border-radius:10px;color:var(--amber);font-weight:800;font-size:0.85rem;cursor:pointer;">Update Points</button>
            </div>

            <!-- Reset Password -->
            <div style="background:var(--surface-card);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:16px;">
                <div style="font-size:0.72rem;color:var(--text-muted);font-weight:800;text-transform:uppercase;margin-bottom:12px;"><i class="fas fa-key" style="color:var(--primary);margin-right:6px;"></i>Reset Password</div>
                <input id="umNewPass" type="password" maxlength="64" placeholder="New password (min 8 chars)" style="width:100%;padding:11px 14px;background:var(--surface-container, var(--surface-solid));border:1.5px solid var(--border);border-radius:10px;color:var(--text-main);font-size:0.9rem;margin-bottom:10px;box-sizing:border-box;outline:none;">
                <button onclick="UserMgmt.resetPassword(${u.id})" class="btn-primary" style="width:100%;padding:11px;border-radius:10px;font-weight:800;font-size:0.85rem;">Reset Password</button>
            </div>

            <!-- Regular Customer / VIP Privileges -->
            <div style="background:var(--surface-card);border-radius:14px;padding:16px;margin-bottom:16px;border:1.5px solid ${u.is_regular_customer ? 'rgba(234,179,8,0.45)' : 'var(--border)'};box-shadow:${u.is_regular_customer ? '0 4px 14px rgba(234,179,8,0.08)' : 'none'};">
                <div style="font-size:0.72rem;color:var(--text-muted);font-weight:800;text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;">
                    <span style="color:var(--text-main);"><i class="fas fa-crown" style="margin-right:6px;color:#eab308;"></i>Regular Customer (VIP)</span>
                    <span style="padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:800;background:${u.is_regular_customer ? 'rgba(234,179,8,0.18)' : 'rgba(0,0,0,0.05)'};color:${u.is_regular_customer ? '#ca8a04' : 'var(--text-muted)'};border:1px solid ${u.is_regular_customer ? 'rgba(234,179,8,0.4)' : 'var(--border)'};">
                        ${u.is_regular_customer ? '★ VIP REGULAR' : 'STANDARD'}
                    </span>
                </div>
                <div style="font-size:0.8rem;color:var(--text-muted);line-height:1.45;margin-bottom:12px;">
                    ${u.is_regular_customer ? 
                        `<span style="color:#ca8a04;font-weight:800;"><i class="fas fa-check-circle" style="color:#eab308;margin-right:4px;"></i>Exempt from Downpayment:</span> This customer can book with ₱0 downpayment (Pay on Pickup). Qualified via ${u.regular_customer_manual ? 'Super Admin manual override' : (u.completed_bookings || 0) + ' completed bookings'}.` 
                        : `Customer currently requires the standard downpayment upon booking. Completed bookings: <strong style="color:var(--text-main);">${u.completed_bookings || 0}</strong>.`}
                </div>
                <button onclick="UserMgmt.toggleRegularCustomer(${u.id}, ${!!u.is_regular_customer})" style="width:100%;padding:11px;background:${u.is_regular_customer ? 'rgba(239,68,68,0.1)' : 'rgba(234,179,8,0.15)'};border:1.5px solid ${u.is_regular_customer ? 'rgba(239,68,68,0.3)' : 'rgba(234,179,8,0.4)'};border-radius:10px;color:${u.is_regular_customer ? '#dc2626' : '#ca8a04'};font-weight:800;font-size:0.82rem;cursor:pointer;">
                    <i class="fas fa-${u.is_regular_customer ? 'user-minus' : 'crown'}" style="margin-right:6px;"></i> ${u.is_regular_customer ? 'Revoke Regular Customer Status' : 'Mark as Regular Customer (VIP)'}
                </button>
            </div>

            <!-- Violation / Strike Record & Account Standing -->
            <div id="umViolationSection_${u.id}" style="background:var(--surface-card);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:16px;">
                <div style="font-size:0.7rem;color:var(--text-muted);font-weight:800;text-transform:uppercase;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;">
                    <span><i class="fas fa-user-shield" style="margin-right:6px;color:#f59e0b;"></i>Account Standing / Violations</span>
                    <span id="umStrikesBadge_${u.id}" style="padding:2px 8px;border-radius:8px;font-weight:800;font-size:0.75rem;background:${u.violation_permanently_restricted ? 'rgba(220,38,38,0.2)' : (u.violation_strikes > 0 ? 'rgba(245,158,11,0.2)' : 'rgba(0,177,79,0.15)')};color:${u.violation_permanently_restricted ? '#dc2626' : (u.violation_strikes > 0 ? '#fb923c' : 'var(--success)')};">
                        ${u.violation_permanently_restricted ? 'PERMANENTLY RESTRICTED' : ((u.violation_strikes || 0) + ' strike' + ((u.violation_strikes || 0) !== 1 ? 's' : ''))}
                    </span>
                </div>

                ${u.violation_permanently_restricted ? `
                <div style="background:rgba(220,38,38,0.15);border:1px solid rgba(220,38,38,0.3);border-radius:10px;padding:10px;margin-bottom:10px;font-size:0.8rem;color:#dc2626;font-weight:700;text-align:center;">
                    <i class="fas fa-ban"></i> Account is PERMANENTLY RESTRICTED from booking
                </div>` : u.booking_suspension_until && new Date(u.booking_suspension_until) > new Date() ? `
                <div style="background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.3);border-radius:10px;padding:10px;margin-bottom:10px;font-size:0.8rem;color:#f59e0b;">
                    <i class="fas fa-clock"></i> <strong>Suspended until:</strong> ${new Date(u.booking_suspension_until).toLocaleString('en-PH', {month:'short',day:'numeric',year:'numeric',hour:'2-digit',minute:'2-digit'})}
                </div>` : `
                <div style="background:rgba(0,177,79,0.08);border:1px solid rgba(0,177,79,0.15);border-radius:10px;padding:8px;margin-bottom:10px;font-size:0.78rem;color:var(--success);text-align:center;">
                    <i class="fas fa-check-circle"></i> Good Standing · No active suspension
                </div>`}

                ${u.violation_commitment_fee_required ? `
                <div style="font-size:0.75rem;color:#fb923c;margin-bottom:10px;background:rgba(245,158,11,0.1);padding:6px 10px;border-radius:8px;">
                    <i class="fas fa-coins" style="margin-right:4px;"></i> ₱200 Commitment fee required on next booking
                </div>` : ''}

                <!-- Action Buttons -->
                <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap;">
                    <button onclick="UserMgmt.toggleEditStanding(${u.id})" style="flex:1;min-width:105px;padding:9px;background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.35);border-radius:10px;color:#f59e0b;font-weight:700;font-size:0.78rem;cursor:pointer;">
                        <i class="fas fa-edit"></i> Edit Standing
                    </button>
                    <button onclick="UserMgmt.loadViolationHistory(${u.id})" style="flex:1;min-width:85px;padding:9px;background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);border-radius:10px;color:#818cf8;font-weight:700;font-size:0.78rem;cursor:pointer;">
                        <i class="fas fa-history"></i> History
                    </button>
                    <button onclick="UserMgmt.resetViolations(${u.id})" style="flex:1;min-width:85px;padding:9px;background:rgba(0,177,79,0.1);border:1px solid rgba(0,177,79,0.25);border-radius:10px;color:var(--success);font-weight:700;font-size:0.78rem;cursor:pointer;">
                        <i class="fas fa-undo"></i> Reset
                    </button>
                    ${!u.violation_permanently_restricted ? `
                    <button onclick="UserMgmt.blacklistUser(${u.id})" style="flex:1;min-width:75px;padding:9px;background:rgba(220,38,38,0.1);border:1px solid rgba(220,38,38,0.25);border-radius:10px;color:#dc2626;font-weight:700;font-size:0.78rem;cursor:pointer;">
                        <i class="fas fa-ban"></i> Ban
                    </button>` : `
                    <button onclick="UserMgmt.liftBlacklist(${u.id})" style="flex:1;min-width:85px;padding:9px;background:rgba(0,177,79,0.1);border:1px solid rgba(0,177,79,0.25);border-radius:10px;color:var(--success);font-weight:700;font-size:0.78rem;cursor:pointer;">
                        <i class="fas fa-unlock"></i> Lift Ban
                    </button>`}
                </div>

                <!-- Inline Edit Form (collapsed by default) -->
                <div id="umEditStandingForm_${u.id}" style="display:none;margin-top:12px;padding:14px;background:rgba(0,0,0,0.35);border:1.5px solid rgba(245,158,11,0.3);border-radius:12px;">
                    <div style="font-weight:800;font-size:0.82rem;color:#f59e0b;margin-bottom:10px;display:flex;align-items:center;gap:6px;">
                        <i class="fas fa-sliders-h"></i> Modify Account Standing &amp; Penalties
                    </div>
                    
                    <div style="margin-bottom:10px;">
                        <label style="display:block;font-size:0.72rem;color:var(--text-muted);font-weight:700;margin-bottom:4px;">STRIKE COUNT</label>
                        <select id="editStrikes_${u.id}" style="width:100%;padding:9px 12px;background:rgba(255,255,255,0.06);border:1px solid var(--border);border-radius:8px;color:white;font-size:0.85rem;">
                            <option value="0" ${(!u.violation_strikes || u.violation_strikes === 0) ? 'selected' : ''}>0 Strikes (Good Standing)</option>
                            <option value="1" ${u.violation_strikes === 1 ? 'selected' : ''}>1 Strike (Caution / 24h default)</option>
                            <option value="2" ${u.violation_strikes === 2 ? 'selected' : ''}>2 Strikes (Suspended / 7d default)</option>
                            <option value="3" ${u.violation_strikes === 3 ? 'selected' : ''}>3 Strikes (Permanent Restriction)</option>
                            <option value="4" ${u.violation_strikes === 4 ? 'selected' : ''}>4 Strikes</option>
                            <option value="5" ${u.violation_strikes === 5 ? 'selected' : ''}>5 Strikes</option>
                        </select>
                    </div>

                    <div style="margin-bottom:10px;">
                        <label style="display:block;font-size:0.72rem;color:var(--text-muted);font-weight:700;margin-bottom:4px;">BOOKING SUSPENSION</label>
                        <select id="editSuspPreset_${u.id}" onchange="UserMgmt.onSuspPresetChange(${u.id})" style="width:100%;padding:9px 12px;background:rgba(255,255,255,0.06);border:1px solid var(--border);border-radius:8px;color:white;font-size:0.85rem;margin-bottom:6px;">
                            <option value="keep">Keep Current Suspension</option>
                            <option value="none">No Suspension (Lift / Clear)</option>
                            <option value="24h">Suspend for 24 Hours from now</option>
                            <option value="7d">Suspend for 7 Days from now</option>
                            <option value="30d">Suspend for 30 Days from now</option>
                            <option value="custom">Set Custom Expiry Date &amp; Time...</option>
                        </select>
                        <input type="datetime-local" id="editSuspCustom_${u.id}" min="2020-01-01T00:00" max="2099-12-31T23:59" style="display:none;width:100%;padding:8px 12px;background:rgba(255,255,255,0.06);border:1px solid var(--border);border-radius:8px;color:white;font-size:0.85rem;" />
                    </div>

                    <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:12px;background:rgba(255,255,255,0.03);padding:10px;border-radius:8px;">
                        <label style="display:flex;align-items:center;gap:8px;font-size:0.8rem;color:var(--text-primary);cursor:pointer;">
                            <input type="checkbox" id="editFeeReq_${u.id}" ${u.violation_commitment_fee_required ? 'checked' : ''} style="width:16px;height:16px;accent-color:#f59e0b;">
                            <span>Require <strong>₱200 Commitment Fee</strong> on next booking</span>
                        </label>
                        <label style="display:flex;align-items:center;gap:8px;font-size:0.8rem;color:#f87171;cursor:pointer;">
                            <input type="checkbox" id="editPermRest_${u.id}" ${u.violation_permanently_restricted ? 'checked' : ''} style="width:16px;height:16px;accent-color:#dc2626;">
                            <span><strong>Permanently restrict</strong> from making bookings</span>
                        </label>
                    </div>

                    <div style="margin-bottom:12px;">
                        <label style="display:block;font-size:0.72rem;color:var(--text-muted);font-weight:700;margin-bottom:4px;">ADMIN NOTE / REASON FOR CHANGE</label>
                        <input type="text" id="editNote_${u.id}" maxlength="200" placeholder="e.g., Customer dispute approved / Strike reduction granted" style="width:100%;padding:9px 12px;background:rgba(255,255,255,0.06);border:1px solid var(--border);border-radius:8px;color:white;font-size:0.85rem;">
                    </div>

                    <div style="display:flex;gap:8px;">
                        <button onclick="UserMgmt.saveStandingEdit(${u.id})" style="flex:2;padding:10px;background:var(--primary);border:none;border-radius:8px;color:white;font-weight:800;font-size:0.82rem;cursor:pointer;">
                            <i class="fas fa-check" style="margin-right:4px;"></i> Save Standing
                        </button>
                        <button onclick="document.getElementById('umEditStandingForm_${u.id}').style.display='none'" style="flex:1;padding:10px;background:rgba(255,255,255,0.08);border:1px solid var(--border);border-radius:8px;color:var(--text-muted);font-weight:700;font-size:0.82rem;cursor:pointer;">
                            Cancel
                        </button>
                    </div>
                </div>

                <div id="umViolationHistory_${u.id}" style="display:none;margin-top:10px;max-height:220px;overflow-y:auto;"></div>
            </div>

            <!-- Freeze / Unfreeze -->
            <div style="background:var(--surface-card);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:16px;">
                <div style="font-size:0.72rem;color:var(--text-muted);font-weight:800;text-transform:uppercase;margin-bottom:12px;">${u.is_frozen ? 'Unfreeze Account' : 'Freeze Account'}</div>
                ${!u.is_frozen ? `<input id="umFreezeReason" type="text" maxlength="200" placeholder="Reason for freezing..." style="width:100%;padding:11px 14px;background:var(--surface-container, var(--surface-solid));border:1.5px solid var(--border);border-radius:10px;color:var(--text-main);font-size:0.88rem;margin-bottom:10px;outline:none;box-sizing:border-box;">` : `<p style="font-size:0.82rem;color:var(--text-muted);margin-bottom:10px;">Reason: ${escapeHtml(u.freeze_reason || 'No reason provided')}</p>`}
                <button onclick="UserMgmt.toggleFreeze(${u.id}, ${u.is_frozen})" style="width:100%;padding:12px;background:${u.is_frozen ? 'rgba(0,177,79,0.12)' : 'rgba(239,68,68,0.12)'};border:1.5px solid ${u.is_frozen ? 'var(--success)' : 'var(--danger)'};border-radius:10px;color:${u.is_frozen ? 'var(--success)' : 'var(--danger)'};font-weight:800;font-size:0.85rem;cursor:pointer;">
                    <i class="fas fa-${u.is_frozen ? 'unlock' : 'lock'}"></i> ${u.is_frozen ? 'Unfreeze Account' : 'Freeze Account'}
                </button>
            </div>







            <!-- Delete -->



            <button onclick="UserMgmt.deleteUser(${u.id}, '${(u.full_name||'').replace(/'/g,"\\'")}' )" style="width:100%;padding:14px;background:rgba(239,68,68,0.1);border:1px solid var(--danger);border-radius:14px;color:var(--danger);font-weight:800;font-size:0.9rem;margin-bottom:10px;">



                <i class="fas fa-trash-alt"></i> Delete Account Permanently



            </button>`;



        },







        closeModal() {



            document.getElementById('umModal').style.display = 'none';



        },







        async saveEdit(userId) {



            const name = document.getElementById('umEditName').value.trim();



            const phone = document.getElementById('umEditPhone').value.trim();



            if (!name) { alert('Full name is required'); return; }



            try {



                const res = await apiFetch(`admin/users/${userId}/edit`, {



                    method: 'PUT',



                    headers: {'Content-Type':'application/json'},



                    body: JSON.stringify({full_name: name, phone})



                });



                const d = await res.json();



                if (!res.ok) throw new Error(d.error);



                showNotification(d.message || 'User updated', 'success');



                this.refresh();



                this.openModal(userId);



            } catch (e) { alert(e.message); }



        },







        async setLoyalty(userId) {



            const pts = document.getElementById('umLoyaltyInput').value;



            if (pts === '' || isNaN(pts)) { alert('Enter a valid number'); return; }



            try {



                const res = await apiFetch(`admin/users/${userId}/loyalty`, {



                    method: 'PUT',



                    headers: {'Content-Type':'application/json'},



                    body: JSON.stringify({points: parseInt(pts)})



                });



                const d = await res.json();



                if (!res.ok) throw new Error(d.error);



                showNotification(d.message || 'Points updated', 'success');



                this.refresh();



                this.openModal(userId);



            } catch (e) { alert(e.message); }



        },







        async resetPassword(userId) {



            const pass = document.getElementById('umNewPass').value;



            if (pass.length < 8) { alert('Password must be at least 8 characters'); return; }



            if (!confirm('Reset this renter\'s password?')) return;



            try {



                const res = await apiFetch(`admin/users/${userId}/reset-password`, {



                    method: 'POST',



                    headers: {'Content-Type':'application/json'},



                    body: JSON.stringify({new_password: pass})



                });



                const d = await res.json();



                if (!res.ok) throw new Error(d.error);



                showNotification(d.message || 'Password reset', 'success');



                document.getElementById('umNewPass').value = '';



            } catch (e) { alert(e.message); }
        },

        async toggleRegularCustomer(userId, currentStatus) {
            const confirmMsg = currentStatus 
                ? 'Revoke Regular Customer (VIP) status? The customer will no longer be exempt from downpayment.'
                : 'Mark this renter as a Regular Customer (VIP)? They will be exempt from downpayment (₱0 DP upon booking).';
            if (!confirm(confirmMsg)) return;
            try {
                const res = await apiFetch(`admin/users/${userId}/toggle-regular-customer`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ is_regular: !currentStatus })
                });
                const d = await res.json();
                if (!res.ok) throw new Error(d.error || 'Failed to update customer status');
                showNotification(d.message || 'Customer VIP status updated', 'success');
                this.refresh();
                this.openModal(userId);
            } catch (e) { alert(e.message); }
        },

        async toggleFreeze(userId, currentlyFrozen) {
        if (typeof anime !== 'undefined') {
            const btn = (window.event && (window.event.currentTarget || window.event.target));
            if (btn) anime({ targets: btn, scale: [1, 0.94, 1], duration: 250, easing: 'easeOutBack' });
        }
        const freeze = !currentlyFrozen;



            let reason = '';



            if (freeze) {
                const reasonEl = document.getElementById('umFreezeReason');
                if (reasonEl) clearInlineError(reasonEl);
                reason = (reasonEl || {}).value || '';
                if (!reason.trim()) { 
                    if (reasonEl) showInlineError(reasonEl, 'Please enter a reason for freezing'); 
                    return; 
                }
            }



            if (!confirm(freeze ? 'Freeze this account?' : 'Unfreeze this account?')) return;



            try {



                const res = await apiFetch(`admin/users/${userId}/freeze`, {



                    method: 'POST',



                    headers: {'Content-Type':'application/json'},



                    body: JSON.stringify({freeze, reason})



                });



                const d = await res.json();



                if (!res.ok) throw new Error(d.error);



                showNotification(d.message || 'Account updated', 'success');



                this.refresh();



                this.openModal(userId);



            } catch (e) { alert(e.message); }



        },







        async deleteUser(userId, name) {



            if (!confirm(`Permanently delete "${name}"? This cannot be undone.`)) return;



            if (!confirm('Are you absolutely sure? All bookings and data will be removed.')) return;



            try {



                const res = await apiFetch(`admin/users/${userId}`, {method: 'DELETE'});



                const d = await res.json();



                if (!res.ok) throw new Error(d.error);



                showNotification(d.message || 'User deleted', 'success');



                this.closeModal();



                this.refresh();



            } catch (e) { alert(e.message); }



        },







        async exportCSV() {
            if (typeof anime !== 'undefined') {
                const _btn = (window.event && (window.event.currentTarget || window.event.target));
                if (_btn) {
                    anime({
                        targets: (_btn.querySelector && _btn.querySelector('i')) || _btn,
                        translateY: [0, -6, 2, 0],
                        duration: 450,
                        easing: 'easeOutBack'
                    });
                }
            }
            try {
                const url = `${API_URL}/admin/users/export`;
                const a = document.createElement('a');
                a.href = url;
                a.download = 'users_export.csv';
                a.click();
            } catch (e) { alert('Export failed: ' + e.message); }
        },

        toggleEditStanding(userId) {
            const form = document.getElementById(`umEditStandingForm_${userId}`);
            if (!form) return;
            form.style.display = form.style.display === 'none' ? 'block' : 'none';
        },

        onSuspPresetChange(userId) {
            const sel = document.getElementById(`editSuspPreset_${userId}`);
            const custom = document.getElementById(`editSuspCustom_${userId}`);
            if (sel && custom) {
                custom.style.display = sel.value === 'custom' ? 'block' : 'none';
            }
        },

        async saveStandingEdit(userId) {
            const strikesEl = document.getElementById(`editStrikes_${userId}`);
            const suspPresetEl = document.getElementById(`editSuspPreset_${userId}`);
            const suspCustomEl = document.getElementById(`editSuspCustom_${userId}`);
            const feeReqEl = document.getElementById(`editFeeReq_${userId}`);
            const permRestEl = document.getElementById(`editPermRest_${userId}`);
            const noteEl = document.getElementById(`editNote_${userId}`);

            const strikes = parseInt(strikesEl ? strikesEl.value : 0);
            const feeReq = feeReqEl ? feeReqEl.checked : false;
            const permRest = permRestEl ? permRestEl.checked : false;
            const note = (noteEl ? noteEl.value : '').trim();

            let suspUntil = undefined;
            const preset = suspPresetEl ? suspPresetEl.value : 'keep';
            const now = new Date();
            if (preset === 'none') {
                suspUntil = null;
            } else if (preset === '24h') {
                suspUntil = new Date(now.getTime() + 24 * 3600 * 1000).toISOString();
            } else if (preset === '7d') {
                suspUntil = new Date(now.getTime() + 7 * 24 * 3600 * 1000).toISOString();
            } else if (preset === '30d') {
                suspUntil = new Date(now.getTime() + 30 * 24 * 3600 * 1000).toISOString();
            } else if (preset === 'custom' && suspCustomEl && suspCustomEl.value) {
                suspUntil = new Date(suspCustomEl.value).toISOString();
            }

            const adminUser = (typeof adminAuth !== 'undefined' && adminAuth.getUser && adminAuth.getUser()) ? adminAuth.getUser() : null;
            const payload = {
                violation_strikes: strikes,
                violation_commitment_fee_required: feeReq,
                violation_permanently_restricted: permRest,
                note: note,
                admin_id: adminUser ? adminUser.id : null
            };
            if (preset !== 'keep') {
                payload.booking_suspension_until = suspUntil;
            }

            try {
                const res = await apiFetch(`admin/users/${userId}/violations/edit`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const d = await res.json();
                if (!res.ok) throw new Error(d.error || 'Failed to update standing');

                if (typeof showNotification === 'function') {
                    showNotification(d.message || 'Account standing updated successfully', 'success');
                } else {
                    alert(d.message || 'Account standing updated successfully');
                }
                this.openModal(userId);
                this.refresh();
            } catch (err) {
                alert('Error updating standing: ' + err.message);
            }
        },

        async resetViolations(userId) {
            if (!confirm('Are you sure you want to reset violation strikes and lift all suspensions for this renter?')) return;
            const note = prompt('Optional note for resetting violations:', 'Admin reset strikes');
            const adminUser = (typeof adminAuth !== 'undefined' && adminAuth.getUser && adminAuth.getUser()) ? adminAuth.getUser() : null;
            try {
                const res = await apiFetch(`admin/users/${userId}/violations/reset`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        note: note || 'Admin reset',
                        admin_id: adminUser ? adminUser.id : null
                    })
                });
                const d = await res.json();
                if (!res.ok) throw new Error(d.error || 'Failed to reset violations');
                if (typeof showNotification === 'function') {
                    showNotification(d.message || 'Violations reset successfully', 'success');
                } else {
                    alert(d.message || 'Violations reset successfully');
                }
                this.openModal(userId);
                this.refresh();
            } catch (err) {
                alert('Error: ' + err.message);
            }
        },

        async blacklistUser(userId) {
            if (!confirm('Permanently restrict this renter from booking?')) return;
            try {
                const res = await apiFetch(`admin/users/${userId}/violations/blacklist`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ blacklist: true })
                });
                const d = await res.json();
                if (!res.ok) throw new Error(d.error || 'Failed to ban renter');
                if (typeof showNotification === 'function') {
                    showNotification(d.message || 'Renter blacklisted from booking', 'success');
                } else {
                    alert(d.message || 'Renter blacklisted from booking');
                }
                this.openModal(userId);
                this.refresh();
            } catch (err) {
                alert('Error: ' + err.message);
            }
        },

        async liftBlacklist(userId) {
            if (!confirm('Lift permanent booking restriction for this renter?')) return;
            try {
                const res = await apiFetch(`admin/users/${userId}/violations/blacklist`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ blacklist: false })
                });
                const d = await res.json();
                if (!res.ok) throw new Error(d.error || 'Failed to lift restriction');
                if (typeof showNotification === 'function') {
                    showNotification(d.message || 'Booking restriction lifted', 'success');
                } else {
                    alert(d.message || 'Booking restriction lifted');
                }
                this.openModal(userId);
                this.refresh();
            } catch (err) {
                alert('Error: ' + err.message);
            }
        },

        async loadViolationHistory(userId) {
            const histDiv = document.getElementById(`umViolationHistory_${userId}`);
            if (!histDiv) return;
            if (histDiv.style.display === 'block') {
                histDiv.style.display = 'none';
                return;
            }
            histDiv.style.display = 'block';
            histDiv.innerHTML = '<div style="text-align:center;padding:10px;font-size:0.75rem;color:var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Loading history...</div>';
            try {
                const res = await apiFetch(`admin/users/${userId}/violations`);
                const data = await res.json();
                const hist = data.history || [];
                if (!hist.length) {
                    histDiv.innerHTML = '<div style="font-size:0.75rem;color:var(--text-muted);text-align:center;padding:8px;background:rgba(255,255,255,0.03);border-radius:8px;">No violation records found for this user.</div>';
                    return;
                }
                histDiv.innerHTML = hist.map(h => {
                    const dt = h.created_at ? new Date(h.created_at).toLocaleString('en-PH', {month:'short',day:'numeric',year:'numeric',hour:'2-digit',minute:'2-digit'}) : 'Unknown';
                    const isReset = Boolean(h.reset_at);
                    return `
                    <div style="background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:8px;padding:8px 10px;margin-bottom:6px;font-size:0.75rem;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                            <span style="font-weight:800;color:${isReset ? 'var(--success)' : '#f87171'};">
                                ${isReset ? '✅ Resolved / Reset' : `⚠️ Strike #${h.violation_number}`}
                            </span>
                            <span style="color:var(--text-muted);font-size:0.7rem;">${dt}</span>
                        </div>
                        <div style="color:var(--text-secondary);">
                            ${h.booking_id ? `Booking #${h.booking_id} · ` : ''}${h.suspension_type || 'Penalty applied'}
                        </div>
                        ${h.reset_note ? `<div style="color:var(--success);font-size:0.7rem;margin-top:2px;"><i class="fas fa-info-circle"></i> ${h.reset_note}</div>` : ''}
                    </div>`;
                }).join('');
            } catch (err) {
                histDiv.innerHTML = `<div style="color:#ef4444;font-size:0.75rem;">Error loading history: ${err.message}</div>`;
            }
        }

    };







    window.UserMgmt = UserMgmt;







    // Auto-load when users tab is opened



    const _origSwitchTab = window.switchTab;



    window.switchTab = function(tabId) {



        _origSwitchTab(tabId);



        if (tabId === 'users' && UserMgmt._all.length === 0) {



            UserMgmt.refresh();



        }



    };



    // ??? END USER MANAGEMENT MODULE ???????????????????????????????????????







    // ============================================================



    // ADMIN CHAT MODULE



    // ============================================================



    const AdminChat = (function () {



        let _pollTimer = null;



        let _currentUserId = null;



        let _currentUserName = '';



        let _lastMsgId = 0;



        let _view = 'inbox'; // 'inbox' | 'conversation'



        let allConversations = [];



        let filteredConversations = [];







        function _esc(str) {



            if (!str) return '';



            return String(str)



                .replace(/&/g, '&amp;').replace(/</g, '&lt;')



                .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');



        }







        function _adminId() {



            const u = adminAuth.getUser();



            return u ? u.id : null;



        }







        // Search utility functions



        function escapeRegex(str) {



            return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');



        }







        function highlightText(text, searchTerm) {



            if (!text || !searchTerm) return text || '';



            const regex = new RegExp('(' + escapeRegex(searchTerm) + ')', 'gi');



            return text.replace(regex, '<mark class="search-highlight">$1</mark>');



        }







        // ?? Inbox ??????????????????????????????????????????????



        function loadInbox() {



            stopPolling();



            _currentUserId = null;



            _view = 'inbox';



            const el = document.getElementById('adminChatContent');



            if (!el) return;



            const aid = _adminId();



            if (!aid) {



                el.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:40px;">Please log in first.</p>';



                return;



            }







            el.innerHTML =



                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">' +



                    '<h1 class="page-title" style="margin:0;">Live Chat</h1>' +



                    '<div style="display:flex;align-items:center;gap:8px;">' +
                    '<button onclick="AdminChatControls.openModal()" class="btn-primary" style="padding:8px 14px;border-radius:10px;font-size:0.82rem;font-weight:700;display:flex;align-items:center;gap:6px;cursor:pointer;border:none;background:var(--primary);color:#fff;"><i class="fas fa-sliders-h"></i> FAQ &amp; AI Controls</button>' +
                    '<button onclick="AdminChat.loadInbox()" style="background:var(--surface);border:1px solid var(--border);color:var(--text-main);width:40px;height:40px;border-radius:12px;cursor:pointer;font-size:0.9rem;"><i class="fas fa-sync-alt"></i></button>' +
                    '</div>' +



                '</div>' +



                '<!-- Chat Search Container -->' +



                '<div class="chat-search-container" style="margin-bottom:16px;">' +



                    '<div class="search-box" style="position:relative;display:flex;align-items:center;">' +



                        '<span class="search-icon" style="position:absolute;left:12px;font-size:1.2rem;color:var(--text-muted);"><i class="fas fa-search"></i></span>' +



                        '<input type="text" id="chatSearchInput" maxlength="50" placeholder="Search conversations by name, email, or message..." autocomplete="off"' +



                            ' oninput="AdminChat.searchConversations(this.value)"' +



                            ' style="width:100%;padding:0.75rem 2.5rem 0.75rem 2.5rem;background:rgba(255,255,255,0.05);border:1px solid var(--border);border-radius:8px;color:var(--text-primary);font-size:0.95rem;outline:none;box-sizing:border-box;"' +



                            ' onfocus="this.style.borderColor=\'var(--primary)\';this.style.boxShadow=\'0 0 0 3px var(--primary-glow)\'"' +



                            ' onblur="this.style.borderColor=\'var(--border)\';this.style.boxShadow=\'none\'">' +



                        '<button class="clear-search hidden" id="clearSearch" onclick="AdminChat.clearSearch()"' +



                            ' style="position:absolute;right:8px;background:none;border:none;color:var(--text-muted);cursor:pointer;padding:4px 8px;border-radius:4px;transition:all 0.2s ease;"' +



                            ' onmouseover="this.style.background=\'rgba(255,255,255,0.1)\';this.style.color=\'var(--text-primary)\'"' +



                            ' onmouseout="this.style.background=\'none\';this.style.color=\'var(--text-muted)\'">' +



                            '<i class="fas fa-times"></i>' +



                        '</button>' +



                    '</div>' +



                    '<div class="search-results-count hidden" id="searchResultsCount"' +



                        ' style="margin-top:0.5rem;padding:0.5rem;background:rgba(0,177,79,0.1);border-radius:6px;text-align:center;">' +



                        '<span id="resultsText" style="font-size:0.85rem;color:var(--primary);font-weight:600;"></span>' +



                    '</div>' +



                '</div>' +



                '<div id="acInboxList" style="margin-bottom:16px;"><div style="text-align:center;padding:30px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin"></i></div></div>' +



                '<button onclick="AdminChat.showUserSearch()" style="width:100%;padding:13px;background:var(--primary);border:none;border-radius:14px;color:#fff;font-weight:700;font-size:0.85rem;cursor:pointer;">' +



                    '<i class="fas fa-plus" style="margin-right:6px;"></i>Start New Conversation' +



                '</button>' +



                '<div id="acUserSearch" style="display:none;margin-top:12px;">' +



                    '<input type="text" id="acUserSearchInput" maxlength="50" placeholder="Search by name or email..." oninput="AdminChat.searchUsers(this.value)"' +



                        ' style="width:100%;padding:12px 14px;background:var(--surface);border:1px solid var(--border);border-radius:12px;color:var(--text-main);font-size:0.85rem;box-sizing:border-box;">' +



                    '<div id="acUserSearchResults" style="margin-top:8px;"></div>' +



                '</div>';







            loadConversations();



        }







        // Load conversations from API



        function loadConversations() {



            const aid = _adminId();



            if (!aid) return;







            fetch(API_URL + '/chat/inbox?viewer_type=admin&viewer_id=' + aid)



                .then(function(r) { return r.json(); })



                .then(function(data) {



                    if (Array.isArray(data)) {



                        allConversations = data;



                        filteredConversations = data.slice();



                        renderConversations(filteredConversations);



                    } else {



                        allConversations = [];



                        filteredConversations = [];



                        renderConversations([]);



                    }



                })



                .catch(function() {



                    const list = document.getElementById('acInboxList');



                    if (list) list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--danger);">Failed to load. Tap refresh.</div>';



                });



        }







        // Search conversations



        function searchConversations(query) {



            const searchTerm = (query || '').toLowerCase().trim();



            



            if (!searchTerm) {



                filteredConversations = allConversations.slice();



                const resultsCount = document.getElementById('searchResultsCount');



                const clearBtn = document.getElementById('clearSearch');



                if (resultsCount) resultsCount.classList.add('hidden');



                if (clearBtn) clearBtn.classList.add('hidden');



                renderConversations(filteredConversations);



                return;



            }



            



            const clearBtn = document.getElementById('clearSearch');



            if (clearBtn) clearBtn.classList.remove('hidden');



            



            filteredConversations = allConversations.filter(function(conv) {



                // Search in customer name



                if (conv.other_name && conv.other_name.toLowerCase().includes(searchTerm)) {



                    return true;



                }



                // Search in email (if available)



                if (conv.other_email && conv.other_email.toLowerCase().includes(searchTerm)) {



                    return true;



                }



                // Search in last message content



                if (conv.last_message && conv.last_message.toLowerCase().includes(searchTerm)) {



                    return true;



                }



                return false;



            });



            



            // Show results count



            const resultsCount = document.getElementById('searchResultsCount');



            const resultsText = document.getElementById('resultsText');



            if (resultsCount && resultsText) {



                resultsText.textContent = filteredConversations.length + ' conversation' + (filteredConversations.length !== 1 ? 's' : '') + ' found';



                resultsCount.classList.remove('hidden');



            }



            



            renderConversations(filteredConversations);



        }







        // Clear search



        function clearSearch() {



            const searchInput = document.getElementById('chatSearchInput');



            if (searchInput) searchInput.value = '';



            searchConversations('');



        }







        // Render conversations



        function renderConversations(conversations) {



            const list = document.getElementById('acInboxList');



            if (!list) return;



            



            // Handle empty conversations



            if (!conversations || conversations.length === 0) {



                const searchInput = document.getElementById('chatSearchInput');



                const hasSearchTerm = searchInput && searchInput.value.trim();



                



                // Display "No results found" message when search is active



                if (hasSearchTerm) {



                    list.innerHTML = '<div class="no-results" style="text-align:center;padding:3rem 1rem;color:var(--text-muted);font-size:0.95rem;">No results found</div>';



                } else {



                    // Display default empty state when no search is active



                    list.innerHTML =



                        '<div style="text-align:center;padding:24px 16px;color:var(--text-muted);">' +



                            '<i class="fas fa-comments" style="font-size:2.5rem;margin-bottom:10px;display:block;opacity:0.3;"></i>' +



                            '<p style="font-size:0.85rem;margin:0;">No conversations yet.<br>Use the button below to start one.</p>' +



                        '</div>';



                }



                return;



            }



            



            // Get search term for highlighting



            const searchInput = document.getElementById('chatSearchInput');



            const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';



            



            // Render conversation items with highlighted search terms



            list.innerHTML = conversations.map(function(c) {



                const initials = (c.other_name || 'U').charAt(0).toUpperCase();



                const unread = parseInt(c.unread_count) || 0;



                



                // Format time metadata



                const ts = c.last_at ? new Date(c.last_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';



                



                // Apply highlighting using highlightText() helper for search term highlighting



                const displayName = searchTerm ? highlightText(_esc(c.other_name), searchTerm) : _esc(c.other_name);



                const displayMessage = searchTerm ? highlightText(_esc(c.last_message || ''), searchTerm) : _esc(c.last_message || '');



                



                // Use data attributes to avoid XSS in onclick - escape for HTML attribute context



                const escapedName = _esc(c.other_name);



                



                // Render conversation item with metadata (time, unread count)



                return '<div class="ac-inbox-item" onclick="AdminChat.openConversation(' + c.other_id + ',\'' + escapedName + '\')">' +



                    '<div class="ac-avatar">' + initials + '</div>' +



                    '<div class="ac-inbox-info">' +



                        '<div class="ac-inbox-name">' + displayName + '</div>' +



                        '<div class="ac-inbox-preview">' + displayMessage + '</div>' +



                    '</div>' +



                    '<div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex-shrink:0;">' +



                        '<span style="font-size:0.65rem;color:var(--text-muted);">' + ts + '</span>' +



                        (unread ? '<span class="ac-unread">' + unread + '</span>' : '') +



                    '</div>' +



                '</div>';



            }).join('');



        }



        function showUserSearch() {



            const box = document.getElementById('acUserSearch');



            if (!box) return;



            const isHidden = box.style.display === 'none';



            box.style.display = isHidden ? 'block' : 'none';



            if (isHidden) {



                const inp = document.getElementById('acUserSearchInput');



                if (inp) { inp.value = ''; inp.focus(); }



                const res = document.getElementById('acUserSearchResults');



                if (res) res.innerHTML = '';



            }



        }







        function searchUsers(q) {



            const res = document.getElementById('acUserSearchResults');



            if (!res) return;



            if (!q || q.length < 2) { res.innerHTML = ''; return; }



            fetch(API_URL + '/users/search?q=' + encodeURIComponent(q) + '&limit=10')



                .then(function(r) { return r.json(); })



                .then(function(data) {



                    if (!Array.isArray(data) || !data.length) {



                        res.innerHTML = '<p style="font-size:0.8rem;color:var(--text-muted);padding:8px 0;">No users found.</p>';



                        return;



                    }



                    res.innerHTML = data.map(function(u) {



                        const name = u.full_name || 'Unknown';



                        return '<div class="ac-inbox-item" style="margin-bottom:4px;" onclick="AdminChat.openConversation(' + u.id + ',\'' + _esc(name) + '\')">' +



                            '<div class="ac-avatar" style="font-size:0.85rem;">' + name.charAt(0).toUpperCase() + '</div>' +



                            '<div class="ac-inbox-info">' +



                                '<div class="ac-inbox-name">' + _esc(name) + '</div>' +



                                '<div class="ac-inbox-preview">' + _esc(maskEmail(u.email || '')) + '</div>' +



                            '</div>' +



                            '<i class="fas fa-chevron-right" style="color:var(--text-muted);"></i>' +



                        '</div>';



                    }).join('');



                })



                .catch(function() {



                    res.innerHTML = '<p style="font-size:0.8rem;color:var(--danger);padding:8px 0;">Search failed.</p>';



                });



        }







        // ?? Conversation ???????????????????????????????????????



        function openConversation(userId, userName) {



            stopPolling();



            _currentUserId = userId;



            _currentUserName = userName;



            _lastMsgId = 0;



            _view = 'conversation';







            const el = document.getElementById('adminChatContent');



            if (!el) return;







            el.innerHTML =



                '<div style="display:flex;align-items:center;gap:12px;padding-bottom:14px;border-bottom:1px solid var(--border);margin-bottom:0;">' +



                    '<button onclick="AdminChat.loadInbox()" style="background:var(--surface);border:1px solid var(--border);color:var(--text-main);width:38px;height:38px;border-radius:10px;flex-shrink:0;cursor:pointer;font-size:0.9rem;"><i class="fas fa-arrow-left"></i></button>' +



                    '<div class="ac-avatar" style="width:36px;height:36px;font-size:0.9rem;">' + _esc(userName).charAt(0).toUpperCase() + '</div>' +



                    '<div>' +



                        '<div style="font-weight:700;font-size:0.95rem;color:var(--text-main);">' + _esc(userName) + '</div>' +



                        '<div style="font-size:0.7rem;color:var(--text-muted);">Customer</div>' +



                    '</div>' +



                '</div>' +



                '<div id="acMessages" style="overflow-y:auto;padding:14px 0;display:flex;flex-direction:column;gap:8px;height:calc(100vh - 280px);"></div>' +



                '<div style="display:flex;gap:10px;padding-top:10px;border-top:1px solid var(--border);">' +



                    '<input type="text" id="acInput" maxlength="500" placeholder="Type a message..." onkeydown="if(event.key===\'Enter\')AdminChat.send()"' +



                        ' style="flex:1;padding:11px 16px;background:var(--surface);border:1px solid var(--border);border-radius:50px;color:var(--text-main);font-size:0.9rem;outline:none;">' +



                    '<button onclick="AdminChat.send()" style="background:var(--primary);color:#ffffff;border:none;border-radius:50%;width:42px;height:42px;display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;">' +



                        '<i class="fas fa-paper-plane"></i>' +



                    '</button>' +



                '</div>';







            const aid = _adminId();



            if (aid) {



                fetch(API_URL + '/chat/mark-read', {



                    method: 'POST',



                    headers: { 'Content-Type': 'application/json' },



                    body: JSON.stringify({ receiver_type: 'admin', receiver_id: aid, sender_type: 'user', sender_id: userId })



                }).catch(function() {});



            }







            _fetchMessages(true);



            _pollTimer = setInterval(function() { _fetchMessages(false); }, 2000);



        }







        function _fetchMessages(initial) {



            const aid = _adminId();



            if (!aid || !_currentUserId) return;



            console.log('[AdminChat] Fetching messages: user_id=' + _currentUserId + ', admin_id=' + aid);



            fetch(API_URL + '/chat/messages?user_id=' + _currentUserId + '&admin_id=' + aid + '&limit=100')



                .then(function(r) { return r.json(); })



                .then(function(msgs) {



                    console.log('[AdminChat] Received ' + (Array.isArray(msgs) ? msgs.length : 0) + ' messages');



                    if (msgs && msgs.length > 0) {



                        console.log('[AdminChat] First message:', JSON.stringify(msgs[0]));



                        console.log('[AdminChat] Last message:', JSON.stringify(msgs[msgs.length - 1]));



                    }



                    



                    const container = document.getElementById('acMessages');



                    if (!container) return;



                    if (!Array.isArray(msgs) || !msgs.length) {



                        if (initial) container.innerHTML =



                            '<div style="text-align:center;color:var(--text-muted);font-size:0.85rem;padding:30px;">No messages yet. Say hello!</div>';



                        return;



                    }



                    const latestId = msgs[msgs.length - 1].id;



                    console.log('[AdminChat] Latest ID: ' + latestId + ', Last ID: ' + _lastMsgId);



                    



                    // Only skip update if not initial AND same lastMsgId AND not forced



                    if (String(latestId) === String(_lastMsgId) && !initial && initial !== 'force') {



                        console.log('[AdminChat] Skipping update - same message ID');



                        return;



                    }







                    // Detect new message from user



                    const lastMsg = msgs[msgs.length - 1];



                    const isNewFromUser = !initial && String(latestId) !== String(_lastMsgId) && lastMsg.sender_type === 'user';



                    _lastMsgId = latestId;







                    // Show pop-up banner



                    if (isNewFromUser) {



                        showAdminChatPopup(_currentUserName, lastMsg.message, _currentUserId);



                    }







                    const atBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 80;



                    console.log('[AdminChat] Rendering ' + msgs.length + ' messages');



                    container.innerHTML = msgs.map(function(m) {



                        const isMe = m.sender_type === 'admin';



                        const ts = m.created_at ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';



                        if (isMe) {



                            return '<div style="display:flex;justify-content:flex-end;">' +



                                '<div style="max-width:78%;background:var(--primary);color:#ffffff;padding:10px 14px;border-radius:18px 18px 4px 18px;font-size:0.875rem;line-height:1.4;">' +



                                    _esc(m.message) +



                                    '<div style="font-size:0.62rem;color:rgba(255,255,255,0.6);margin-top:3px;text-align:right;">' + ts + '</div>' +



                                '</div>' +



                            '</div>';



                        } else {



                            return '<div style="display:flex;justify-content:flex-start;">' +



                                '<div style="max-width:78%;background:var(--surface);border:1px solid var(--border);color:var(--text-main);padding:10px 14px;border-radius:18px 18px 18px 4px;font-size:0.875rem;line-height:1.4;">' +



                                    _esc(m.message) +



                                    '<div style="font-size:0.62rem;color:var(--text-muted);margin-top:3px;">' + ts + '</div>' +



                                '</div>' +



                            '</div>';



                        }



                    }).join('');







                    if (initial || atBottom) container.scrollTop = container.scrollHeight;







                    fetch(API_URL + '/chat/mark-read', {



                        method: 'POST',



                        headers: { 'Content-Type': 'application/json' },



                        body: JSON.stringify({ receiver_type: 'admin', receiver_id: aid, sender_type: 'user', sender_id: _currentUserId })



                    }).catch(function() {});



                })



                .catch(function(err) {



                    console.error('[AdminChat] Error fetching messages:', err);



                });



        }







        function send() {



            const inputEl = document.getElementById('acInput');



            if (!inputEl) { console.error('CHAT: no input element'); return; }



            const msg = (inputEl.value || '').trim();



            const aid = _adminId();



            console.log('CHAT SEND: msg=' + msg + ' aid=' + aid + ' userId=' + _currentUserId);



            if (!msg) { console.error('CHAT: empty message'); return; }



            if (!aid) { alert('Not logged in - cannot send'); return; }



            if (!_currentUserId) { alert('No user selected'); return; }



            inputEl.value = '';



            inputEl.disabled = true;







            const payload = { sender_type: 'admin', sender_id: aid, receiver_type: 'user', receiver_id: _currentUserId, message: msg };



            console.log('CHAT PAYLOAD:', JSON.stringify(payload));







            fetch(API_URL + '/chat/send', {



                method: 'POST',



                headers: { 'Content-Type': 'application/json' },



                body: JSON.stringify(payload)



            })



                .then(function(r) {



                    console.log('CHAT SEND response status:', r.status);



                    return r.json().then(function(d) {



                        console.log('CHAT SEND response:', JSON.stringify(d));



                        // Force refresh by resetting _lastMsgId



                        _lastMsgId = null;



                        _fetchMessages(false);



                    });



                })



                .catch(function(err) { alert('Send failed: ' + (err.message || 'Unknown error')); })



                .finally(function() { if (inputEl) inputEl.disabled = false; });



        }







        function stopPolling() {



            if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }



        }







        function updateNavBadge() {



            const aid = _adminId();



            if (!aid) return;



            fetch(API_URL + '/chat/inbox?viewer_type=admin&viewer_id=' + aid)



                .then(function(r) { return r.json(); })



                .then(function(data) {



                    const badge = document.getElementById('adminChatNavBadge');



                    if (!badge) return;



                    let total = 0;



                    if (Array.isArray(data)) data.forEach(function(c) { total += parseInt(c.unread_count) || 0; });



                    if (total > 0) {



                        badge.textContent = total > 9 ? '9+' : String(total);



                        badge.style.display = 'flex';



                    } else {



                        badge.style.display = 'none';



                    }



                })



                .catch(function() {});



        }







        return { 



            loadInbox: loadInbox, 



            openConversation: openConversation, 



            send: send, 



            stopPolling: stopPolling, 



            showUserSearch: showUserSearch, 



            searchUsers: searchUsers, 



            updateNavBadge: updateNavBadge,



            loadConversations: loadConversations,



            searchConversations: searchConversations,



            clearSearch: clearSearch,



            renderConversations: renderConversations



        };



    })();


    /* ==========================================================================
       ADMIN CHAT CONTROLS MODULE (Live Chat FAQs & AI Assistant Controls)
       ========================================================================== */
    window.AdminChatControls = (function() {
        let _data = {
            settings: {
                chat_faq_enabled: true,
                chat_faq_autoreply_enabled: true,
                ai_assistant_enabled: true,
                ai_assistant_autoreply_enabled: true,
                ai_assistant_greeting: "",
                ai_assistant_fallback: ""
            },
            faqs: []
        };

        function _apiUrl(path) {
            if (typeof API_URL !== 'undefined' && API_URL) {
                return API_URL + path;
            }
            if (typeof API_BASE !== 'undefined' && API_BASE) {
                return API_BASE + path;
            }
            return path;
        }

        function _esc(str) {
            if (!str) return '';
            const d = document.createElement('div');
            d.textContent = str;
            return d.innerHTML;
        }

        async function openModal() {
            const modal = document.getElementById('adminChatControlsModal');
            if (!modal) return;
            modal.style.display = 'flex';
            switchTab('faqs');
            await loadControls();
        }

        function closeModal() {
            const modal = document.getElementById('adminChatControlsModal');
            if (modal) modal.style.display = 'none';
        }

        function handleBackdropClick(e) {
            if (e.target && e.target.id === 'adminChatControlsModal') {
                closeModal();
            }
        }

        function switchTab(tabName) {
            const tabFaqs = document.getElementById('chatCtrlTabFaqs');
            const tabAi = document.getElementById('chatCtrlTabAi');
            const paneFaqs = document.getElementById('chatCtrlPaneFaqs');
            const paneAi = document.getElementById('chatCtrlPaneAi');

            if (tabName === 'faqs') {
                if (tabFaqs) {
                    tabFaqs.style.background = 'var(--primary)';
                    tabFaqs.style.color = '#fff';
                    tabFaqs.style.border = 'none';
                }
                if (tabAi) {
                    tabAi.style.background = 'transparent';
                    tabAi.style.color = 'var(--text-muted)';
                    tabAi.style.border = '1px solid var(--border)';
                }
                if (paneFaqs) paneFaqs.style.display = 'block';
                if (paneAi) paneAi.style.display = 'none';
            } else {
                if (tabAi) {
                    tabAi.style.background = 'var(--primary)';
                    tabAi.style.color = '#fff';
                    tabAi.style.border = 'none';
                }
                if (tabFaqs) {
                    tabFaqs.style.background = 'transparent';
                    tabFaqs.style.color = 'var(--text-muted)';
                    tabFaqs.style.border = '1px solid var(--border)';
                }
                if (paneFaqs) paneFaqs.style.display = 'none';
                if (paneAi) paneAi.style.display = 'block';
            }
        }

        async function loadControls() {
            try {
                const res = await fetch(_apiUrl('/admin/chat/controls'));
                if (!res.ok) throw new Error('Failed to load controls (' + res.status + ')');
                const json = await res.json();
                _data = json;

                // Populate toggles
                const s = json.settings || {};
                const elFaqEn = document.getElementById('chatCtrlFaqEnabled');
                if (elFaqEn) elFaqEn.checked = !!s.chat_faq_enabled;

                const elFaqAuto = document.getElementById('chatCtrlFaqAutoreplyEnabled');
                if (elFaqAuto) elFaqAuto.checked = !!s.chat_faq_autoreply_enabled;

                const elAiEn = document.getElementById('chatCtrlAiEnabled');
                if (elAiEn) elAiEn.checked = !!s.ai_assistant_enabled;

                const elAiAuto = document.getElementById('chatCtrlAiAutoreplyEnabled');
                if (elAiAuto) elAiAuto.checked = !!s.ai_assistant_autoreply_enabled;

                const elAiGreet = document.getElementById('chatCtrlAiGreeting');
                if (elAiGreet) elAiGreet.value = s.ai_assistant_greeting || "";

                const elAiFall = document.getElementById('chatCtrlAiFallback');
                if (elAiFall) elAiFall.value = s.ai_assistant_fallback || "";

                renderFaqList(json.faqs || []);
            } catch (err) {
                console.error('[AdminChatControls] Error loading controls:', err);
                if (typeof showToast === 'function') {
                    showToast('Failed to load chat controls: ' + err.message, 'error');
                }
            }
        }

        function renderFaqList(faqs) {
            const container = document.getElementById('chatCtrlFaqList');
            const countBadge = document.getElementById('chatCtrlFaqCount');
            if (countBadge) countBadge.textContent = faqs ? faqs.length : 0;
            if (!container) return;

            if (!faqs || faqs.length === 0) {
                container.innerHTML = '<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:0.85rem; background:var(--surface-card); border-radius:12px; border:1px solid var(--border);">No FAQ items found. Click "+ Add New FAQ" to create one.</div>';
                return;
            }

            let html = '';
            faqs.forEach(function(item) {
                const isActive = !!item.is_active;
                const statusBadge = isActive
                    ? '<span style="font-size:0.7rem; font-weight:800; color:#10b981; background:rgba(16,185,129,0.12); padding:3px 8px; border-radius:8px;"><i class="fas fa-check-circle"></i> Active</span>'
                    : '<span style="font-size:0.7rem; font-weight:800; color:#6b7280; background:rgba(107,114,128,0.12); padding:3px 8px; border-radius:8px;"><i class="fas fa-eye-slash"></i> Inactive</span>';

                html += '<div class="faq-admin-card">';
                html += '  <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:8px; flex-wrap:wrap;">';
                html += '    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">';
                html += '      <span style="font-weight:800; font-size:0.9rem; color:var(--text-main); background:rgba(0,177,79,0.1); border:1px solid rgba(0,177,79,0.25); padding:4px 10px; border-radius:8px;">' + _esc(item.chip_label) + '</span>';
                html += '      <span style="font-size:0.7rem; color:var(--text-muted); background:rgba(255,255,255,0.05); padding:3px 8px; border-radius:6px;">Order: #' + (item.display_order || 0) + '</span>';
                html += '      ' + statusBadge;
                html += '    </div>';
                html += '    <div style="display:flex; align-items:center; gap:8px;">';
                html += '      <button type="button" onclick="AdminChatControls.toggleFaqStatus(' + item.id + ', ' + (!isActive) + ')" title="' + (isActive ? 'Deactivate' : 'Activate') + '" style="padding:6px 10px; border-radius:8px; font-size:0.75rem; font-weight:700; cursor:pointer; background:rgba(255,255,255,0.06); border:1px solid var(--border); color:var(--text-main);"><i class="fas ' + (isActive ? 'fa-toggle-on' : 'fa-toggle-off') + '"></i></button>';
                html += '      <button type="button" onclick="AdminChatControls.openFaqFormModal(' + item.id + ')" title="Edit" style="padding:6px 10px; border-radius:8px; font-size:0.75rem; font-weight:700; cursor:pointer; background:rgba(0,177,79,0.15); border:1px solid rgba(0,177,79,0.3); color:var(--primary);"><i class="fas fa-pencil-alt"></i> Edit</button>';
                html += '      <button type="button" onclick="AdminChatControls.deleteFaq(' + item.id + ')" title="Delete" style="padding:6px 10px; border-radius:8px; font-size:0.75rem; font-weight:700; cursor:pointer; background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); color:#ef4444;"><i class="fas fa-trash-alt"></i></button>';
                html += '    </div>';
                html += '  </div>';

                html += '  <div style="font-size:0.85rem; font-weight:700; color:var(--text-main); margin-bottom:6px;">' + _esc(item.question) + '</div>';
                html += '  <div style="font-size:0.72rem; color:var(--text-muted); margin-bottom:8px;"><strong>Keywords:</strong> ' + _esc(item.keywords) + '</div>';
                html += '  <div style="font-size:0.78rem; color:var(--text-muted); background:rgba(0,0,0,0.15); padding:10px 12px; border-radius:8px; border-left:3px solid var(--primary); white-space:pre-wrap; line-height:1.4;">' + _esc(item.answer) + '</div>';
                html += '</div>';
            });
            container.innerHTML = html;
        }

        async function saveSettings() {
            const faqEnabled = document.getElementById('chatCtrlFaqEnabled') ? document.getElementById('chatCtrlFaqEnabled').checked : true;
            const faqAutoreply = document.getElementById('chatCtrlFaqAutoreplyEnabled') ? document.getElementById('chatCtrlFaqAutoreplyEnabled').checked : true;
            const aiEnabled = document.getElementById('chatCtrlAiEnabled') ? document.getElementById('chatCtrlAiEnabled').checked : true;
            const aiAutoreply = document.getElementById('chatCtrlAiAutoreplyEnabled') ? document.getElementById('chatCtrlAiAutoreplyEnabled').checked : true;

            try {
                const res = await fetch(_apiUrl('/admin/chat/controls'), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        chat_faq_enabled: faqEnabled,
                        chat_faq_autoreply_enabled: faqAutoreply,
                        ai_assistant_enabled: aiEnabled,
                        ai_assistant_autoreply_enabled: aiAutoreply
                    })
                });
                if (!res.ok) throw new Error('Save failed');
                if (typeof showToast === 'function') {
                    showToast('Chat settings updated', 'success');
                }
            } catch (err) {
                console.error('[AdminChatControls] Save settings error:', err);
                if (typeof showToast === 'function') {
                    showToast('Failed to save settings: ' + err.message, 'error');
                }
            }
        }

        async function saveAiSettings() {
            const btn = document.getElementById('btnSaveAiSettings');
            const origHtml = btn ? btn.innerHTML : '';
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            }

            const greeting = document.getElementById('chatCtrlAiGreeting') ? document.getElementById('chatCtrlAiGreeting').value : '';
            const fallback = document.getElementById('chatCtrlAiFallback') ? document.getElementById('chatCtrlAiFallback').value : '';
            const aiEnabled = document.getElementById('chatCtrlAiEnabled') ? document.getElementById('chatCtrlAiEnabled').checked : true;
            const aiAutoreply = document.getElementById('chatCtrlAiAutoreplyEnabled') ? document.getElementById('chatCtrlAiAutoreplyEnabled').checked : true;

            try {
                const res = await fetch(_apiUrl('/admin/chat/controls'), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ai_assistant_enabled: aiEnabled,
                        ai_assistant_autoreply_enabled: aiAutoreply,
                        ai_assistant_greeting: greeting,
                        ai_assistant_fallback: fallback
                    })
                });
                if (!res.ok) throw new Error('Save failed');
                if (typeof showToast === 'function') {
                    showToast('AI Assistant settings saved successfully!', 'success');
                }
            } catch (err) {
                console.error('[AdminChatControls] Error saving AI settings:', err);
                if (typeof showToast === 'function') {
                    showToast('Failed to save AI settings: ' + err.message, 'error');
                }
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = origHtml;
                }
            }
        }

        function openFaqFormModal(faqId) {
            const subModal = document.getElementById('adminFaqFormModal');
            const titleEl = document.getElementById('adminFaqFormTitle');
            const form = document.getElementById('adminFaqForm');
            if (!subModal || !form) return;

            document.getElementById('faqFormId').value = '';
            document.getElementById('faqFormChipLabel').value = '';
            document.getElementById('faqFormCategory').value = 'general';
            document.getElementById('faqFormQuestion').value = '';
            document.getElementById('faqFormKeywords').value = '';
            document.getElementById('faqFormAnswer').value = '';
            document.getElementById('faqFormDisplayOrder').value = (_data.faqs ? _data.faqs.length + 1 : 1);
            document.getElementById('faqFormIsActive').checked = true;

            if (faqId) {
                const item = (_data.faqs || []).find(f => f.id === faqId);
                if (item) {
                    if (titleEl) titleEl.innerHTML = '<i class="fas fa-edit" style="color:var(--primary);"></i> Edit FAQ';
                    document.getElementById('faqFormId').value = item.id;
                    document.getElementById('faqFormChipLabel').value = item.chip_label || '';
                    document.getElementById('faqFormCategory').value = item.category || 'general';
                    document.getElementById('faqFormQuestion').value = item.question || '';
                    document.getElementById('faqFormKeywords').value = item.keywords || '';
                    document.getElementById('faqFormAnswer').value = item.answer || '';
                    document.getElementById('faqFormDisplayOrder').value = item.display_order || 1;
                    document.getElementById('faqFormIsActive').checked = !!item.is_active;
                }
            } else {
                if (titleEl) titleEl.innerHTML = '<i class="fas fa-plus-circle" style="color:var(--primary);"></i> Add New FAQ';
            }

            subModal.style.display = 'flex';
        }

        function closeFaqFormModal() {
            const subModal = document.getElementById('adminFaqFormModal');
            if (subModal) subModal.style.display = 'none';
        }

        function handleFaqBackdropClick(e) {
            if (e.target && e.target.id === 'adminFaqFormModal') {
                closeFaqFormModal();
            }
        }

        async function saveFaq() {
            const btn = document.getElementById('btnSaveFaqItem');
            const origHtml = btn ? btn.innerHTML : '';
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            }

            const id = document.getElementById('faqFormId').value;
            const chipLabel = document.getElementById('faqFormChipLabel').value.trim();
            const category = document.getElementById('faqFormCategory').value.trim() || 'general';
            const question = document.getElementById('faqFormQuestion').value.trim();
            const keywords = document.getElementById('faqFormKeywords').value.trim();
            const answer = document.getElementById('faqFormAnswer').value.trim();
            const displayOrder = parseInt(document.getElementById('faqFormDisplayOrder').value, 10) || 0;
            const isActive = document.getElementById('faqFormIsActive').checked;

            if (!chipLabel || !question || !answer) {
                alert('Please fill out Chip Label, Question, and Answer.');
                if (btn) { btn.disabled = false; btn.innerHTML = origHtml; }
                return;
            }

            const payload = {
                chip_label: chipLabel,
                category: category,
                question: question,
                keywords: keywords,
                answer: answer,
                display_order: displayOrder,
                is_active: isActive
            };

            const url = id ? _apiUrl('/admin/chat/faqs/' + id) : _apiUrl('/admin/chat/faqs');
            const method = id ? 'PUT' : 'POST';

            try {
                const res = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (!res.ok) {
                    const errJson = await res.json().catch(() => ({}));
                    throw new Error(errJson.error || 'Request failed with status ' + res.status);
                }

                closeFaqFormModal();
                if (typeof showToast === 'function') {
                    showToast(id ? 'FAQ updated successfully!' : 'FAQ created successfully!', 'success');
                }
                await loadControls();
            } catch (err) {
                console.error('[AdminChatControls] Save FAQ error:', err);
                alert('Failed to save FAQ: ' + err.message);
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = origHtml;
                }
            }
        }

        async function toggleFaqStatus(faqId, newActiveStatus) {
            try {
                const res = await fetch(_apiUrl('/admin/chat/faqs/' + faqId), {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ is_active: newActiveStatus })
                });
                if (!res.ok) throw new Error('Failed to update status');
                if (typeof showToast === 'function') {
                    showToast('FAQ status updated', 'success');
                }
                await loadControls();
            } catch (err) {
                console.error('[AdminChatControls] Error toggling FAQ status:', err);
                if (typeof showToast === 'function') {
                    showToast('Failed to toggle status: ' + err.message, 'error');
                }
            }
        }

        async function deleteFaq(faqId) {
            const item = (_data.faqs || []).find(f => f.id === faqId);
            const name = item ? item.chip_label : 'this FAQ';
            if (!confirm('Are you sure you want to delete ' + name + '? This cannot be undone.')) {
                return;
            }

            try {
                const res = await fetch(_apiUrl('/admin/chat/faqs/' + faqId), {
                    method: 'DELETE'
                });
                if (!res.ok) throw new Error('Delete failed');
                if (typeof showToast === 'function') {
                    showToast('FAQ deleted successfully', 'success');
                }
                await loadControls();
            } catch (err) {
                console.error('[AdminChatControls] Error deleting FAQ:', err);
                if (typeof showToast === 'function') {
                    showToast('Failed to delete FAQ: ' + err.message, 'error');
                }
            }
        }

        return {
            openModal: openModal,
            closeModal: closeModal,
            handleBackdropClick: handleBackdropClick,
            switchTab: switchTab,
            loadControls: loadControls,
            saveSettings: saveSettings,
            saveAiSettings: saveAiSettings,
            openFaqFormModal: openFaqFormModal,
            closeFaqFormModal: closeFaqFormModal,
            handleFaqBackdropClick: handleFaqBackdropClick,
            saveFaq: saveFaq,
            toggleFaqStatus: toggleFaqStatus,
            deleteFaq: deleteFaq
        };
    })();









    window.AdminChat = AdminChat;



    // END ADMIN CHAT MODULE







    // Admin Chat Pop-up Banner



    window.showAdminChatPopup = function(senderName, message, userId) {
        var existing = document.getElementById('adminChatPopup');
        if (existing) existing.remove();

        var banner = document.createElement('div');
        banner.id = 'adminChatPopup';
        banner.style.cssText = 'position:fixed;top:72px;left:12px;right:12px;z-index:6000;background:var(--primary);color:#ffffff;border-radius:14px;padding:12px 14px;box-shadow:0 8px 24px rgba(0,0,0,0.25);display:flex;align-items:center;gap:10px;cursor:pointer;';
        banner.innerHTML =
            '<div style="width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,0.2);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-weight:700;font-size:0.9rem;">' + (senderName||'U').charAt(0).toUpperCase() + '</div>' +
            '<div style="flex:1;min-width:0;">' +
                '<div style="font-size:0.72rem;font-weight:700;opacity:0.85;">' + (senderName||'Customer') + ' sent a message</div>' +
                '<div style="font-size:0.82rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + (message||'') + '</div>' +
            '</div>' +
            '<button onclick="document.getElementById(\'adminChatPopup\').remove()" style="background:rgba(255,255,255,0.2);border:none;color:#fff;width:26px;height:26px;border-radius:50%;cursor:pointer;font-size:0.75rem;flex-shrink:0;">x</button>';

        banner.onclick = function(e) {
            if (e.target.tagName === 'BUTTON') return;
            banner.remove();
            if (userId && typeof AdminChat !== 'undefined') {
                window._suppressChatInbox = true;
                switchTab('chat');
                AdminChat.openConversation(userId, senderName);
            } else {
                switchTab('chat');
            }
        };

        document.body.appendChild(banner);
        setTimeout(function() { if (banner.parentNode) banner.remove(); }, 6000);
    };







    // Background inbox polling (when not on chat tab)



    var _adminBgChatTimer = null;



    var _adminBgLastAt = '';



    function startAdminBgChatPolling() {



        if (_adminBgChatTimer) return;



        _adminBgChatTimer = setInterval(function() {



            if (typeof currentTab !== 'undefined' && currentTab === 'chat') return;



            const user = adminAuth.getUser();



            if (!user) return;



            fetch(API_URL + '/chat/inbox?viewer_type=admin&viewer_id=' + user.id)



                .then(function(r) { return r.json(); })



                .then(function(data) {



                    if (!Array.isArray(data)) return;



                    let totalUnread = 0;



                    data.forEach(function(c) { totalUnread += parseInt(c.unread_count) || 0; });



                    const badge = document.getElementById('adminChatNavBadge');



                    if (badge) {



                        if (totalUnread > 0) { badge.textContent = totalUnread > 9 ? '9+' : String(totalUnread); badge.style.display = 'flex'; }



                        else { badge.style.display = 'none'; }



                    }



                    const conv = data.find(function(c) { return parseInt(c.unread_count) > 0; });



                    if (conv && conv.last_at && conv.last_at !== _adminBgLastAt) {



                        _adminBgLastAt = conv.last_at;



                        showAdminChatPopup(conv.other_name, conv.last_message, conv.other_id);



                    }



                })



                .catch(function() {});



        }, 10000);



    }



    window.startAdminBgChatPolling = startAdminBgChatPolling;







    // Test Push Notification



    window.testAdminPushNotification = function() {



        const user = adminAuth.getUser();



        if (!user) { alert('Please log in first.'); return; }



        fetch(API_URL + '/debug/test-push', {



            method: 'POST',



            headers: { 'Content-Type': 'application/json' },



            body: JSON.stringify({ admin_id: user.id })



        })



        .then(function(r) { return r.json(); })



        .then(function(data) {



            if (data.success) {



                showNotification('Test push sent! Check your notifications.', 'success');



            } else {



                showNotification('Push failed: ' + (data.error || 'Unknown error'), 'error');



            }



        })



        .catch(function(err) {



            showNotification('Network error: ' + err.message, 'error');



        });



    };

    // === Blocking UI - auto-wraps all fetch calls ===
    var _adminFetchCount = 0;

    // ?? Skeleton screen helpers ??
    function skelLine(h, w, mb) {
        h = h || 12; w = w || '100%'; mb = mb || 8;
        return '<div style="height:'+h+'px;width:'+w+';border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;margin-bottom:'+mb+'px;"></div>';
    }
    function skelCard(lines) {
        return '<div style="background:var(--bg-card,#fff);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:10px;">' + lines.map(function(l){return skelLine(l[0],l[1],l[2]);}).join('') + '</div>';
    }

    // ?? Show skeleton for admin sections ??
    function showSkeleton(containerId, type) {
        var el = document.getElementById(containerId);
        if (!el) return;
        var html = '';
        if (type === 'stats') {
            html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">';
            for (var i=0;i<3;i++) html += '<div style="background:var(--bg-card,#fff);border:1px solid var(--border);border-radius:14px;padding:16px;">'+skelLine(10,'60%',10)+skelLine(28,'80%',0)+'</div>';
            html += '</div>';
        } else if (type === 'list') {
            for (var j=0;j<5;j++) html += '<div style="background:var(--bg-card,#fff);border:1px solid var(--border);border-radius:12px;padding:14px;margin-bottom:8px;display:flex;gap:12px;align-items:center;"><div style="width:40px;height:40px;border-radius:50%;flex-shrink:0;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;"></div><div style="flex:1;">'+skelLine(12,'70%',6)+skelLine(10,'50%',0)+'</div></div>';
        } else if (type === 'table') {
            html = '<table style="width:100%;border-collapse:collapse;">';
            for (var k=0;k<6;k++) html += '<tr style="border-bottom:1px solid var(--border);"><td style="padding:14px 8px;">'+skelLine(12,'80%',0)+'</td><td style="padding:14px 8px;">'+skelLine(12,'60%',0)+'</td><td style="padding:14px 8px;">'+skelLine(12,'70%',0)+'</td><td style="padding:14px 8px;">'+skelLine(12,'50%',0)+'</td></tr>';
            html += '</table>';
        } else {
            html = skelCard([[12,'100%',8],[10,'80%',0]]) + skelCard([[12,'100%',8],[10,'60%',0]]) + skelCard([[12,'100%',8],[10,'70%',0]]);
        }
        el.innerHTML = html;
    }

    function showAdminLoading(show) {
        var el = document.getElementById('adminLoadingOverlay');
        if (el) el.style.display = show ? 'flex' : 'none';
        document.body.style.overflow = show ? 'hidden' : '';
    }
    (function() {
        var _orig = window.fetch;
        var _SKIP = ['/notifications', '/fcm-token', '/gps', '/chat/messages', '/paymongo/status', 'blynk.cloud'];
        window.fetch = function(url, opts) {
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
        };
    })();

    // === Full-screen blocking UI for write operations ===
    function showAdminBlockingUI(show) {
        var el = document.getElementById('adminBlockingOverlay');
        if (!el) {
            el = document.createElement('div');
            el.id = 'adminBlockingOverlay';
            el.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.45);z-index:999999;'
                + 'display:none;align-items:center;justify-content:center;flex-direction:column;gap:14px;'
                + 'backdrop-filter:blur(2px);';
            el.innerHTML = '<div style="width:52px;height:52px;border:4px solid rgba(255,255,255,0.3);'
                + 'border-top-color:#00B14F;border-radius:50%;animation:adminSpin 0.75s linear infinite;"></div>'
                + '<p style="color:#fff;font-size:0.9rem;font-weight:700;letter-spacing:0.3px;">Processing...</p>';
            document.body.appendChild(el);
        }
        el.style.display = show ? 'flex' : 'none';
        document.body.style.overflow = show ? 'hidden' : '';
    }


    // ?? Skeleton screen helpers ??
    function skelLine(h, w, mb) {
        h = h || 12; w = w || '100%'; mb = mb || 8;
        return '<div style="height:'+h+'px;width:'+w+';border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;margin-bottom:'+mb+'px;"></div>';
    }
    function skelCard(lines) {
        return '<div style="background:var(--bg-card,#fff);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:10px;">' + lines.map(function(l){return skelLine(l[0],l[1],l[2]);}).join('') + '</div>';
    }

    // ?? Show skeleton for admin sections ??
    function showSkeleton(containerId, type) {
        var el = document.getElementById(containerId);
        if (!el) return;
        var html = '';
        if (type === 'stats') {
            html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">';
            for (var i=0;i<3;i++) html += '<div style="background:var(--bg-card,#fff);border:1px solid var(--border);border-radius:14px;padding:16px;">'+skelLine(10,'60%',10)+skelLine(28,'80%',0)+'</div>';
            html += '</div>';
        } else if (type === 'list') {
            for (var j=0;j<5;j++) html += '<div style="background:var(--bg-card,#fff);border:1px solid var(--border);border-radius:12px;padding:14px;margin-bottom:8px;display:flex;gap:12px;align-items:center;"><div style="width:40px;height:40px;border-radius:50%;flex-shrink:0;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;"></div><div style="flex:1;">'+skelLine(12,'70%',6)+skelLine(10,'50%',0)+'</div></div>';
        } else if (type === 'table') {
            html = '<table style="width:100%;border-collapse:collapse;">';
            for (var k=0;k<6;k++) html += '<tr style="border-bottom:1px solid var(--border);"><td style="padding:14px 8px;">'+skelLine(12,'80%',0)+'</td><td style="padding:14px 8px;">'+skelLine(12,'60%',0)+'</td><td style="padding:14px 8px;">'+skelLine(12,'70%',0)+'</td><td style="padding:14px 8px;">'+skelLine(12,'50%',0)+'</td></tr>';
            html += '</table>';
        } else {
            html = skelCard([[12,'100%',8],[10,'80%',0]]) + skelCard([[12,'100%',8],[10,'60%',0]]) + skelCard([[12,'100%',8],[10,'70%',0]]);
        }
        el.innerHTML = html;
    }

    // --- SMTP OAUTH EMAIL CONFIGURATION ---
    function toggleSmtpConfigModal() {
        const modal = document.getElementById('smtpConfigModal');
        if (modal) {
            modal.style.display = 'flex';
            loadSmtpStatus();
        }
    }

    function closeSmtpConfigModal() {
        const modal = document.getElementById('smtpConfigModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    function closeSmtpConfigModalBackdrop(event) {
        if (event.target === event.currentTarget) {
            closeSmtpConfigModal();
        }
    }

    async function loadSmtpStatus() {
        const statusDetail = document.getElementById('smtpStatusDetail');
        const actionsDiv = document.getElementById('smtpOAuthActions');
        const label = document.getElementById('smtpStatusLabel');
        
        if (statusDetail) statusDetail.textContent = "Loading status...";
        
        try {
            const res = await fetch(API_BASE + '/api/admin/smtp/status');
            const data = await res.json();
            
            let statusHtml = '';
            if (data.is_linked && data.is_valid) {
                statusHtml = `<span style="color:#00B14F;"><i class="fas fa-check-circle"></i> Google OAuth Active</span><br><span style="font-size:0.8rem;color:var(--text-muted);font-weight:normal;">${data.email}</span>`;
                if (label) label.textContent = `Connected as ${data.email}`;
            } else if (data.is_linked && !data.is_valid) {
                statusHtml = `<span style="color:#ef4444;"><i class="fas fa-exclamation-triangle"></i> Token Expired / Needs Re-auth</span><br><span style="font-size:0.8rem;color:var(--text-muted);font-weight:normal;">${data.email}</span><br><span style="font-size:0.75rem;color:#ef4444;">Google test token expired. Please click Re-Authorize below or enter an App Password.</span>`;
                if (label) label.textContent = `Email Token Expired (${data.email})`;
            } else if (data.has_manual_smtp) {
                statusHtml = `<span style="color:#00B14F;"><i class="fas fa-key"></i> Gmail App Password Active</span><br><span style="font-size:0.8rem;color:var(--text-muted);font-weight:normal;">${data.manual_smtp_user || 'Configured'}</span>`;
                if (label) label.textContent = `SMTP Active (${data.manual_smtp_user || 'App Password'})`;
            } else {
                statusHtml = `<span style="color:var(--text-muted);"><i class="fas fa-times-circle"></i> Not Configured</span><br><span style="font-size:0.75rem;color:var(--text-muted);">Connect Gmail or enter App Password below</span>`;
                if (label) label.textContent = "Click to configure notification email";
            }
            if (statusDetail) statusDetail.innerHTML = statusHtml;

            if (actionsDiv) {
                actionsDiv.innerHTML = `
                    <div style="display:flex;flex-direction:column;gap:8px;">
                        <button onclick="connectSmtpGmail()" class="btn-premium" style="width:100%;padding:11px;font-size:0.85rem;font-weight:700;color:white;border-radius:10px;background:var(--primary);border-color:var(--primary);cursor:pointer;">
                            <i class="fab fa-google"></i> ${data.is_linked && !data.is_valid ? 'Re-Authorize Gmail Account' : (data.is_linked ? 'Reconnect Gmail' : 'Connect Gmail Account')}
                        </button>
                        ${data.is_linked ? `
                            <button onclick="disconnectSmtpGmail()" class="btn-premium" style="background:transparent;border:1px solid #ef4444;width:100%;padding:8px;font-size:0.8rem;font-weight:600;color:#ef4444;border-radius:8px;cursor:pointer;">
                                <i class="fas fa-unlink"></i> Disconnect Google OAuth
                            </button>
                        ` : ''}
                    </div>

                    <div style="margin-top:14px;padding-top:14px;border-top:1px solid var(--border);">
                        <div style="font-size:0.8rem;font-weight:700;color:var(--text-main);margin-bottom:6px;display:flex;align-items:center;gap:6px;">
                            <i class="fas fa-shield-alt" style="color:var(--primary);"></i> Permanent Option: Gmail App Password
                        </div>
                        <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:10px;line-height:1.4;">
                            Generate a 16-character password in Google Account (Security &gt; 2-Step Verification &gt; App Passwords) for 100% reliable, never-expiring email sending.
                        </div>
                        <div style="display:flex;flex-direction:column;gap:8px;">
                            <input id="manualSmtpEmail" type="email" maxlength="60" placeholder="Your Gmail address (e.g. yourname@gmail.com)" style="width:100%;padding:10px 12px;background:var(--surface);border:1px solid var(--border);border-radius:8px;color:var(--text-main);font-size:0.8rem;" value="${data.manual_smtp_user || (data.email || '')}">
                            <input id="manualSmtpPass" type="password" maxlength="64" placeholder="16-character Gmail App Password" style="width:100%;padding:10px 12px;background:var(--surface);border:1px solid var(--border);border-radius:8px;color:var(--text-main);font-size:0.8rem;">
                            <button onclick="saveManualSmtpSettings()" class="btn-premium" style="width:100%;padding:10px;font-size:0.8rem;font-weight:700;background:rgba(255,255,255,0.08);border:1px solid var(--border);color:var(--text-main);border-radius:8px;cursor:pointer;">
                                <i class="fas fa-save"></i> Save Gmail App Password
                            </button>
                        </div>
                    </div>

                    <div style="margin-top:14px;padding-top:14px;border-top:1px solid var(--border);">
                        <div style="font-size:0.8rem;font-weight:700;color:var(--text-main);margin-bottom:6px;">
                            <i class="fas fa-paper-plane" style="color:var(--primary);"></i> Test Email Sending
                        </div>
                        <div style="display:flex;gap:6px;">
                            <input id="testEmailRecipient" type="email" maxlength="60" placeholder="Enter recipient email..." style="flex:1;padding:8px 12px;background:var(--surface);border:1px solid var(--border);border-radius:8px;color:var(--text-main);font-size:0.8rem;" value="${data.email || ''}">
                            <button onclick="sendTestNotificationEmail()" class="btn-premium" style="padding:8px 14px;font-size:0.8rem;font-weight:700;background:var(--primary);color:white;border-radius:8px;cursor:pointer;">
                                Test Send
                            </button>
                        </div>
                        <div id="testEmailFeedback" style="font-size:0.75rem;margin-top:6px;"></div>
                    </div>
                `;
            }
        } catch (e) {
            if (statusDetail) statusDetail.textContent = "Error loading status";
        }
    }

    async function saveManualSmtpSettings() {
        const email = document.getElementById('manualSmtpEmail')?.value?.trim();
        const appPass = document.getElementById('manualSmtpPass')?.value?.trim();
        if (!email || !appPass) {
            alert('Please provide both your Gmail address and 16-character App Password.');
            return;
        }
        try {
            const res = await fetch(API_BASE + '/api/admin/smtp/manual-save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email, app_password: appPass })
            });
            const d = await res.json();
            if (res.ok && d.success) {
                alert('Gmail App Password saved and verified successfully!');
                loadSmtpStatus();
            } else {
                alert('Failed to save App Password: ' + (d.error || 'Unknown error'));
            }
        } catch (e) {
            alert('Error saving App Password: ' + e.message);
        }
    }

    async function sendTestNotificationEmail() {
        const recipient = document.getElementById('testEmailRecipient')?.value?.trim();
        const fb = document.getElementById('testEmailFeedback');
        if (!recipient) {
            alert('Please enter a recipient email.');
            return;
        }
        if (fb) fb.innerHTML = '<span style="color:var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Sending test email...</span>';
        try {
            const res = await fetch(API_BASE + '/api/admin/smtp/test-send?email=' + encodeURIComponent(recipient));
            const d = await res.json();
            if (res.ok && d.success) {
                if (fb) fb.innerHTML = `<span style="color:#00B14F;"><i class="fas fa-check"></i> ${d.message}</span>`;
            } else {
                if (fb) fb.innerHTML = `<span style="color:#ef4444;"><i class="fas fa-times"></i> ${d.error || 'Failed to send'}</span>`;
            }
        } catch (e) {
            if (fb) fb.innerHTML = `<span style="color:#ef4444;">Error: ${e.message}</span>`;
        }
    }

    async function connectSmtpGmail() {
        try {
            const res = await fetch(API_BASE + '/api/admin/smtp/auth-url');
            const data = await res.json();
            if (data.auth_url) {
                const width = 500, height = 600;
                const left = (window.screen.width - width) / 2;
                const top = (window.screen.height - height) / 2;
                window.open(data.auth_url, 'google_smtp_oauth', `width=${width},height=${height},top=${top},left=${left}`);
            }
        } catch (e) {
            alert("Failed to initiate authentication link.");
        }
    }

    async function disconnectSmtpGmail() {
        if (!confirm("Are you sure you want to disconnect this email address? Notifications will fallback to default SMTP settings.")) return;
        try {
            const res = await fetch(API_BASE + '/api/admin/smtp/disconnect', { method: 'POST' });
            if (res.ok) {
                loadSmtpStatus();
            } else {
                alert("Failed to disconnect Gmail account.");
            }
        } catch (e) {
            alert("Error disconnecting account.");
        }
    }

    window.addEventListener("message", function(event) {
        if (event.data === "smtp_oauth_success") {
            loadSmtpStatus();
        }
    }, false);

    // Bind exports to window
    window.toggleSmtpConfigModal = toggleSmtpConfigModal;
    window.closeSmtpConfigModal = closeSmtpConfigModal;
    window.closeSmtpConfigModalBackdrop = closeSmtpConfigModalBackdrop;
    window.connectSmtpGmail = connectSmtpGmail;
    window.disconnectSmtpGmail = disconnectSmtpGmail;
    window.loadSmtpStatus = loadSmtpStatus;
    window.saveManualSmtpSettings = saveManualSmtpSettings;
    window.sendTestNotificationEmail = sendTestNotificationEmail;

    // Load status after init
    setTimeout(function() {
        if (window.adminAuth && window.adminAuth.isLoggedIn && window.adminAuth.isLoggedIn()) {
            loadSmtpStatus();
        }
    }, 2000);

