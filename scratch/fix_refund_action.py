# -*- coding: utf-8 -*-
# Add "Upload Proof + Mark as Refunded" section to admin booking Details modal

OLD_REFUND_SECTION = """                ${b.payment_status === 'Refund Pending' ? `
                <div style="background:#fffbeb;border-radius:12px;padding:14px;margin-bottom:14px;border:1.5px solid #fde68a;">
                    <div style="font-size:0.65rem;color:#d97706;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;display:flex;align-items:center;gap:5px;">
                        <i class="fas fa-clock"></i> Refund Pending &#8212; Action Required
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;">
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Refund Amount</div><div style="font-size:0.95rem;font-weight:800;color:#d97706;">${fmtMoney(b.refund_amount)}</div></div>
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Channel</div><div style="font-size:0.88rem;font-weight:700;color:#0f172a;">${b.refund_channel || '&#8212;'}</div></div>
                    </div>
                    ${b.refund_account_name ? `
                    <div style="background:#fff;border-radius:8px;padding:10px;border:1px solid #fde68a;">
                        <div style="font-size:0.72rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:6px;">Customer Refund Account</div>
                        <div style="font-size:0.88rem;font-weight:700;color:#0f172a;margin-bottom:2px;">${b.refund_account_name}</div>
                        <div style="font-size:0.85rem;color:#374151;font-weight:600;">${b.refund_account_number || ''}</div>
                    </div>` : `
                    <div style="font-size:0.78rem;color:#92400e;padding:8px;background:#fef3c7;border-radius:8px;">
                        <i class="fas fa-exclamation-circle" style="margin-right:4px;"></i>Customer has not yet submitted refund account details.
                    </div>`}
                </div>` : ''}"""

NEW_REFUND_SECTION = """                ${b.payment_status === 'Refund Pending' ? `
                <div style="background:#fffbeb;border-radius:12px;padding:14px;margin-bottom:14px;border:1.5px solid #fde68a;">
                    <div style="font-size:0.65rem;color:#d97706;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;display:flex;align-items:center;gap:5px;">
                        <i class="fas fa-clock"></i> Refund Pending &#8212; Action Required
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;">
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Refund Amount</div><div style="font-size:0.95rem;font-weight:800;color:#d97706;">${fmtMoney(b.refund_amount)}</div></div>
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Channel</div><div style="font-size:0.88rem;font-weight:700;color:#0f172a;">${b.refund_channel || '&#8212;'}</div></div>
                    </div>
                    ${b.refund_account_name ? `
                    <div style="background:#fff;border-radius:8px;padding:10px;border:1px solid #fde68a;margin-bottom:10px;">
                        <div style="font-size:0.72rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:6px;">Customer Refund Account</div>
                        <div style="font-size:0.88rem;font-weight:700;color:#0f172a;margin-bottom:2px;">${b.refund_account_name}</div>
                        <div style="font-size:0.85rem;color:#374151;font-weight:600;">${b.refund_account_number || ''}</div>
                    </div>
                    <div style="background:#fff;border-radius:8px;padding:10px;border:1px solid #fde68a;margin-bottom:10px;">
                        <div style="font-size:0.72rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:8px;">Step 1 &#8212; Upload Transfer Proof</div>
                        <input type="file" id="refundProofFile_${b.id}" accept="image/*" onchange="Bookings._onProofSelected(${b.id}, this)"
                            style="display:none;">
                        <button onclick="document.getElementById('refundProofFile_${b.id}').click()"
                            style="width:100%;padding:9px;background:#f8fafc;border:1.5px dashed #94a3b8;border-radius:8px;color:#374151;font-size:0.8rem;font-weight:600;cursor:pointer;margin-bottom:6px;">
                            <i class="fas fa-upload" style="margin-right:6px;color:#d97706;"></i><span id="refundProofLabel_${b.id}">Choose proof image</span>
                        </button>
                        <div style="font-size:0.72rem;color:#94a3b8;margin-bottom:8px;">Step 2 &#8212; Reference / Transaction No. (optional)</div>
                        <input type="text" id="refundRefInput_${b.id}" placeholder="e.g. TXN123456789"
                            style="width:100%;padding:8px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:0.82rem;color:#0f172a;background:#f8fafc;box-sizing:border-box;margin-bottom:10px;">
                        <button id="markRefundedBtn_${b.id}" onclick="Bookings.markRefunded(${b.id})" disabled
                            style="width:100%;padding:10px;background:#d1d5db;border:none;border-radius:10px;color:#fff;font-size:0.82rem;font-weight:700;cursor:not-allowed;">
                            <i class="fas fa-check-circle" style="margin-right:6px;"></i>Mark as Refunded
                        </button>
                    </div>` : `
                    <div style="font-size:0.78rem;color:#92400e;padding:8px;background:#fef3c7;border-radius:8px;">
                        <i class="fas fa-exclamation-circle" style="margin-right:4px;"></i>Customer has not yet submitted refund account details.
                    </div>`}
                </div>` : ''}"""

for path in ['admin_app/index.html', 'admin_mobile/www/index.html']:
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        c = f.read()
    if OLD_REFUND_SECTION in c:
        c = c.replace(OLD_REFUND_SECTION, NEW_REFUND_SECTION, 1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)
        print(path, ': Done')
    else:
        print(path, ': NOT FOUND')
