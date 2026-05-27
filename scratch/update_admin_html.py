import re

with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# Replace the showBookingDetail function to fetch and display license details
booking_view_match = re.search(r'view\(id\) \{.*?\n(.*?const content = `)', content, re.DOTALL)
if booking_view_match:
    print("Found booking view function")

    # Let's write a replacement for the view(id) function.
    # It seems to be inside `const Bookings = { ... view(id) { ... } ... }`
    # Let's use Python's replace to add a fetch call inside view(id)
    
    old_view_start = """
        view(id) {
            const b = this.data.find(x => x.id === id);
            if (!b) return;

            const isCancellable = ['Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing'].includes(b.status);
            const isApprovable = (b.status === 'Pending');

            const content = `"""

    new_view_start = """
        async view(id) {
            const b = this.data.find(x => x.id === id);
            if (!b) return;

            const isCancellable = ['Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing'].includes(b.status);
            const isApprovable = (b.status === 'Pending');

            // Fetch license details
            let licenseHtml = '<p style="font-size: 0.85rem; color: var(--text-muted);">Loading license details...</p>';
            try {
                const res = await fetch(`${API_BASE}/api/admin/bookings/${id}/license-details`);
                if (res.ok) {
                    const lData = await res.json();
                    if (lData && lData.license_number) {
                        licenseHtml = `
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
                                ${lData.license_front_url ? `<button onclick="viewLicenseImage('${lData.license_front_url}')" class="btn-outline" style="flex:1;font-size:0.75rem;padding:6px;">Front</button>` : ''}
                                ${lData.license_back_url ? `<button onclick="viewLicenseImage('${lData.license_back_url}')" class="btn-outline" style="flex:1;font-size:0.75rem;padding:6px;">Back</button>` : ''}
                            </div>
                        `;
                    } else {
                        licenseHtml = '<p style="font-size: 0.85rem; color: var(--text-muted);">No license details provided by user.</p>';
                    }
                } else {
                    licenseHtml = '<p style="font-size: 0.85rem; color: var(--danger);">Failed to load license details.</p>';
                }
            } catch (e) {
                licenseHtml = '<p style="font-size: 0.85rem; color: var(--danger);">Error loading license details.</p>';
            }

            const content = `"""

    content = content.replace(old_view_start, new_view_start)

    # Insert the block into the template
    old_insertion_point = """
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="font-size: 1rem; color: #6366f1; font-weight: 800;">Vehicle Inspections</h3>"""

    new_insertion_point = """
                    <div style="background: rgba(15, 23, 42, 0.4); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); margin-top: 5px;">
                        <h3 style="font-size: 1rem; color: #6366f1; font-weight: 800; margin-bottom: 10px;">Driver's License Details</h3>
                        <div id="bookingLicenseDetailsWrapper">
                            ${licenseHtml}
                        </div>
                    </div>

                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="font-size: 1rem; color: #6366f1; font-weight: 800;">Vehicle Inspections</h3>"""

    content = content.replace(old_insertion_point, new_insertion_point)

    with open('admin_mobile/www/index.html', 'w', encoding='latin-1') as f:
        f.write(content)
    print("SUCCESS: admin_mobile/www/index.html updated for booking view")
else:
    print("Failed to find booking view pattern")

