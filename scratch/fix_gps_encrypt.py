# -*- coding: utf-8 -*-
# Updates GPS refresh() to respect encrypted state from Blynk

OLD_COORDS_BLOCK = """                const lat = parseFloat(data.v1);
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
                }"""

NEW_COORDS_BLOCK = """                const rawLat = String(data.v1 || '');
                const rawLng = String(data.v2 || '');
                const sats = data.v3 || '0';
                const isEncrypted = rawLat.includes('ENCRYPTED') || rawLat === '' || rawLat === '0';

                // Update status badge
                const badge = document.getElementById('gpsStatusBadge');
                if (badge) {
                    if (isEncrypted) {
                        badge.textContent = 'ENCRYPTED';
                        badge.style.color = '#d97706';
                    } else {
                        badge.textContent = isOnline ? 'LIVE' : 'WAITING';
                        badge.style.color = isOnline ? 'var(--success)' : 'var(--amber, #d97706)';
                    }
                }

                // Update coordinates display
                const latEl = document.getElementById('gpsLat');
                const lngEl = document.getElementById('gpsLng');
                const satsEl = document.getElementById('gpsSats');
                const upEl = document.getElementById('gpsLastUpdate');

                if (isEncrypted) {
                    // Location is encrypted - show hidden state
                    if (latEl) { latEl.textContent = '*** ENCRYPTED ***'; latEl.style.color = '#d97706'; latEl.style.fontSize = '0.7rem'; }
                    if (lngEl) { lngEl.textContent = '*** ENCRYPTED ***'; lngEl.style.color = '#d97706'; lngEl.style.fontSize = '0.7rem'; }
                    if (satsEl) { satsEl.textContent = 'Hidden'; satsEl.style.color = '#94a3b8'; }
                    if (upEl) upEl.textContent = 'Location encrypted';
                } else {
                    const lat = parseFloat(rawLat);
                    const lng = parseFloat(rawLng);
                    if (!isNaN(lat) && !isNaN(lng)) {
                        this.lat = lat;
                        this.lng = lng;
                        if (latEl) { latEl.textContent = lat.toFixed(6); latEl.style.color = ''; latEl.style.fontSize = ''; }
                        if (lngEl) { lngEl.textContent = lng.toFixed(6); lngEl.style.color = ''; lngEl.style.fontSize = ''; }
                        if (satsEl) { satsEl.textContent = sats; satsEl.style.color = ''; }
                        if (upEl) upEl.textContent = 'Updated ' + new Date().toLocaleTimeString();
                    } else {
                        if (latEl) { latEl.textContent = '--'; latEl.style.color = ''; }
                        if (lngEl) { lngEl.textContent = '--'; lngEl.style.color = ''; }
                        if (satsEl) satsEl.textContent = '0';
                        if (upEl) upEl.textContent = 'No GPS fix';
                    }
                }"""

for path in ['admin_mobile/www/index.html', 'admin_app/index.html']:
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        c = f.read()
    if OLD_COORDS_BLOCK in c:
        c = c.replace(OLD_COORDS_BLOCK, NEW_COORDS_BLOCK, 1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)
        print(path, ': Done')
    else:
        print(path, ': OLD BLOCK NOT FOUND')
