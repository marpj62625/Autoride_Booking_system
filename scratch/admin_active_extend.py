# -*- coding: utf-8 -*-
with open('admin_mobile/www/index.html', 'rb') as f:
    content = f.read().decode('cp1252')

# ?? 1. Add View Details + Chat buttons to ActiveNow booking cards ??
# Find the closing of each active card in render() - after the two grid cells
old_card_end = (
    '                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">\r\n'
    '                        <div style="background:var(--surface-container);border-radius:10px;padding:8px 10px;">\r\n'
    '                            <div style="font-size:0.58rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:2px;">Return By</div>\r\n'
    '                            <div style="font-size:0.78rem;font-weight:700;color:var(--text-main);">${endStr}</div>\r\n'
    '                        </div>\r\n'
    '                        <div style="background:var(--surface-container);border-radius:10px;padding:8px 10px;">\r\n'
    '                            <div style="font-size:0.58rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:2px;">Time Left</div>\r\n'
    '                            <div id="${cdId}" style="font-size:0.78rem;font-weight:800;color:#00B14F;">-</div>\r\n'
    '                        </div>\r\n'
    '                    </div>\r\n'
    '                </div>`;\r\n'
    '            }).join(\'\');'
)

new_card_end = (
    '                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;">\r\n'
    '                        <div style="background:var(--surface-container);border-radius:10px;padding:8px 10px;">\r\n'
    '                            <div style="font-size:0.58rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:2px;">Return By</div>\r\n'
    '                            <div style="font-size:0.78rem;font-weight:700;color:var(--text-main);">${endStr}</div>\r\n'
    '                        </div>\r\n'
    '                        <div style="background:var(--surface-container);border-radius:10px;padding:8px 10px;">\r\n'
    '                            <div style="font-size:0.58rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:2px;">Time Left</div>\r\n'
    '                            <div id="${cdId}" style="font-size:0.78rem;font-weight:800;color:#00B14F;">-</div>\r\n'
    '                        </div>\r\n'
    '                    </div>\r\n'
    '                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">\r\n'
    '                        <button onclick="Bookings.view(${b.id})" style="padding:9px 8px;background:rgba(99,102,241,0.12);color:#818cf8;border:1px solid rgba(99,102,241,0.25);border-radius:10px;font-size:0.72rem;font-weight:700;cursor:pointer;">\r\n'
    '                            <i class="fas fa-eye" style="margin-right:4px;"></i>View Details\r\n'
    '                        </button>\r\n'
    '                        <button onclick="AdminChatWithUser(${b.id})" style="padding:9px 8px;background:rgba(0,177,79,0.1);color:#00B14F;border:1px solid rgba(0,177,79,0.25);border-radius:10px;font-size:0.72rem;font-weight:700;cursor:pointer;">\r\n'
    '                            <i class="fas fa-comments" style="margin-right:4px;"></i>Chat\r\n'
    '                        </button>\r\n'
    '                    </div>\r\n'
    '                </div>`;\r\n'
    '            }).join(\'\');'
)

if old_card_end in content:
    content = content.replace(old_card_end, new_card_end, 1)
    print('Step 1 done: ActiveNow cards get View Details + Chat buttons')
else:
    print('Step 1: pattern not found')

# ?? 2. Add Extension Requests section in the New Bookings tab ??
# Add it right after the newBookingsList div closing tag
old_nb_end = '            <div id="newBookingsList">\r\n                <div style="text-align: center; padding: 40px; color: var(--text-muted);">Loading...</div>\r\n            </div>\r\n        </div>'
new_nb_end = (
    '            <div id="newBookingsList">\r\n'
    '                <div style="text-align: center; padding: 40px; color: var(--text-muted);">Loading...</div>\r\n'
    '            </div>\r\n'
    '\r\n'
    '            <!-- Extension Requests -->\r\n'
    '            <div style="margin-top:20px;">\r\n'
    '                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">\r\n'
    '                    <h3 style="font-size:1rem;font-weight:800;color:var(--text-main);display:flex;align-items:center;gap:8px;">\r\n'
    '                        <i class="fas fa-calendar-plus" style="color:var(--primary);"></i> Extension Requests\r\n'
    '                        <span id="extReqBadge" style="display:none;background:#ef4444;color:white;border-radius:50%;width:18px;height:18px;font-size:0.65rem;font-weight:900;align-items:center;justify-content:center;"></span>\r\n'
    '                    </h3>\r\n'
    '                    <button onclick="Extensions.load()" style="background:var(--surface-container);border:1px solid var(--border);color:var(--text-muted);padding:6px 10px;border-radius:8px;font-size:0.75rem;cursor:pointer;"><i class="fas fa-sync-alt"></i></button>\r\n'
    '                </div>\r\n'
    '                <div id="extensionRequestsList"><div style="text-align:center;padding:20px;color:var(--text-muted);font-size:0.8rem;">No pending extension requests.</div></div>\r\n'
    '            </div>\r\n'
    '        </div>'
)

if old_nb_end in content:
    content = content.replace(old_nb_end, new_nb_end, 1)
    print('Step 2 done: Extension Requests section added to New Bookings tab')
else:
    print('Step 2: pattern not found')

# ?? 3. Add Extensions JS object before switchBookingTab ??
old_switch = '    window.switchBookingTab = function(tab) {'
new_switch = (
    '    // --- EXTENSIONS MODULE ---\r\n'
    '    window.AdminChatWithUser = function(bookingId) {\r\n'
    '        // Find user info from Bookings.data, then open chat\r\n'
    '        const b = (Bookings.data || []).find(x => x.id === bookingId);\r\n'
    '        const name = b ? (b.customer_name || "Customer") : "Customer";\r\n'
    '        // We need user_id - fetch it via booking detail or use booking_id as fallback\r\n'
    '        fetch(`${API_BASE}/api/admin/bookings/${bookingId}/license-details`)\r\n'
    '            .then(r => r.json()).then(d => {\r\n'
    '                // license-details has user_id indirectly; use booking endpoint\r\n'
    '                return fetch(`${API_URL}/bookings?admin_id=`);\r\n'
    '            }).catch(() => {});\r\n'
    '        // Simpler: open chat tab and show user search pre-filled\r\n'
    '        switchTab("chat");\r\n'
    '        setTimeout(() => {\r\n'
    '            AdminChat.showUserSearch();\r\n'
    '            const inp = document.getElementById("acUserSearchInput");\r\n'
    '            if (inp) { inp.value = name; AdminChat.searchUsers(name); }\r\n'
    '        }, 300);\r\n'
    '    };\r\n'
    '\r\n'
    '    const Extensions = {\r\n'
    '        async load() {\r\n'
    '            const list = document.getElementById(\'extensionRequestsList\');\r\n'
    '            if (!list) return;\r\n'
    '            list.innerHTML = \'<div style="text-align:center;padding:20px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin"></i></div>\';\r\n'
    '            try {\r\n'
    '                const res = await fetch(`${API_URL}/admin/extensions`);\r\n'
    '                const data = res.ok ? await res.json() : [];\r\n'
    '                const badge = document.getElementById(\'extReqBadge\');\r\n'
    '                if (badge) { badge.textContent = data.length; badge.style.display = data.length > 0 ? \'inline-flex\' : \'none\'; }\r\n'
    '                if (!data.length) { list.innerHTML = \'<div style="text-align:center;padding:20px;color:var(--text-muted);font-size:0.8rem;">No pending extension requests.</div>\'; return; }\r\n'
    '                list.innerHTML = data.map(e => `\r\n'
    '                    <div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:14px;margin-bottom:10px;border-left:3px solid #f59e0b;">\r\n'
    '                        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">\r\n'
    '                            <div>\r\n'
    '                                <div style="font-size:0.7rem;color:var(--text-muted);font-weight:700;">Booking #${e.booking_id}</div>\r\n'
    '                                <div style="font-size:0.88rem;font-weight:800;color:var(--text-main);">${e.customer_name || \'Customer\'}</div>\r\n'
    '                                <div style="font-size:0.75rem;color:var(--text-muted);">${e.car || \'\'}</div>\r\n'
    '                            </div>\r\n'
    '                            <span style="background:rgba(245,158,11,0.15);color:#f59e0b;border:1px solid rgba(245,158,11,0.3);padding:3px 8px;border-radius:20px;font-size:0.62rem;font-weight:800;">PENDING</span>\r\n'
    '                        </div>\r\n'
    '                        <div style="background:var(--surface-container);border-radius:10px;padding:10px;margin-bottom:10px;font-size:0.8rem;">\r\n'
    '                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">\r\n'
    '                                <div><div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Current End</div><div style="font-weight:700;color:var(--text-main);">${e.original_end_date}</div></div>\r\n'
    '                                <div><div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Requested End</div><div style="font-weight:700;color:#f59e0b;">${e.new_end_date}</div></div>\r\n'
    '                                <div><div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Extension</div><div style="font-weight:700;color:var(--text-main);">${e.extension_days} day${e.extension_days !== 1 ? \'s\' : \'\'}</div></div>\r\n'
    '                                <div><div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Amount Paid</div><div style="font-weight:800;color:#00B14F;">&#8369;${parseFloat(e.extension_price||0).toLocaleString()}</div></div>\r\n'
    '                            </div>\r\n'
    '                            <div style="margin-top:8px;font-size:0.75rem;color:var(--text-muted);">Method: <span style="color:var(--text-main);font-weight:600;">${e.payment_method || \'N/A\'}</span>${e.reference_number ? \' &bull; Ref: \' + e.reference_number : \'\'}</div>\r\n'
    '                            ${e.payment_proof_url ? `<img src="${e.payment_proof_url}" style="width:100%;border-radius:8px;margin-top:8px;max-height:150px;object-fit:contain;background:rgba(0,0,0,0.2);">` : \'\'}\r\n'
    '                        </div>\r\n'
    '                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">\r\n'
    '                            <button onclick="Extensions.approve(${e.id})" style="padding:10px;background:var(--primary);color:white;border:none;border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;">\r\n'
    '                                <i class="fas fa-check" style="margin-right:4px;"></i>Approve\r\n'
    '                            </button>\r\n'
    '                            <button onclick="Extensions.reject(${e.id})" style="padding:10px;background:rgba(239,68,68,0.12);color:#ef4444;border:1px solid rgba(239,68,68,0.3);border-radius:10px;font-size:0.78rem;font-weight:700;cursor:pointer;">\r\n'
    '                                <i class="fas fa-times" style="margin-right:4px;"></i>Reject\r\n'
    '                            </button>\r\n'
    '                        </div>\r\n'
    '                    </div>\r\n'
    '                `).join(\'\');\r\n'
    '            } catch(err) {\r\n'
    '                if (list) list.innerHTML = \'<div style="color:var(--danger);text-align:center;padding:12px;">Failed to load extensions.</div>\';\r\n'
    '            }\r\n'
    '        },\r\n'
    '\r\n'
    '        async approve(extId) {\r\n'
    '            if (!confirm(\'Approve this extension request?\\n\\nThis will update the booking end date.\')) return;\r\n'
    '            try {\r\n'
    '                const res = await fetch(`${API_URL}/admin/extensions/${extId}/approve`, { method: \'PUT\' });\r\n'
    '                const data = await res.json();\r\n'
    '                if (res.ok) {\r\n'
    '                    showNotification(\'Extension approved! Booking end date updated.\', \'success\');\r\n'
    '                    this.load();\r\n'
    '                    Bookings.refresh();\r\n'
    '                } else { showNotification(data.error || \'Failed to approve\', \'error\'); }\r\n'
    '            } catch(err) { showNotification(\'Network error\', \'error\'); }\r\n'
    '        },\r\n'
    '\r\n'
    '        async reject(extId) {\r\n'
    '            const note = prompt(\'Reason for rejection (customer will be notified of refund-upon-return):\');\r\n'
    '            if (note === null) return;\r\n'
    '            try {\r\n'
    '                const res = await fetch(`${API_URL}/admin/extensions/${extId}/reject`, {\r\n'
    '                    method: \'PUT\',\r\n'
    '                    headers: { \'Content-Type\': \'application/json\' },\r\n'
    '                    body: JSON.stringify({ note: note || \'Extension rejected. Refund upon vehicle return.\' })\r\n'
    '                });\r\n'
    '                const data = await res.json();\r\n'
    '                if (res.ok) {\r\n'
    '                    showNotification(\'Extension rejected. Customer notified of refund.\', \'success\');\r\n'
    '                    this.load();\r\n'
    '                } else { showNotification(data.error || \'Failed to reject\', \'error\'); }\r\n'
    '            } catch(err) { showNotification(\'Network error\', \'error\'); }\r\n'
    '        }\r\n'
    '    };\r\n'
    '\r\n'
    '    window.switchBookingTab = function(tab) {'
)

if old_switch in content:
    content = content.replace(old_switch, new_switch, 1)
    print('Step 3 done: Extensions JS module added')
else:
    print('Step 3: switchBookingTab pattern not found')

# ?? 4. Load extensions when New Bookings tab is opened ??
old_new_tab = (
    "        } else if (tab === 'new') {\r\n"
    "            const newTab = document.getElementById('tabNew');\r\n"
    "            if (newTab) newTab.style.display = 'block';\r\n"
    "            const newBtn = document.getElementById('tabBtnNew');\r\n"
    "            if (newBtn) {\r\n"
    "                newBtn.style.border = '1px solid var(--primary)';\r\n"
    "                newBtn.style.background = 'var(--primary)';\r\n"
    "                newBtn.style.color = 'white';\r\n"
    "            }\r\n"
    "            if (typeof Bookings !== 'undefined') {\r\n"
    "                Bookings.renderNew();\r\n"
    "            }"
)
new_new_tab = (
    "        } else if (tab === 'new') {\r\n"
    "            const newTab = document.getElementById('tabNew');\r\n"
    "            if (newTab) newTab.style.display = 'block';\r\n"
    "            const newBtn = document.getElementById('tabBtnNew');\r\n"
    "            if (newBtn) {\r\n"
    "                newBtn.style.border = '1px solid var(--primary)';\r\n"
    "                newBtn.style.background = 'var(--primary)';\r\n"
    "                newBtn.style.color = 'white';\r\n"
    "            }\r\n"
    "            if (typeof Bookings !== 'undefined') {\r\n"
    "                Bookings.renderNew();\r\n"
    "            }\r\n"
    "            if (typeof Extensions !== 'undefined') {\r\n"
    "                Extensions.load();\r\n"
    "            }"
)

if old_new_tab in content:
    content = content.replace(old_new_tab, new_new_tab, 1)
    print('Step 4 done: Extensions.load() called when New Bookings tab opens')
else:
    print('Step 4: pattern not found')

# ?? 5. Also call Extensions.load() after Bookings.refresh() ??
old_refresh_call = (
    "                this.render();\r\n"
    "                this.renderNew();\r\n"
    "                ActiveNow.render(this.data);"
)
new_refresh_call = (
    "                this.render();\r\n"
    "                this.renderNew();\r\n"
    "                ActiveNow.render(this.data);\r\n"
    "                if (typeof Extensions !== 'undefined') Extensions.load();"
)
if old_refresh_call in content:
    content = content.replace(old_refresh_call, new_refresh_call, 1)
    print('Step 5 done: Extensions.load() called after Bookings.refresh()')
else:
    print('Step 5: refresh call pattern not found')

with open('admin_mobile/www/index.html', 'wb') as f:
    f.write(content.encode('cp1252'))
print('Admin index.html saved')
