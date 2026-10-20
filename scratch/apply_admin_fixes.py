import sys

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update CSS in admin_app/index.html
old_css = """        /* Mobile Landscape & Short Screen Responsiveness */
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
        }"""

new_css = """        /* Universal tab-content responsive layout & scroll anchor offset */
        .tab-content {
            scroll-margin-top: calc(76px + env(safe-area-inset-top, 0px));
            max-width: 100%;
            box-sizing: border-box;
            word-wrap: break-word;
        }

        /* Fleet Calendar scroll container base styles */
        .fleet-calendar-scroll-container,
        #fleetCalendarScrollContainer {
            overflow: auto;
            max-height: calc(100vh - 270px);
            min-height: 250px;
            background: var(--surface-solid);
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
            -webkit-overflow-scrolling: touch;
            touch-action: pan-x pan-y;
        }

        /* Mobile Landscape & Short Screen Responsiveness */
        @media (orientation: landscape) and (max-height: 550px) {
            .mobile-header {
                height: calc(44px + env(safe-area-inset-top, 0px)) !important;
                padding: env(safe-area-inset-top, 0px) 12px 0 !important;
            }
            .mobile-header .logo-wrap img {
                width: 22px !important;
                height: 22px !important;
            }
            .mobile-header .logo-wrap span {
                font-size: 0.85rem !important;
            }
            .mobile-header .admin-badge {
                padding: 1px 5px !important;
                font-size: 0.6rem !important;
            }
            .main-content {
                padding-top: calc(48px + env(safe-area-inset-top, 0px)) !important;
                padding-bottom: calc(52px + env(safe-area-inset-bottom, 0px)) !important;
                overflow-y: auto !important;
            }
            .tab-content {
                scroll-margin-top: calc(48px + env(safe-area-inset-top, 0px)) !important;
            }
            .bottom-nav {
                height: calc(46px + env(safe-area-inset-bottom, 0px)) !important;
                padding-bottom: env(safe-area-inset-bottom, 0px) !important;
            }
            .bottom-nav .nav-item span {
                display: none !important;
            }
            .bottom-nav .nav-item i {
                font-size: 1.15rem !important;
            }
            .page-title {
                font-size: 1.15rem !important;
                margin-bottom: 2px !important;
            }
            .page-subtitle {
                display: none !important;
            }

            /* Fleet Calendar Landscape Overhaul: 100% Viewport Height & Zero Scroll-Lock */
            body.fleet-calendar-active .bottom-nav,
            body:has(#fleet-calendar:not([style*="display: none"]):not([style*="display:none"])) .bottom-nav {
                display: none !important;
            }
            body.fleet-calendar-active .main-content,
            body:has(#fleet-calendar:not([style*="display: none"]):not([style*="display:none"])) .main-content {
                padding-top: calc(44px + env(safe-area-inset-top, 0px)) !important;
                padding-bottom: env(safe-area-inset-bottom, 0px) !important;
                overflow-y: auto !important;
            }
            #fleet-calendar {
                padding: 4px 8px !important;
            }
            #fleet-calendar .stat-card {
                padding: 6px 10px !important;
                border-radius: 8px !important;
            }
            #fcTopBanner {
                display: none !important;
            }
            #fcSummaryBanner {
                display: none !important;
            }
            #fcToolbar {
                margin-bottom: 6px !important;
                gap: 4px !important;
                flex-wrap: nowrap !important;
                overflow-x: auto !important;
                -webkit-overflow-scrolling: touch !important;
                width: 100% !important;
                padding-bottom: 2px !important;
            }
            #fleetCalendarSearchWrap {
                min-width: 110px !important;
                width: 130px !important;
                flex-shrink: 1 !important;
            }
            #fleetCalendarSearch {
                padding: 5px 8px 5px 24px !important;
                font-size: 0.72rem !important;
            }
            #fleetCalendarMonthLabel {
                min-width: 110px !important;
                font-size: 0.76rem !important;
            }
            .fc-btn-text {
                display: none !important;
            }
            .fleet-calendar-scroll-container,
            #fleetCalendarScrollContainer {
                max-height: calc(100vh - 56px) !important;
                min-height: calc(100vh - 56px) !important;
                height: calc(100vh - 56px) !important;
                border-radius: 8px !important;
                overflow: auto !important;
                -webkit-overflow-scrolling: touch !important;
                touch-action: pan-x pan-y !important;
            }

            /* GPS Tracking Landscape Constraints */
            #gps .chart-card {
                height: calc(100vh - 120px) !important;
                min-height: 240px !important;
            }
            #gps .stat-card {
                padding: 10px 14px !important;
                margin-bottom: 12px !important;
            }

            /* Live Chat Landscape Constraints */
            #acMessages {
                height: calc(100vh - 160px) !important;
            }
        }"""

if old_css not in content:
    print("ERROR: old_css not found!")
    sys.exit(1)

content = content.replace(old_css, new_css, 1)
print("SUCCESS: CSS updated.")

# 2. Update Fleet Calendar HTML markup
old_fc_html = """        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="width:32px; height:32px; border-radius:8px; background:rgba(0,177,79,0.15); color:#00B14F; display:flex; align-items:center; justify-content:center; font-size:1rem;">
                        <i class="fas fa-calendar-alt"></i>
                    </span>
                    <h2 style="font-size: 1.25rem; font-weight: 800; color: var(--text-main); margin: 0;">Fleet Schedule & Dispatch Dashboard</h2>
                </div>
                <p style="margin: 4px 0 0; font-size: 0.75rem; color: var(--text-muted);">Real-time vehicle schedule monitoring, customer tracking, and one-stop pricing/payment manager.</p>
            </div>

            <!-- Toolbar: Month navigation, today button, search box -->
            <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                <div style="position: relative; min-width: 220px;">
                    <i class="fas fa-search" style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); font-size: 0.75rem; color: var(--text-muted);"></i>
                    <input type="text" id="fleetCalendarSearch" placeholder="Filter customer or car..." oninput="FleetCalendar.onSearch(this.value)"
                           style="width: 100%; padding: 7px 10px 7px 28px; font-size: 0.78rem; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-solid); color: var(--text-main); outline: none;">
                </div>
                <button onclick="FleetCalendar.goToToday()" class="btn-secondary" style="padding: 7px 12px; border-radius: 8px; font-size: 0.78rem; font-weight: 700; cursor: pointer; background: var(--surface-solid); border: 1px solid var(--border); color: var(--text-main);">
                    Today
                </button>
                <div style="display: flex; gap: 4px; align-items: center; background: var(--surface-solid); padding: 3px 6px; border-radius: 10px; border: 1px solid var(--border);">
                    <button onclick="FleetCalendar.prevMonth()" class="btn-primary" style="padding: 5px 10px; border-radius: 6px; font-size: 0.75rem; cursor: pointer; background: var(--primary); border: none; color: white;"><i class="fas fa-chevron-left"></i></button>
                    <span id="fleetCalendarMonthLabel" style="font-weight: 800; font-size: 0.85rem; min-width: 190px; text-align: center; color: var(--text-main);"></span>
                    <button onclick="FleetCalendar.nextMonth()" class="btn-primary" style="padding: 5px 10px; border-radius: 6px; font-size: 0.75rem; cursor: pointer; background: var(--primary); border: none; color: white;"><i class="fas fa-chevron-right"></i></button>
                </div>
                <!-- View Mode: 2 Months (Default) / 1 Month -->
                <div style="display: inline-flex; background: var(--surface-solid); padding: 2px; border-radius: 8px; border: 1px solid var(--border); gap: 2px;">
                    <button type="button" id="fcView2MonthsBtn" onclick="FleetCalendar.setViewMonths(2)" title="View 2 consecutive months in one screen" style="padding: 5px 9px; font-size: 0.74rem; font-weight: 800; border-radius: 6px; border: none; cursor: pointer; background: #00B14F; color: white;">2 Months</button>
                    <button type="button" id="fcView1MonthBtn" onclick="FleetCalendar.setViewMonths(1)" title="View single month" style="padding: 5px 9px; font-size: 0.74rem; font-weight: 700; border-radius: 6px; border: none; cursor: pointer; background: transparent; color: var(--text-muted);">1 Month</button>
                </div>
                <button onclick="FleetCalendar.refresh()" class="btn-secondary" title="Refresh Schedule" style="padding: 7px 10px; border-radius: 8px; font-size: 0.8rem; cursor: pointer; background: var(--surface-solid); border: 1px solid var(--border); color: var(--text-muted);">
                    <i class="fas fa-sync-alt"></i>
                </button>
                <button type="button" onclick="FleetCalendar.openExportModal()" class="btn-primary" title="Export Fleet Schedule & Bookings to Excel" style="padding: 7px 14px; border-radius: 8px; font-size: 0.78rem; font-weight: 700; cursor: pointer; background: #00B14F; border: none; color: white; display: flex; align-items: center; gap: 6px; box-shadow: 0 2px 6px rgba(0,177,79,0.3);">
                    <i class="fas fa-file-excel"></i> <span>Export Excel</span>
                </button>
                <button type="button" onclick="FleetCalendar.openImportModal()" class="btn-primary" title="Import Fleet Schedule & Bookings from Excel" style="padding: 7px 14px; border-radius: 8px; font-size: 0.78rem; font-weight: 700; cursor: pointer; background: #0f766e; border: none; color: white; display: flex; align-items: center; gap: 6px; box-shadow: 0 2px 6px rgba(15,118,110,0.3);">
                    <i class="fas fa-file-import"></i> <span>Import Excel</span>
                </button>
            </div>
        </div>

        <!-- Quick Summary & Instructions Banner -->
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; font-size: 0.74rem; color: var(--text-muted); flex-wrap: wrap; background: var(--surface-solid); padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border);">"""

new_fc_html = """        <div id="fcTopBanner" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="width:32px; height:32px; border-radius:8px; background:rgba(0,177,79,0.15); color:#00B14F; display:flex; align-items:center; justify-content:center; font-size:1rem;">
                        <i class="fas fa-calendar-alt"></i>
                    </span>
                    <h2 style="font-size: 1.25rem; font-weight: 800; color: var(--text-main); margin: 0;">Fleet Schedule & Dispatch Dashboard</h2>
                </div>
                <p style="margin: 4px 0 0; font-size: 0.75rem; color: var(--text-muted);">Real-time vehicle schedule monitoring, customer tracking, and one-stop pricing/payment manager.</p>
            </div>

            <!-- Toolbar: Month navigation, today button, search box -->
            <div id="fcToolbar" style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                <div id="fleetCalendarSearchWrap" style="position: relative; min-width: 220px;">
                    <i class="fas fa-search" style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); font-size: 0.75rem; color: var(--text-muted);"></i>
                    <input type="text" id="fleetCalendarSearch" placeholder="Filter customer or car..." oninput="FleetCalendar.onSearch(this.value)"
                           style="width: 100%; padding: 7px 10px 7px 28px; font-size: 0.78rem; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-solid); color: var(--text-main); outline: none;">
                </div>
                <button onclick="FleetCalendar.goToToday()" class="btn-secondary" style="padding: 7px 12px; border-radius: 8px; font-size: 0.78rem; font-weight: 700; cursor: pointer; background: var(--surface-solid); border: 1px solid var(--border); color: var(--text-main);">
                    Today
                </button>
                <div style="display: flex; gap: 4px; align-items: center; background: var(--surface-solid); padding: 3px 6px; border-radius: 10px; border: 1px solid var(--border);">
                    <button onclick="FleetCalendar.prevMonth()" class="btn-primary" style="padding: 5px 10px; border-radius: 6px; font-size: 0.75rem; cursor: pointer; background: var(--primary); border: none; color: white;"><i class="fas fa-chevron-left"></i></button>
                    <span id="fleetCalendarMonthLabel" style="font-weight: 800; font-size: 0.85rem; min-width: 190px; text-align: center; color: var(--text-main);"></span>
                    <button onclick="FleetCalendar.nextMonth()" class="btn-primary" style="padding: 5px 10px; border-radius: 6px; font-size: 0.75rem; cursor: pointer; background: var(--primary); border: none; color: white;"><i class="fas fa-chevron-right"></i></button>
                </div>
                <!-- View Mode: 2 Months (Default) / 1 Month -->
                <div style="display: inline-flex; background: var(--surface-solid); padding: 2px; border-radius: 8px; border: 1px solid var(--border); gap: 2px;">
                    <button type="button" id="fcView2MonthsBtn" onclick="FleetCalendar.setViewMonths(2)" title="View 2 consecutive months in one screen" style="padding: 5px 9px; font-size: 0.74rem; font-weight: 800; border-radius: 6px; border: none; cursor: pointer; background: #00B14F; color: white;">2 Months</button>
                    <button type="button" id="fcView1MonthBtn" onclick="FleetCalendar.setViewMonths(1)" title="View single month" style="padding: 5px 9px; font-size: 0.74rem; font-weight: 700; border-radius: 6px; border: none; cursor: pointer; background: transparent; color: var(--text-muted);">1 Month</button>
                </div>
                <button onclick="FleetCalendar.refresh()" class="btn-secondary" title="Refresh Schedule" style="padding: 7px 10px; border-radius: 8px; font-size: 0.8rem; cursor: pointer; background: var(--surface-solid); border: 1px solid var(--border); color: var(--text-muted);">
                    <i class="fas fa-sync-alt"></i>
                </button>
                <button type="button" onclick="FleetCalendar.openExportModal()" class="btn-primary" title="Export Fleet Schedule & Bookings to Excel" style="padding: 7px 14px; border-radius: 8px; font-size: 0.78rem; font-weight: 700; cursor: pointer; background: #00B14F; border: none; color: white; display: flex; align-items: center; gap: 6px; box-shadow: 0 2px 6px rgba(0,177,79,0.3);">
                    <i class="fas fa-file-excel"></i> <span class="fc-btn-text">Export Excel</span>
                </button>
                <button type="button" onclick="FleetCalendar.openImportModal()" class="btn-primary" title="Import Fleet Schedule & Bookings from Excel" style="padding: 7px 14px; border-radius: 8px; font-size: 0.78rem; font-weight: 700; cursor: pointer; background: #0f766e; border: none; color: white; display: flex; align-items: center; gap: 6px; box-shadow: 0 2px 6px rgba(15,118,110,0.3);">
                    <i class="fas fa-file-import"></i> <span class="fc-btn-text">Import Excel</span>
                </button>
            </div>
        </div>

        <!-- Quick Summary & Instructions Banner -->
        <div id="fcSummaryBanner" style="display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; font-size: 0.74rem; color: var(--text-muted); flex-wrap: wrap; background: var(--surface-solid); padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border);">"""

if old_fc_html not in content:
    print("ERROR: old_fc_html not found!")
    sys.exit(1)

content = content.replace(old_fc_html, new_fc_html, 1)
print("SUCCESS: Fleet Calendar HTML updated.")

# 3. Update fleetCalendarScrollContainer to use class
old_container = '<div id="fleetCalendarScrollContainer" style="overflow: auto; max-height: calc(100vh - 270px); min-height: 250px; background: var(--surface-solid); border-radius: 12px; border: 1px solid var(--border); box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);">'
new_container = '<div id="fleetCalendarScrollContainer" class="fleet-calendar-scroll-container">'

if old_container not in content:
    print("ERROR: old_container not found!")
    sys.exit(1)

content = content.replace(old_container, new_container, 1)
print("SUCCESS: fleetCalendarScrollContainer updated.")

# 4. Update switchTab to set body.fleet-calendar-active class
old_switch = """            const target = document.getElementById(tabId);
            if (target) {
                target.style.display = 'block';
                const mainContentEl = document.querySelector('.main-content');
                if (mainContentEl) {
                    mainContentEl.scrollTo({ top: 0, behavior: 'instant' });
                    // Lock overflow ONLY on true desktop monitors (width >= 769 AND height >= 600)
                    if (tabId === 'fleet-calendar' && window.innerWidth >= 769 && window.innerHeight >= 600) {
                        mainContentEl.style.overflowY = 'hidden';
                    } else {
                        mainContentEl.style.overflowY = 'auto';
                    }
                }"""

new_switch = """            const target = document.getElementById(tabId);
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
                }"""

if old_switch not in content:
    print("ERROR: old_switch not found!")
    sys.exit(1)

content = content.replace(old_switch, new_switch, 1)
print("SUCCESS: switchTab updated.")

# 5. Update GPS Map HTML markup to include touch overlay & toggle button
old_gps_frame = """        <div class="chart-card" style="padding:0;overflow:hidden;height:min(580px, calc(100vh - 200px));min-height:460px;position:relative;margin-bottom:24px;border-radius:16px;">
            <iframe id="blynkMapFrame" src="about:blank" data-src="https://car-rental-inlaguna.vercel.app/" loading="lazy" style="width:100%;height:100%;border:none;display:block;" allow="geolocation" allowfullscreen></iframe>
        </div>"""

new_gps_frame = """        <div class="chart-card" style="padding:0;overflow:hidden;height:min(580px, calc(100vh - 200px));min-height:460px;position:relative;margin-bottom:24px;border-radius:16px;">
            <div id="gpsMapWrapper" style="position:relative; width:100%; height:100%;">
                <iframe id="blynkMapFrame" src="about:blank" data-src="https://car-rental-inlaguna.vercel.app/" loading="lazy" style="width:100%;height:100%;border:none;display:block;pointer-events:none;" allow="geolocation" allowfullscreen></iframe>
                <div id="gpsMapTouchOverlay" style="position:absolute; inset:0; z-index:10; display:flex; align-items:center; justify-content:center; background:rgba(0,0,0,0.08); cursor:pointer;" onclick="if(window.GPS)GPS.toggleMapInteractive(true)">
                    <div style="background:rgba(15,23,42,0.85); color:white; padding:8px 16px; border-radius:20px; font-size:0.75rem; font-weight:700; display:flex; align-items:center; gap:6px; box-shadow:0 4px 12px rgba(0,0,0,0.3); backdrop-filter:blur(4px); border:1px solid rgba(255,255,255,0.15);">
                        <i class="fas fa-hand-pointer" style="color:var(--primary);"></i> Tap to Interact with Map
                    </div>
                </div>
                <button id="gpsMapLockBtn" type="button" style="display:none; position:absolute; top:12px; right:12px; z-index:12; background:rgba(15,23,42,0.85); color:white; border:1px solid rgba(255,255,255,0.2); padding:6px 12px; border-radius:8px; font-size:0.72rem; font-weight:700; cursor:pointer;" onclick="if(window.GPS)GPS.toggleMapInteractive(false)">
                    <i class="fas fa-lock"></i> Exit Map Mode
                </button>
            </div>
        </div>"""

if old_gps_frame not in content:
    print("ERROR: old_gps_frame not found!")
    sys.exit(1)

content = content.replace(old_gps_frame, new_gps_frame, 1)
print("SUCCESS: GPS map frame markup updated.")

# 6. Add toggleMapInteractive to GPS JS object
old_gps_init = """        async init() {
            const frame = document.getElementById('blynkMapFrame');
            if (frame && (!frame.src || frame.src === 'about:blank' || frame.src.endsWith('about:blank'))) {
                frame.src = frame.getAttribute('data-src') || 'https://car-rental-inlaguna.vercel.app/';
            }
            await this.loadFleetVehicles();
            await this.loadLastKnownLocationFromDB();
        },"""

new_gps_init = """        toggleMapInteractive(enable) {
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
        },"""

if old_gps_init not in content:
    print("ERROR: old_gps_init not found!")
    sys.exit(1)

content = content.replace(old_gps_init, new_gps_init, 1)
print("SUCCESS: GPS toggleMapInteractive added.")

# Write back to admin_app/index.html
with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("ALL ADMIN INDEX PATCHES APPLIED SUCCESSFULLY!")
