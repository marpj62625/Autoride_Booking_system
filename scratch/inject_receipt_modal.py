import sys

with open('admin_mobile/www/index.html', 'rb') as f:
    content = f.read().decode('cp1252')

new_method = r"""
        async showReceiptModal(bookingId) {
            const modal = document.getElementById('receiptPreviewModal');
            const body = document.getElementById('receiptBody');
            if (!modal || !body) return;

            modal.style.display = 'flex';
            body.innerHTML = '<div style="text-align:center;color:rgba(255,255,255,0.4);padding:30px;"><i class="fas fa-spinner fa-spin"></i> Loading receipt...</div>';

            try {
                const [bRes, pRes] = await Promise.all([
                    fetch(`${API_BASE}/api/admin/bookings/${bookingId}`).then(r => r.json()),
                    fetch(`${API_BASE}/api/admin/bookings/${bookingId}/payment-proof`).then(r => r.json()).catch(() => [])
                ]);
                const b = bRes.booking || bRes;
                const proofs = Array.isArray(pRes) ? pRes : [];
                const fmt = n => parseFloat(n||0).toLocaleString('en-PH', {minimumFractionDigits:2});
                const fmtD = d => d ? new Date(d).toLocaleDateString('en-PH', {year:'numeric',month:'short',day:'numeric'}) : 'N/A';

                let rows = `<tr><td style="padding:6px 0;color:rgba(255,255,255,0.7);">Base Rental Rate</td><td style="text-align:right;color:white;font-weight:600;">&#8369;${fmt(b.base_price)}</td></tr>`;
                if (parseFloat(b.addon_price||0)>0) rows += `<tr><td style="padding:6px 0;color:rgba(255,255,255,0.7);">Insurance/Extras</td><td style="text-align:right;color:white;font-weight:600;">&#8369;${fmt(b.addon_price)}</td></tr>`;
                if (parseFloat(b.insurance_price||0)>0) rows += `<tr><td style="padding:6px 0;color:rgba(255,255,255,0.7);">Basic Insurance</td><td style="text-align:right;color:white;font-weight:600;">&#8369;${fmt(b.insurance_price)}</td></tr>`;
                if (parseFloat(b.discount_amount||0)>0) rows += `<tr><td style="padding:6px 0;color:#f87171;">Promo Discount</td><td style="text-align:right;color:#f87171;font-weight:600;">-&#8369;${fmt(b.discount_amount)}</td></tr>`;
                if (parseFloat(b.points_discount_amount||0)>0) rows += `<tr><td style="padding:6px 0;color:#f87171;">Points Redemption</td><td style="text-align:right;color:#f87171;font-weight:600;">-&#8369;${fmt(b.points_discount_amount)}</td></tr>`;

                const proofItems = proofs.filter(p => p.payment_proof_url);
                const proofsHtml = proofItems.length ? `
                    <div style="margin-top:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.08);">
                        <div style="font-size:0.68rem;font-weight:700;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:10px;">Payment Proof</div>
                        ${proofItems.map(p => `
                            <div style="margin-bottom:8px;">
                                <div style="font-size:0.72rem;color:rgba(255,255,255,0.5);margin-bottom:4px;">${p.method||'Payment'}${p.reference_number?' &bull; '+p.reference_number:''}<span style="float:right;color:#00B14F;font-weight:700;">&#8369;${fmt(p.amount)}</span></div>
                                <img src="${p.payment_proof_url}" style="width:100%;border-radius:8px;max-height:200px;object-fit:contain;background:rgba(0,0,0,0.3);">
                            </div>
                        `).join('')}
                    </div>` : '';

                body.innerHTML = `
                    <div style="padding:4px 0 14px;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:14px;">
                        <div style="font-size:1rem;font-weight:900;color:white;">RECEIPT #${String(b.id).padStart(6,'0')}</div>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px;">
                        <div>
                            <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:4px;">Billed To</div>
                            <div style="font-size:0.85rem;color:white;font-weight:600;">${b.customer_name||b.full_name||'N/A'}</div>
                            <div style="font-size:0.75rem;color:rgba(255,255,255,0.5);">${b.email||''}</div>
                        </div>
                        <div>
                            <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:4px;">Rental Period</div>
                            <div style="font-size:0.8rem;color:white;">${fmtD(b.start_date)}</div>
                            <div style="font-size:0.8rem;color:rgba(255,255,255,0.6);">to ${fmtD(b.end_date)}</div>
                        </div>
                    </div>
                    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:12px;margin-bottom:14px;">
                        <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:6px;">Vehicle</div>
                        <div style="font-size:0.85rem;color:white;font-weight:600;">${b.car||(b.brand+' '+b.model)||'N/A'}</div>
                        <div style="font-size:0.75rem;color:rgba(255,255,255,0.5);">${b.plate_number||''}${b.rental_type?' &bull; '+b.rental_type:''}</div>
                    </div>
                    <div>
                        <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:8px;">Cost Breakdown</div>
                        <table style="width:100%;font-size:0.82rem;border-collapse:collapse;">${rows}</table>
                        <div style="display:flex;justify-content:space-between;align-items:center;border-top:1px solid rgba(255,255,255,0.15);margin-top:10px;padding-top:10px;">
                            <span style="font-weight:800;color:white;">Total Payable</span>
                            <span style="font-weight:900;color:#00B14F;font-size:1.05rem;">&#8369;${fmt(b.total_price)}</span>
                        </div>
                        ${parseFloat(b.points_earned||0)>0?`<div style="text-align:right;font-size:0.72rem;color:#4ade80;margin-top:6px;">+${b.points_earned} loyalty points earned</div>`:''}
                    </div>
                    ${proofsHtml}
                `;
            } catch(err) {
                body.innerHTML = '<div style="text-align:center;color:#f87171;padding:20px;"><i class="fas fa-exclamation-circle"></i> Failed to load receipt</div>';
            }
        }
"""

# Replace the Inspections closing "};" with method + "};"
old_closing = '        }\r\n    };\r\n\r\n    function openChangePasswordModal'
new_closing = '        },\r\n' + new_method.replace('\n', '\r\n') + '\r\n    };\r\n\r\n    function openChangePasswordModal'

if old_closing in content:
    content = content.replace(old_closing, new_closing, 1)
    with open('admin_mobile/www/index.html', 'wb') as f:
        f.write(content.encode('cp1252'))
    print('Done - showReceiptModal added to Inspections')
else:
    print('ERROR: closing pattern not found')
    idx = content.find('    };\r\n\r\n    function openChangePasswordModal')
    print('idx:', idx)
