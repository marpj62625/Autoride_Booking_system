import sys
import shutil

print("Applying Pickup & Return filters and sort enhancements...")

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# =========================================================================
# 1. Update Sort options in #newBookingsSort and #allBookingsSort
# =========================================================================
old_sort_options = """                        <option value="date_desc">Date (Newest)</option>
                        <option value="date_asc">Date (Oldest)</option>
                        <option value="name_asc">Name (A–Z)</option>"""

new_sort_options = """                        <option value="date_desc">Date (Newest)</option>
                        <option value="date_asc">Date (Oldest)</option>
                        <option value="pickup_asc">🚗 Pickup (Soonest / Malapit na)</option>
                        <option value="return_asc">🔄 Return (Due Soonest / Malapit na)</option>
                        <option value="name_asc">Name (A–Z)</option>"""

count_sort = content.count(old_sort_options)
print(f"Found old_sort_options in {count_sort} places (expected 2: newBookingsSort and allBookingsSort)")
if count_sort == 2:
    content = content.replace(old_sort_options, new_sort_options)
    print("[OK] Updated sort dropdown options.")
else:
    print(f"[WARN] count_sort was {count_sort}")

# =========================================================================
# 2. Add 'Pickup Soon' & 'Return Soon' chips in #tabNew
# =========================================================================
old_tab_new_chips = """                <button class="nb-chip nb-chip-active" data-filter="pending" onclick="Bookings.setNewFilter('pending',this)" style="flex-shrink:0;padding:7px 14px;background:var(--primary);color:white;border:1px solid var(--primary);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">New</button>
                <button class="nb-chip" data-filter="confirmed" onclick="Bookings.setNewFilter('confirmed',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">Confirmed</button>"""

new_tab_new_chips = """                <button class="nb-chip nb-chip-active" data-filter="pending" onclick="Bookings.setNewFilter('pending',this)" style="flex-shrink:0;padding:7px 14px;background:var(--primary);color:white;border:1px solid var(--primary);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">New</button>
                <button class="nb-chip" data-filter="pickup_soon" onclick="Bookings.setNewFilter('pickup_soon',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;"><i class="fas fa-calendar-check" style="margin-right:5px;color:var(--primary);"></i>Pickup Soon</button>
                <button class="nb-chip" data-filter="return_soon" onclick="Bookings.setNewFilter('return_soon',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;"><i class="fas fa-undo-alt" style="margin-right:5px;color:#d97706;"></i>Return Soon</button>
                <button class="nb-chip" data-filter="confirmed" onclick="Bookings.setNewFilter('confirmed',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">Confirmed</button>"""

if old_tab_new_chips in content:
    content = content.replace(old_tab_new_chips, new_tab_new_chips)
    print("[OK] Added Pickup Soon & Return Soon chips in #tabNew.")
else:
    print("[WARN] old_tab_new_chips not found!")

# =========================================================================
# 3. Add 'Pickup Soon' & 'Return Soon' chips in #tabAll
# =========================================================================
old_tab_all_chips = """                <button class="bk-chip bk-chip-active" data-filter="all" onclick="Bookings.setFilter('all',this)" style="flex-shrink:0;padding:8px 14px;background:var(--primary);color:white;border:1px solid var(--primary);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">All</button>
                <button class="bk-chip" data-filter="pending" onclick="Bookings.setFilter('pending',this)" style="flex-shrink:0;padding:8px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">New</button>"""

new_tab_all_chips = """                <button class="bk-chip bk-chip-active" data-filter="all" onclick="Bookings.setFilter('all',this)" style="flex-shrink:0;padding:8px 14px;background:var(--primary);color:white;border:1px solid var(--primary);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">All</button>
                <button class="bk-chip" data-filter="pickup_soon" onclick="Bookings.setFilter('pickup_soon',this)" style="flex-shrink:0;padding:8px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;"><i class="fas fa-calendar-check" style="margin-right:5px;color:var(--primary);"></i>Pickup Soon</button>
                <button class="bk-chip" data-filter="return_soon" onclick="Bookings.setFilter('return_soon',this)" style="flex-shrink:0;padding:8px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;"><i class="fas fa-undo-alt" style="margin-right:5px;color:#d97706;"></i>Return Soon</button>
                <button class="bk-chip" data-filter="pending" onclick="Bookings.setFilter('pending',this)" style="flex-shrink:0;padding:8px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">New</button>"""

if old_tab_all_chips in content:
    content = content.replace(old_tab_all_chips, new_tab_all_chips)
    print("[OK] Added Pickup Soon & Return Soon chips in #tabAll.")
else:
    print("[WARN] old_tab_all_chips not found!")

# =========================================================================
# 4. Update Bookings object in JS with getPickupTime, getReturnTime, sortBookings
# =========================================================================
old_bk_methods = """        getDate(b) {
            const d = b.created_at || b.start_date || b.booking_date;
            return d ? new Date(d).getTime() : 0;
        },"""

new_bk_methods = """        getDate(b) {
            const d = b.created_at || b.start_date || b.booking_date;
            return d ? new Date(d).getTime() : 0;
        },

        getPickupTime(b) {
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
        },"""

if old_bk_methods in content:
    content = content.replace(old_bk_methods, new_bk_methods)
    print("[OK] Added getPickupTime and getReturnTime to Bookings.")
else:
    print("[WARN] old_bk_methods not found!")

# Update sortBookings cases:
old_sort_cases = """            switch (sortKey) {
                case 'date_asc':
                    return copy.sort((a, b) => this.getDate(a) - this.getDate(b));"""

new_sort_cases = """            switch (sortKey) {
                case 'date_asc':
                    return copy.sort((a, b) => this.getDate(a) - this.getDate(b));
                case 'pickup_asc':
                    return copy.sort((a, b) => this.getPickupTime(a) - this.getPickupTime(b));
                case 'return_asc':
                    return copy.sort((a, b) => this.getReturnTime(a) - this.getReturnTime(b));"""

if old_sort_cases in content:
    content = content.replace(old_sort_cases, new_sort_cases)
    print("[OK] Added pickup_asc and return_asc cases in sortBookings.")
else:
    print("[WARN] old_sort_cases not found!")

# =========================================================================
# 5. Update Bookings.renderNew() filtering logic
# =========================================================================
old_render_new_logic = """            if (this._newFilter !== 'all') {
                filtered = filtered.filter(b => {
                    const s = (b.status||'').toLowerCase().replace(' ', '_');
                    return s === this._newFilter || (b.status||'') === statusMap[this._newFilter];
                });
            }

            // Apply sorting to new bookings
            filtered = this.sortBookings(filtered, this._newSortBy || 'date_desc');"""

new_render_new_logic = """            if (this._newFilter === 'pickup_soon') {
                // Confirmed or approved bookings waiting for pickup
                const pickupStatuses = ['confirmed', 'approved', 'pending'];
                filtered = filtered.filter(b => pickupStatuses.includes((b.status || '').toLowerCase()));
                // If sort isn't explicitly changed, prioritize soonest pickup
                const sortKey = (this._newSortBy && this._newSortBy !== 'date_desc') ? this._newSortBy : 'pickup_asc';
                filtered = this.sortBookings(filtered, sortKey);
            } else if (this._newFilter === 'return_soon') {
                // Picked up or ongoing rentals waiting to be returned
                const returnStatuses = ['picked up', 'ongoing'];
                filtered = filtered.filter(b => returnStatuses.includes((b.status || '').toLowerCase()));
                // If sort isn't explicitly changed, prioritize soonest due return
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
            }"""

if old_render_new_logic in content:
    content = content.replace(old_render_new_logic, new_render_new_logic)
    print("[OK] Updated renderNew() filtering logic for pickup_soon & return_soon.")
else:
    print("[WARN] old_render_new_logic not found!")

# =========================================================================
# 6. Update Bookings.render() filtering logic for #tabAll
# =========================================================================
old_render_logic = """            // Apply status filter
            const statusMap = { pending: 'Pending', confirmed: 'Confirmed', approved: 'Approved', picked_up: 'Picked Up', completed: 'Completed', cancelled: 'Cancelled' };
            const filtered = this._filter === 'all' ? this.data : this.data.filter(b => { const s = (b.status||'').toLowerCase().replace(' ', '_'); return s === this._filter || (b.status||'') === statusMap[this._filter]; });

            // Apply selected sorting to all bookings
            const sorted = this.sortBookings(filtered, this._sortBy || 'date_desc');"""

new_render_logic = """            // Apply status filter
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
            const sorted = this.sortBookings(filteredList, activeSortKey);"""

if old_render_logic in content:
    content = content.replace(old_render_logic, new_render_logic)
    print("[OK] Updated render() filtering logic for #tabAll.")
else:
    print("[WARN] old_render_logic not found!")

# =========================================================================
# 7. Add Visual Urgency Badges (Pickup Soon / Return Soon / Overdue) to Cards
# =========================================================================
old_card_pill = """                        <span class="pill ${this.getPillClass(b.status)}">${b.status || 'PENDING'}</span>"""

new_card_pill = """                        <div style="display:flex;align-items:center;flex-wrap:wrap;justify-content:flex-end;gap:5px;">
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
                        </div>"""

count_pill = content.count(old_card_pill)
print(f"Found old_card_pill in {count_pill} places (renderNew and render)")
if count_pill >= 2:
    content = content.replace(old_card_pill, new_card_pill)
    print("[OK] Added Visual Urgency Badges to booking cards.")
else:
    print(f"[WARN] count_pill was {count_pill}")

# =========================================================================
# 8. Sort ActiveNow by return date (due soonest first)
# =========================================================================
old_active_now = """            const active = (allBookings || []).filter(b =>
                b.status === 'Picked Up' || b.status === 'Ongoing'
            );"""

new_active_now = """            const active = (allBookings || []).filter(b =>
                b.status === 'Picked Up' || b.status === 'Ongoing'
            );

            // Sort by return date (due soonest first so urgent returns are at top)
            active.sort((a, b) => {
                const getRet = (x) => {
                    if (!x.end_date) return Infinity;
                    const t = x.end_time ? String(x.end_time).substring(0, 5) : '23:59';
                    const ds = String(x.end_date).split('T')[0];
                    const ts = new Date(`${ds}T${t}:00`).getTime();
                    return isNaN(ts) ? new Date(x.end_date).getTime() : ts;
                };
                return getRet(a) - getRet(b);
            });"""

if old_active_now in content:
    content = content.replace(old_active_now, new_active_now)
    print("[OK] Updated ActiveNow.render to sort by return date (due soonest first).")
else:
    print("[WARN] old_active_now not found!")

# Write updated admin_app/index.html
with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("[SUCCESS] admin_app/index.html written.")

# Copy to admin_mobile/www/index.html
shutil.copyfile('admin_app/index.html', 'admin_mobile/www/index.html')
print("[SUCCESS] admin_mobile/www/index.html copied.")
