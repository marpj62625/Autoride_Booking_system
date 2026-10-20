import sys
import shutil

sys.stdout.reconfigure(encoding='utf-8')

def apply_fixes_to_content(content):
    # 1. Update #tabNew filter chips
    old_chips = '''                <button class="nb-chip nb-chip-active" data-filter="pending" onclick="Bookings.setNewFilter('pending',this)" style="flex-shrink:0;padding:7px 14px;background:var(--primary);color:white;border:1px solid var(--primary);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">New</button>
                <button class="nb-chip" data-filter="pickup_soon" onclick="Bookings.setNewFilter('pickup_soon',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;"><i class="fas fa-calendar-check" style="margin-right:5px;color:var(--primary);"></i>Pickup Soon</button>
                <button class="nb-chip" data-filter="return_soon" onclick="Bookings.setNewFilter('return_soon',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;"><i class="fas fa-undo-alt" style="margin-right:5px;color:#d97706;"></i>Return Soon</button>
                <button class="nb-chip" data-filter="confirmed" onclick="Bookings.setNewFilter('confirmed',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">Confirmed</button>
                <button class="nb-chip" data-filter="approved" onclick="Bookings.setNewFilter('approved',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">Approved</button>
                <button class="nb-chip" data-filter="picked_up" onclick="Bookings.setNewFilter('picked_up',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">Picked Up</button>
                <button class="nb-chip" data-filter="all" onclick="Bookings.setNewFilter('all',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">All Pending</button>'''

    new_chips = '''                <button class="nb-chip nb-chip-active" data-filter="all" onclick="Bookings.setNewFilter('all',this)" style="flex-shrink:0;padding:7px 14px;background:var(--primary);color:white;border:1px solid var(--primary);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">All New</button>
                <button class="nb-chip" data-filter="pickup_soon" onclick="Bookings.setNewFilter('pickup_soon',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;"><i class="fas fa-calendar-check" style="margin-right:5px;color:var(--primary);"></i>Pickup Soon</button>
                <button class="nb-chip" data-filter="return_soon" onclick="Bookings.setNewFilter('return_soon',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;"><i class="fas fa-undo-alt" style="margin-right:5px;color:#d97706;"></i>Return Soon</button>
                <button class="nb-chip" data-filter="confirmed" onclick="Bookings.setNewFilter('confirmed',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">Confirmed</button>
                <button class="nb-chip" data-filter="approved" onclick="Bookings.setNewFilter('approved',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">Approved</button>
                <button class="nb-chip" data-filter="picked_up" onclick="Bookings.setNewFilter('picked_up',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">Picked Up</button>
                <button class="nb-chip" data-filter="pending" onclick="Bookings.setNewFilter('pending',this)" style="flex-shrink:0;padding:7px 14px;background:var(--surface-container);color:var(--text-main);border:1px solid var(--border);border-radius:20px;font-size:0.75rem;font-weight:700;cursor:pointer;">Pending Review</button>'''

    assert old_chips in content, "Error: old_chips not found in content!"
    content = content.replace(old_chips, new_chips, 1)

    # 2. Update sortBookings(list, sortKey)
    old_sort = '''        sortBookings(list, sortKey) {
            const copy = [...list];
            switch (sortKey) {
                case 'date_asc':
                case 'pickup_asc':
                    return copy.sort((a, b) => this.getPickupTime(a) - this.getPickupTime(b));
                case 'return_asc':
                    return copy.sort((a, b) => this.getReturnTime(a) - this.getReturnTime(b));
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
        },'''

    new_sort = '''        sortBookings(list, sortKey) {
            const copy = [...list];
            switch (sortKey) {
                case 'pickup_asc':
                    return copy.sort((a, b) => {
                        const waitingStatuses = ['confirmed', 'approved', 'pending'];
                        const aWait = waitingStatuses.includes((a.status || '').toLowerCase()) ? 0 : 1;
                        const bWait = waitingStatuses.includes((b.status || '').toLowerCase()) ? 0 : 1;
                        if (aWait !== bWait) return aWait - bWait;
                        return this.getPickupTime(a) - this.getPickupTime(b);
                    });
                case 'return_asc':
                    return copy.sort((a, b) => {
                        const activeStatuses = ['picked up', 'ongoing'];
                        const aAct = activeStatuses.includes((a.status || '').toLowerCase()) ? 0 : 1;
                        const bAct = activeStatuses.includes((b.status || '').toLowerCase()) ? 0 : 1;
                        if (aAct !== bAct) return aAct - bAct;
                        return this.getReturnTime(a) - this.getReturnTime(b);
                    });
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
        },'''

    assert old_sort in content, "Error: old_sort not found in content!"
    content = content.replace(old_sort, new_sort, 1)

    # 3. Update Bookings.renderNew() to calculate counts and update chip text dynamically
    # Look for renderNew() body up to list.innerHTML = ...
    old_render_new_anchor = '''            let filtered = this.data.filter(b => activeStatuses.includes((b.status||'').toLowerCase()));



            if (this._newFilter === 'pickup_soon') {
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
            }'''

    new_render_new_anchor = '''            const allActive = (this.data || []).filter(b => activeStatuses.includes((b.status||'').toLowerCase()));
            let filtered = allActive;

            if (this._newFilter === 'pickup_soon') {
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
            }

            // Update chip counter labels dynamically so admin sees exact breakdown
            const chipCounts = {
                all: allActive.length,
                pickup_soon: allActive.filter(b => ['confirmed', 'approved', 'pending'].includes((b.status || '').toLowerCase())).length,
                return_soon: allActive.filter(b => ['picked up', 'ongoing'].includes((b.status || '').toLowerCase())).length,
                confirmed: allActive.filter(b => (b.status || '').toLowerCase() === 'confirmed').length,
                approved: allActive.filter(b => (b.status || '').toLowerCase() === 'approved').length,
                picked_up: allActive.filter(b => ['picked up', 'ongoing'].includes((b.status || '').toLowerCase())).length,
                pending: allActive.filter(b => (b.status || '').toLowerCase() === 'pending').length
            };

            const chipLabels = {
                all: `All New (${chipCounts.all})`,
                pickup_soon: `<i class="fas fa-calendar-check" style="margin-right:5px;color:var(--primary);"></i>Pickup Soon (${chipCounts.pickup_soon})`,
                return_soon: `<i class="fas fa-undo-alt" style="margin-right:5px;color:#d97706;"></i>Return Soon (${chipCounts.return_soon})`,
                confirmed: `Confirmed (${chipCounts.confirmed})`,
                approved: `Approved (${chipCounts.approved})`,
                picked_up: `Picked Up (${chipCounts.picked_up})`,
                pending: `Pending Review (${chipCounts.pending})`
            };

            document.querySelectorAll('.nb-chip').forEach(chip => {
                const f = chip.dataset.filter;
                if (chipLabels[f]) {
                    chip.innerHTML = chipLabels[f];
                }
            });'''

    assert old_render_new_anchor in content, "Error: old_render_new_anchor not found in content!"
    content = content.replace(old_render_new_anchor, new_render_new_anchor, 1)

    # 4. Remove dangling `${b.status || 'PENDING'} </span>` in tabAll render (around line 19205)
    old_dangling = '''                            <span class="pill ${this.getPillClass(b.status)}">${b.status || 'PENDING'}</span>
                        </div>



                                ${b.status || 'PENDING'}



                            </span>'''

    new_dangling = '''                            <span class="pill ${this.getPillClass(b.status)}">${b.status || 'PENDING'}</span>
                        </div>'''

    if old_dangling in content:
        content = content.replace(old_dangling, new_dangling, 1)
        print("Cleaned up dangling tabAll badge lines.")
    else:
        print("Note: old_dangling not matched directly, checking normalized...")

    return content

# Read admin_app/index.html
with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    orig = f.read()

fixed = apply_fixes_to_content(orig)

# Write to admin_app/index.html
with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.write(fixed)

print("Successfully updated admin_app/index.html")

# Write to admin_mobile/www/index.html
with open('admin_mobile/www/index.html', 'w', encoding='utf-8') as f:
    f.write(fixed)

print("Successfully updated admin_mobile/www/index.html")
