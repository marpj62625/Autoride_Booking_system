import sys
import re

print("Starting Admin Sorting patch...")

# --- 1. Patch backend/app.py ---
with open('backend/app.py', 'r', encoding='utf-8') as f:
    backend_code = f.read()

old_sql_fragment = "ld.emergency_contact_phone, ld.emergency_contact_relationship,\n                       u.is_verified\n                FROM users u"
new_sql_fragment = "ld.emergency_contact_phone, ld.emergency_contact_relationship,\n                       u.is_verified, CAST(u.created_at AS TEXT) AS created_at\n                FROM users u"

if old_sql_fragment in backend_code:
    backend_code = backend_code.replace(old_sql_fragment, new_sql_fragment)
    with open('backend/app.py', 'w', encoding='utf-8') as f:
        f.write(backend_code)
    print("[SUCCESS] backend/app.py updated with created_at for pending-verifications")
else:
    print("[INFO] backend/app.py already updated or fragment not matched exactly")


# --- 2. Patch helper for index.html (admin_app and admin_mobile) ---
def patch_admin_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # A. Tab "New Bookings" HTML header (#tabNew)
    old_tab_new = """            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-main);">New Bookings</h3>
                <button onclick="Bookings.refresh()" style="background: var(--surface-container); border: 1px solid var(--border); color: var(--text-muted); padding: 7px 12px; border-radius: 10px; font-size: 0.75rem; font-weight: 700;">
                    <i class="fas fa-sync-alt"></i>
                </button>
            </div>"""

    new_tab_new = """            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
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
            </div>"""

    if old_tab_new in content:
        content = content.replace(old_tab_new, new_tab_new)
        print(f"[OK] Patched #tabNew header in {filepath}")
    else:
        print(f"[WARN] old_tab_new not found in {filepath}")

    # B. Tab "All Bookings" HTML header (#tabAll)
    old_tab_all = """            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-main);">All Bookings</h3>
                <div style="display: flex; gap: 10px;">
                    <button onclick="Bookings.refresh()" style="background: var(--surface-container); border: 1px solid var(--border); color: var(--text-secondary); padding: 6px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: 600;">Refresh</button>
                </div>
            </div>"""

    new_tab_all = """            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
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
            </div>"""

    if old_tab_all in content:
        content = content.replace(old_tab_all, new_tab_all)
        print(f"[OK] Patched #tabAll header in {filepath}")
    else:
        print(f"[WARN] old_tab_all not found in {filepath}")

    # C. Verifications search and sort bar (above #verificationsList)
    old_verif_html = """        <div id="verificationsList" style="display: grid; gap: 16px; margin-bottom: 40px;">"""
    new_verif_html = """        <!-- Search and Sort Bar for Verifications -->
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
        </div>

        <div id="verificationsList" style="display: grid; gap: 16px; margin-bottom: 40px;">"""

    if old_verif_html in content:
        content = content.replace(old_verif_html, new_verif_html)
        print(f"[OK] Added Verifications search and sort bar in {filepath}")
    else:
        print(f"[WARN] old_verif_html not found in {filepath}")

    # D. User Management Search and Sort Bar (#users)
    old_um_html = """    <div style="display:flex; gap:10px; margin-bottom:12px;">
        <div style="flex:1; position:relative;">
            <i class="fas fa-search" style="position:absolute; left:16px; top:50%; transform:translateY(-50%); color:#64748b; font-size:0.9rem;"></i>
            <input type="text" id="umSearch" oninput="UserMgmt.applyFilters()" placeholder="Search name, email, phone..." style="width:100%; padding:12px 14px 12px 42px; background:#ffffff; border:1.5px solid #cbd5e1; border-radius:50px; color:#0f172a; font-size:0.88rem; font-weight:600; outline:none; box-sizing:border-box;">
        </div>
        <button onclick="UserMgmt.exportCSV()" style="background:rgba(0,177,79,0.1); border:1.5px solid #00B14F; color:#00B14F; width:46px; border-radius:50px; display:flex; align-items:center; justify-content:center; cursor:pointer;" title="Export CSV"><i class="fas fa-download" style="font-size:0.9rem;"></i></button>
    </div>"""

    new_um_html = """    <div style="display:flex; gap:10px; margin-bottom:12px; align-items:center; flex-wrap:wrap;">
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
    </div>"""

    if old_um_html in content:
        content = content.replace(old_um_html, new_um_html)
        print(f"[OK] Patched UserMgmt search and sort HTML in {filepath}")
    else:
        print(f"[WARN] old_um_html not found in {filepath}")

    # E. Bookings object JavaScript logic
    old_bookings_decl = """    const Bookings = {
        data: [],
        _filter: 'all',
        _newFilter: 'all',"""

    new_bookings_decl = """    const Bookings = {
        data: [],
        _filter: 'all',
        _newFilter: 'all',
        _sortBy: 'date_desc',
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
            this.render();
        },

        setNewSort(key) {
            this._newSortBy = key;
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
        },"""

    if old_bookings_decl in content:
        content = content.replace(old_bookings_decl, new_bookings_decl)
        print(f"[OK] Patched Bookings methods in {filepath}")
    else:
        print(f"[WARN] old_bookings_decl not found in {filepath}")

    # F. Bookings.renderNew() sorting
    old_render_new_filter = """            if (this._newFilter !== 'all') {
                filtered = filtered.filter(b => {
                    const s = (b.status||'').toLowerCase().replace(' ', '_');
                    return s === this._newFilter || (b.status||'') === statusMap[this._newFilter];
                });
            }

            // Update badge count"""

    new_render_new_filter = """            if (this._newFilter !== 'all') {
                filtered = filtered.filter(b => {
                    const s = (b.status||'').toLowerCase().replace(' ', '_');
                    return s === this._newFilter || (b.status||'') === statusMap[this._newFilter];
                });
            }

            // Apply selected sorting to new bookings
            filtered = this.sortBookings(filtered, this._newSortBy || 'date_desc');

            // Update badge count"""

    if old_render_new_filter in content:
        content = content.replace(old_render_new_filter, new_render_new_filter)
        print(f"[OK] Added sortBookings to renderNew in {filepath}")
    else:
        print(f"[WARN] old_render_new_filter not found in {filepath}")

    # G. Bookings.render() sorting
    old_render_filter = """            const filtered = this._filter === 'all' ? this.data : this.data.filter(b => { const s = (b.status||'').toLowerCase().replace(' ', '_'); return s === this._filter || (b.status||'') === statusMap[this._filter]; });

            if (filtered.length === 0) {"""

    new_render_filter = """            const filtered = this._filter === 'all' ? this.data : this.data.filter(b => { const s = (b.status||'').toLowerCase().replace(' ', '_'); return s === this._filter || (b.status||'') === statusMap[this._filter]; });

            // Apply selected sorting to all bookings
            const sorted = this.sortBookings(filtered, this._sortBy || 'date_desc');

            if (sorted.length === 0) {"""

    if old_render_filter in content:
        content = content.replace(old_render_filter, new_render_filter)
        content = content.replace("list.innerHTML = filtered.map(b => `", "list.innerHTML = sorted.map(b => `")
        print(f"[OK] Added sortBookings to render in {filepath}")
    else:
        print(f"[WARN] old_render_filter not found in {filepath}")

    # H. Verifications object JS
    old_verif_obj = """    const Verifications = {
        data: [],
        async refresh() {"""

    new_verif_obj = """    const Verifications = {
        data: [],
        _searchQuery: '',
        _sortBy: 'date_desc',

        onSearch(query) {
            this._searchQuery = (query || '').toLowerCase().trim();
            this.render();
        },

        setSort(sortKey) {
            this._sortBy = sortKey;
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
        },

        async refresh() {"""

    if old_verif_obj in content:
        content = content.replace(old_verif_obj, new_verif_obj)
        print(f"[OK] Added Verifications sort & search state/methods in {filepath}")
    else:
        print(f"[WARN] old_verif_obj not found in {filepath}")

    # I. Verifications.render()
    old_verif_render = """        render() {
            const list = document.getElementById('verificationsList');
            if (!this.data || this.data.length === 0) {
                list.innerHTML = `
                    <div style="text-align: center; padding: 60px 20px; background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border);">
                        <i class="fas fa-user-shield" style="font-size: 3rem; color: var(--text-muted); opacity: 0.3; margin-bottom: 15px;"></i>
                        <p style="color: var(--text-muted); font-weight: 600;">No pending verifications.</p>
                    </div>`;
                return;
            }

            list.innerHTML = this.data.map(v => {"""

    new_verif_render = """        render() {
            const list = document.getElementById('verificationsList');
            if (!list) return;

            let displayData = Array.isArray(this.data) ? this.data : [];

            // Apply search query
            if (this._searchQuery) {
                const q = this._searchQuery;
                displayData = displayData.filter(v =>
                    (v.full_name || '').toLowerCase().includes(q) ||
                    (v.email || '').toLowerCase().includes(q) ||
                    (v.phone || '').toLowerCase().includes(q) ||
                    (v.license_number || '').toLowerCase().includes(q)
                );
            }

            // Apply sort
            displayData = this.sortList(displayData, this._sortBy || 'date_desc');

            if (!displayData || displayData.length === 0) {
                list.innerHTML = `
                    <div style="text-align: center; padding: 60px 20px; background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border);">
                        <i class="fas fa-user-shield" style="font-size: 3rem; color: var(--text-muted); opacity: 0.3; margin-bottom: 15px;"></i>
                        <p style="color: var(--text-muted); font-weight: 600;">${this._searchQuery ? 'No verifications match your search.' : 'No pending verifications.'}</p>
                    </div>`;
                return;
            }

            list.innerHTML = displayData.map(v => {"""

    if old_verif_render in content:
        content = content.replace(old_verif_render, new_verif_render)
        print(f"[OK] Patched Verifications.render in {filepath}")
    else:
        print(f"[WARN] old_verif_render not found in {filepath}")

    # J. UserMgmt sort methods
    old_um_methods = """        setFilter(f, btn) {
            this._filter = f;
            document.querySelectorAll('.um-filter-btn').forEach(b => {
                b.classList.remove('active');
                b.style.background = '#ffffff';
                b.style.color = '#1e293b';
                b.style.borderColor = '#cbd5e1';
            });

            btn.classList.add('active');
            btn.style.background = '#00B14F';
            btn.style.color = '#ffffff';
            btn.style.borderColor = '#00B14F';

            this.applyFilters();
        },

        applyFilters() {
            const q = (document.getElementById('umSearch').value || '').toLowerCase();
            let list = this._all;
            if (this._filter === 'verified') list = list.filter(u => u.is_verified === 2);
            else if (this._filter === 'unverified') list = list.filter(u => u.is_verified !== 2);
            else if (this._filter === 'frozen') list = list.filter(u => u.is_frozen);
            else if (this._filter === 'violations') list = list.filter(u => (u.violation_strikes > 0 || u.booking_suspension_until || u.violation_permanently_restricted));

            if (q) list = list.filter(u =>
                (u.full_name || '').toLowerCase().includes(q) ||
                (u.email || '').toLowerCase().includes(q) ||
                (u.phone || '').toLowerCase().includes(q)
            );

            this._render(list);
        },"""

    new_um_methods = """        _sortBy: 'date_desc',

        setSort(key) {
            this._sortBy = key;
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
        },

        setFilter(f, btn) {
            this._filter = f;
            document.querySelectorAll('.um-filter-btn').forEach(b => {
                b.classList.remove('active');
                b.style.background = '#ffffff';
                b.style.color = '#1e293b';
                b.style.borderColor = '#cbd5e1';
            });

            btn.classList.add('active');
            btn.style.background = '#00B14F';
            btn.style.color = '#ffffff';
            btn.style.borderColor = '#00B14F';

            this.applyFilters();
        },

        applyFilters() {
            const q = (document.getElementById('umSearch').value || '').toLowerCase();
            let list = this._all;
            if (this._filter === 'verified') list = list.filter(u => u.is_verified === 2);
            else if (this._filter === 'unverified') list = list.filter(u => u.is_verified !== 2);
            else if (this._filter === 'frozen') list = list.filter(u => u.is_frozen);
            else if (this._filter === 'violations') list = list.filter(u => (u.violation_strikes > 0 || u.booking_suspension_until || u.violation_permanently_restricted));

            if (q) list = list.filter(u =>
                (u.full_name || '').toLowerCase().includes(q) ||
                (u.email || '').toLowerCase().includes(q) ||
                (u.phone || '').toLowerCase().includes(q)
            );

            // Apply selected sorting
            list = this.sortUsers(list, this._sortBy || 'date_desc');

            this._render(list);
        },"""

    if old_um_methods in content:
        content = content.replace(old_um_methods, new_um_methods)
        print(f"[OK] Patched UserMgmt sort methods in {filepath}")
    else:
        print(f"[WARN] old_um_methods not found in {filepath}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[COMPLETED] Written {filepath}")

patch_admin_html('admin_app/index.html')
patch_admin_html('admin_mobile/www/index.html')
print("All patches finished successfully!")
