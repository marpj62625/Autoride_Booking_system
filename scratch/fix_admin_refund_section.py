with open('admin_app/index.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find the closing area of the view() modal in admin_app
# Target: after reference_number div, before actionBtns line
old_marker = '                </div>\n                ${actionBtns ? `<div style="display:flex;gap:8px;flex-wrap:wrap;">${actionBtns}</div>` : \'\'}'

new_section = '''                </div>
                ${b.payment_status === 'Refund Pending' ? `
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
                </div>` : ''}
                ${actionBtns ? `<div style="display:flex;gap:8px;flex-wrap:wrap;">${actionBtns}</div>` : ''}'''

if old_marker in content:
    content = content.replace(old_marker, new_section, 1)
    with open('admin_app/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Done - refund section added to admin_app')
else:
    # Try to find it differently
    idx = content.find('${actionBtns ? `<div style="display:flex;gap:8px;flex-wrap:wrap;">${actionBtns}</div>` : \'\'}')
    print('actionBtns line found at:', idx)
    if idx > 0:
        print('Context:', repr(content[idx-200:idx+100]))
