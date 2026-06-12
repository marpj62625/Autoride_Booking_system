# -*- coding: utf-8 -*-
with open('admin_mobile/www/index.html', 'rb') as f:
    content = f.read().decode('cp1252')

# The render() section uses LF (\n) not CRLF (\r\n)
old = ("                        <!-- Contextual action buttons -->\n"
       "                        <div style=\"display:flex; gap:8px; flex-wrap:wrap;\">\n"
       "\n"
       "                            ${b.status?.toLowerCase() === 'pending' ? `\n"
       "                                <button onclick=\"Bookings.approve(${b.id})\"\n"
       "                                    style=\"flex:1; min-width:100px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;\">\n"
       "                                    <i class=\"fas fa-check\" style=\"margin-right:4px;\"></i>Approve\n"
       "                                </button>\n"
       "                                <button onclick=\"Bookings.reject(${b.id})\"\n"
       "                                    style=\"flex:1; min-width:100px; padding:10px 8px; background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;\">\n"
       "                                    <i class=\"fas fa-times\" style=\"margin-right:4px;\"></i>Reject\n"
       "                                </button>\n"
       "                            ` : ''}")

new = ("                        <!-- Contextual action buttons -->\n"
       "                        <div style=\"display:flex; gap:8px; flex-wrap:wrap;\">\n"
       "\n"
       "                            ${(b.payment_status === 'Pending Payment' && b.status?.toLowerCase() === 'pending') ? `\n"
       "                                <button onclick=\"Bookings.markCashReceived(${b.id})\"\n"
       "                                    style=\"flex:1; min-width:120px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;\">\n"
       "                                    <i class=\"fas fa-money-bill-wave\" style=\"margin-right:4px;\"></i>Cash Received\n"
       "                                </button>\n"
       "                                <button onclick=\"Bookings.reject(${b.id})\"\n"
       "                                    style=\"flex:1; min-width:100px; padding:10px 8px; background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;\">\n"
       "                                    <i class=\"fas fa-times\" style=\"margin-right:4px;\"></i>Reject\n"
       "                                </button>\n"
       "                            ` : ''}")

if old in content:
    content = content.replace(old, new, 1)
    with open('admin_mobile/www/index.html', 'wb') as f:
        f.write(content.encode('cp1252'))
    print('Done - render() action buttons now check payment_status === Pending Payment')
else:
    print('Pattern not found')
    # Find approximate location
    idx = content.find("Bookings.approve(${b.id})")
    if idx >= 0:
        print('Found Bookings.approve at:', idx)
        print(repr(content[idx-300:idx+200]))
