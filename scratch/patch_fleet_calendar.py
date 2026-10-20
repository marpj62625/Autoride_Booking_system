import os

def patch_file(filepath):
    print(f"Patching {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add getTimeHalf if not present
    if 'getTimeHalf(timeStr,' not in content:
        old_hash = """            return this.paletteColors[Math.abs(hash) % this.paletteColors.length];
        },"""
        new_hash = """            return this.paletteColors[Math.abs(hash) % this.paletteColors.length];
        },

        getTimeHalf(timeStr, defaultHalf = 'AM') {
            if (!timeStr) return defaultHalf;
            let s = String(timeStr).trim().toLowerCase();
            if (s.includes('am')) return 'AM';
            if (s.includes('pm')) return 'PM';
            const parts = s.split(':').map(Number);
            if (!isNaN(parts[0])) return parts[0] >= 12 ? 'PM' : 'AM';
            return defaultHalf;
        },"""
        if old_hash in content:
            content = content.replace(old_hash, new_hash, 1)
            print("  Added getTimeHalf")
        else:
            print("  Warning: old_hash not found")

    # 2. Replace Header generation
    old_header_start = "            // 2-Tier Header:"
    old_header_end = "            const headerRowEl = document.getElementById('fleetCalendarHeaderRow');\n            if (headerRowEl) headerRowEl.innerHTML = row2Html;"

    new_header_block = """            // 2-Tier Header:
            // Row 1: Day Name & Number (Colspan 2 for AM and PM)
            // Left sticky cell spans 2 rows
            let row1Html = `<th rowspan="2" class="fc-vcol fc-vhead" style="padding: 10px 12px; border: 1px solid var(--border); text-align: left; background: var(--surface-solid); font-weight: 800; min-width: 180px; width: 180px; max-width: 180px; position: sticky; left: 0; z-index: 20; border-right: 2px solid var(--border); color: var(--text-main); font-size: 0.8rem; vertical-align: middle;">
                <div style="display:flex; align-items:center; gap:6px;">
                    <i class="fas fa-car-side" style="color:#00B14F;"></i>
                    <span class="fc-vhead-text">VEHICLE / UNIT</span>
                </div>
            </th>`;

            // Row 2: Sub-columns for AM and PM
            let row2Html = '';

            for (let d = 1; d <= daysInMonth; d++) {
                const dayDate = new Date(year, month, d);
                const dayOfWeek = dayDate.getDay();
                const isWeekend = (dayOfWeek === 0 || dayOfWeek === 6);
                const isToday = isCurrentMonth && today.getDate() === d;
                
                const dowBg = isToday ? 'rgba(0,177,79,0.18)' : (isWeekend ? 'rgba(239, 68, 68, 0.08)' : 'var(--surface-solid)');
                const dowColor = isToday ? '#00B14F' : (isWeekend ? '#ef4444' : 'var(--text-muted)');
                const dateBg = isToday ? 'rgba(0,177,79,0.22)' : (isWeekend ? 'rgba(239, 68, 68, 0.04)' : 'var(--surface-solid)');
                const dateColor = isToday ? '#00B14F' : 'var(--text-main)';

                row1Html += `<th colspan="2" style="padding: 4px 2px; border: 1px solid var(--border); text-align: center; background: ${dowBg};">
                    <div style="font-weight: 800; font-size: 0.62rem; color: ${dowColor}; text-transform: uppercase;">${dayNamesShort[dayOfWeek]}</div>
                    <div style="font-weight: 900; font-size: 0.82rem; color: ${dateColor}; line-height: 1.1;">${d}</div>
                </th>`;

                row2Html += `<th style="padding: 2px; border: 1px solid var(--border); border-right: 1px dashed var(--border); border-bottom: 2px solid var(--border); text-align: center; font-weight: 800; font-size: 0.58rem; min-width: 28px; width: 28px; background: ${dateBg}; color: ${isToday ? '#00B14F' : 'var(--text-muted)'};">AM</th>`;
                row2Html += `<th style="padding: 2px; border: 1px solid var(--border); border-bottom: 2px solid var(--border); text-align: center; font-weight: 800; font-size: 0.58rem; min-width: 28px; width: 28px; background: ${dateBg}; color: ${isToday ? '#00B14F' : 'var(--text-muted)'};">PM</th>`;
            }

            const daysOfWeekEl = document.getElementById('fleetCalendarDaysOfWeekRow');
            if (daysOfWeekEl) daysOfWeekEl.innerHTML = row1Html;
            const headerRowEl = document.getElementById('fleetCalendarHeaderRow');
            if (headerRowEl) headerRowEl.innerHTML = row2Html;"""

    if old_header_start in content and old_header_end in content:
        start_idx = content.find(old_header_start)
        end_idx = content.find(old_header_end) + len(old_header_end)
        content = content[:start_idx] + new_header_block + content[end_idx:]
        print("  Updated Header generation successfully")
    else:
        print("  Warning: Header block not found")

    # 3. Replace Body rows generation
    old_body_start = "            // Render Body Rows (Gantt Schedule with Colspan)"
    old_body_end = "            const bodyEl = document.getElementById('fleetCalendarBody');\n            if (bodyEl) bodyEl.innerHTML = bodyHtml;"

    new_body_block = """            const totalSlots = daysInMonth * 2;
            const mStart = new Date(year, month, 1, 0, 0, 0);
            const mEnd = new Date(year, month, daysInMonth, 23, 59, 59);

            // Render Body Rows (Gantt Schedule with Colspan - AM & PM slots)
            let bodyHtml = "";
            filteredVehicles.forEach(v => {
                let rowHtml = `<tr style="border-bottom: 1px solid var(--border); transition: background 0.15s; height: 54px;">`;
                
                // Sticky Vehicle Cell (Green Box matching Excel reference with live daily rate & quick edit icon)
                rowHtml += `<td class="fc-vcol" onmouseenter="FleetCalendar.showVehicleTooltip(event, ${v.id})" onmouseleave="FleetCalendar.hideTooltip()" onclick="FleetCalendar.handleVehicleClick(event, ${v.id})"
                    style="padding: 6px 8px; border: 1px solid var(--border); background: var(--surface-solid); position: sticky; left: 0; z-index: 10; box-shadow: 2px 0 5px rgba(0,0,0,0.06); border-right: 2px solid var(--border); min-width: 180px; width: 180px; max-width: 180px; cursor: pointer; vertical-align: middle;" title="Click to view details or change vehicle daily rate">
                    <div class="fc-vbox" style="background: #15803d; color: white; padding: 5px 8px; border-radius: 8px; font-weight: 800; font-size: 0.72rem; text-shadow: 0 1px 2px rgba(0,0,0,0.3); line-height: 1.25; box-shadow: 0 2px 4px rgba(0,0,0,0.12); display: flex; flex-direction: column; justify-content: center; transition: transform 0.15s, box-shadow 0.15s;"
                         onmouseover="this.style.transform='scale(1.02)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)';"
                         onmouseout="this.style.transform='none'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.12)';">
                        <div class="fc-vname" style="font-weight: 900; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; letter-spacing: 0.2px;">${v.brand} ${v.model}</div>
                        <div class="fc-vmeta" style="display: flex; align-items: center; justify-content: space-between; gap: 4px; margin-top: 3px;">
                            <span style="font-size: 0.62rem; color: #bbf7d0; font-weight: 700; letter-spacing: 0.3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${v.plate_number || 'NO PLATE'}</span>
                            <span style="font-size: 0.62rem; color: #fef08a; font-weight: 800; background: rgba(0,0,0,0.25); padding: 1px 5px; border-radius: 4px; white-space: nowrap; display: inline-flex; align-items: center; gap: 3px;" title="Daily Rental Rate">
                                ₱${parseFloat(v.daily_rate||0).toLocaleString()}/d <i class="fas fa-edit fc-vedit" style="font-size: 0.55rem; opacity: 0.85;"></i>
                            </span>
                        </div>
                    </div>
                </td>`;

                // Calculate slot ranges for all active bookings of vehicle v
                const vBookings = (this.bookings || []).filter(bk => {
                    if (String(bk.vehicle_id) !== String(v.id)) return false;
                    if (bk.status === 'cancelled' || bk.status === 'rejected') return false;
                    return true;
                }).map(bk => {
                    const sStr = String(bk.start_date || '').split('T')[0];
                    const eStr = String(bk.end_date || '').split('T')[0];
                    const sParts = sStr.split('-').map(Number);
                    const eParts = eStr.split('-').map(Number);
                    if (sParts.length < 3 || eParts.length < 3) return null;

                    const bStart = new Date(sParts[0], sParts[1] - 1, sParts[2]);
                    const bEnd = new Date(eParts[0], eParts[1] - 1, eParts[2]);
                    if (bEnd < mStart || bStart > mEnd) return null;

                    let startSlot = 0;
                    if (bStart >= mStart) {
                        const half = FleetCalendar.getTimeHalf(bk.start_time, 'AM');
                        startSlot = (bStart.getDate() - 1) * 2 + (half === 'PM' ? 1 : 0);
                    }
                    let endSlot = totalSlots - 1;
                    if (bEnd <= mEnd) {
                        const half = FleetCalendar.getTimeHalf(bk.end_time, 'PM');
                        endSlot = (bEnd.getDate() - 1) * 2 + (half === 'PM' ? 1 : 0);
                    }
                    if (endSlot < startSlot) endSlot = startSlot;
                    return { booking: bk, startSlot, endSlot };
                }).filter(Boolean);

                // Sort by startSlot
                vBookings.sort((a, b) => a.startSlot - b.startSlot);

                // Calculate blackout slot ranges
                const vBlackouts = (this.blackouts || []).filter(bo => {
                    const isAff = !bo.affected_vehicles || bo.affected_vehicles === 'all' || 
                                  bo.affected_vehicles.split(',').map(s => s.trim()).includes(String(v.id));
                    return isAff;
                }).map(bo => {
                    const sStr = String(bo.start_date || '').split('T')[0];
                    const eStr = String(bo.end_date || '').split('T')[0];
                    const sParts = sStr.split('-').map(Number);
                    const eParts = eStr.split('-').map(Number);
                    if (sParts.length < 3 || eParts.length < 3) return null;

                    const bStart = new Date(sParts[0], sParts[1] - 1, sParts[2]);
                    const bEnd = new Date(eParts[0], eParts[1] - 1, eParts[2]);
                    if (bEnd < mStart || bStart > mEnd) return null;

                    let startSlot = 0;
                    if (bStart >= mStart) startSlot = (bStart.getDate() - 1) * 2;
                    let endSlot = totalSlots - 1;
                    if (bEnd <= mEnd) endSlot = (bEnd.getDate() - 1) * 2 + 1;
                    if (endSlot < startSlot) endSlot = startSlot;
                    return { blackout: bo, startSlot, endSlot };
                }).filter(Boolean);

                // Render slots 0 to totalSlots - 1
                let s = 0;
                while (s < totalSlots) {
                    const d = Math.floor(s / 2) + 1;
                    const half = (s % 2 === 0) ? 'AM' : 'PM';
                    const dayDate = new Date(year, month, d);
                    const dow = dayDate.getDay();
                    const isWeekend = (dow === 0 || dow === 6);

                    // 1. Check booking covering slot s
                    const bkItem = vBookings.find(item => item.startSlot <= s && s <= item.endSlot);
                    if (bkItem) {
                        const bk = bkItem.booking;
                        const spanSlots = Math.min(bkItem.endSlot - s + 1, totalSlots - s);
                        const color = this.getBookingColor(bk);
                        const custName = (bk.customer_name || 'Customer').toUpperCase();
                        const rate = parseFloat(bk.total_price || 0);
                        const paid = parseFloat(bk.amount_paid || 0);
                        const bal = parseFloat(bk.balance_amount !== undefined ? bk.balance_amount : Math.max(0, rate - paid));

                        rowHtml += `<td colspan="${spanSlots}"
                            onclick="FleetCalendar.openBookingQuickModal(${bk.id})"
                            onmouseenter="FleetCalendar.showBookingTooltip(event, ${bk.id})"
                            onmouseleave="FleetCalendar.hideTooltip()"
                            style="padding: 2px 3px; border: 1px solid rgba(0,0,0,0.12); cursor: pointer; vertical-align: middle; height: 54px;">
                            <div style="background: ${color.bg}; color: ${color.text}; border: 1.5px solid ${color.border}; border-radius: 8px; padding: 4px 6px; font-weight: 800; line-height: 1.25; box-shadow: 0 2px 5px rgba(0,0,0,0.1); height: calc(100% - 2px); display: flex; flex-direction: column; justify-content: center; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; transition: transform 0.15s, box-shadow 0.15s;"
                                 onmouseover="this.style.transform='scale(1.01)'; this.style.boxShadow='0 4px 10px rgba(0,0,0,0.18)';"
                                 onmouseout="this.style.transform='none'; this.style.boxShadow='0 2px 5px rgba(0,0,0,0.1)';">
                                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: ${spanSlots === 1 ? '0.62rem' : '0.76rem'}; font-weight: 900; letter-spacing: 0.2px;">
                                    <i class="fas fa-user" style="font-size: 0.6rem; margin-right: 3px; opacity: 0.85;"></i>${custName}
                                </div>
                                <div style="font-size: 0.62rem; font-weight: 800; opacity: 0.95; display: flex; align-items: center; gap: 4px; margin-top: 1px; overflow: hidden;">
                                    <span>₱${Math.round(rate).toLocaleString()}</span>
                                    ${spanSlots > 1 ? (bal > 0 
                                        ? `<span style="background: #ef4444; color: white; padding: 1px 4px; border-radius: 4px; font-size: 0.55rem; font-weight: 800;">Bal: ₱${Math.round(bal).toLocaleString()}</span>` 
                                        : `<span style="background: #16a34a; color: white; padding: 1px 4px; border-radius: 4px; font-size: 0.55rem; font-weight: 800;">PAID</span>`) : ''
                                    }
                                </div>
                            </div>
                        </td>`;

                        s += spanSlots;
                        continue;
                    }

                    // 2. Check blackout covering slot s
                    const boItem = vBlackouts.find(item => item.startSlot <= s && s <= item.endSlot);
                    if (boItem) {
                        const spanSlots = Math.min(boItem.endSlot - s + 1, totalSlots - s);
                        rowHtml += `<td colspan="${spanSlots}" style="padding: 0; border: 1px solid var(--border); text-align: center; background: repeating-linear-gradient(45deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.15) 5px, rgba(239, 68, 68, 0.28) 5px, rgba(239, 68, 68, 0.28) 10px); min-width: 28px; height: 54px;" title="Blackout Blocked">
                            <span style="background: rgba(239,68,68,0.2); color: #dc2626; font-size: 0.58rem; font-weight: 800; padding: 1px 3px; border-radius: 4px;">OFF</span>
                        </td>`;
                        s += spanSlots;
                        continue;
                    }

                    // 3. Empty slot
                    const borderRight = (half === 'AM') ? '1px dashed var(--border)' : '1.5px solid var(--border)';
                    rowHtml += `<td style="padding: 0; border: 1px solid var(--border); border-right: ${borderRight}; text-align: center; min-width: 28px; width: 28px; height: 54px; background: ${isWeekend ? 'rgba(0,0,0,0.015)' : 'transparent'};"></td>`;
                    s++;
                }

                rowHtml += `</tr>`;
                bodyHtml += rowHtml;
            });

            if (filteredVehicles.length === 0) {
                bodyHtml = `<tr><td colspan="${totalSlots + 1}" style="text-align: center; padding: 40px; color: var(--text-muted); font-size: 0.88rem;">No vehicles or bookings matching "${this.searchQuery}"</td></tr>`;
            }
            
            const bodyEl = document.getElementById('fleetCalendarBody');
            if (bodyEl) bodyEl.innerHTML = bodyHtml;"""

    if old_body_start in content and old_body_end in content:
        start_idx = content.find(old_body_start)
        end_idx = content.find(old_body_end) + len(old_body_end)
        content = content[:start_idx] + new_body_block + content[end_idx:]
        print("  Updated Body rows generation successfully")
    else:
        print("  Warning: Body block not found")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Done patching {filepath}!")

if __name__ == '__main__':
    patch_file('AutorideSystem/admin_app/index.html')
    patch_file('AutorideSystem/admin_mobile/www/index.html')
