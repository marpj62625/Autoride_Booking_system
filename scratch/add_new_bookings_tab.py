with open('admin_mobile/www/index.html', 'rb') as f:
    content = f.read().decode('cp1252')

# ?? 1. Add "New Bookings" tab button before All Bookings ??
old_tab_btn = (
    '            <button onclick="switchBookingTab(\'all\')" id="tabBtnAll" c'
)
# Find the full line
idx = content.find("            <button onclick=\"switchBookingTab('all')\"")
line_end = content.find('\r\n', idx)
all_btn_block = content[idx:line_end+2]  # includes newline

new_btn = (
    '            <button onclick="switchBookingTab(\'new\')" id="tabBtnNew" '
    'class="booking-tab-btn" style="padding: 10px 18px; border-radius: 50px; '
    'border: 1px solid var(--border); background: var(--surface-container); '
    'color: var(--text-secondary); font-weight: 700; font-size: 0.78rem; '
    'white-space: nowrap; flex-shrink: 0; display: flex; align-items: center; gap: 6px;">\r\n'
    '                <i class="fas fa-bell" style="font-size: 0.75rem; margin-right: 6px;"></i> New Bookings\r\n'
    '                <span id="newBookingsBadge" style="display:none;background:#ef4444;color:white;border-radius:50%;width:18px;height:18px;font-size:0.65rem;font-weight:900;align-items:center;justify-content:center;"></span>\r\n'
    '            </button>\r\n'
)

content = content.replace(all_btn_block, new_btn + all_btn_block, 1)
print('Step 1: New Bookings tab button added')

# ?? 2. Add "New Bookings" tab content div before tabAll ??
tab_content_new = '''
        <!-- NEW BOOKINGS TAB CONTENT -->
        <div id="tabNew" class="booking-tab-content" style="display: none;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-main);">New Bookings</h3>
                <button onclick="Bookings.refresh()" style="background: var(--surface-container); border: 1px solid var(--border); color: var(--text-muted); padding: 7px 12px; border-radius: 10px; font-size: 0.75rem; font-weight: 700;">
                    <i class="fas fa-sync-alt"></i>
                </button>
            </div>
            <!-- Status filter chips for new bookings tab -->
            <div style="display:flex;gap:8px;overflow-x:auto;padding-bottom:8px;margin-bottom:16px;scrollbar-width:none;">
                <button class="nb-chip nb-chip-active" data-filter="all" onclick="Bookings.setNewFilter('all',this)" style="flex-shrink:0;padding:7px 14px;background:var(--primary);color:white;border:1px solid var(--primary);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">All Pending</button>
                <button class="nb-chip" data-filter="pending" onclick="Bookings.setNewFilter('pending',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">New</button>
                <button class="nb-chip" data-filter="confirmed" onclick="Bookings.setNewFilter('confirmed',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">Confirmed</button>
                <button class="nb-chip" data-filter="approved" onclick="Bookings.setNewFilter('approved',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">Approved</button>
                <button class="nb-chip" data-filter="picked_up" onclick="Bookings.setNewFilter('picked_up',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">Picked Up</button>
            </div>
            <div id="newBookingsList">
                <div style="text-align: center; padding: 40px; color: var(--text-muted);">Loading...</div>
            </div>
        </div>

'''

insert_before = '        <!-- ALL BOOKINGS TAB CONTENT -->'
content = content.replace(insert_before, tab_content_new + insert_before, 1)
print('Step 2: tabNew HTML added')

# ?? 3. Add setNewFilter + renderNew methods to Bookings object ??
# Insert after setFilter method (find its closing comma)
old_set_filter_end = (
    '            this.render();\r\n'
    '        },\r\n'
    '        render()'
)

new_methods = (
    '            this.render();\r\n'
    '        },\r\n'
    '        _newFilter: \'all\',\r\n'
    '        setNewFilter(filter, btn) {\r\n'
    '            this._newFilter = filter;\r\n'
    '            document.querySelectorAll(\'.nb-chip\').forEach(b => {\r\n'
    '                const active = b.dataset.filter === filter;\r\n'
    '                b.style.background  = active ? \'var(--primary)\' : \'var(--surface-container)\';\r\n'
    '                b.style.borderColor = active ? \'var(--primary)\' : \'var(--border)\';\r\n'
    '                b.style.color       = active ? \'white\' : \'var(--text-main)\';\r\n'
    '            });\r\n'
    '            this.renderNew();\r\n'
    '        },\r\n'
    '        renderNew() {\r\n'
    '            const list = document.getElementById(\'newBookingsList\');\r\n'
    '            if (!list) return;\r\n'
    '            // Show pending + confirmed + approved + picked up\r\n'
    '            const activeStatuses = [\'pending\', \'confirmed\', \'approved\', \'picked up\', \'ongoing\'];\r\n'
    '            const statusMap = { pending: \'Pending\', confirmed: \'Confirmed\', approved: \'Approved\', picked_up: \'Picked Up\' };\r\n'
    '            let filtered = this.data.filter(b => activeStatuses.includes((b.status||\'\').toLowerCase()));\r\n'
    '            if (this._newFilter !== \'all\') {\r\n'
    '                filtered = filtered.filter(b => {\r\n'
    '                    const s = (b.status||\'\').toLowerCase().replace(\' \', \'_\');\r\n'
    '                    return s === this._newFilter || (b.status||\'\') === statusMap[this._newFilter];\r\n'
    '                });\r\n'
    '            }\r\n'
    '            // Update badge count\r\n'
    '            const pendingCount = this.data.filter(b => (b.status||\'\').toLowerCase() === \'pending\').length;\r\n'
    '            const badge = document.getElementById(\'newBookingsBadge\');\r\n'
    '            if (badge) {\r\n'
    '                badge.textContent = pendingCount;\r\n'
    '                badge.style.display = pendingCount > 0 ? \'inline-flex\' : \'none\';\r\n'
    '            }\r\n'
    '            if (filtered.length === 0) {\r\n'
    '                list.innerHTML = `<div style="text-align:center;padding:60px 20px;color:var(--text-muted);">\r\n'
    '                    <i class="fas fa-inbox" style="font-size:2.5rem;opacity:0.3;margin-bottom:12px;display:block;"></i>\r\n'
    '                    <p style="font-weight:600;">No bookings in this queue.</p></div>`;\r\n'
    '                return;\r\n'
    '            }\r\n'
    '            list.innerHTML = filtered.map(b => `\r\n'
    '                <div class="stat-card" style="padding: 20px; margin-bottom: 16px;">\r\n'
    '                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">\r\n'
    '                        <div>\r\n'
    '                            <span style="font-size: 0.7rem; color: var(--text-muted); font-weight: 800; letter-spacing: 0.5px;">#${b.id}</span>\r\n'
    '                            <h4 style="font-size: 1.1rem; font-weight: 800; margin-top: 2px;">${b.customer_name || \'Guest User\'}</h4>\r\n'
    '                        </div>\r\n'
    '                        <span class="pill ${this.getPillClass(b.status)}">${b.status || \'PENDING\'}</span>\r\n'
    '                    </div>\r\n'
    '                    <div style="display: flex; gap: 14px; margin-bottom: 20px; background: rgba(255,255,255,0.03); padding: 12px; border-radius: 12px;">\r\n'
    '                        <div style="width: 44px; height: 44px; background: rgba(99,102,241,0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center;">\r\n'
    '                            <i class="fas fa-car" style="font-size: 1.2rem; color: var(--primary);"></i>\r\n'
    '                        </div>\r\n'
    '                        <div style="flex: 1;">\r\n'
    '                            <p style="font-size: 0.9rem; font-weight: 700; color: var(--text-main);">${b.car || \'Unknown Vehicle\'}</p>\r\n'
    '                            <p style="font-size: 0.75rem; color: var(--text-muted);">\r\n'
    '                                <i class="far fa-calendar-alt" style="margin-right:4px;"></i>\r\n'
    '                                ${b.start_date ? new Date(b.start_date).toLocaleDateString() : \'N/A\'} - ${b.end_date ? new Date(b.end_date).toLocaleDateString() : \'N/A\'}\r\n'
    '                            </p>\r\n'
    '                        </div>\r\n'
    '                    </div>\r\n'
    '                    <div style="padding-top: 16px; border-top: 1px solid var(--border);">\r\n'
    '                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">\r\n'
    '                            <div style="font-size: 1.2rem; font-weight: 900; color: var(--success);">&#8369;${parseFloat(b.total_price||0).toLocaleString()}</div>\r\n'
    '                            <button onclick="Bookings.view(${b.id})" class="btn-outline" style="padding: 8px 14px; font-size: 0.72rem; font-weight: 700; border-radius: 10px;">\r\n'
    '                                <i class="fas fa-eye" style="margin-right:4px;"></i>Details\r\n'
    '                            </button>\r\n'
    '                        </div>\r\n'
    '                        <div style="display:flex; gap:8px; flex-wrap:wrap;">\r\n'
    '                            ${b.status?.toLowerCase() === \'pending\' ? `\r\n'
    '                                <button onclick="Bookings.approve(${b.id})" style="flex:1; min-width:100px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;">\r\n'
    '                                    <i class="fas fa-check" style="margin-right:4px;"></i>Approve\r\n'
    '                                </button>\r\n'
    '                                <button onclick="Bookings.reject(${b.id})" style="flex:1; min-width:100px; padding:10px 8px; background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;">\r\n'
    '                                    <i class="fas fa-times" style="margin-right:4px;"></i>Reject\r\n'
    '                                </button>\r\n'
    '                            ` : \'\'}\r\n'
    '                            ${(b.status?.toLowerCase() === \'confirmed\' || b.status?.toLowerCase() === \'approved\') ? `\r\n'
    '                                <button onclick="Inspections.openModal(${b.id}, \'pickup\')" style="flex:1; min-width:110px; padding:10px 8px; background:var(--amber,#f59e0b); color:white; border:none; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;">\r\n'
    '                                    <i class="fas fa-search-plus" style="margin-right:4px;"></i>Pickup Inspect\r\n'
    '                                </button>\r\n'
    '                                <button onclick="Bookings.pickup(${b.id})" style="flex:1; min-width:110px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;">\r\n'
    '                                    <i class="fas fa-car" style="margin-right:4px;"></i>Mark Picked Up\r\n'
    '                                </button>\r\n'
    '                            ` : \'\'}\r\n'
    '                            ${(b.status?.toLowerCase() === \'picked up\' || b.status?.toLowerCase() === \'ongoing\') ? `\r\n'
    '                                <button onclick="Inspections.openModal(${b.id}, \'return\')" style="flex:1; min-width:110px; padding:10px 8px; background:var(--amber,#f59e0b); color:white; border:none; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;">\r\n'
    '                                    <i class="fas fa-clipboard-check" style="margin-right:4px;"></i>Return Inspect\r\n'
    '                                </button>\r\n'
    '                                <button onclick="Bookings.complete(${b.id})" style="flex:1; min-width:110px; padding:10px 8px; background:var(--primary); color:white; border:none; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer;">\r\n'
    '                                    <i class="fas fa-flag-checkered" style="margin-right:4px;"></i>Mark Returned\r\n'
    '                                </button>\r\n'
    '                            ` : \'\'}\r\n'
    '                        </div>\r\n'
    '                    </div>\r\n'
    '                </div>\r\n'
    '            `).join(\'\');\r\n'
    '        },\r\n'
    '        render()'
)

if old_set_filter_end in content:
    content = content.replace(old_set_filter_end, new_methods, 1)
    print('Step 3: setNewFilter + renderNew methods added')
else:
    print('ERROR: setFilter end pattern not found')
    idx = content.find('this.render();\r\n        },\r\n        render()')
    print('  idx:', idx)

# ?? 4. Update switchBookingTab to handle 'new' tab ??
old_switch_end = (
    '        } else if (tab === \'all\') {\r\n'
    '            const allTab = document.getElementById(\'tabAll\');\r\n'
    '            if (allTab) allTab.style.display = \'block\';\r\n'
    '            const allBtn = document.getElementById(\'tabBtnAll\');\r\n'
    '            if (allBtn) {\r\n'
    '                allBtn.style.border = \'1px solid var(--primary)\';\r\n'
    '                allBtn.style.background = \'var(--primary)\';\r\n'
    '                allBtn.style.color = \'white\';\r\n'
    '            }\r\n'
    '            // Refresh all bookings\r\n'
    '            if (typeof Bookings !== \'undefined\') {\r\n'
    '                Bookings.render();\r\n'
    '            }\r\n'
    '        }\r\n'
    '    };'
)

new_switch_end = (
    '        } else if (tab === \'new\') {\r\n'
    '            const newTab = document.getElementById(\'tabNew\');\r\n'
    '            if (newTab) newTab.style.display = \'block\';\r\n'
    '            const newBtn = document.getElementById(\'tabBtnNew\');\r\n'
    '            if (newBtn) {\r\n'
    '                newBtn.style.border = \'1px solid var(--primary)\';\r\n'
    '                newBtn.style.background = \'var(--primary)\';\r\n'
    '                newBtn.style.color = \'white\';\r\n'
    '            }\r\n'
    '            if (typeof Bookings !== \'undefined\') {\r\n'
    '                Bookings.renderNew();\r\n'
    '            }\r\n'
    '        } else if (tab === \'all\') {\r\n'
    '            const allTab = document.getElementById(\'tabAll\');\r\n'
    '            if (allTab) allTab.style.display = \'block\';\r\n'
    '            const allBtn = document.getElementById(\'tabBtnAll\');\r\n'
    '            if (allBtn) {\r\n'
    '                allBtn.style.border = \'1px solid var(--primary)\';\r\n'
    '                allBtn.style.background = \'var(--primary)\';\r\n'
    '                allBtn.style.color = \'white\';\r\n'
    '            }\r\n'
    '            if (typeof Bookings !== \'undefined\') {\r\n'
    '                Bookings.render();\r\n'
    '            }\r\n'
    '        }\r\n'
    '    };'
)

if old_switch_end in content:
    content = content.replace(old_switch_end, new_switch_end, 1)
    print('Step 4: switchBookingTab updated for new tab')
else:
    print('ERROR: switchBookingTab end not found')

# ?? 5. Also call renderNew() after Bookings.refresh() so badge updates ??
old_render_call = (
    '                this.render();\r\n'
    '                ActiveNow.render(this.data);'
)
new_render_call = (
    '                this.render();\r\n'
    '                this.renderNew();\r\n'
    '                ActiveNow.render(this.data);'
)
if old_render_call in content:
    content = content.replace(old_render_call, new_render_call, 1)
    print('Step 5: renderNew() called after refresh')
else:
    print('Step 5: pattern not found (ok, will update manually)')

with open('admin_mobile/www/index.html', 'wb') as f:
    f.write(content.encode('cp1252'))
print('Saved')
