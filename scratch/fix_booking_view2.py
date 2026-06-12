with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

VIEW_START_MARKER = "        view(id) {\n            const b = this.data.find(x => x.id === id);\n            if (!b) { console.error('Booking not found:', id); return; }\n            const fmtDate"
VIEW_END_MARKER = "        getPillClass(s) {"

idx_start = content.find(VIEW_START_MARKER)
idx_end = content.find(VIEW_END_MARKER, idx_start)

if idx_start == -1 or idx_end == -1:
    print('ERROR: markers not found', idx_start, idx_end)
    exit(1)

print(f'Replacing view() at {idx_start}-{idx_end}, length={idx_end-idx_start}')

NEW_VIEW = r"""        view(id) {
            const b = this.data.find(x => x.id === id);
            if (!b) { console.error('Booking not found:', id); return; }

            const fmtDate = d => d ? new Date(d).toLocaleDateString('en-PH', {year:'numeric',month:'short',day:'numeric'}) : 'N/A';
            const fmtMoney = v => '&#8369;' + parseFloat(v||0).toLocaleString('en-PH',{minimumFractionDigits:2,maximumFractionDigits:2});

            const statusStyles = {
                'pending':   { bg:'#fef9c3', color:'#854d0e', border:'#fde047' },
                'confirmed': { bg:'#dbeafe', color:'#1e40af', border:'#93c5fd' },
                'approved':  { bg:'#dbeafe', color:'#1e40af', border:'#93c5fd' },
                'picked up': { bg:'#dcfce7', color:'#166534', border:'#86efac' },
                'ongoing':   { bg:'#dcfce7', color:'#166534', border:'#86efac' },
                'completed': { bg:'#d1fae5', color:'#065f46', border:'#6ee7b7' },
                'cancelled': { bg:'#fee2e2', color:'#991b1b', border:'#fca5a5' },
                'rejected':  { bg:'#fee2e2', color:'#991b1b', border:'#fca5a5' },
            };
            const ss = statusStyles[(b.status||'').toLowerCase()] || { bg:'#f1f5f9', color:'#475569', border:'#cbd5e1' };

            let addonRows = '';
            if (parseFloat(b.addon_price||0) > 0 && b.addons) {
                try {
                    const addons = typeof b.addons === 'string' ? JSON.parse(b.addons) : b.addons;
                    if (Array.isArray(addons) && addons.length) {
                        const perAddon = parseFloat(b.addon_price||0) / addons.length;
                        addonRows = addons.map(a => `
                            <div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f1f5f9;">
                                <span style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:#374151;"><i class="fas fa-plus-circle" style="color:#00B14F;font-size:0.7rem;"></i>${a}</span>
                                <span style="font-size:0.82rem;font-weight:600;color:#374151;">${fmtMoney(perAddon)}</span>
                            </div>`).join('');
                    }
                } catch(e) {}
            }

            const st = (b.status||'').toLowerCase();
            let actionBtns = '';
            if (b.payment_status === 'Pending Payment' && st === 'pending') {
                actionBtns += `<button onclick="Bookings.markCashReceived(${b.id})" style="flex:1;min-width:130px;padding:11px 10px;background:#00B14F;color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-money-bill-wave"></i>Cash Received</button>`;
                actionBtns += `<button onclick="Bookings.reject(${b.id})" style="flex:1;min-width:100px;padding:11px 10px;background:#fff;color:#ef4444;border:1.5px solid #fca5a5;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-times"></i>Reject</button>`;
            }
            if (st === 'confirmed' || st === 'approved') {
                actionBtns += `<button onclick="Inspections.openModal(${b.id},'pickup')" style="flex:1;min-width:120px;padding:11px 10px;background:#f59e0b;color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-search-plus"></i>Pickup Inspect</button>`;
                actionBtns += `<button onclick="Bookings.pickup(${b.id})" style="flex:1;min-width:120px;padding:11px 10px;background:#00B14F;color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-car"></i>Mark Picked Up</button>`;
            }
            if (st === 'picked up' || st === 'ongoing') {
                actionBtns += `<button onclick="Inspections.openModal(${b.id},'return')" style="flex:1;min-width:120px;padding:11px 10px;background:#f59e0b;color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-clipboard-check"></i>Return Inspect</button>`;
                actionBtns += `<button onclick="Bookings.complete(${b.id})" style="flex:1;min-width:120px;padding:11px 10px;background:#00B14F;color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-flag-checkered"></i>Mark Returned</button>`;
            }
            if (b.payment_status === 'Partially Paid') {
                actionBtns += `<button onclick="Bookings.markPaid(${b.id})" style="flex:1;min-width:120px;padding:11px 10px;background:#10b981;color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-check-circle"></i>Mark Fully Paid</button>`;
            }
            if (st !== 'cancelled' && st !== 'rejected' && st !== 'completed') {
                actionBtns += `<button onclick="Bookings.cancel(${b.id})" style="flex:1;min-width:100px;padding:11px 10px;background:#fff;color:#ef4444;border:1.5px solid #fca5a5;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:5px;"><i class="fas fa-ban"></i>Cancel</button>`;
            }

            document.getElementById('bookingDetailContent').innerHTML = `
            <div style="color:#0f172a;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;">
                    <div>
                        <div style="font-size:0.65rem;color:#94a3b8;font-weight:800;letter-spacing:1px;text-transform:uppercase;">Booking</div>
                        <div style="font-size:1.3rem;font-weight:900;color:#0f172a;letter-spacing:-0.5px;">#${b.id}</div>
                    </div>
                    <span style="padding:6px 14px;border-radius:20px;font-size:0.72rem;font-weight:800;letter-spacing:0.3px;background:${ss.bg};color:${ss.color};border:1.5px solid ${ss.border};">${(b.status||'PENDING').toUpperCase()}</span>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;">
                    <div style="background:#f8fafc;border-radius:12px;padding:12px;border:1px solid #e2e8f0;">
                        <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
                            <div style="width:28px;height:28px;background:#dbeafe;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="fas fa-user" style="color:#3b82f6;font-size:0.7rem;"></i></div>
                            <span style="font-size:0.62rem;color:#94a3b8;font-weight:800;text-transform:uppercase;">Customer</span>
                        </div>
                        <div style="font-weight:800;font-size:0.88rem;color:#0f172a;margin-bottom:2px;">${b.customer_name||'N/A'}</div>
                        <div style="font-size:0.72rem;color:#64748b;word-break:break-all;">${b.customer_email||''}</div>
                    </div>
                    <div style="background:#f8fafc;border-radius:12px;padding:12px;border:1px solid #e2e8f0;">
                        <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
                            <div style="width:28px;height:28px;background:#dcfce7;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="fas fa-car" style="color:#16a34a;font-size:0.7rem;"></i></div>
                            <span style="font-size:0.62rem;color:#94a3b8;font-weight:800;text-transform:uppercase;">Vehicle</span>
                        </div>
                        <div style="font-weight:800;font-size:0.85rem;color:#0f172a;line-height:1.3;">${b.car||'N/A'}</div>
                    </div>
                </div>
                <div style="background:#f8fafc;border-radius:12px;padding:14px;margin-bottom:14px;border:1px solid #e2e8f0;">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:${b.pickup_location ? '10px' : '0'};">
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:3px;display:flex;align-items:center;gap:4px;"><i class="fas fa-calendar-check" style="color:#00B14F;"></i>Pickup</div><div style="font-weight:700;font-size:0.9rem;color:#0f172a;">${fmtDate(b.start_date)}</div></div>
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:3px;display:flex;align-items:center;gap:4px;"><i class="fas fa-calendar-times" style="color:#ef4444;"></i>Return</div><div style="font-weight:700;font-size:0.9rem;color:#0f172a;">${fmtDate(b.end_date)}</div></div>
                    </div>
                    ${b.pickup_location ? `<div style="padding-top:10px;border-top:1px solid #e2e8f0;display:flex;align-items:flex-start;gap:6px;"><i class="fas fa-map-marker-alt" style="color:#ef4444;margin-top:2px;font-size:0.8rem;"></i><div style="font-size:0.82rem;color:#374151;">${b.pickup_location}</div></div>` : ''}
                </div>
                <div style="background:#f8fafc;border-radius:12px;padding:14px;margin-bottom:14px;border:1px solid #e2e8f0;">
                    <div style="font-size:0.65rem;color:#94a3b8;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:12px;display:flex;align-items:center;gap:5px;"><i class="fas fa-receipt" style="color:#00B14F;"></i>Price Breakdown</div>
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f1f5f9;"><span style="font-size:0.82rem;color:#374151;">Base Rental</span><span style="font-size:0.82rem;font-weight:600;color:#374151;">${fmtMoney(b.base_price)}</span></div>
                    ${addonRows}
                    ${parseFloat(b.insurance_price||0)>0 ? `<div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f1f5f9;"><span style="font-size:0.82rem;color:#374151;">Insurance${b.insurance_type ? ' ('+b.insurance_type+')' : ''}</span><span style="font-size:0.82rem;font-weight:600;color:#374151;">${fmtMoney(b.insurance_price)}</span></div>` : ''}
                    ${parseFloat(b.discount_amount||0)>0 ? `<div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f1f5f9;"><span style="font-size:0.82rem;color:#16a34a;"><i class="fas fa-tag" style="margin-right:4px;"></i>Discount</span><span style="font-size:0.82rem;font-weight:600;color:#16a34a;">-${fmtMoney(b.discount_amount)}</span></div>` : ''}
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0 0;"><span style="font-size:0.92rem;font-weight:800;color:#0f172a;">TOTAL</span><span style="font-size:1.1rem;font-weight:900;color:#00B14F;">${fmtMoney(b.total_price)}</span></div>
                </div>
                <div style="background:#f8fafc;border-radius:12px;padding:14px;margin-bottom:${actionBtns ? '14px' : '0'};border:1px solid #e2e8f0;">
                    <div style="font-size:0.65rem;color:#94a3b8;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:12px;display:flex;align-items:center;gap:5px;"><i class="fas fa-credit-card" style="color:#3b82f6;"></i>Payment</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;">
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Method</div><div style="font-size:0.85rem;font-weight:700;color:#0f172a;">${b.payment_method||'N/A'}</div></div>
                        <div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Status</div><div style="font-size:0.82rem;font-weight:700;color:${b.payment_status==='Paid'?'#16a34a':b.payment_status==='Refund Pending'?'#d97706':b.payment_status==='Partially Paid'?'#2563eb':'#374151'};">${b.payment_status||'N/A'}</div></div>
                    </div>
                    ${parseFloat(b.amount_paid||0)>0 ? `<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;"><div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Amount Paid</div><div style="font-size:0.85rem;font-weight:700;color:#16a34a;">${fmtMoney(b.amount_paid)}</div></div>${parseFloat(b.balance_amount||0)>0?`<div><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:2px;">Balance Due</div><div style="font-size:0.85rem;font-weight:700;color:#ef4444;">${fmtMoney(b.balance_amount)}</div></div>`:''}</div>` : ''}
                    ${b.reference_number ? `<div style="padding-top:8px;border-top:1px solid #f1f5f9;"><div style="font-size:0.62rem;color:#94a3b8;font-weight:700;text-transform:uppercase;margin-bottom:3px;">Reference #</div><div style="font-size:0.78rem;font-weight:600;color:#0f172a;word-break:break-all;background:#fff;padding:6px 8px;border-radius:6px;border:1px solid #e2e8f0;">${b.reference_number}</div></div>` : ''}
                </div>
                ${actionBtns ? `<div style="display:flex;gap:8px;flex-wrap:wrap;">${actionBtns}</div>` : ''}
            </div>`;

            const modal = document.getElementById('bookingDetailsModal');
            modal.style.display = 'flex';
            if (typeof modalOpen === 'function') modalOpen();
        },

"""

content = content[:idx_start] + NEW_VIEW + content[idx_end:]

with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done - view() replaced safely')
