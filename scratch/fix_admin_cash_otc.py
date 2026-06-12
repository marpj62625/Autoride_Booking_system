# -*- coding: utf-8 -*-
with open('admin_mobile/www/index.html', 'rb') as f:
    content = f.read().decode('cp1252')

changes = 0

# 1. render() - replace approve/reject condition
old1 = ("                            ${b.status?.toLowerCase() === 'pending' ? `\r\n"
        "                                <button onclick=\"Bookings.approve(${b.id})\"\r\n"
        "                                    style=\"flex:1; min-width:100px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;\">\r\n"
        "                                    <i class=\"fas fa-check\" style=\"margin-right:4px;\"></i>Approve\r\n"
        "                                </button>\r\n"
        "                                <button onclick=\"Bookings.reject(${b.id})\"\r\n"
        "                                    style=\"flex:1; min-width:100px; padding:10px 8px; background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;\">\r\n"
        "                                    <i class=\"fas fa-times\" style=\"margin-right:4px;\"></i>Reject\r\n"
        "                                </button>\r\n"
        "                            ` : ''}")

new1 = ("                            ${(b.payment_status === 'Pending Payment' && b.status?.toLowerCase() === 'pending') ? `\r\n"
        "                                <button onclick=\"Bookings.markCashReceived(${b.id})\"\r\n"
        "                                    style=\"flex:1; min-width:120px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;\">\r\n"
        "                                    <i class=\"fas fa-money-bill-wave\" style=\"margin-right:4px;\"></i>Cash Received\r\n"
        "                                </button>\r\n"
        "                                <button onclick=\"Bookings.reject(${b.id})\"\r\n"
        "                                    style=\"flex:1; min-width:100px; padding:10px 8px; background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); border-radius:10px; font-size:0.75rem; font-weight:800; cursor:pointer;\">\r\n"
        "                                    <i class=\"fas fa-times\" style=\"margin-right:4px;\"></i>Reject\r\n"
        "                                </button>\r\n"
        "                            ` : ''}")

if old1 in content:
    content = content.replace(old1, new1, 1)
    changes += 1
    print('Step 1 done: render() condition updated')
else:
    print('Step 1: pattern not found')

# 2. renderNew() - replace approve/reject condition
old2 = ("                            ${b.status?.toLowerCase() === 'pending' ? `\r\n"
        "                                <button onclick=\"Bookings.approve(${b.id})\" style=\"flex:1; min-width:100px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;\">\r\n"
        "                                    <i class=\"fas fa-check\" style=\"margin-right:4px;\"></i>Approve\r\n"
        "                                </button>\r\n"
        "                                <button onclick=\"Bookings.reject(${b.id})\" style=\"flex:1; min-width:100px; padding:10px 8px; background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;\">\r\n"
        "                                    <i class=\"fas fa-times\" style=\"margin-right:4px;\"></i>Reject\r\n"
        "                                </button>\r\n"
        "                            ` : ''}")

new2 = ("                            ${(b.payment_status === 'Pending Payment' && b.status?.toLowerCase() === 'pending') ? `\r\n"
        "                                <button onclick=\"Bookings.markCashReceived(${b.id})\" style=\"flex:1; min-width:120px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;\">\r\n"
        "                                    <i class=\"fas fa-money-bill-wave\" style=\"margin-right:4px;\"></i>Cash Received\r\n"
        "                                </button>\r\n"
        "                                <button onclick=\"Bookings.reject(${b.id})\" style=\"flex:1; min-width:100px; padding:10px 8px; background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;\">\r\n"
        "                                    <i class=\"fas fa-times\" style=\"margin-right:4px;\"></i>Reject\r\n"
        "                                </button>\r\n"
        "                            ` : ''}")

if old2 in content:
    content = content.replace(old2, new2, 1)
    changes += 1
    print('Step 2 done: renderNew() condition updated')
else:
    print('Step 2: pattern not found')

# 3. Add markCashReceived method after approve()
old3 = ("        async approve(id) {\r\n"
        "            if (!confirm('Approve this booking?')) return;\r\n"
        "            try {\r\n"
        "                const res = await fetch(`${API_URL}/bookings/${id}/approve`, { method: 'PUT' });\r\n"
        "                if (res.ok) {\r\n"
        "                    showNotification('Booking Approved!', 'success');\r\n"
        "                    document.getElementById('bookingDetailsModal').style.display = 'none'; modalClose();\r\n"
        "                    this.refresh();\r\n"
        "                } else {\r\n"
        "                    const data = await res.json();\r\n"
        "                    showNotification(data.error || 'Failed to approve', 'error');\r\n"
        "                }\r\n"
        "            } catch (err) { showNotification('Network error', 'error'); }\r\n"
        "        },")

new3 = ("        async approve(id) {\r\n"
        "            if (!confirm('Approve this booking?')) return;\r\n"
        "            try {\r\n"
        "                const res = await fetch(`${API_URL}/bookings/${id}/approve`, { method: 'PUT' });\r\n"
        "                if (res.ok) {\r\n"
        "                    showNotification('Booking Approved!', 'success');\r\n"
        "                    document.getElementById('bookingDetailsModal').style.display = 'none'; modalClose();\r\n"
        "                    this.refresh();\r\n"
        "                } else {\r\n"
        "                    const data = await res.json();\r\n"
        "                    showNotification(data.error || 'Failed to approve', 'error');\r\n"
        "                }\r\n"
        "            } catch (err) { showNotification('Network error', 'error'); }\r\n"
        "        },\r\n"
        "\r\n"
        "        async markCashReceived(id) {\r\n"
        "            if (!confirm('Confirm cash payment received for this booking?\\n\\nThis will confirm the booking and mark it as paid.')) return;\r\n"
        "            try {\r\n"
        "                const res = await fetch(`${API_URL}/bookings/${id}/approve`, { method: 'PUT' });\r\n"
        "                if (res.ok) {\r\n"
        "                    showNotification('Cash received! Booking confirmed.', 'success');\r\n"
        "                    document.getElementById('bookingDetailsModal').style.display = 'none'; modalClose();\r\n"
        "                    this.refresh();\r\n"
        "                } else {\r\n"
        "                    const data = await res.json();\r\n"
        "                    showNotification(data.error || 'Failed to confirm', 'error');\r\n"
        "                }\r\n"
        "            } catch (err) { showNotification('Network error', 'error'); }\r\n"
        "        },")

if old3 in content:
    content = content.replace(old3, new3, 1)
    changes += 1
    print('Step 3 done: markCashReceived() method added')
else:
    print('Step 3: approve() method pattern not found')

# 4. Also update the view() details modal - isApprovable should use payment_status too
old4 = "            const isApprovable = (b.status === 'Pending');"
new4 = "            const isApprovable = (b.status === 'Pending' && b.payment_status === 'Pending Payment');"
if old4 in content:
    content = content.replace(old4, new4, 1)
    changes += 1
    print('Step 4 done: view() isApprovable condition updated')
else:
    print('Step 4: isApprovable pattern not found')

# 5. Update view() approve button label to "Cash Received & Confirm"
old5 = ('                            <button onclick="Bookings.approve(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; '
        'padding: 14px; border-radius: 8px; font-weight: 600; font-size: 0.95rem;">Approve Booking</button>')
new5 = ('                            <button onclick="Bookings.markCashReceived(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; '
        'padding: 14px; border-radius: 8px; font-weight: 600; font-size: 0.95rem;"><i class="fas fa-money-bill-wave" style="margin-right:6px;"></i>Cash Received & Confirm</button>')
if old5 in content:
    content = content.replace(old5, new5, 1)
    changes += 1
    print('Step 5 done: view() approve button updated')
else:
    print('Step 5: view approve button not found')

with open('admin_mobile/www/index.html', 'wb') as f:
    f.write(content.encode('cp1252'))
print(f'\nSaved - {changes} changes applied')
