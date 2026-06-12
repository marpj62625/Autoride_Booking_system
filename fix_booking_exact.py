import sys

with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if 'async view(id) {' in line:
        start_idx = i
    if start_idx != -1 and "document.getElementById('bookingDetailContent').innerHTML = content;" in line:
        end_idx = i
        break

if start_idx == -1 or end_idx == -1:
    print("Could not find the bounds.")
    sys.exit(1)

new_code = """        async view(id) {
            const b = this.data.find(x => x.id === id);
            if (!b) return;
            
            const isCancellable = ['Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing'].includes(b.status);
            const isApprovable = (b.status === 'Pending');

            // Fetch license details for this booking
            let licenseHtml = '<p style="font-size: 0.85rem; color: var(--text-muted);">No license details available.</p>';
            try {
                const licRes = await fetch(`${API_BASE}/api/admin/bookings/${id}/license-details`);
                if (licRes.ok) {
                    const lData = await licRes.json();
                    if (lData && lData.license_number) {
                        licenseHtml = `
                            <div style="font-size: 0.95rem; line-height: 1.6; color: #1e293b;">
                                <div><span style="color:#64748b">Full Name:</span> <span style="font-weight:600">${lData.full_name || '-'}</span></div>
                                <div><span style="color:#64748b">DOB:</span> <span style="font-weight:600">${lData.date_of_birth || '-'}</span></div>
                                <div><span style="color:#64748b">License #:</span> <span style="font-weight:600">${lData.license_number}</span></div>
                                <div><span style="color:#64748b">Expiry:</span> <span style="font-weight:600">${lData.expiry_date || '-'}</span></div>
                            </div>
                            <div style="display:flex; gap:10px; margin-top: 15px;">
                                <button onclick="viewLicenseImage('${lData.license_front_url}')" ${!lData.license_front_url ? 'disabled' : ''} style="flex:1;padding:12px;font-size:0.9rem;border-radius:8px;border:1px solid #e2e8f0;background:white;color:#64748b;font-weight:600;">Front Image</button>
                                <button onclick="viewLicenseImage('${lData.license_back_url}')" ${!lData.license_back_url ? 'disabled' : ''} style="flex:1;padding:12px;font-size:0.9rem;border-radius:8px;border:1px solid #e2e8f0;background:white;color:#64748b;font-weight:600;">Back Image</button>
                            </div>
                            </div> <!-- close license wrapper -->
                            
                            <div style="margin-top: 25px; font-size: 0.95rem; line-height: 1.6; color: #1e293b;">
                                <h3 style="font-size: 1.05rem; color: #0f172a; font-weight: 800; margin-bottom: 10px;">Emergency Contact</h3>
                                <div><span style="color:#64748b">Name:</span> <span style="font-weight:600">${lData.emergency_contact_name || '-'}</span></div>
                                <div><span style="color:#64748b">Phone:</span> <span style="font-weight:600">${lData.emergency_contact_phone || '-'}</span></div>
                                <div><span style="color:#64748b">Rel:</span> <span style="font-weight:600">${lData.emergency_contact_relation || '-'}</span></div>
                            </div>
                            <!-- dummy closing to balance template -->
                            <div style="display:none">
                        `;
                    }
                }
            } catch (e) { console.error('License fetch error:', e); }

            const paymentBg = b.payment_status === 'Paid' ? '#dcfce7' : '#fee2e2';
            const paymentColor = b.payment_status === 'Paid' ? '#16a34a' : '#ef4444';
            const statusBg = ['Confirmed', 'Approved', 'Picked Up', 'Ongoing'].includes(b.status) ? '#dcfce7' : (['Pending'].includes(b.status) ? '#fef3c7' : '#fee2e2');
            const statusColor = ['Confirmed', 'Approved', 'Picked Up', 'Ongoing'].includes(b.status) ? '#16a34a' : (['Pending'].includes(b.status) ? '#d97706' : '#ef4444');

            const content = `
                <div style="display: flex; flex-direction: column; gap: 24px; background: white; padding-bottom: 20px;">
                    <h2 style="font-size: 1.8rem; font-weight: 900; color: #0f172a; margin: 0; letter-spacing: -0.5px;">Booking Details #${b.id}</h2>

                    <div style="display: grid; grid-template-columns: 1fr 1.2fr 1.2fr; gap: 15px 10px; align-items: start;">
                        <!-- Row 1 -->
                        <div>
                            <label style="color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Customer</label>
                            <div style="font-weight: 600; font-size: 0.95rem; color: #0f172a; margin-top: 4px; word-break: break-word;">${b.customer_name || 'Guest'}</div>
                        </div>
                        <div>
                            <label style="color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Vehicle</label>
                            <div style="font-weight: 600; font-size: 0.95rem; color: #0f172a; margin-top: 4px; word-break: break-word;">${b.car || '-'}</div>
                        </div>
                        <div>
                            <label style="color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Rental Period</label>
                            <div style="font-weight: 600; font-size: 0.95rem; color: #0f172a; margin-top: 4px; word-break: break-word; line-height: 1.4;">${b.start_date ? new Date(b.start_date).toLocaleDateString() : '-'} to<br>${b.end_date ? new Date(b.end_date).toLocaleDateString() : '-'}</div>
                        </div>
                        
                        <!-- Row 2 -->
                        <div>
                            <label style="color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Payment Status</label>
                            <div style="margin-top: 6px;">
                                <span style="background: ${paymentBg}; color: ${paymentColor}; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">${(b.payment_status || 'Unpaid')}</span>
                            </div>
                        </div>
                        <div>
                            <label style="color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Total Price</label>
                            <div style="font-weight: 700; color: #0f172a; font-size: 0.95rem; margin-top: 6px;">&#8369;${b.total_price ? b.total_price.toFixed(2) : '0.00'}</div>
                        </div>
                        <div>
                            <label style="color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Booking Status</label>
                            <div style="margin-top: 6px;">
                                <span style="background: ${statusBg}; color: ${statusColor}; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">${(b.status || 'PENDING')}</span>
                            </div>
                        </div>
                    </div>

                    <!-- INSPECTION SECTION -->
                    <div style="border: 1px solid #e2e8f0; padding: 18px; border-radius: 12px; margin-top: 5px;">
                        <h3 style="font-size: 1.1rem; color: #00B14F; font-weight: 700; margin-bottom: 15px;">Driver's License Details</h3>
                        <div id="bookingLicenseDetailsWrapper">
                            ${licenseHtml}
                        </div>
                    </div>

                    <div style="margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h3 style="font-size: 1.1rem; color: #0f172a; font-weight: 800;">Vehicle Inspections</h3>
                            <button id="mBtnAddInsp" style="padding: 8px 14px; background: #00B14F; border: none; color: white; border-radius: 8px; font-weight: 600; font-size: 0.8rem;">+ New Inspection</button>
                        </div>

                        <div id="mInspList" style="min-height: 40px; border-bottom: 1px solid #f1f5f9; padding-bottom: 15px;">
                            <p style="font-size: 0.85rem; color: #94a3b8; text-align: center; margin: 20px 0;">No inspections yet.</p>
                        </div>
                    </div>

                    <div id="mInspForm" style="display: none; background: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
                        <h4 style="font-size: 0.95rem; color: #0f172a; margin-bottom: 15px; font-weight: 800;">Add New Inspection</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                            <select id="mfInspType" style="padding: 12px; background: white; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 0.85rem;">
                                <option value="pickup">Pickup</option>
                                <option value="return">Return</option>
                            </select>
                            <input type="number" id="mfInspMileage" placeholder="Mileage (km)" style="padding: 12px; background: white; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 0.85rem;">
                        </div>
                        <select id="mfInspFuel" style="width: 100%; padding: 12px; background: white; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 8px; margin-bottom: 10px; font-size: 0.85rem;">
                            <option value="Full">Full Tank</option>
                            <option value="Empty">Empty</option>
                        </select>
                        <input type="file" id="mfInspPhotos" multiple accept="image/*" style="font-size: 0.8rem; color: #64748b; width: 100%; margin-bottom: 10px;">
                        <textarea id="mfInspNotes" placeholder="Condition Notes..." style="width: 100%; height: 70px; background: white; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 8px; margin-bottom: 10px; padding: 12px; font-size: 0.85rem;"></textarea>
                        <div style="display: flex; gap: 10px;">
                            <button id="mBtnCancelInsp" class="btn-outline" style="flex: 1; padding: 12px; font-size: 0.85rem; border-color: #cbd5e1; color: #64748b;">Cancel</button>
                            <button id="mBtnSaveInsp" class="btn-premium" style="flex: 1; padding: 12px; font-size: 0.85rem; background: #00B14F; color: white; border: none;">Save</button>
                        </div>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 5px;">
                        ${isApprovable ? `
                            <button onclick="Bookings.approve(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; padding: 14px; border-radius: 8px; font-weight: 600; font-size: 0.95rem;">Approve Booking</button>
                            <button onclick="Bookings.reject(${b.id})" style="width: 100%; background: white; color: #ef4444; border: 1px solid #ef4444; padding: 14px; border-radius: 8px; font-weight: 600; font-size: 0.95rem;">Reject Booking</button>
                        ` : ''}

                        ${b.status === 'Confirmed' || b.status === 'Approved' ? `
                            <button onclick="Bookings.pickup(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; padding: 14px; border-radius: 8px; font-weight: 600; font-size: 0.95rem; display: flex; align-items: center; justify-content: center; gap: 8px;"><i class="fas fa-car"></i> Mark as Picked Up</button>
                        ` : ''}

                        ${b.status === 'Picked Up' ? `
                            <button onclick="Bookings.complete(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; padding: 14px; border-radius: 8px; font-weight: 600; font-size: 0.95rem; display: flex; align-items: center; justify-content: center; gap: 8px;"><i class="fas fa-check-circle"></i> Complete Booking (Returned)</button>
                        ` : ''}

                        ${b.payment_status === 'Partially Paid' ? `
                            <button onclick="Bookings.markPaid(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; padding: 14px; border-radius: 8px; font-weight: 600; font-size: 0.95rem;">Mark as Fully Paid</button>
                        ` : ''}

                        <div style="display: flex; gap: 10px;">
                            <button onclick="window.open('${API_BASE}/api/bookings/${b.id}/receipt', '_blank')" style="flex: 1; padding: 14px; font-size: 0.85rem; background: white; border: 1px solid #00B14F; color: #00B14F; border-radius: 8px; font-weight: 600;">Download Receipt</button>
                            ${isCancellable ? `
                                <button onclick="Bookings.cancel(${b.id})" style="flex: 1; padding: 14px; font-size: 0.85rem; background: white; border: 1px solid #00B14F; color: #00B14F; border-radius: 8px; font-weight: 600;">Cancel Booking</button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
            document.getElementById('bookingDetailContent').innerHTML = content;
"""

new_lines = lines[:start_idx] + [new_code] + lines[end_idx+1:]
with open('admin_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.writelines(new_lines)
print("Replaced view() with exact layout.")
