
    (function() {
        'use strict';

        var IS_DESKTOP = window.innerWidth >= 769;
        window.addEventListener('resize', function() {
            IS_DESKTOP = window.innerWidth >= 769;
        });

        /* ?? DASHBOARD: classify flex rows with semantic classes ?? */
        function applyDashboardGrid() {
            if (!IS_DESKTOP) return;
            var dash = document.getElementById('dashboard');
            if (!dash) return;

            // Only process rows that haven't been classified yet
            var rows = Array.from(dash.children).filter(function(el) {
                if (el.tagName !== 'DIV') return false;
                if (el.classList.contains('dash-kpi-row') ||
                    el.classList.contains('dash-chart-row') ||
                    el.classList.contains('dash-pie-row')) return false;
                var s = el.getAttribute('style') || '';
                return s.indexOf('display:flex') > -1 || s.indexOf('display:-webkit-flex') > -1;
            });

            rows.forEach(function(row, i) {
                // IMPORTANT: clear inline display so CSS takes over
                // but do NOT touch display on .tab-content elements
                row.style.removeProperty('display');
                row.style.removeProperty('margin-bottom');

                if (i === 0) row.classList.add('dash-kpi-row');
                else if (i === 1) row.classList.add('dash-chart-row');
                else if (i === 2) row.classList.add('dash-pie-row');
                else row.classList.add('dash-chart-row');

                // Remove flex:1 from children so grid sizing works
                Array.from(row.children).forEach(function(card) {
                    card.style.removeProperty('flex');
                    card.style.removeProperty('-webkit-flex');
                });
            });
        }

        /* ?? VEHICLES: convert list to grid cards ?? */
        function applyVehiclesGrid() {
            if (!IS_DESKTOP) return;
            var container = document.getElementById('vehiclesList');
            if (!container) return;
            var ul = container.querySelector('ul');
            if (!ul || ul.classList.contains('veh-desktop-grid')) return;
            ul.classList.add('veh-desktop-grid');
            // Mark each list item
            Array.from(ul.querySelectorAll('li')).forEach(function(li) {
                li.classList.add('veh-card-desktop');
                // Remove inline border-radius and border-bottom that creates list look
                li.style.removeProperty('border-radius');
                li.style.removeProperty('border-bottom');
            });
        }

        /* ?? OBSERVER: watch vehiclesList for re-renders ?? */
        function watchVehiclesList() {
            var container = document.getElementById('vehiclesList');
            if (!container) return;
            var observer = new MutationObserver(function() {
                setTimeout(applyVehiclesGrid, 50);
            });
            observer.observe(container, { childList: true, subtree: false });
        }

        /* ?? VERIFICATIONS: add desktop class to cards ?? */
        function applyVerificationsLayout() {
            if (!IS_DESKTOP) return;
            var list = document.getElementById('verificationsList');
            if (!list) return;
            // Remove inline display/grid to let CSS handle it
            list.style.removeProperty('display');
            list.style.removeProperty('gap');
            list.classList.add('veri-desktop-list');
            // Tag each stat-card child
            Array.from(list.children).forEach(function(card) {
                if (card.classList.contains('veri-desktop-card')) return;
                card.classList.add('veri-desktop-card');
            });
        }

        function watchVerificationsList() {
            var container = document.getElementById('verificationsList');
            if (!container) return;
            var observer = new MutationObserver(function() {
                setTimeout(applyVerificationsLayout, 50);
            });
            observer.observe(container, { childList: true, subtree: false });
        }

        /* ---- USER MANAGEMENT: grid layout for user cards ---- */
        function applyUserMgmtLayout() {
            if (!IS_DESKTOP) return;
            var umList = document.getElementById('umList');
            if (!umList) return;
            umList.classList.add('um-desktop-list');
            Array.from(umList.children).forEach(function(card) {
                if (card.style && card.style.display !== 'none') {
                    card.classList.add('um-desktop-card');
                }
            });
            // Fix tab: only remove bottom padding (was 100px for mobile nav bar)
            var tab = document.getElementById('users');
            if (tab) {
                tab.style.removeProperty('padding-bottom');
                tab.classList.add('users-desktop-tab');
            }
        }

        function watchUserList() {
            var container = document.getElementById('umList');
            if (!container) return;
            var observer = new MutationObserver(function() {
                setTimeout(applyUserMgmtLayout, 50);
            });
            observer.observe(container, { childList: true, subtree: false });
        }

        /* ?? INIT ?? */
        document.addEventListener('DOMContentLoaded', function() {
            applyDashboardGrid();
            watchVehiclesList();
            watchVerificationsList();
            watchUserList();
        });
        window.addEventListener('resize', function() {
            applyDashboardGrid();
            applyVehiclesGrid();
            applyVerificationsLayout();
            applyUserMgmtLayout();
        });

        // Re-apply when clicking nav items
        document.addEventListener('click', function(e) {
            var el = e.target.closest('[data-tab="dashboard"], [onclick*="dashboard"]');
            if (el) setTimeout(applyDashboardGrid, 150);
            var vel = e.target.closest('[data-tab="vehicles"], [onclick*="vehicles"]');
            if (vel) setTimeout(applyVehiclesGrid, 300);
            var verl = e.target.closest('[data-tab="verifications"], [onclick*="verifications"]');
            if (verl) setTimeout(applyVerificationsLayout, 300);
            var uml = e.target.closest('[data-tab="users"], [onclick*="users"]');
            if (uml) setTimeout(applyUserMgmtLayout, 300);
        });
    })();
    