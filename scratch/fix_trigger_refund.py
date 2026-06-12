# -*- coding: utf-8 -*-
# Add Trigger Refund button and method to admin_app

with open('admin_app/index.html', 'r', encoding='utf-8', errors='replace') as f:
    c = f.read()

# 1. Add Trigger Refund button in view() action buttons
old_btn = """            if (st !== 'cancelled' && st !== 'rejected' && st !== 'completed') {
                actionBtns += `<button onclick="Bookings.cancel(${b.id})" style="flex:1;min-width:100px;padding:11px 10px;background:#fff;color:#ef4444;border:1.5px solid #fca5a5;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-ban"></i>Cancel</button>`;
            }"""

new_btn = """            if (st !== 'cancelled' && st !== 'rejected' && st !== 'completed') {
                actionBtns += `<button onclick="Bookings.cancel(${b.id})" style="flex:1;min-width:100px;padding:11px 10px;background:#fff;color:#ef4444;border:1.5px solid #fca5a5;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-ban"></i>Cancel</button>`;
            }
            // Trigger Refund button for cancelled bookings with paid status
            if (st === 'cancelled' && b.payment_status === 'Paid') {
                actionBtns += `<button onclick="Bookings.triggerRefund(${b.id})" style="flex:1;min-width:130px;padding:11px 10px;background:#f59e0b;color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-undo"></i>Trigger Refund</button>`;
            }"""

if old_btn in c:
    c = c.replace(old_btn, new_btn, 1)
    print('Trigger Refund button added to view()')
else:
    print('ERROR: cancel button block not found')

# 2. Add triggerRefund method before getPillClass
TRIGGER_REFUND_METHOD = """        async triggerRefund(id) {
            const b = this.data.find(x => x.id === id);
            const ps = b ? b.payment_status : 'Paid';
            if (!confirm(`Trigger refund for Booking #${id}?\\n\\nThis will calculate the refund based on cancellation time vs pickup date (48h policy).\\n\\nCurrent status: ${ps}`)) return;
            try {
                const res = await fetch(`${API_BASE}/api/bookings/${id}/trigger-refund`, { method: 'POST', headers: {'Content-Type':'application/json'} });
                const data = await res.json();
                if (res.ok) {
                    alert(`Refund triggered!\\nRefund: ${data.refund_amount}\\nNon-refundable: ${data.non_refundable_fee||0}\\nHours before pickup: ${data.hours_before_pickup}h\\nCancelled: ${data.cancellation_time}\\nPickup was: ${data.pickup_time}`);
                    document.getElementById('bookingDetailsModal').style.display = 'none';
                    if (typeof modalClose === 'function') modalClose();
                    this.refresh();
                } else {
                    alert(data.error || 'Failed to trigger refund');
                }
            } catch(e) {
                alert('Connection error');
            }
        },

        getPillClass(s) {"""

# Find the getPillClass in admin_app (it has blank lines between)
gpc_idx = c.find('        getPillClass(s) {')
# Find the closing of view() just before it
view_end = c.rfind('            if (typeof modalOpen === \'function\') modalOpen();\n        },', 0, gpc_idx)
if view_end != -1:
    insert_after = view_end + len("            if (typeof modalOpen === 'function') modalOpen();\n        },")
    c = c[:insert_after] + '\n' + TRIGGER_REFUND_METHOD + c[gpc_idx + len('        getPillClass(s) {'):]
    print('triggerRefund method added')
else:
    print('ERROR: could not find insertion point for triggerRefund method')

with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')
