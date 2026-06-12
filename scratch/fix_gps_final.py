# -*- coding: utf-8 -*-
# Updates GPS module in both admin files to use correct Blynk multi-pin API

NEW_JS = """    // --- GPS MODULE (Blynk IoT) ---
    const GPS = {
        BLYNK_TOKEN: '6fub_AeSZfywBab9j-d7KRXWKFPMwIxz',
        BLYNK_SERVER: 'sgp1.blynk.cloud',
        lat: null,
        lng: null,
        lastActive: 0,
        timer: null,

        async refresh() {
            try {
                // Fetch all pins in a single request (same as car-rental site)
                const res = await fetch(
                    `https://${this.BLYNK_SERVER}/external/api/get?token=${this.BLYNK_TOKEN}&v1&v2&v3&v4&_=${Date.now()}`
                );
                if (!res.ok) { this._showOffline('Device offline'); return; }

                const data = await res.json();
                const now = Date.now();

                // V4 is the heartbeat pin - update lastActive if it changed
                if (data.v4 !== undefined) this.lastActive = now;

                // Check if device is online (within 20 seconds)
                const isOnline = (now - this.lastActive) < 20000;
                if (!isOnline && this.lastActive > 0) { this._showOffline('Device offline'); return; }

                const lat = parseFloat(data.v1);
                const lng = parseFloat(data.v2);
                const sats = data.v3 || '0';

                // Update status badge
                const badge = document.getElementById('gpsStatusBadge');
                if (badge) {
                    badge.textContent = isOnline ? 'LIVE' : 'WAITING';
                    badge.style.color = isOnline ? 'var(--success)' : 'var(--amber, #d97706)';
                }

                // Update coordinates display
                const latEl = document.getElementById('gpsLat');
                const lngEl = document.getElementById('gpsLng');
                const satsEl = document.getElementById('gpsSats');
                const upEl = document.getElementById('gpsLastUpdate');

                if (!isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0) {
                    this.lat = lat;
                    this.lng = lng;
                    if (latEl) latEl.textContent = lat.toFixed(6);
                    if (lngEl) lngEl.textContent = lng.toFixed(6);
                    if (satsEl) satsEl.textContent = sats;
                    if (upEl) upEl.textContent = 'Updated ' + new Date().toLocaleTimeString();
                } else {
                    if (latEl) latEl.textContent = '--';
                    if (lngEl) lngEl.textContent = '--';
                    if (satsEl) satsEl.textContent = '0';
                    if (upEl) upEl.textContent = 'No GPS fix';
                }

            } catch(e) { this._showOffline('Connection error'); }
        },

        _showOffline(reason) {
            const badge = document.getElementById('gpsStatusBadge');
            if (badge) { badge.textContent = 'OFFLINE'; badge.style.color = 'var(--text-muted)'; }
            const upEl = document.getElementById('gpsLastUpdate');
            if (upEl) upEl.textContent = reason || 'No signal';
        },

        openMap() {
            window.open('https://car-rental-inlaguna.vercel.app/', '_blank');
        },

        startLive() {
            this.refresh();
            if (this.timer) clearInterval(this.timer);
            this.timer = setInterval(() => this.refresh(), 10000);
        },

        stopLive() {
            if (this.timer) { clearInterval(this.timer); this.timer = null; }
        }
    };

"""

NEW_HTML_MOBILE = """    <!-- GPS TRACKING TAB -->
    <div id="gps" class="tab-content" style="display: none;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
            <h1 class="page-title" style="margin:0;">GPS Tracking</h1>
            <span id="gpsStatusBadge" style="font-size:0.6rem;padding:4px 10px;background:rgba(0,177,79,0.1);color:var(--success);border-radius:20px;font-weight:800;border:1px solid currentColor;">LIVE</span>
        </div>

        <!-- Live Map iframe -->
        <div class="stat-card" style="padding:0;overflow:hidden;height:320px;position:relative;border-radius:20px;border:1px solid var(--border);margin-bottom:16px;">
            <iframe id="blynkMapFrame" src="https://car-rental-inlaguna.vercel.app/" style="width:100%;height:100%;border:none;" allow="geolocation" allowfullscreen></iframe>
            <div style="position:absolute;top:10px;left:10px;z-index:10;background:rgba(15,23,42,0.8);backdrop-filter:blur(5px);border-radius:8px;padding:5px 10px;display:flex;align-items:center;gap:6px;">
                <span id="gpsLiveDot" style="width:7px;height:7px;background:#00B14F;border-radius:50%;animation:pulse 1.5s infinite;display:inline-block;"></span>
                <span style="font-size:0.68rem;font-weight:700;color:white;">Live Tracker</span>
            </div>
            <div style="position:absolute;bottom:10px;right:10px;z-index:10;display:flex;gap:6px;">
                <button onclick="GPS.refresh()" style="background:rgba(15,23,42,0.85);backdrop-filter:blur(5px);border:1px solid rgba(255,255,255,0.15);color:white;padding:7px 11px;border-radius:8px;font-size:0.7rem;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:4px;">
                    <i class="fas fa-sync-alt"></i>
                </button>
                <button onclick="GPS.openMap()" style="background:rgba(15,23,42,0.85);backdrop-filter:blur(5px);border:1px solid rgba(255,255,255,0.15);color:white;padding:7px 11px;border-radius:8px;font-size:0.7rem;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:4px;">
                    <i class="fas fa-external-link-alt"></i> Full Map
                </button>
            </div>
        </div>

        <!-- Live Coordinates -->
        <div class="stat-card" style="padding:14px;margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <h3 style="font-size:0.85rem;font-weight:700;color:var(--text-main);">Live Coordinates</h3>
                <span id="gpsLastUpdate" style="font-size:0.65rem;color:var(--text-muted);">Fetching...</span>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
                <div style="background:var(--surface-container);border-radius:10px;padding:10px;text-align:center;">
                    <div style="font-size:0.58rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:3px;">Latitude</div>
                    <div id="gpsLat" style="font-size:0.85rem;font-weight:800;color:var(--text-main);">--</div>
                </div>
                <div style="background:var(--surface-container);border-radius:10px;padding:10px;text-align:center;">
                    <div style="font-size:0.58rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:3px;">Longitude</div>
                    <div id="gpsLng" style="font-size:0.85rem;font-weight:800;color:var(--text-main);">--</div>
                </div>
                <div style="background:var(--surface-container);border-radius:10px;padding:10px;text-align:center;">
                    <div style="font-size:0.58rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:3px;">Satellites</div>
                    <div id="gpsSats" style="font-size:0.85rem;font-weight:800;color:var(--primary);">--</div>
                </div>
            </div>
        </div>
    </div>

"""

NEW_HTML_APP = """    <!-- GPS TRACKING TAB -->



    <div id="gps" class="tab-content" style="display: none;">



        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
            <h1 class="page-title" style="margin:0;">GPS Tracking</h1>
            <span id="gpsStatusBadge" style="font-size:0.6rem;padding:4px 10px;background:rgba(0,177,79,0.1);color:var(--success);border-radius:20px;font-weight:800;border:1px solid currentColor;">LIVE</span>
        </div>

        <div class="chart-card" style="padding:0;overflow:hidden;height:400px;position:relative;margin-bottom:20px;">
            <iframe id="blynkMapFrame" src="https://car-rental-inlaguna.vercel.app/" style="width:100%;height:100%;border:none;" allow="geolocation" allowfullscreen></iframe>
            <div style="position:absolute;top:14px;left:14px;z-index:10;background:rgba(15,23,42,0.8);backdrop-filter:blur(5px);border-radius:10px;padding:7px 14px;display:flex;align-items:center;gap:8px;">
                <span style="width:8px;height:8px;background:#00B14F;border-radius:50%;animation:pulse 1.5s infinite;display:inline-block;"></span>
                <span style="font-size:0.72rem;font-weight:700;color:white;">Live Tracker</span>
            </div>
            <div style="position:absolute;bottom:14px;right:14px;z-index:10;display:flex;gap:8px;">
                <button onclick="GPS.refresh()" style="background:rgba(15,23,42,0.85);backdrop-filter:blur(5px);border:1px solid rgba(255,255,255,0.15);color:white;padding:9px 14px;border-radius:10px;font-size:0.75rem;font-weight:600;cursor:pointer;">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
                <button onclick="GPS.openMap()" style="background:rgba(15,23,42,0.85);backdrop-filter:blur(5px);border:1px solid rgba(255,255,255,0.15);color:white;padding:9px 14px;border-radius:10px;font-size:0.75rem;font-weight:600;cursor:pointer;">
                    <i class="fas fa-external-link-alt"></i> Full Map
                </button>
            </div>
        </div>

        <div class="chart-card" style="padding:20px;margin-bottom:20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                <h3 style="font-size:0.9rem;font-weight:700;color:var(--text-main);">Live Coordinates</h3>
                <span id="gpsLastUpdate" style="font-size:0.7rem;color:var(--text-muted);">Fetching...</span>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;">
                <div style="background:var(--surface-container);border-radius:12px;padding:14px;border:1px solid var(--border);text-align:center;">
                    <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:4px;">Latitude</div>
                    <div id="gpsLat" style="font-size:1rem;font-weight:800;color:var(--text-main);">--</div>
                </div>
                <div style="background:var(--surface-container);border-radius:12px;padding:14px;border:1px solid var(--border);text-align:center;">
                    <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:4px;">Longitude</div>
                    <div id="gpsLng" style="font-size:1rem;font-weight:800;color:var(--text-main);">--</div>
                </div>
                <div style="background:var(--surface-container);border-radius:12px;padding:14px;border:1px solid var(--border);text-align:center;">
                    <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:4px;">Satellites</div>
                    <div id="gpsSats" style="font-size:1rem;font-weight:800;color:var(--primary);">--</div>
                </div>
            </div>
        </div>



    </div>



    """

import re

# ---- admin_mobile ----
with open('admin_mobile/www/index.html', 'r', encoding='utf-8', errors='replace') as f:
    c = f.read()

# Replace GPS tab HTML
gps_start = c.find('    <!-- GPS TRACKING TAB -->')
gps_end = c.find('    <!-- INSTRUCTIONS TAB -->', gps_start)
if gps_start != -1 and gps_end != -1:
    c = c[:gps_start] + NEW_HTML_MOBILE + c[gps_end:]
    print('admin_mobile: GPS tab HTML replaced')
else:
    print('admin_mobile: GPS tab NOT FOUND', gps_start, gps_end)

# Replace GPS JS module
gps_js_start = c.find('    // --- GPS MODULE')
gps_js_end = c.find('    // --- ACTIVITY MODULE ---', gps_js_start)
if gps_js_start != -1 and gps_js_end != -1:
    c = c[:gps_js_start] + NEW_JS + c[gps_js_end:]
    print('admin_mobile: GPS JS replaced')
    print('  Activity still:', c.find('const Activity') != -1)
else:
    print('admin_mobile: GPS JS NOT FOUND', gps_js_start, gps_js_end)

with open('admin_mobile/www/index.html', 'w', encoding='utf-8') as f:
    f.write(c)

# ---- admin_app ----
with open('admin_app/index.html', 'r', encoding='utf-8', errors='replace') as f:
    c = f.read()

# Replace GPS tab HTML
gps_start = c.find('    <!-- GPS TRACKING TAB -->')
gps_end = c.find('    <!-- INSTRUCTIONS TAB -->', gps_start)
if gps_start != -1 and gps_end != -1:
    c = c[:gps_start] + NEW_HTML_APP + c[gps_end:]
    print('admin_app: GPS tab HTML replaced')
else:
    print('admin_app: GPS tab NOT FOUND', gps_start, gps_end)

# Replace GPS JS module
gps_js_start = c.find('    // --- GPS MODULE')
gps_js_end = c.find('    // --- ACTIVITY MODULE ---', gps_js_start)
if gps_js_start != -1 and gps_js_end != -1:
    c = c[:gps_js_start] + NEW_JS + c[gps_js_end:]
    print('admin_app: GPS JS replaced')
    print('  Activity still:', c.find('const Activity') != -1)
    print('  AdminChat still:', c.find('const AdminChat') != -1)
else:
    print('admin_app: GPS JS NOT FOUND', gps_js_start, gps_js_end)

with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('Done')
