import sys
import shutil

print("Executing Pickup & Return updates on admin_app/index.html...")

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def find_line(sub, start_from=0):
    for i in range(start_from, len(lines)):
        if sub in lines[i]:
            return i
    raise ValueError(f"Substring not found: {sub}")

# =========================================================================
# 1. Update #newBookingsSort options
# =========================================================================
idx_new_sort = find_line('id="newBookingsSort"')
idx_new_date_asc = find_line('<option value="date_asc">Date (Oldest)</option>', idx_new_sort)
lines.insert(idx_new_date_asc + 1, """                        <option value="pickup_asc">🚗 Pickup (Soonest / Malapit na)</option>
                        <option value="return_asc">🔄 Return (Due Soonest / Malapit na)</option>\n""")
print("[OK] Added pickup_asc & return_asc to #newBookingsSort.")

# =========================================================================
# 2. Update #allBookingsSort options
# =========================================================================
idx_all_sort = find_line('id="allBookingsSort"')
idx_all_date_asc = find_line('<option value="date_asc">Date (Oldest)</option>', idx_all_sort)
lines.insert(idx_all_date_asc + 1, """                        <option value="pickup_asc">🚗 Pickup (Soonest / Malapit na)</option>
                        <option value="return_asc">🔄 Return (Due Soonest / Malapit na)</option>\n""")
print("[OK] Added pickup_asc & return_asc to #allBookingsSort.")

# =========================================================================
# 3. Add 'Pickup Soon' & 'Return Soon' chips in #tabNew
# =========================================================================
idx_tab_new = find_line('<div id="tabNew"')
idx_nb_pending = find_line('data-filter="pending"', idx_tab_new)
lines.insert(idx_nb_pending + 1, """                <button class="nb-chip" data-filter="pickup_soon" onclick="Bookings.setNewFilter('pickup_soon',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;"><i class="fas fa-calendar-check" style="margin-right:5px;color:var(--primary);"></i>Pickup Soon</button>
                <button class="nb-chip" data-filter="return_soon" onclick="Bookings.setNewFilter('return_soon',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;"><i class="fas fa-undo-alt" style="margin-right:5px;color:#d97706;"></i>Return Soon</button>\n""")
print("[OK] Added Pickup Soon & Return Soon chips in #tabNew.")

# =========================================================================
# 4. Add 'Pickup Soon' & 'Return Soon' chips in #tabAll
# =========================================================================
idx_tab_all = find_line('<div id="tabAll"')
idx_bk_all = find_line('data-filter="all"', idx_tab_all)
lines.insert(idx_bk_all + 1, """                <button class="bk-chip" data-filter="pickup_soon" onclick="Bookings.setFilter('pickup_soon',this)" style="flex-shrink:0;padding:8px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;"><i class="fas fa-calendar-check" style="margin-right:5px;color:var(--primary);"></i>Pickup Soon</button>
                <button class="bk-chip" data-filter="return_soon" onclick="Bookings.setFilter('return_soon',this)" style="flex-shrink:0;padding:8px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;"><i class="fas fa-undo-alt" style="margin-right:5px;color:#d97706;"></i>Return Soon</button>\n""")
print("[OK] Added Pickup Soon & Return Soon chips in #tabAll.")

# =========================================================================
# 5. Add getPickupTime & getReturnTime to Bookings JS
# =========================================================================
idx_bk_obj = find_line('const Bookings = {')
idx_get_date = find_line('getDate(b) {', idx_bk_obj)
# find closing brace of getDate
idx_get_date_end = find_line('},', idx_get_date)

lines.insert(idx_get_date_end + 1, """\n        getPickupTime(b) {
            if (!b.start_date) return Infinity;
            const timeStr = b.start_time ? String(b.start_time).substring(0, 5) : '00:00';
            const dateStr = String(b.start_date).split('T')[0];
            const ts = new Date(`${dateStr}T${timeStr}:00`).getTime();
            return isNaN(ts) ? (new Date(b.start_date).getTime() || Infinity) : ts;
        },

        getReturnTime(b) {
            if (!b.end_date) return Infinity;
            const timeStr = b.end_time ? String(b.end_time).substring(0, 5) : '23:59';
            const dateStr = String(b.end_date).split('T')[0];
            const ts = new Date(`${dateStr}T${timeStr}:00`).getTime();
            return isNaN(ts) ? (new Date(b.end_date).getTime() || Infinity) : ts;
        },\n""")
print("[OK] Inserted getPickupTime and getReturnTime into Bookings.")

# =========================================================================
# 6. Add pickup_asc & return_asc to sortBookings
# =========================================================================
idx_sort_bk = find_line('sortBookings(list, sortKey) {', idx_bk_obj)
idx_case_date_asc = find_line("case 'date_asc':", idx_sort_bk)

lines.insert(idx_case_date_asc + 1, """                case 'pickup_asc':
                    return copy.sort((a, b) => this.getPickupTime(a) - this.getPickupTime(b));
                case 'return_asc':
                    return copy.sort((a, b) => this.getReturnTime(a) - this.getReturnTime(b));\n""")
print("[OK] Inserted pickup_asc and return_asc cases into sortBookings.")

# =========================================================================
# 7. Update Bookings.renderNew() filter logic
# =========================================================================
idx_render_new = find_line('renderNew() {', idx_bk_obj)
idx_rn_filter_check = find_line("if (this._newFilter !== 'all') {", idx_render_new)
idx_rn_sort_call = find_line("filtered = this.sortBookings(filtered, this._newSortBy || 'date_desc');", idx_rn_filter_check)

new_rn_filter_block = """            if (this._newFilter === 'pickup_soon') {
                const pickupStatuses = ['confirmed', 'approved', 'pending'];
                filtered = filtered.filter(b => pickupStatuses.includes((b.status || '').toLowerCase()));
                const sortKey = (this._newSortBy && this._newSortBy !== 'date_desc') ? this._newSortBy : 'pickup_asc';
                filtered = this.sortBookings(filtered, sortKey);
            } else if (this._newFilter === 'return_soon') {
                const returnStatuses = ['picked up', 'ongoing'];
                filtered = filtered.filter(b => returnStatuses.includes((b.status || '').toLowerCase()));
                const sortKey = (this._newSortBy && this._newSortBy !== 'date_desc') ? this._newSortBy : 'return_asc';
                filtered = this.sortBookings(filtered, sortKey);
            } else if (this._newFilter !== 'all') {
                filtered = filtered.filter(b => {
                    const s = (b.status||'').toLowerCase().replace(' ', '_');
                    return s === this._newFilter || (b.status||'') === statusMap[this._newFilter];
                });
                filtered = this.sortBookings(filtered, this._newSortBy || 'date_desc');
            } else {
                filtered = this.sortBookings(filtered, this._newSortBy || 'date_desc');
            }\n"""

lines[idx_rn_filter_check:idx_rn_sort_call+1] = [new_rn_filter_block]
print("[OK] Updated Bookings.renderNew() filter logic.")

# =========================================================================
# 8. Update Bookings.render() filter logic for #tabAll
# =========================================================================
idx_render_all = find_line('render() {', idx_render_new + 20)
idx_all_filter_check = find_line("const filtered = this._filter === 'all' ?", idx_render_all)
idx_all_sort_call = find_line("const sorted = this.sortBookings(filtered, this._sortBy || 'date_desc');", idx_all_filter_check)

new_all_filter_block = """            // Apply status filter
            const statusMap = { pending: 'Pending', confirmed: 'Confirmed', approved: 'Approved', picked_up: 'Picked Up', completed: 'Completed', cancelled: 'Cancelled' };
            let filteredList = this.data;
            let activeSortKey = this._sortBy || 'date_desc';

            if (this._filter === 'pickup_soon') {
                const pickupStatuses = ['confirmed', 'approved', 'pending'];
                filteredList = this.data.filter(b => pickupStatuses.includes((b.status || '').toLowerCase()));
                if (!this._sortBy || this._sortBy === 'date_desc') activeSortKey = 'pickup_asc';
            } else if (this._filter === 'return_soon') {
                const returnStatuses = ['picked up', 'ongoing'];
                filteredList = this.data.filter(b => returnStatuses.includes((b.status || '').toLowerCase()));
                if (!this._sortBy || this._sortBy === 'date_desc') activeSortKey = 'return_asc';
            } else if (this._filter !== 'all') {
                filteredList = this.data.filter(b => {
                    const s = (b.status||'').toLowerCase().replace(' ', '_');
                    return s === this._filter || (b.status||'') === statusMap[this._filter];
                });
            }

            // Apply selected sorting to all bookings
            const sorted = this.sortBookings(filteredList, activeSortKey);\n"""

lines[idx_all_filter_check:idx_all_sort_call+1] = [new_all_filter_block]
print("[OK] Updated Bookings.render() filter logic.")

# =========================================================================
# 9. Add Card Urgency Badges (Pickup Soon / Return Soon / Overdue) to Cards
# =========================================================================
# Update in renderNew:
idx_rn_pill = find_line('class="pill ${this.getPillClass(b.status)}"', idx_render_new)
# Update in render:
idx_all_pill = find_line('class="pill ${this.getPillClass(b.status)}"', idx_render_all)

urgency_badge_snippet = """                        <div style="display:flex;align-items:center;flex-wrap:wrap;justify-content:flex-end;gap:5px;">
                            ${(() => {
                                const now = Date.now();
                                const pTime = Bookings.getPickupTime(b);
                                const rTime = Bookings.getReturnTime(b);
                                const st = (b.status || '').toLowerCase();
                                if (['picked up', 'ongoing'].includes(st)) {
                                    if (rTime < now) {
                                        return `<span style="background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.35);padding:2px 8px;border-radius:12px;font-size:0.62rem;font-weight:800;display:inline-flex;align-items:center;gap:4px;"><i class="fas fa-exclamation-circle"></i> RETURN OVERDUE</span>`;
                                    } else if (rTime - now <= 36 * 3600 * 1000) {
                                        return `<span style="background:rgba(245,158,11,0.15);color:#d97706;border:1px solid rgba(245,158,11,0.35);padding:2px 8px;border-radius:12px;font-size:0.62rem;font-weight:800;display:inline-flex;align-items:center;gap:4px;"><i class="fas fa-undo-alt"></i> RETURN SOON</span>`;
                                    }
                                } else if (['confirmed', 'approved', 'pending'].includes(st)) {
                                    if (pTime >= now - 12 * 3600 * 1000 && pTime - now <= 36 * 3600 * 1000) {
                                        return `<span style="background:rgba(0,177,79,0.15);color:#00B14F;border:1px solid rgba(0,177,79,0.35);padding:2px 8px;border-radius:12px;font-size:0.62rem;font-weight:800;display:inline-flex;align-items:center;gap:4px;"><i class="fas fa-clock"></i> PICKUP SOON</span>`;
                                    }
                                }
                                return '';
                            })()}
                            <span class="pill ${this.getPillClass(b.status)}">${b.status || 'PENDING'}</span>
                        </div>\n"""

# Replace in renderAll first (higher line number)
lines[idx_all_pill] = urgency_badge_snippet
# Replace in renderNew
lines[idx_rn_pill] = urgency_badge_snippet
print("[OK] Inserted visual urgency badges in both renderNew and render.")

# =========================================================================
# 10. Update ActiveNow to sort by return date (due soonest first)
# =========================================================================
idx_active_now_obj = find_line('const ActiveNow = {')
idx_an_filter = find_line('const active = (allBookings || []).filter(b =>', idx_active_now_obj)
idx_an_filter_end = find_line(');', idx_an_filter)

new_an_filter_block = """            const active = (allBookings || []).filter(b =>
                b.status === 'Picked Up' || b.status === 'Ongoing'
            );

            // Prioritize due returns (closest return date & time first)
            active.sort((a, b) => {
                const getRet = (x) => {
                    if (!x.end_date) return Infinity;
                    const t = x.end_time ? String(x.end_time).substring(0, 5) : '23:59';
                    const ds = String(x.end_date).split('T')[0];
                    const ts = new Date(`${ds}T${t}:00`).getTime();
                    return isNaN(ts) ? new Date(x.end_date).getTime() : ts;
                };
                return getRet(a) - getRet(b);
            });\n"""

lines[idx_an_filter:idx_an_filter_end+1] = [new_an_filter_block]
print("[OK] Updated ActiveNow.render to sort by return date due soonest.")

# Write updated file
with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("[SUCCESS] admin_app/index.html updated successfully!")

shutil.copyfile('admin_app/index.html', 'admin_mobile/www/index.html')
print("[SUCCESS] admin_mobile/www/index.html synchronized!")
