import re

with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

old_license = '''            // Fetch license details for this booking
            let licenseHtml = '<p style=\"font-size: 0.85rem; color: var(--text-muted);\">No license details available.</p>';
            try {
                const licRes = await fetch(`${API_BASE}/api/admin/bookings/${id}/license-details`);
                if (licRes.ok) {
                    const lData = await licRes.json();
                    if (lData && lData.license_number) {
                        licenseHtml = `
                            <div style=\"display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;\">
                                <div><span style=\"color:var(--text-muted)\">License #:</span> <span style=\"color:white;font-weight:600\">${lData.license_number}</span></div>
                                <div><span style=\"color:var(--text-muted)\">Expiry:</span> <span style=\"color:white;font-weight:600\">${lData.expiry_date || 'N/A'}</span></div>
                                <div><span style=\"color:var(--text-muted)\">Class:</span> <span style=\"color:white;font-weight:600\">${lData.license_class || 'N/A'}</span></div>
                                <div><span style=\"color:var(--text-muted)\">Country/State:</span> <span style=\"color:white;font-weight:600\">${lData.issuing_country || 'N/A'}</span></div>
                            </div>
                            <div style=\"margin-top: 10px; font-size: 0.85rem;\">
                                <div><span style=\"color:var(--text-muted)\">Full Name:</span> <span style=\"color:white;font-weight:600\">${lData.full_name || 'N/A'}</span></div>
                                <div><span style=\"color:var(--text-muted)\">DOB:</span> <span style=\"color:white;font-weight:600\">${lData.date_of_birth || 'N/A'}</span></div>
                            </div>
                            <div style=\"margin-top: 10px; font-size: 0.85rem; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);\">
                                <p style=\"color:var(--text-muted);font-weight:700;margin-bottom:5px;\">Emergency Contact</p>
                                <div><span style=\"color:var(--text-muted)\">Name:</span> <span style=\"color:white;font-weight:600\">${lData.emergency_contact_name || 'N/A'}</span></div>
                                <div><span style=\"color:var(--text-muted)\">Phone:</span> <span style=\"color:white;font-weight:600\">${lData.emergency_contact_phone || 'N/A'}</span></div>
                                <div><span style=\"color:var(--text-muted)\">Rel:</span> <span style=\"color:white;font-weight:600\">${lData.emergency_contact_relation || 'N/A'}</span></div>
                            </div>
                            <div style=\"display:flex; gap:10px; margin-top: 10px;\">
                                ${lData.license_front_url ? `<button onclick=\"viewLicenseImage('${lData.license_front_url}')\" class=\"btn-outline\" style=\"flex:1;padding:8px;font-size:0.8rem\">Front Image</button>` : ''}
                                ${lData.license_back_url ? `<button onclick=\"viewLicenseImage('${lData.license_back_url}')\" class=\"btn-outline\" style=\"flex:1;padding:8px;font-size:0.8rem\">Back Image</button>` : ''}
                            </div>`;
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

content = content.replace(old_license, new_license)

old_template_start = '''            const content = `

                <div style="display: grid; gap: 15px;">
                    <h2 style="font-size: 1.8rem; font-weight: 900; color: var(--text-main); margin-bottom: 5px; letter-spacing: -1px;">Booking Details #${b.id}</h2>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <label style="color: var(--text-muted); font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Customer</label>
                            <p style="font-weight: 700; font-size: 1.1rem; color: var(--text-main); margin-top: 2px;">${b.customer_name || 'Guest'}</p>
                        </div>
                        <div>
                            <label style="color: var(--text-muted); font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Vehicle</label>
                            <p style="font-weight: 700; font-size: 1rem; color: var(--text-main); margin-top: 2px;">${b.car || '-'}</p>
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <label style="color: var(--text-muted); font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Rental Period</label>
                            <p style="font-weight: 700; font-size: 1rem; color: var(--text-main); margin-top: 2px;">${b.start_date ? new Date(b.start_date).toLocaleDateString() : '-'} to ${b.end_date ? new Date(b.end_date).toLocaleDateString() : '-'}</p>
                        </div>
                        <div>
                            <label style="color: var(--text-muted); font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Payment Status</label>
                            <p style="font-weight: 700; font-size: 1rem; margin-top: 2px; color: ${b.payment_status === 'Paid' ? 'var(--success)' : 'var(--danger)'};">${(b.payment_status || 'Unpaid').toUpperCase()}</p>
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <label style="color: var(--text-muted); font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Total Price</label>
                            <p style="font-weight: 800; color: var(--success); font-size: 1.2rem; margin-top: 2px;">&#8369;${b.total_price ? b.total_price.toFixed(2) : '0.00'}</p>
                        </div>
                        <div>
                            <label style="color: var(--text-muted); font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Booking Status</label>
                            <p style="font-weight: 900; color: var(--text-main); font-size: 1.1rem; margin-top: 2px;">${(b.status || 'PENDING').toUpperCase()}</p>
                        </div>
                    </div>

                    <div style="height: 1px; background: var(--border); margin: 10px 0;"></div>

                    <!-- INSPECTION SECTION -->
                    <div style="background: rgba(15, 23, 42, 0.4); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 5px;">
                        <h3 style="font-size: 1rem; color: #00B14F; font-weight: 800; margin-bottom: 10px;">Driver's License Details</h3>
                        <div id="bookingLicenseDetailsWrapper">
                            ${licenseHtml}
                        </div>
                    </div>

                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="font-size: 1rem; color: #00B14F; font-weight: 800;">Vehicle Inspections</h3>
                        <button id="mBtnAddInsp" style="padding: 8px 16px; background: #00B14F; border: none; color: white; border-radius: 10px; font-weight: 600; font-size: 0.8rem;">+ New Inspection</button>
                    </div>

                    <div id="mInspList" style="min-height: 40px;">
                        <p style="font-size: 0.85rem; color: var(--text-muted);">No inspections recorded yet.</p>
                    </div>

                    <div id="mInspForm" style="display: none; background: rgba(15, 23, 42, 0.4); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px;">
                        <h4 style="font-size: 0.9rem; color: white; margin-bottom: 15px;">Add New Inspection</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                            <select id="mfInspType" style="padding: 10px; background: var(--surface-container); color: var(--text-primary); border: 1px solid var(--border); border-radius: 8px; font-size: 0.8rem;">
                                <option value="pickup">Pickup</option>
                                <option value="return">Return</option>
                            </select>
                            <input type="number" id="mfInspMileage" placeholder="Mileage (km)" style="padding: 10px; background: var(--surface-container); color: var(--text-primary); border: 1px solid var(--border); border-radius: 8px; font-size: 0.8rem;">
                        </div>
                        <select id="mfInspFuel" style="width: 100%; padding: 10px; background: var(--surface-container); color: var(--text-primary); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 10px; font-size: 0.8rem;">
                            <option value="Full">Full Tank</option>
                            <option value="Empty">Empty</option>
                        </select>
                        <input type="file" id="mfInspPhotos" multiple accept="image/*" style="font-size: 0.75rem; color: #94a3b8; width: 100%; margin-bottom: 10px;">
                        <textarea id="mfInspNotes" placeholder="Condition Notes..." style="width: 100%; height: 60px; background: var(--surface-container); color: var(--text-primary); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 10px; padding: 10px; font-size: 0.8rem;"></textarea>
                        <div style="display: flex; gap: 10px;">
                            <button id="mBtnCancelInsp" class="btn-outline" style="flex: 1; padding: 10px; font-size: 0.8rem;">Cancel</button>
                            <button id="mBtnSaveInsp" class="btn-premium" style="flex: 1; padding: 10px; font-size: 0.8rem;">Save</button>
                        </div>
                    </div>

                    ${isApprovable ? `
                        <button onclick="Bookings.approve(${b.id})" class="btn-premium" style="width: 100%; background: var(--success); margin-top: 10px;">Approve Booking</button>
                        <button onclick="Bookings.reject(${b.id})" class="btn-premium" style="width: 100%; background: var(--danger); margin-top: 8px;">Reject Booking</button>
                    ` : ''}

                    ${b.status === 'Confirmed' || b.status === 'Approved' ? `
                        <button onclick="Bookings.pickup(${b.id})" class="btn-premium" style="width: 100%; background: #7c3aed; margin-top: 10px;"><i class="fas fa-key" style="margin-right:8px;"></i> Mark as Picked Up</button>
                    ` : ''}

                    ${b.status === 'Picked Up' ? `
                        <button onclick="Bookings.complete(${b.id})" class="btn-premium" style="width: 100%; background: #005339; margin-top: 10px;"><i class="fas fa-check-circle" style="margin-right:8px;"></i> Complete Booking (Returned)</button>
                    ` : ''}

                    <div style="display: grid; grid-template-columns: 0.8fr 1.2fr 1.2fr; gap: 10px; margin-top: 20px;">
                        <button onclick="document.getElementById('bookingDetailsModal').style.display='none'" class="btn-outline" style="padding: 12px 5px; font-size: 0.85rem;">Close</button>
                        <button onclick="window.open('${API_BASE}/api/bookings/${b.id}/receipt', '_blank')" class="btn-premium" style="padding: 12px 5px; font-size: 0.85rem;"><i class="fas fa-file-invoice" style="margin-right: 4px;"></i> Download Receipt</button>
                        ${isCancellable ? `
                            <button onclick="Bookings.cancel(${b.id})" class="btn-outline" style="padding: 12px 5px; font-size: 0.85rem; background: transparent; border: 1px solid var(--border); color: var(--text-secondary);">Cancel Booking</button>
                        ` : ''}
                    </div>

                    ${b.payment_status === 'Partially Paid' ? `
                        <button onclick="Bookings.markPaid(${b.id})" class="btn-premium" style="width: 100%; background: #00B14F; margin-top: 10px;">Mark as Fully Paid</button>
                    ` : ''}
                </div>
            `;'''


new_template_start = '''            const content = `

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
                    </div>

                    <div style="margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h3 style="font-size: 1.1rem; color: var(--text-main); font-weight: 700;">Vehicle Inspections</h3>
                            <button id="mBtnAddInsp" style="padding: 6px 14px; background: #00B14F; border: none; color: white; border-radius: 8px; font-weight: 600; font-size: 0.8rem;">+ New Inspection</button>
                        </div>

                        <div id="mInspList" style="min-height: 40px;">
                            <p style="font-size: 0.85rem; color: var(--text-muted); text-align: center; margin: 20px 0;">No inspections yet.</p>
                        </div>
                    </div>

                    <div id="mInspForm" style="display: none; background: var(--surface-container); padding: 15px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 20px;">
                        <h4 style="font-size: 0.9rem; color: var(--text-main); margin-bottom: 15px;">Add New Inspection</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                            <select id="mfInspType" style="padding: 10px; background: var(--bg-input, var(--surface)); color: var(--text-primary); border: 1px solid var(--border); border-radius: 8px; font-size: 0.8rem;">
                                <option value="pickup">Pickup</option>
                                <option value="return">Return</option>
                            </select>
                            <input type="number" id="mfInspMileage" placeholder="Mileage (km)" style="padding: 10px; background: var(--bg-input, var(--surface)); color: var(--text-primary); border: 1px solid var(--border); border-radius: 8px; font-size: 0.8rem;">
                        </div>
                        <select id="mfInspFuel" style="width: 100%; padding: 10px; background: var(--bg-input, var(--surface)); color: var(--text-primary); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 10px; font-size: 0.8rem;">
                            <option value="Full">Full Tank</option>
                            <option value="Empty">Empty</option>
                        </select>
                        <input type="file" id="mfInspPhotos" multiple accept="image/*" style="font-size: 0.75rem; color: var(--text-muted); width: 100%; margin-bottom: 10px;">
                        <textarea id="mfInspNotes" placeholder="Condition Notes..." style="width: 100%; height: 60px; background: var(--bg-input, var(--surface)); color: var(--text-primary); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 10px; padding: 10px; font-size: 0.8rem;"></textarea>
                        <div style="display: flex; gap: 10px;">
                            <button id="mBtnCancelInsp" class="btn-outline" style="flex: 1; padding: 10px; font-size: 0.8rem; border-color: var(--border); color: var(--text-secondary);">Cancel</button>
                            <button id="mBtnSaveInsp" class="btn-premium" style="flex: 1; padding: 10px; font-size: 0.8rem; background: #00B14F; color: white; border: none;">Save</button>
                        </div>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 10px; border-top: 1px solid var(--border); padding-top: 20px;">
                        ${isApprovable ? `
                            <button onclick="Bookings.approve(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; padding: 14px; border-radius: 10px; font-weight: 600; font-size: 0.95rem;">Approve Booking</button>
                            <button onclick="Bookings.reject(${b.id})" style="width: 100%; background: transparent; color: var(--danger); border: 1px solid var(--danger); padding: 14px; border-radius: 10px; font-weight: 600; font-size: 0.95rem;">Reject Booking</button>
                        ` : ''}

                        ${b.status === 'Confirmed' || b.status === 'Approved' ? `
                            <button onclick="Bookings.pickup(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; padding: 14px; border-radius: 10px; font-weight: 600; font-size: 0.95rem; display: flex; align-items: center; justify-content: center; gap: 8px;"><i class="fas fa-car"></i> Mark as Picked Up</button>
                        ` : ''}

                        ${b.status === 'Picked Up' ? `
                            <button onclick="Bookings.complete(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; padding: 14px; border-radius: 10px; font-weight: 600; font-size: 0.95rem; display: flex; align-items: center; justify-content: center; gap: 8px;"><i class="fas fa-check-circle"></i> Complete Booking (Returned)</button>
                        ` : ''}

                        ${b.payment_status === 'Partially Paid' ? `
                            <button onclick="Bookings.markPaid(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; padding: 14px; border-radius: 10px; font-weight: 600; font-size: 0.95rem;">Mark as Fully Paid</button>
                        ` : ''}

                        <div style="display: flex; gap: 10px;">
                            <button onclick="window.open('${API_BASE}/api/bookings/${b.id}/receipt', '_blank')" style="flex: 1; padding: 14px; font-size: 0.9rem; background: transparent; border: 1px solid #00B14F; color: #00B14F; border-radius: 10px; font-weight: 600;">Download Receipt</button>
                            ${isCancellable ? `
                                <button onclick="Bookings.cancel(${b.id})" style="flex: 1; padding: 14px; font-size: 0.9rem; background: transparent; border: 1px solid #00B14F; color: #00B14F; border-radius: 10px; font-weight: 600;">Cancel Booking</button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;'''

content = content.replace(old_template_start, new_template_start)

# Fix modal container X button to align with design (already matches but let's make sure it doesn't have "Booking Details" in a header that conflicts with our inner h2)
# Currently line 1421: <h2 style="font-size: 1.5rem; font-weight: 900; color: white; margin: 0; letter-spacing: -1px;">Booking Details</h2>
# We want it to be smaller and centered, like the screenshot.
old_modal_header = '''            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                <h2 style="font-size: 1.5rem; font-weight: 900; color: white; margin: 0; letter-spacing: -1px;">Booking Details</h2>
                <button onclick="document.getElementById('bookingDetailsModal').style.display='none'" class="menu-btn"><i class="fas fa-times"></i></button>
            </div>'''
new_modal_header = '''            <div style="position: relative; display: flex; justify-content: center; align-items: center; margin-bottom: 24px; padding-bottom: 15px; border-bottom: 1px solid var(--border);">
                <button onclick="document.getElementById('bookingDetailsModal').style.display='none'" style="position: absolute; left: 0; background: transparent; border: none; color: var(--text-main); font-size: 1.2rem; padding: 5px;"><i class="fas fa-times"></i></button>
                <h2 style="font-size: 1.1rem; font-weight: 700; color: var(--text-main); margin: 0;">Booking Details</h2>
            </div>'''
content = content.replace(old_modal_header, new_modal_header)

# Remove the "Close Details" button at the bottom since we already have it in the layout or X at top
old_close_details = '''            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid var(--border);">
                <button onclick="document.getElementById('bookingDetailsModal').style.display='none'" class="btn-outline" style="width: 100%;">Close Details</button>
            </div>'''
content = content.replace(old_close_details, '')

with open('admin_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(content)

print("Applied new UI for booking detail")
