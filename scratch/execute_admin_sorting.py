import sys
import shutil

print("Executing Admin Sorting updates on admin_app/index.html...")

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

total_lines = len(lines)
print(f"Total lines in admin_app/index.html: {total_lines}")

# --- Helper to find line containing substring ---
def find_line(sub, start_from=0):
    for i in range(start_from, len(lines)):
        if sub in lines[i]:
            return i
    raise ValueError(f"Substring not found: {sub}")

# =========================================================================
# 1. Update tabNew header
# =========================================================================
idx_tab_new = find_line('<div id="tabNew"')
# Find the header flex div starting around idx_tab_new
idx_new_header_start = find_line('<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">', idx_tab_new)
# Find the closing </div> of this header (after the button)
idx_sync_btn = find_line('<i class="fas fa-sync-alt"></i>', idx_new_header_start)
idx_btn_close = find_line('</button>', idx_sync_btn)
idx_new_header_end = find_line('</div>', idx_btn_close)

print(f"tabNew header found: lines {idx_new_header_start+1} to {idx_new_header_end+1}")

new_tab_new_html = """            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
                <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-main); margin: 0;">New Bookings</h3>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <label for="newBookingsSort" style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600; white-space: nowrap;"><i class="fas fa-sort" style="margin-right:4px;"></i>Sort:</label>
                    <select id="newBookingsSort" onchange="Bookings.setNewSort(this.value)" style="padding: 7px 10px; background: var(--surface-container); border: 1px solid var(--border); border-radius: 8px; color: var(--text-main); font-size: 0.78rem; font-weight: 600; outline: none; cursor: pointer;">
                        <option value="date_desc">Date (Newest)</option>
                        <option value="date_asc">Date (Oldest)</option>
                        <option value="name_asc">Name (A–Z)</option>
                        <option value="name_desc">Name (Z–A)</option>
                        <option value="duration_desc">Duration (Longest)</option>
                        <option value="duration_asc">Duration (Shortest)</option>
                        <option value="amount_desc">Amount (High to Low)</option>
                        <option value="amount_asc">Amount (Low to High)</option>
                    </select>
                    <button onclick="Bookings.refresh()" style="background: var(--surface-container); border: 1px solid var(--border); color: var(--text-muted); padding: 7px 12px; border-radius: 10px; font-size: 0.75rem; font-weight: 700; cursor: pointer;" title="Refresh">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </div>
            </div>\n"""

lines[idx_new_header_start:idx_new_header_end+1] = [new_tab_new_html]
print("[OK] Tab New header replaced successfully.")

# =========================================================================
# 2. Update tabAll header
# =========================================================================
idx_tab_all = find_line('<div id="tabAll"')
idx_all_header_start = find_line('<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">', idx_tab_all)
idx_refresh_btn = find_line('Bookings.refresh()', idx_all_header_start)
idx_all_header_end = find_line('</div>', idx_refresh_btn + 1)
# Note there is an inner div closing, then the flex container closing
idx_all_header_end = find_line('</div>', idx_all_header_end + 1)

print(f"tabAll header found: lines {idx_all_header_start+1} to {idx_all_header_end+1}")

new_tab_all_html = """            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
                <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-main); margin: 0;">All Bookings</h3>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <label for="allBookingsSort" style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600; white-space: nowrap;"><i class="fas fa-sort" style="margin-right:4px;"></i>Sort:</label>
                    <select id="allBookingsSort" onchange="Bookings.setSort(this.value)" style="padding: 7px 10px; background: var(--surface-container); border: 1px solid var(--border); border-radius: 8px; color: var(--text-main); font-size: 0.78rem; font-weight: 600; outline: none; cursor: pointer;">
                        <option value="date_desc">Date (Newest)</option>
                        <option value="date_asc">Date (Oldest)</option>
                        <option value="name_asc">Name (A–Z)</option>
                        <option value="name_desc">Name (Z–A)</option>
                        <option value="duration_desc">Duration (Longest)</option>
                        <option value="duration_asc">Duration (Shortest)</option>
                        <option value="amount_desc">Amount (High to Low)</option>
                        <option value="amount_asc">Amount (Low to High)</option>
                    </select>
                    <button onclick="Bookings.refresh()" style="background: var(--surface-container); border: 1px solid var(--border); color: var(--text-secondary); padding: 6px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: 600; cursor: pointer;">Refresh</button>
                </div>
            </div>\n"""

lines[idx_all_header_start:idx_all_header_end+1] = [new_tab_all_html]
print("[OK] Tab All header replaced successfully.")

# =========================================================================
# 3. Add Verifications search & sort bar above #verificationsList
# =========================================================================
idx_verif_list = find_line('<div id="verificationsList"')
print(f"verificationsList found at line {idx_verif_list+1}")

verif_search_sort_html = """        <!-- Search and Sort Bar for Verifications -->
        <div style="display: flex; gap: 10px; margin-bottom: 18px; align-items: center; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 200px; position: relative;">
                <i class="fas fa-search" style="position: absolute; left: 16px; top: 50%; transform: translateY(-50%); color: var(--text-muted); font-size: 0.85rem;"></i>
                <input type="text" id="verificationsSearch" oninput="Verifications.onSearch(this.value)" placeholder="Search name, license no, email..." style="width: 100%; padding: 11px 14px 11px 40px; background: var(--surface); border: 1.5px solid var(--border); border-radius: 12px; color: var(--text-main); font-size: 0.85rem; font-weight: 600; outline: none; box-sizing: border-box;">
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <label for="verificationsSort" style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600; white-space: nowrap;"><i class="fas fa-sort" style="margin-right: 4px;"></i>Sort:</label>
                <select id="verificationsSort" onchange="Verifications.setSort(this.value)" style="padding: 10px 12px; background: var(--surface); border: 1.5px solid var(--border); border-radius: 12px; color: var(--text-main); font-size: 0.82rem; font-weight: 700; outline: none; cursor: pointer;">
                    <option value="date_desc">Submitted (Newest)</option>
                    <option value="date_asc">Submitted (Oldest / FIFO)</option>
                    <option value="name_asc">Name (A–Z)</option>
                    <option value="name_desc">Name (Z–A)</option>
                    <option value="expiry_asc">License Expiry (Soonest)</option>
                    <option value="expiry_desc">License Expiry (Furthest)</option>
                </select>
            </div>
        </div>\n\n"""

lines.insert(idx_verif_list, verif_search_sort_html)
print("[OK] Verifications search & sort bar inserted.")

# =========================================================================
# 4. Update User Management search & filter bar (#umSearch)
# =========================================================================
idx_um_search = find_line('id="umSearch"')
# Walk backward to find the outer container: <div style="display:flex; gap:10px; margin-bottom:12px;">
idx_um_bar_start = idx_um_search
while idx_um_bar_start > 0 and 'display:flex; gap:10px; margin-bottom:12px;' not in lines[idx_um_bar_start]:
    idx_um_bar_start -= 1

# Walk forward to find the export button and closing </div>
idx_um_export = find_line('UserMgmt.exportCSV()', idx_um_search)
idx_um_bar_end = find_line('</div>', idx_um_export)

print(f"umSearch container found: lines {idx_um_bar_start+1} to {idx_um_bar_end+1}")

new_um_search_html = """    <div style="display:flex; gap:10px; margin-bottom:12px; align-items:center; flex-wrap:wrap;">
        <div style="flex:1; min-width:200px; position:relative;">
            <i class="fas fa-search" style="position:absolute; left:16px; top:50%; transform:translateY(-50%); color:#64748b; font-size:0.9rem;"></i>
            <input type="text" id="umSearch" oninput="UserMgmt.applyFilters()" placeholder="Search name, email, phone..." style="width:100%; padding:12px 14px 12px 42px; background:#ffffff; border:1.5px solid #cbd5e1; border-radius:50px; color:#0f172a; font-size:0.88rem; font-weight:600; outline:none; box-sizing:border-box;">
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            <select id="umSort" onchange="UserMgmt.setSort(this.value)" style="padding:11px 14px; background:#ffffff; border:1.5px solid #cbd5e1; border-radius:50px; color:#0f172a; font-size:0.82rem; font-weight:700; outline:none; cursor:pointer;">
                <option value="date_desc">Registered (Newest)</option>
                <option value="date_asc">Registered (Oldest)</option>
                <option value="name_asc">Name (A–Z)</option>
                <option value="name_desc">Name (Z–A)</option>
                <option value="bookings_desc">Bookings (Most)</option>
                <option value="bookings_asc">Bookings (Least)</option>
                <option value="loyalty_desc">Points (Highest)</option>
                <option value="verified_first">Verified First</option>
            </select>
            <button onclick="UserMgmt.exportCSV()" style="background:rgba(0,177,79,0.1); border:1.5px solid #00B14F; color:#00B14F; width:44px; height:44px; border-radius:50px; display:flex; align-items:center; justify-content:center; cursor:pointer; flex-shrink:0;" title="Export CSV"><i class="fas fa-download" style="font-size:0.9rem;"></i></button>
        </div>
    </div>\n"""

lines[idx_um_bar_start:idx_um_bar_end+1] = [new_um_search_html]
print("[OK] UserMgmt search and sort bar replaced successfully.")

# =========================================================================
# 5. Update Bookings Object in JS
# =========================================================================
idx_bookings_obj = find_line('const Bookings = {')
idx_bookings_data = find_line('data: [],', idx_bookings_obj)

print(f"Bookings object found at line {idx_bookings_obj+1}")

bookings_sort_helpers = """        _sortBy: 'date_desc',
        _newSortBy: 'date_desc',

        getDurationDays(b) {
            if (b.days != null && !isNaN(b.days) && Number(b.days) > 0) return Number(b.days);
            if (b.total_days != null && !isNaN(b.total_days) && Number(b.total_days) > 0) return Number(b.total_days);
            if (b.start_date && b.end_date) {
                const start = new Date(b.start_date).getTime();
                const end = new Date(b.end_date).getTime();
                if (!isNaN(start) && !isNaN(end) && end >= start) {
                    return Math.max(1, Math.round((end - start) / 86400000));
                }
            }
            return 1;
        },

        getDate(b) {
            const d = b.created_at || b.start_date || b.booking_date;
            return d ? new Date(d).getTime() : 0;
        },

        getAmount(b) {
            const val = b.total_price != null ? b.total_price : (b.total_amount != null ? b.total_amount : b.amount);
            return Number(val) || 0;
        },

        getName(b) {
            return (b.customer_name || b.renter_name || b.full_name || 'Guest User').trim().toLowerCase();
        },

        setSort(key) {
            this._sortBy = key;
            const el = document.getElementById('allBookingsSort');
            if (el && el.value !== key) el.value = key;
            this.render();
        },

        setNewSort(key) {
            this._newSortBy = key;
            const el = document.getElementById('newBookingsSort');
            if (el && el.value !== key) el.value = key;
            this.renderNew();
        },

        sortBookings(list, sortKey) {
            const copy = [...list];
            switch (sortKey) {
                case 'date_asc':
                    return copy.sort((a, b) => this.getDate(a) - this.getDate(b));
                case 'name_asc':
                    return copy.sort((a, b) => this.getName(a).localeCompare(this.getName(b)));
                case 'name_desc':
                    return copy.sort((a, b) => this.getName(b).localeCompare(this.getName(a)));
                case 'duration_desc':
                    return copy.sort((a, b) => this.getDurationDays(b) - this.getDurationDays(a));
                case 'duration_asc':
                    return copy.sort((a, b) => this.getDurationDays(a) - this.getDurationDays(b));
                case 'amount_desc':
                    return copy.sort((a, b) => this.getAmount(b) - this.getAmount(a));
                case 'amount_asc':
                    return copy.sort((a, b) => this.getAmount(a) - this.getAmount(b));
                case 'date_desc':
                default:
                    return copy.sort((a, b) => this.getDate(b) - this.getDate(a));
            }
        },\n"""

lines.insert(idx_bookings_data + 1, bookings_sort_helpers)
print("[OK] Inserted Bookings sorting helpers and properties.")

# Next, inside Bookings.renderNew():
# Find: if (this._newFilter !== 'all') { ... }
# Followed by // Update badge count
idx_render_new = find_line('renderNew() {', idx_bookings_obj)
idx_badge_count = find_line('// Update badge count', idx_render_new)

# Insert sort call before badge count
lines.insert(idx_badge_count, """            // Apply sorting to new bookings
            filtered = this.sortBookings(filtered, this._newSortBy || 'date_desc');\n\n""")
print("[OK] Inserted sortBookings into Bookings.renderNew().")

# Next, inside Bookings.render():
idx_render = find_line('render() {', idx_render_new + 10)
idx_render_filtered = find_line('const filtered = this._filter === \'all\' ?', idx_render)
idx_render_if_empty = find_line('if (filtered.length === 0) {', idx_render_filtered)

# We want:
# const sorted = this.sortBookings(filtered, this._sortBy || 'date_desc');
# if (sorted.length === 0) {
# ...
# list.innerHTML = sorted.map(b => `
lines[idx_render_if_empty] = "            const sorted = this.sortBookings(filtered, this._sortBy || 'date_desc');\n            if (sorted.length === 0) {\n"
idx_list_map = find_line('list.innerHTML = filtered.map(b => `', idx_render_if_empty)
lines[idx_list_map] = "            list.innerHTML = sorted.map(b => `\n"
print("[OK] Inserted sortBookings into Bookings.render().")

# =========================================================================
# 6. Update Verifications Object in JS
# =========================================================================
idx_verif_obj = find_line('const Verifications = {')
idx_verif_data = find_line('data: [],', idx_verif_obj)

verif_sort_props = """        _searchQuery: '',
        _sortBy: 'date_desc',

        onSearch(query) {
            this._searchQuery = (query || '').toLowerCase().trim();
            this.render();
        },

        setSort(sortKey) {
            this._sortBy = sortKey;
            const el = document.getElementById('verificationsSort');
            if (el && el.value !== sortKey) el.value = sortKey;
            this.render();
        },

        sortList(list, sortKey) {
            const copy = [...list];
            switch (sortKey) {
                case 'date_asc':
                    return copy.sort((a, b) => {
                        const da = a.created_at ? new Date(a.created_at).getTime() : 0;
                        const db = b.created_at ? new Date(b.created_at).getTime() : 0;
                        return (da && db) ? da - db : (a.id || 0) - (b.id || 0);
                    });
                case 'name_asc':
                    return copy.sort((a, b) => (a.full_name || '').localeCompare(b.full_name || ''));
                case 'name_desc':
                    return copy.sort((a, b) => (b.full_name || '').localeCompare(a.full_name || ''));
                case 'expiry_asc':
                    return copy.sort((a, b) => {
                        const ea = a.license_expiry ? new Date(a.license_expiry).getTime() : Infinity;
                        const eb = b.license_expiry ? new Date(b.license_expiry).getTime() : Infinity;
                        return (isNaN(ea) ? Infinity : ea) - (isNaN(eb) ? Infinity : eb);
                    });
                case 'expiry_desc':
                    return copy.sort((a, b) => {
                        const ea = a.license_expiry ? new Date(a.license_expiry).getTime() : 0;
                        const eb = b.license_expiry ? new Date(b.license_expiry).getTime() : 0;
                        return (isNaN(eb) ? 0 : eb) - (isNaN(ea) ? 0 : ea);
                    });
                case 'date_desc':
                default:
                    return copy.sort((a, b) => {
                        const da = a.created_at ? new Date(a.created_at).getTime() : 0;
                        const db = b.created_at ? new Date(b.created_at).getTime() : 0;
                        return (da && db) ? db - da : (b.id || 0) - (a.id || 0);
                    });
            }
        },\n"""

lines.insert(idx_verif_data + 1, verif_sort_props)
print("[OK] Inserted Verifications sort & search state and methods.")

# Now in Verifications.render():
idx_verif_render = find_line('render() {', idx_verif_obj)
idx_verif_render_empty = find_line('if (!this.data || this.data.length === 0) {', idx_verif_render)
# Replace the empty check and map logic:
idx_verif_map = find_line('list.innerHTML = this.data.map(v => {', idx_verif_render_empty)

verif_render_replacement = """            let displayData = Array.isArray(this.data) ? this.data : [];

            // Apply search filter
            if (this._searchQuery) {
                const q = this._searchQuery;
                displayData = displayData.filter(v =>
                    (v.full_name || '').toLowerCase().includes(q) ||
                    (v.email || '').toLowerCase().includes(q) ||
                    (v.phone || '').toLowerCase().includes(q) ||
                    (v.license_number || '').toLowerCase().includes(q)
                );
            }

            // Apply sorting
            displayData = this.sortList(displayData, this._sortBy || 'date_desc');

            if (!displayData || displayData.length === 0) {
                list.innerHTML = `
                    <div style="text-align: center; padding: 60px 20px; background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border);">
                        <i class="fas fa-user-shield" style="font-size: 3rem; color: var(--text-muted); opacity: 0.3; margin-bottom: 15px;"></i>
                        <p style="color: var(--text-muted); font-weight: 600;">${this._searchQuery ? 'No verifications match your search.' : 'No pending verifications.'}</p>
                    </div>`;
                return;
            }

            list.innerHTML = displayData.map(v => {\n"""

lines[idx_verif_render_empty:idx_verif_map+1] = [verif_render_replacement]
print("[OK] Patched Verifications.render().")

# =========================================================================
# 7. Update UserMgmt Object in JS
# =========================================================================
idx_um_obj = find_line('const UserMgmt = {')
idx_um_set_filter = find_line('setFilter(f, btn) {', idx_um_obj)

um_sort_methods = """        _sortBy: 'date_desc',

        setSort(key) {
            this._sortBy = key;
            const el = document.getElementById('umSort');
            if (el && el.value !== key) el.value = key;
            this.applyFilters();
        },

        sortUsers(list, sortKey) {
            const copy = [...list];
            switch (sortKey) {
                case 'date_asc':
                    return copy.sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));
                case 'name_asc':
                    return copy.sort((a, b) => (a.full_name || '').localeCompare(b.full_name || ''));
                case 'name_desc':
                    return copy.sort((a, b) => (b.full_name || '').localeCompare(a.full_name || ''));
                case 'bookings_desc':
                    return copy.sort((a, b) => (Number(b.total_bookings) || 0) - (Number(a.total_bookings) || 0));
                case 'bookings_asc':
                    return copy.sort((a, b) => (Number(a.total_bookings) || 0) - (Number(b.total_bookings) || 0));
                case 'loyalty_desc':
                    return copy.sort((a, b) => (Number(b.loyalty_points) || 0) - (Number(a.loyalty_points) || 0));
                case 'verified_first':
                    return copy.sort((a, b) => (b.is_verified === 2 ? 1 : 0) - (a.is_verified === 2 ? 1 : 0));
                case 'date_desc':
                default:
                    return copy.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
            }
        },\n"""

lines.insert(idx_um_set_filter, um_sort_methods)
print("[OK] Inserted UserMgmt sorting helpers and properties.")

# Inside UserMgmt.applyFilters():
idx_um_apply = find_line('applyFilters() {', idx_um_set_filter)
idx_um_render_call = find_line('this._render(list);', idx_um_apply)

lines.insert(idx_um_render_call, """            // Apply user management sort
            list = this.sortUsers(list, this._sortBy || 'date_desc');\n\n""")
print("[OK] Inserted sortUsers into UserMgmt.applyFilters().")

# Write out the updated admin_app/index.html
with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("[SUCCESS] admin_app/index.html updated successfully!")

# Copy to admin_mobile/www/index.html so they are 100% identical
shutil.copyfile('admin_app/index.html', 'admin_mobile/www/index.html')
print("[SUCCESS] Copied to admin_mobile/www/index.html!")
