with open('admin_mobile/www/index.html', 'rb') as f:
    content = f.read().decode('cp1252')

# Find and replace the showReceiptModal method
start_marker = '        async showReceiptModal(bookingId) {'
end_marker = '        }\r\n\r\n    };\r\n\r\n    function openChangePasswordModal'

idx1 = content.find(start_marker)
idx2 = content.find(end_marker, idx1)

if idx1 < 0 or idx2 < 0:
    print('ERROR: markers not found', idx1, idx2)
    exit(1)

old_method = content[idx1:idx2]

new_method = r"""        async showReceiptModal(bookingId) {
            const modal = document.getElementById('receiptPreviewModal');
            const body = document.getElementById('receiptBody');
            if (!modal || !body) return;

            // Use already-loaded booking data from Bookings.data
            const b = Bookings.data.find(x => x.id === bookingId);
            if (!b) {
                modal.style.display = 'flex';
                body.innerHTML = '<div style="text-align:center;color:#f87171;padding:20px;"><i class="fas fa-exclamation-circle"></i> Booking not found</div>';
                return;
            }

            modal.style.display = 'flex';
            body.innerHTML = '<div style="text-align:center;color:rgba(255,255,255,0.4);padding:30px;"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';

            // Fetch payment proofs using correct API_URL
            let proofs = [];
            try {
                const pRes = await fetch(`${API_URL}/admin/bookings/${bookingId}/payment-proof`);
                if (pRes.ok) proofs = await pRes.json();
                if (!Array.isArray(proofs)) proofs = [];
            } catch(e) { proofs = []; }

            const fmt = n => parseFloat(n||0).toLocaleString('en-PH', {minimumFractionDigits:2});
            const fmtD = d => {
                if (!d) return 'N/A';
                try { return new Date(d).toLocaleDateString('en-PH', {year:'numeric',month:'short',day:'numeric'}); }
                catch(e) { return String(d).split('T')[0]; }
            };

            // Build proof images HTML
            const proofItems = proofs.filter(p => p.payment_proof_url);
            const proofsHtml = proofItems.length ? `
                <div style="margin-top:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.08);">
                    <div style="font-size:0.68rem;font-weight:700;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:10px;">Payment Proof</div>
                    ${proofItems.map(p => `
                        <div style="margin-bottom:8px;">
                            <div style="font-size:0.72rem;color:rgba(255,255,255,0.5);margin-bottom:4px;">
                                ${p.method||'Payment'}${p.reference_number?' &bull; '+p.reference_number:''}
                                <span style="float:right;color:#00B14F;font-weight:700;">&#8369;${fmt(p.amount)}</span>
                            </div>
                            <img src="${p.payment_proof_url}" style="width:100%;border-radius:8px;max-height:200px;object-fit:contain;background:rgba(0,0,0,0.3);">
                        </div>
                    `).join('')}
                </div>` : '';

            body.innerHTML = `
                <div style="padding:4px 0 14px;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:14px;">
                    <div style="font-size:1rem;font-weight:900;color:white;">RECEIPT #${String(b.id).padStart(6,'0')}</div>
                    <div style="font-size:0.75rem;color:rgba(255,255,255,0.4);margin-top:2px;">Status: <span style="color:#00B14F;font-weight:700;">${(b.status||'').toUpperCase()}</span></div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px;">
                    <div>
                        <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:4px;">Billed To</div>
                        <div style="font-size:0.85rem;color:white;font-weight:600;">${b.customer_name||'N/A'}</div>
                    </div>
                    <div>
                        <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:4px;">Rental Period</div>
                        <div style="font-size:0.8rem;color:white;">${fmtD(b.start_date)}</div>
                        <div style="font-size:0.8rem;color:rgba(255,255,255,0.6);">to ${fmtD(b.end_date)}</div>
                    </div>
                </div>
                <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:12px;margin-bottom:14px;">
                    <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:6px;">Vehicle</div>
                    <div style="font-size:0.85rem;color:white;font-weight:600;">${b.car||'N/A'}</div>
                    <div style="font-size:0.75rem;color:rgba(255,255,255,0.5);">${b.rental_type||''}</div>
                </div>
                <div>
                    <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:8px;">Payment</div>
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:rgba(0,177,79,0.1);border:1px solid rgba(0,177,79,0.3);border-radius:10px;">
                        <span style="font-weight:800;color:white;">Total Amount</span>
                        <span style="font-weight:900;color:#00B14F;font-size:1.1rem;">&#8369;${fmt(b.total_price)}</span>
                    </div>
                    <div style="font-size:0.75rem;color:rgba(255,255,255,0.5);margin-top:6px;text-align:right;">
                        Payment: <span style="color:${b.payment_status==='paid'?'#4ade80':'#fbbf24'};font-weight:700;">${(b.payment_status||'pending').toUpperCase()}</span>
                    </div>
                </div>
                ${proofsHtml}
            `;
        }"""

content = content[:idx1] + new_method + '\r\n\r\n    };\r\n\r\n    function openChangePasswordModal' + content[idx2 + len(end_marker):]
with open('admin_mobile/www/index.html', 'wb') as f:
    f.write(content.encode('cp1252'))
print('Done - showReceiptModal fixed')
