import re

with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# Replace openModal and _renderModal
old_openModal = """
        async openModal(userId) {
            document.getElementById('umModal').style.display = 'block';
            document.getElementById('umModalContent').innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:1.5rem;"></i></div>';
            try {
                const res = await apiFetch(`admin/users/${userId}`);
                const u = await res.json();
                if (!res.ok) throw new Error(u.error || 'Failed to load user');
                this._renderModal(u);
            } catch (e) {
                document.getElementById('umModalContent').innerHTML = `<div style="color:var(--danger);text-align:center;padding:20px;">${e.message}</div>`;
            }
        },

        _renderModal(u) {"""

new_openModal = """
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

        _renderModal(u, lData) {"""

content = content.replace(old_openModal, new_openModal)


old_stats_end = """
            <!-- Stats -->
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:20px;">
                <div style="background:rgba(0,0,0,0.2);border-radius:14px;padding:12px;text-align:center;">
                    <div style="font-size:1.2rem;font-weight:900;color:var(--primary-light);">${u.total_bookings || 0}</div>
                    <div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Bookings</div>
                </div>
                <div style="background:rgba(0,0,0,0.2);border-radius:14px;padding:12px;text-align:center;">
                    <div style="font-size:1.2rem;font-weight:900;color:var(--success);">${u.completed_bookings || 0}</div>
                    <div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Completed</div>
                </div>
                <div style="background:rgba(0,0,0,0.2);border-radius:14px;padding:12px;text-align:center;">
                    <div style="font-size:1rem;font-weight:900;color:var(--amber);">&#8369;${(u.total_spent||0).toLocaleString()}</div>
                    <div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Spent</div>
                </div>
            </div>
"""

new_stats_end = old_stats_end + """
            <!-- License Details Section -->
            <div style="background: rgba(15, 23, 42, 0.4); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px;">
                <h3 style="font-size: 1rem; color: #6366f1; font-weight: 800; margin-bottom: 10px;">Driver's License Details</h3>
                ${lData && lData.license_number ? `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;">
                        <div><span style="color:var(--text-muted)">License #:</span> <span style="color:white;font-weight:600">${lData.license_number}</span></div>
                        <div><span style="color:var(--text-muted)">Expiry:</span> <span style="color:white;font-weight:600">${lData.expiry_date || '-'}</span></div>
                        <div><span style="color:var(--text-muted)">Class:</span> <span style="color:white;font-weight:600">${lData.license_class || '-'}</span></div>
                        <div><span style="color:var(--text-muted)">Country/State:</span> <span style="color:white;font-weight:600">${lData.issuing_country_state || '-'}</span></div>
                    </div>
                    <div style="margin-top: 10px; font-size: 0.85rem;">
                        <div><span style="color:var(--text-muted)">Full Name:</span> <span style="color:white;font-weight:600">${lData.full_name || '-'}</span></div>
                        <div><span style="color:var(--text-muted)">DOB:</span> <span style="color:white;font-weight:600">${lData.date_of_birth || '-'}</span></div>
                    </div>
                    <div style="margin-top: 10px; font-size: 0.85rem; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <p style="color:var(--text-muted);font-weight:700;margin-bottom:5px;">Emergency Contact</p>
                        <div><span style="color:var(--text-muted)">Name:</span> <span style="color:white;font-weight:600">${lData.emergency_contact_name || '-'}</span></div>
                        <div><span style="color:var(--text-muted)">Phone:</span> <span style="color:white;font-weight:600">${lData.emergency_contact_phone || '-'}</span></div>
                        <div><span style="color:var(--text-muted)">Rel:</span> <span style="color:white;font-weight:600">${lData.emergency_contact_relationship || '-'}</span></div>
                    </div>
                    <div style="display:flex; gap:10px; margin-top: 10px;">
                        ${lData.license_front_url ? `<button onclick="viewLicenseImage('${lData.license_front_url}')" class="btn-outline" style="flex:1;font-size:0.75rem;padding:6px;">Front Image</button>` : ''}
                        ${lData.license_back_url ? `<button onclick="viewLicenseImage('${lData.license_back_url}')" class="btn-outline" style="flex:1;font-size:0.75rem;padding:6px;">Back Image</button>` : ''}
                    </div>
                ` : `<p style="font-size: 0.85rem; color: var(--text-muted);">No license details provided by user.</p>`}
            </div>
"""

content = content.replace(old_stats_end, new_stats_end)

with open('admin_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(content)

print("SUCCESS: user view updated")
