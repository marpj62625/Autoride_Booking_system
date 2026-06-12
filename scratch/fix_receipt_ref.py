with open('admin_mobile/www/index.html', 'rb') as f:
    content = f.read().decode('cp1252')

# Find the payment section in showReceiptModal and replace it to include ref number
old = r"""                <div>
                    <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:8px;">Payment</div>
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:rgba(0,177,79,0.1);border:1px solid rgba(0,177,79,0.3);border-radius:10px;">
                        <span style="font-weight:800;color:white;">Total Amount</span>
                        <span style="font-weight:900;color:#00B14F;font-size:1.1rem;">&#8369;${fmt(b.total_price)}</span>
                    </div>
                    <div style="font-size:0.75rem;color:rgba(255,255,255,0.5);margin-top:6px;text-align:right;">
                        Payment: <span style="color:${b.payment_status==='paid'?'#4ade80':'#fbbf24'};font-weight:700;">${(b.payment_status||'pending').toUpperCase()}</span>
                    </div>
                </div>"""

new = r"""                <div>
                    <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:8px;">Payment</div>
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:rgba(0,177,79,0.1);border:1px solid rgba(0,177,79,0.3);border-radius:10px;">
                        <span style="font-weight:800;color:white;">Total Amount</span>
                        <span style="font-weight:900;color:#00B14F;font-size:1.1rem;">&#8369;${fmt(b.total_price)}</span>
                    </div>
                    <div style="font-size:0.75rem;color:rgba(255,255,255,0.5);margin-top:6px;display:flex;justify-content:space-between;align-items:center;">
                        <span>Payment: <span style="color:${b.payment_status==='paid'?'#4ade80':'#fbbf24'};font-weight:700;">${(b.payment_status||'pending').toUpperCase()}</span></span>
                    </div>
                    ${proofs.length > 0 ? proofs.map(p => `
                        <div style="margin-top:8px;padding:10px;background:rgba(255,255,255,0.04);border-radius:8px;border:1px solid rgba(255,255,255,0.07);">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                                <span style="font-size:0.72rem;color:rgba(255,255,255,0.5);">${p.method||'Payment'}</span>
                                <span style="font-size:0.75rem;color:#00B14F;font-weight:700;">&#8369;${fmt(p.amount)}</span>
                            </div>
                            ${p.reference_number ? `<div style="font-size:0.78rem;color:white;font-weight:600;">Ref #: <span style="color:#a5f3fc;font-family:monospace;">${p.reference_number}</span></div>` : ''}
                            <div style="font-size:0.7rem;color:rgba(255,255,255,0.35);margin-top:2px;">Status: ${(p.status||'pending').toUpperCase()}</div>
                        </div>
                    `).join('') : ''}
                </div>"""

if old in content:
    content = content.replace(old, new, 1)
    with open('admin_mobile/www/index.html', 'wb') as f:
        f.write(content.encode('cp1252'))
    print('Done')
else:
    print('Pattern not found - trying CRLF version')
    old_crlf = old.replace('\n', '\r\n')
    if old_crlf in content:
        content = content.replace(old_crlf, new, 1)
        with open('admin_mobile/www/index.html', 'wb') as f:
            f.write(content.encode('cp1252'))
        print('Done (CRLF)')
    else:
        # Find it manually
        idx = content.find('Total Amount')
        if idx > 0:
            print('Found Total Amount at', idx)
            print(repr(content[idx-200:idx+400]))
