# -*- coding: utf-8 -*-
# Add _onProofSelected and markRefunded methods to Bookings object in both admin files

NEW_METHODS = """
        _onProofSelected(bookingId, input) {
            if (!input.files || !input.files[0]) return;
            const label = document.getElementById('refundProofLabel_' + bookingId);
            if (label) label.textContent = input.files[0].name;
            const btn = document.getElementById('markRefundedBtn_' + bookingId);
            if (btn) {
                btn.disabled = false;
                btn.style.background = '#10b981';
                btn.style.cursor = 'pointer';
            }
        },

        async markRefunded(bookingId) {
            const fileInput = document.getElementById('refundProofFile_' + bookingId);
            const refInput = document.getElementById('refundRefInput_' + bookingId);
            if (!fileInput || !fileInput.files || !fileInput.files[0]) {
                showNotification('Please upload a transfer proof first.', 'error');
                return;
            }
            const user = adminAuth.getUser();
            const formData = new FormData();
            formData.append('booking_id', bookingId);
            formData.append('admin_id', user ? user.id : 1);
            formData.append('refund_amount', '0');
            formData.append('refund_method', 'Transfer');
            formData.append('refund_ref', refInput ? refInput.value : '');
            formData.append('proof', fileInput.files[0]);

            const btn = document.getElementById('markRefundedBtn_' + bookingId);
            if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...'; }

            try {
                const res = await fetch(`${API_BASE}/api/admin/upload-refund-proof`, {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed');
                showNotification('Refund marked as completed! Customer has been notified.', 'success');
                document.getElementById('bookingDetailsModal').style.display = 'none';
                if (typeof modalClose === 'function') modalClose();
                this.refresh();
            } catch(err) {
                showNotification(err.message, 'error');
                if (btn) { btn.disabled = false; btn.style.background = '#10b981'; btn.innerHTML = '<i class=\"fas fa-check-circle\" style=\"margin-right:6px;\"></i>Mark as Refunded'; }
            }
        },

"""

for path in ['admin_app/index.html', 'admin_mobile/www/index.html']:
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        c = f.read()

    # Insert before getPillClass
    marker = '        getPillClass(s) {'
    idx = c.find(marker)
    if idx == -1:
        print(path, ': getPillClass not found')
        continue

    c = c[:idx] + NEW_METHODS + c[idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print(path, ': methods added, length:', len(c))
