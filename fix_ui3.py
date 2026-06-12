import re

with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# First fix the header title
old_modal_header = '''            <div style="position: relative; display: flex; justify-content: center; align-items: center; margin-bottom: 24px; padding-bottom: 15px; border-bottom: 1px solid var(--border);">
                <button onclick="document.getElementById('bookingDetailsModal').style.display='none'" style="position: absolute; left: 0; background: transparent; border: none; color: var(--text-main); font-size: 1.2rem; padding: 5px;"><i class="fas fa-times"></i></button>
                <h2 style="font-size: 1.1rem; font-weight: 700; color: var(--text-main); margin: 0;">Booking Details</h2>
            </div>'''
new_modal_header = '''            <div style="position: relative; display: flex; justify-content: center; align-items: center; margin-bottom: 24px; padding-bottom: 15px; border-bottom: 1px solid rgba(0,0,0,0.05);">
                <button onclick="document.getElementById('bookingDetailsModal').style.display='none'" style="position: absolute; left: 0; background: transparent; border: none; color: #1e293b; font-size: 1.2rem; padding: 5px;"><i class="fas fa-times"></i></button>
                <h2 style="font-size: 1.1rem; font-weight: 700; color: #0f172a; margin: 0;">Booking Details</h2>
            </div>'''
content = content.replace(old_modal_header, new_modal_header)

old_license = '''            // Fetch license details for this booking
            let licenseHtml = '<p style=\"font-size: 0.85rem; color: var(--text-muted);\">No license details available.</p>';
            try {
                const licRes = await fetch(`${API_BASE}/api/admin/bookings/${id}/license-details`);
                if (licRes.ok) {
                    const lData = await licRes.json();
                    if (lData && lData.license_number) {
                        licenseHtml = `
                            <div style=\"margin-bottom: 20px; font-size: 0.95rem; line-height: 1.6; color: var(--text-main);\">
                                <div>Full Name: ${lData.full_name || 'N/A'}</div>
                                <div>DOB: ${lData.date_of_birth || 'N/A'}</div>
                                <div>License #: ${lData.license_number}</div>
                                <div>Expiry: ${lData.expiry_date || 'N/A'}</div>
                            </div>
                            <div style=\"display:flex; gap:10px; margin-top: 10px;\">
                                <button onclick=\"viewLicenseImage('${lData.license_front_url}')\" ${!lData.license_front_url ? 'disabled' : ''} style=\"flex:1;padding:12px;font-size:0.9rem;border-radius:8px;border:1px solid var(--border);background:var(--surface-container);color:var(--text-muted);font-weight:600;\">Front Image</button>
                                <button onclick=\"viewLicenseImage('${lData.license_back_url}')\" ${!lData.license_back_url ? 'disabled' : ''} style=\"flex:1;padding:12px;font-size:0.9rem;border-radius:8px;border:1px solid var(--border);background:var(--surface-container);color:var(--text-muted);font-weight:600;\">Back Image</button>
                            </div>
                            </div> <!-- close license wrapper -->
                            <div style=\"margin-top: 20px; font-size: 0.95rem; line-height: 1.6; color: var(--text-main);\">
                                <h3 style=\"font-size: 1rem; color: var(--text-main); font-weight: 800; margin-bottom: 5px;\">Emergency Contact</h3>
                                <div>Name: ${lData.emergency_contact_name || 'N/A'}</div>
                                <div>Phone: ${lData.emergency_contact_phone || 'N/A'}</div>
                                <div>Rel: ${lData.emergency_contact_relation || 'N/A'}</div>
                            </div>
                            <!-- open dummy div to balance closing tag in main template -->
                            <div style=\"display:none\">`;
                    }
                }
            } catch (e) { console.error('License fetch error:', e); }'''

new_license = '''            // Fetch license details for this booking
            let licenseHtml = '<p style=\"font-size: 0.85rem; color: var(--text-muted);\">No license details available.</p>';
            try {
                const licRes = await fetch(`${API_BASE}/api/admin/bookings/${id}/license-details`);
                if (licRes.ok) {
                    const lData = await licRes.json();
                    if (lData && lData.license_number) {
                        licenseHtml = `
                            <div style=\"display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;\">
                                <div><span style=\"color:#94a3b8\">License #:</span> <span style=\"color:white;font-weight:600\">${lData.license_number}</span></div>
                                <div><span style=\"color:#94a3b8\">Expiry:</span> <span style=\"color:white;font-weight:600\">${lData.expiry_date || 'N/A'}</span></div>
                                <div><span style=\"color:#94a3b8\">Class:</span> <span style=\"color:white;font-weight:600\">${lData.license_class || 'N/A'}</span></div>
                                <div><span style=\"color:#94a3b8\">Country/State:</span> <span style=\"color:white;font-weight:600\">${lData.issuing_country || 'N/A'}</span></div>
                            </div>
                            <div style=\"margin-top: 10px; font-size: 0.85rem;\">
                                <div><span style=\"color:#94a3b8\">Full Name:</span> <span style=\"color:white;font-weight:600\">${lData.full_name || 'N/A'}</span></div>
                                <div><span style=\"color:#94a3b8\">DOB:</span> <span style=\"color:white;font-weight:600\">${lData.date_of_birth || 'N/A'}</span></div>
                            </div>
                            </div> <!-- close license wrapper -->
                            <div style=\"margin-top: 20px; font-size: 0.85rem; padding-top: 15px; border-top: 1px solid rgba(0,0,0,0.1); color: #0f172a;\">
                                <h3 style=\"font-size: 1rem; color: #0f172a; font-weight: 800; margin-bottom: 5px;\">Emergency Contact</h3>
                                <div><span style=\"color:#64748b; font-weight:600\">Name:</span> ${lData.emergency_contact_name || 'N/A'}</div>
                                <div><span style=\"color:#64748b; font-weight:600\">Phone:</span> ${lData.emergency_contact_phone || 'N/A'}</div>
                                <div><span style=\"color:#64748b; font-weight:600\">Rel:</span> ${lData.emergency_contact_relation || 'N/A'}</div>
                            </div>
                            <div style=\"display:none\">`;
                    }
                }
            } catch (e) { console.error('License fetch error:', e); }'''

content = content.replace(old_license, new_license)

old_template_start = '''            const content = `

                <div style="display: flex; flex-direction: column; gap: 20px;">
                    <h2 style="font-size: 1.6rem; font-weight: 800; color: var(--text-main); margin: 0; letter-spacing: -0.5px;">Booking Details #${b.id}</h2>

                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; align-items: start;">
                        <div>
                            <label style="color: var(--text-muted); font-size: 0.65rem; font-weight: 700; text-transform: uppercase;">Customer</label>
                            <div style="font-weight: 600; font-size: 0.95rem; color: var(--text-main); margin-top: 2px; word-break: break-word;">${b.customer_name || 'Guest'}</div>
                        </div>
                        <div>
                            <label style="color: var(--text-muted); font-size: 0.65rem; font-weight: 700; text-transform: uppercase;">Vehicle</label>
                            <div style="font-weight: 600; font-size: 0.95rem; color: var(--text-main); margin-top: 2px; word-break: break-word;">${b.car || '-'}</div>
                        </div>
                        <div>
                            <label style="color: var(--text-muted); font-size: 0.65rem; font-weight: 700; text-transform: uppercase;">Rental Period</label>
                            <div style="font-weight: 600; font-size: 0.95rem; color: var(--text-main); margin-top: 2px; word-break: break-word;">${b.start_date ? new Date(b.start_date).toLocaleDateString() : '-'} to<br>${b.end_date ? new Date(b.end_date).toLocaleDateString() : '-'}</div>
                        </div>
                        <div>
                            <label style="color: var(--text-muted); font-size: 0.65rem; font-weight: 700; text-transform: uppercase;">Payment Status</label>
                            <div style="margin-top: 4px;">
                                <span style="background: ${b.payment_status === 'Paid' ? 'rgba(0,177,79,0.1)' : 'rgba(239,68,68,0.1)'}; color: ${b.payment_status === 'Paid' ? '#00B14F' : 'var(--danger)'}; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">${(b.payment_status || 'Unpaid')}</span>
                            </div>
                        </div>
                        <div>
                            <label style="color: var(--text-muted); font-size: 0.65rem; font-weight: 700; text-transform: uppercase;">Total Price</label>
                            <div style="font-weight: 700; color: var(--text-main); font-size: 0.95rem; margin-top: 2px;">&#8369;${b.total_price ? b.total_price.toFixed(2) : '0.00'}</div>
                        </div>
                        <div>
                            <label style="color: var(--text-muted); font-size: 0.65rem; font-weight: 700; text-transform: uppercase;">Booking Status</label>
                            <div style="margin-top: 4px;">
                                <span style="background: rgba(0,177,79,0.1); color: #00B14F; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">${(b.status || 'PENDING')}</span>
                            </div>
                        </div>
                    </div>

                    <!-- INSPECTION SECTION -->
                    <div style="border: 1px solid var(--border); padding: 15px; border-radius: 12px; margin-top: 10px;">
                        <h3 style="font-size: 1.1rem; color: #00B14F; font-weight: 700; margin-bottom: 15px;">Driver's License Details</h3>
                        <div id="bookingLicenseDetailsWrapper">
                            ${licenseHtml}
                        </div>
                    </div>'''

new_template_start = '''            const content = `

                <div style="display: flex; flex-direction: column; gap: 20px;">
                    <h2 style="font-size: 2rem; font-weight: 900; color: #0f172a; margin: 0; line-height: 1.1;">Booking Details<br>#${b.id}</h2>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; margin-top: 10px;">
                        <div>
                            <label style="color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Customer</label>
                            <div style="font-weight: 800; font-size: 1.1rem; color: #0f172a; margin-top: 4px; word-break: break-word;">${b.customer_name || 'Guest'}</div>
                        </div>
                        <div>
                            <label style="color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Vehicle</label>
                            <div style="font-weight: 800; font-size: 1.1rem; color: #0f172a; margin-top: 4px; word-break: break-word;">${b.car || '-'}</div>
                        </div>
                        
                        <div>
                            <label style="color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Rental Period</label>
                            <div style="font-weight: 800; font-size: 1rem; color: #0f172a; margin-top: 4px; word-break: break-word;">${b.start_date ? new Date(b.start_date).toLocaleDateString() : '-'} to<br>${b.end_date ? new Date(b.end_date).toLocaleDateString() : '-'}</div>
                        </div>
                        <div>
                            <label style="color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Payment Status</label>
                            <div style="font-weight: 800; font-size: 1.1rem; margin-top: 4px; color: ${b.payment_status === 'Paid' ? '#00B14F' : '#ef4444'};">${(b.payment_status || 'Unpaid')}</div>
                        </div>
                        
                        <div>
                            <label style="color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Total Price</label>
                            <div style="font-weight: 900; color: #00B14F; font-size: 1.3rem; margin-top: 4px;">&#8369;${b.total_price ? b.total_price.toFixed(2) : '0.00'}</div>
                        </div>
                        <div>
                            <label style="color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Booking Status</label>
                            <div style="font-weight: 900; color: #0f172a; font-size: 1.1rem; margin-top: 4px; text-transform: uppercase;">${(b.status || 'PENDING')}</div>
                        </div>
                    </div>
                    
                    <div style="height: 1px; background: rgba(0,0,0,0.05); margin: 5px 0;"></div>

                    <!-- INSPECTION SECTION -->
                    <div style="background: #94a3b8; padding: 15px; border-radius: 12px; margin-top: 5px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);">
                        <h3 style="font-size: 1.1rem; color: #00B14F; font-weight: 800; margin-bottom: 10px;">Driver's License Details</h3>
                        <div id="bookingLicenseDetailsWrapper">
                            ${licenseHtml}
                        </div>
                    </div>'''

content = content.replace(old_template_start, new_template_start)

# In light mode (which the modal is in the screenshot) the background of the modal needs to be white/off-white.
# Currently the admin is in dark mode usually. Let's make sure the text for Vehicle Inspections is dark.
content = content.replace(
    '<h3 style="font-size: 1.1rem; color: var(--text-main); font-weight: 700;">Vehicle Inspections</h3>',
    '<h3 style="font-size: 1.1rem; color: #0f172a; font-weight: 800;">Vehicle Inspections</h3>'
)
content = content.replace(
    '<h4 style="font-size: 0.9rem; color: var(--text-main); margin-bottom: 15px;">Add New Inspection</h4>',
    '<h4 style="font-size: 0.9rem; color: #0f172a; margin-bottom: 15px; font-weight: 800;">Add New Inspection</h4>'
)

# And let's update the modal container background itself so it looks like the screenshot (light background).
old_booking_modal = '''    <div id="bookingDetailsModal" class="premium-modal">
        <div class="modal-content">'''
new_booking_modal = '''    <div id="bookingDetailsModal" class="premium-modal" style="background: rgba(15,23,42,0.9);">
        <div class="modal-content" style="background: #f8fafc; color: #0f172a; padding: 25px; border-radius: 20px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.2);">'''
content = content.replace(old_booking_modal, new_booking_modal)


with open('admin_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(content)

print("Applied exact UI from screenshot")
