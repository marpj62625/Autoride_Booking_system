# -*- coding: utf-8 -*-
# Safe GPS module replacement for admin_app - only replaces GPS section, leaves everything else intact

with open('admin_app/index.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# ---- 1. Replace GPS tab HTML ----
gps_html_start = content.find('    <!-- GPS TRACKING TAB -->')
gps_html_end = content.find('    <!-- INSTRUCTIONS TAB -->', gps_html_start)

if gps_html_start == -1 or gps_html_end == -1:
    print('ERROR: GPS tab HTML boundaries not found')
else:
    new_gps_html = '''    <!-- GPS TRACKING TAB -->



    <div id="gps" class="tab-content" style="display: none;">



        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
            <h1 class="page-title" style="margin:0;">GPS Tracking</h1>
            <span id="gpsStatusBadge" style="font-size:0.6rem;padding:4px 10px;background:rgba(0,177,79,0.1);color:var(--success);border-radius:20px;font-weight:800;border:1px solid currentColor;">LIVE</span>
        </div>

        <div class="chart-card" style="padding:0;overflow:hidden;height:400px;position:relative;margin-bottom:20px;">
            <iframe id="blynkMapFrame" src="about:blank" style="width:100%;height:100%;border:none;" allowfullscreen></iframe>
            <div style="position:absolute;top:14px;left:14px;z-index:10;background:rgba(15,23,42,0.8);backdrop-filter:blur(5px);border-radius:10px;padding:7px 14px;display:flex;align-items:center;gap:8px;">
                <span style="width:8px;height:8px;background:#00B14F;border-radius:50%;animation:pulse 1.5s infinite;display:inline-block;"></span>
                <span style="font-size:0.72rem;font-weight:700;color:white;">Blynk IoT - Live</span>
            </div>
            <div style="position:absolute;bottom:14px;right:14px;z-index:10;display:flex;gap:8px;">
                <button onclick="GPS.refresh()" style="background:rgba(15,23,42,0.85);backdrop-filter:blur(5px);border:1px solid rgba(255,255,255,0.15);color:white;padding:9px 14px;border-radius:10px;font-size:0.75rem;font-weight:600;cursor:pointer;"><i class="fas fa-sync-alt"></i> Refresh</button>
                <button onclick="GPS.openBlynk()" style="background:rgba(15,23,42,0.85);backdrop-filter:blur(5px);border:1px solid rgba(255,255,255,0.15);color:white;padding:9px 14px;border-radius:10px;font-size:0.75rem;font-weight:600;cursor:pointer;"><i class="fas fa-external-link-alt"></i> Open Map</button>
            </div>
        </div>

        <div class="chart-card" style="padding:20px;margin-bottom:20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                <h3 style="font-size:0.9rem;font-weight:700;color:var(--text-main);">Vehicle Location</h3>
                <span id="gpsLastUpdate" style="font-size:0.7rem;color:var(--text-muted);">Fetching...</span>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
                <div style="background:var(--surface-container);border-radius:12px;padding:14px;border:1px solid var(--border);">
                    <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:4px;">Latitude</div>
                    <div id="gpsLat" style="font-size:1.1rem;font-weight:800;color:var(--text-main);">--</div>
                </div>
                <div style="background:var(--surface-container);border-radius:12px;padding:14px;border:1px solid var(--border);">
                    <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:4px;">Longitude</div>
                    <div id="gpsLng" style="font-size:1.1rem;font-weight:800;color:var(--text-main);">--</div>
                </div>
            </div>
        </div>



    </div>



    '''
    content = content[:gps_html_start] + new_gps_html + content[gps_html_end:]
    print('GPS tab HTML replaced, new length:', len(content))

# ---- 2. Replace only the GPS JS MODULE (stop before Activity) ----
gps_js_start = content.find('    // --- GPS MODULE ---')
gps_js_end = content.find('    // --- ACTIVITY MODULE ---', gps_js_start)

if gps_js_start == -1 or gps_js_end == -1:
    print('ERROR: GPS JS boundaries not found. start:', gps_js_start, 'end:', gps_js_end)
else:
    new_gps_js = '''    // --- GPS MODULE (Blynk IoT) ---
    const GPS = {
        BLYNK_TOKEN: '6fub_AeSZfywBab9j-d7KRXWKFPMwIxz',
        BLYNK_SERVER: 'sgp1.blynk.cloud',
        lat: null,
        lng: null,
        timer: null,

        async refresh() {
            try {
                const [latRes, lngRes] = await Promise.all([
                    fetch(`https://${this.BLYNK_SERVER}/external/api/get?token=${this.BLYNK_TOKEN}&V0`),
                    fetch(`https://${this.BLYNK_SERVER}/external/api/get?token=${this.BLYNK_TOKEN}&V1`)
                ]);
                const lat = parseFloat(await latRes.text());
                const lng = parseFloat(await lngRes.text());

                if (!isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0) {
                    this.lat = lat; this.lng = lng;
                    const frame = document.getElementById('blynkMapFrame');
                    if (frame) frame.src = `https://maps.google.com/maps?q=${lat},${lng}&z=16&output=embed`;
                    const latEl = document.getElementById('gpsLat');
                    const lngEl = document.getElementById('gpsLng');
                    const upEl = document.getElementById('gpsLastUpdate');
                    if (latEl) latEl.textContent = lat.toFixed(6);
                    if (lngEl) lngEl.textContent = lng.toFixed(6);
                    if (upEl) upEl.textContent = 'Updated ' + new Date().toLocaleTimeString();
                    const badge = document.getElementById('gpsStatusBadge');
                    if (badge) { badge.textContent = 'LIVE'; badge.style.color = 'var(--success)'; }
                } else {
                    this._showOffline();
                }
            } catch(e) { this._showOffline(); }
        },

        _showOffline() {
            const badge = document.getElementById('gpsStatusBadge');
            if (badge) { badge.textContent = 'OFFLINE'; badge.style.color = 'var(--text-muted)'; }
            const upEl = document.getElementById('gpsLastUpdate');
            if (upEl) upEl.textContent = 'No signal';
        },

        openBlynk() {
            if (this.lat && this.lng) {
                window.open(`https://maps.google.com/maps?q=${this.lat},${this.lng}&z=16`, '_blank');
            } else {
                window.open(`https://${this.BLYNK_SERVER}`, '_blank');
            }
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


    '''
    content = content[:gps_js_start] + new_gps_js + content[gps_js_end:]
    print('GPS JS module replaced safely')
    print('Activity still present:', content.find('const Activity') != -1)
    print('AdminChat still present:', content.find('const AdminChat') != -1)

with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done. Final length:', len(content))
