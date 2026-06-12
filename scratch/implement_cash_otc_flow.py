# -*- coding: utf-8 -*-
import sys

# ===== CHANGE 1: payment_routes.py — Cash OTC stays Pending =====
with open('backend/routers/payment_routes.py', 'r', encoding='utf-8', errors='replace') as f:
    payment_content = f.read()

# Replace the auto-confirm for all payments with conditional logic based on method
old_update = """        cur.execute(\"\"\"
            UPDATE bookings 
            SET status = 'Confirmed', payment_status = %s
            WHERE id = %s
        \"\"\", (new_payment_status, booking_id,))"""

new_update = """        # Check if payment method is cash OTC
        is_cash = 'cash' in (method or '').lower() or 'over the counter' in (method or '').lower()
        
        if is_cash:
            # Cash OTC: Keep booking Pending, payment awaiting admin collection
            cur.execute(\"\"\"
                UPDATE bookings 
                SET status = 'Pending', payment_status = 'Pending Payment'
                WHERE id = %s
            \"\"\", (booking_id,))
        else:
            # Online payment: auto-confirm
            cur.execute(\"\"\"
                UPDATE bookings 
                SET status = 'Confirmed', payment_status = %s
                WHERE id = %s
            \"\"\", (new_payment_status, booking_id,))"""

if old_update in payment_content:
    payment_content = payment_content.replace(old_update, new_update, 1)
    with open('backend/routers/payment_routes.py', 'w', encoding='utf-8', newline='') as f:
        f.write(payment_content)
    print('? payment_routes.py: Cash OTC now stays Pending until admin confirms')
else:
    print('? payment_routes.py: pattern not found')
    sys.exit(1)

# ===== CHANGE 2: app.py — Add payment_method to GET /bookings =====
with open('backend/app.py', 'rb') as f:
    app_content = f.read().decode('utf-8', errors='replace')

# Add LEFT JOIN to payments to get the method
old_query = """            SELECT b.id, u.full_name AS customer_name,

                   CONCAT(v.brand, ' ', v.model, ' (', v.plate_number, ')') AS car,

                   b.start_date, b.end_date, b.total_price, b.status,

                   b.payment_status,

                   b.pickup_location, b.rental_type, b.addons,

                   b.driver_id, d.full_name AS driver_name

            FROM bookings b

            JOIN users u ON b.user_id = u.id

            JOIN vehicles v ON b.vehicle_id = v.id

            LEFT JOIN drivers d ON b.driver_id = d.id"""

new_query = """            SELECT b.id, u.full_name AS customer_name,

                   CONCAT(v.brand, ' ', v.model, ' (', v.plate_number, ')') AS car,

                   b.start_date, b.end_date, b.total_price, b.status,

                   b.payment_status,

                   b.pickup_location, b.rental_type, b.addons,

                   b.driver_id, d.full_name AS driver_name,

                   p.method AS payment_method

            FROM bookings b

            JOIN users u ON b.user_id = u.id

            JOIN vehicles v ON b.vehicle_id = v.id

            LEFT JOIN drivers d ON b.driver_id = d.id

            LEFT JOIN (
                SELECT booking_id, method 
                FROM payments 
                WHERE id IN (SELECT MAX(id) FROM payments GROUP BY booking_id)
            ) p ON p.booking_id = b.id"""

if old_query in app_content:
    app_content = app_content.replace(old_query, new_query, 1)
    with open('backend/app.py', 'wb') as f:
        f.write(app_content.encode('utf-8'))
    print('? app.py: Added payment_method to GET /bookings')
else:
    print('? app.py: GET /bookings query not found')
    sys.exit(1)

# ===== CHANGE 3: admin index.html — Show buttons only for cash OTC pending =====
with open('admin_mobile/www/index.html', 'rb') as f:
    admin_content = f.read().decode('cp1252')

# Update render() and renderNew() approve/reject condition
old_condition_render = """                            ${b.status?.toLowerCase() === 'pending' ? `
                                <button onclick="Bookings.approve(${b.id})"
                                    style="flex:1; min-width:100px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;">
                                    <i class="fas fa-check" style="margin-right:4px;"></i>Approve
                                </button>
                                <button onclick="Bookings.reject(${b.id})"
                                    style="flex:1; min-width:100px; padding:10px 8px; background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;">
                                    <i class="fas fa-times" style="margin-right:4px;"></i>Reject
                                </button>
                            ` : ''}"""

new_condition_render = """                            ${(b.payment_status === 'Pending Payment' && b.status?.toLowerCase() === 'pending') ? `
                                <button onclick="Bookings.markCashReceived(${b.id})"
                                    style="flex:1; min-width:120px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;">
                                    <i class="fas fa-money-bill-wave" style="margin-right:4px;"></i>Cash Received
                                </button>
                                <button onclick="Bookings.reject(${b.id})"
                                    style="flex:1; min-width:100px; padding:10px 8px; background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;">
                                    <i class="fas fa-times" style="margin-right:4px;"></i>Reject
                                </button>
                            ` : ''}"""

admin_content = admin_content.replace(old_condition_render, new_condition_render, 1)

# Same replacement for renderNew()
old_condition_new = """                            ${b.status?.toLowerCase() === 'pending' ? `
                                <button onclick="Bookings.approve(${b.id})" style="flex:1; min-width:100px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;">
                                    <i class="fas fa-check" style="margin-right:4px;"></i>Approve
                                </button>
                                <button onclick="Bookings.reject(${b.id})" style="flex:1; min-width:100px; padding:10px 8px; background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;">
                                    <i class="fas fa-times" style="margin-right:4px;"></i>Reject
                                </button>
                            ` : ''}"""

new_condition_new = """                            ${(b.payment_status === 'Pending Payment' && b.status?.toLowerCase() === 'pending') ? `
                                <button onclick="Bookings.markCashReceived(${b.id})" style="flex:1; min-width:120px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;">
                                    <i class="fas fa-money-bill-wave" style="margin-right:4px;"></i>Cash Received
                                </button>
                                <button onclick="Bookings.reject(${b.id})" style="flex:1; min-width:100px; padding:10px 8px; background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;">
                                    <i class="fas fa-times" style="margin-right:4px;"></i>Reject
                                </button>
                            ` : ''}"""

admin_content = admin_content.replace(old_condition_new, new_condition_new, 1)

# Add markCashReceived method after approve method
old_approve = """        async approve(id) {
            if (!confirm('Approve this booking?')) return;
            try {
                const res = await fetch(`${API_URL}/bookings/${id}/approve`, { method: 'PUT' });
                if (res.ok) {
                    showNotification('Booking Approved!', 'success');
                    document.getElementById('bookingDetailsModal').style.display = 'none'; modalClose();
                    this.refresh();
                } else {
                    const data = await res.json();
                    showNotification(data.error || 'Failed to approve', 'error');
                }
            } catch (err) { showNotification('Network error', 'error'); }
        },"""

new_methods = """        async approve(id) {
            if (!confirm('Approve this booking?')) return;
            try {
                const res = await fetch(`${API_URL}/bookings/${id}/approve`, { method: 'PUT' });
                if (res.ok) {
                    showNotification('Booking Approved!', 'success');
                    document.getElementById('bookingDetailsModal').style.display = 'none'; modalClose();
                    this.refresh();
                } else {
                    const data = await res.json();
                    showNotification(data.error || 'Failed to approve', 'error');
                }
            } catch (err) { showNotification('Network error', 'error'); }
        },

        async markCashReceived(id) {
            if (!confirm('Confirm you have received cash payment for this booking?\\n\\nThis will confirm the booking and mark payment as received.')) return;
            try {
                const res = await fetch(`${API_URL}/bookings/${id}/approve`, { method: 'PUT' });
                if (res.ok) {
                    showNotification('Cash payment confirmed! Booking approved.', 'success');
                    document.getElementById('bookingDetailsModal').style.display = 'none'; modalClose();
                    this.refresh();
                } else {
                    const data = await res.json();
                    showNotification(data.error || 'Failed to confirm', 'error');
                }
            } catch (err) { showNotification('Network error', 'error'); }
        },"""

if old_approve in admin_content:
    admin_content = admin_content.replace(old_approve, new_methods, 1)
    with open('admin_mobile/www/index.html', 'wb') as f:
        f.write(admin_content.encode('cp1252'))
    print('? admin index.html: Buttons now show only for cash OTC pending, added markCashReceived')
else:
    print('? admin index.html: approve method not found')
    sys.exit(1)

print('\n? All changes applied successfully!')
print('\nSummary:')
print('  - Cash OTC bookings now stay Pending until admin marks cash received')
print('  - Admin sees payment_method field in booking data')
print('  - "Cash Received" + "Reject" buttons only show for cash OTC pending bookings')
print('  - Online payments (GCash/Card) auto-confirm as before')
