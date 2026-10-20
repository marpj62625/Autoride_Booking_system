const assert = require('assert');

console.log("Running unit tests for sorting functions...");

// --- 1. Test Bookings Sorting ---
const Bookings = {
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
    }
};

const mockBookings = [
    { id: 1, customer_name: 'Charlie Day', created_at: '2026-05-01', days: 2, total_price: 3000 },
    { id: 2, customer_name: 'Alice Smith', created_at: '2026-05-10', days: 7, total_price: 15000 },
    { id: 3, customer_name: 'Bob Jones', created_at: '2026-05-05', days: 4, total_price: 8000 }
];

// Test name A-Z
let res = Bookings.sortBookings(mockBookings, 'name_asc');
assert.strictEqual(res[0].customer_name, 'Alice Smith');
assert.strictEqual(res[2].customer_name, 'Charlie Day');

// Test name Z-A
res = Bookings.sortBookings(mockBookings, 'name_desc');
assert.strictEqual(res[0].customer_name, 'Charlie Day');
assert.strictEqual(res[2].customer_name, 'Alice Smith');

// Test date desc (newest first)
res = Bookings.sortBookings(mockBookings, 'date_desc');
assert.strictEqual(res[0].id, 2); // 2026-05-10
assert.strictEqual(res[2].id, 1); // 2026-05-01

// Test duration desc (longest first)
res = Bookings.sortBookings(mockBookings, 'duration_desc');
assert.strictEqual(res[0].id, 2); // 7 days
assert.strictEqual(res[2].id, 1); // 2 days

// Test amount desc (highest first)
res = Bookings.sortBookings(mockBookings, 'amount_desc');
assert.strictEqual(res[0].total_price, 15000);
assert.strictEqual(res[2].total_price, 3000);

console.log("[PASS] Bookings sorting unit tests passed!");


// --- 2. Test UserMgmt Sorting ---
const UserMgmt = {
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
    }
};

const mockUsers = [
    { id: 10, full_name: 'Zoe Saldana', created_at: '2026-01-01', total_bookings: 5, loyalty_points: 100, is_verified: 0 },
    { id: 11, full_name: 'Aaron Paul', created_at: '2026-03-01', total_bookings: 15, loyalty_points: 500, is_verified: 2 },
    { id: 12, full_name: 'Mary Jane', created_at: '2026-02-01', total_bookings: 2, loyalty_points: 50, is_verified: 2 }
];

// Test name A-Z
res = UserMgmt.sortUsers(mockUsers, 'name_asc');
assert.strictEqual(res[0].full_name, 'Aaron Paul');
assert.strictEqual(res[2].full_name, 'Zoe Saldana');

// Test total bookings desc
res = UserMgmt.sortUsers(mockUsers, 'bookings_desc');
assert.strictEqual(res[0].total_bookings, 15);
assert.strictEqual(res[2].total_bookings, 2);

// Test loyalty points desc
res = UserMgmt.sortUsers(mockUsers, 'loyalty_desc');
assert.strictEqual(res[0].loyalty_points, 500);

// Test verified first
res = UserMgmt.sortUsers(mockUsers, 'verified_first');
assert.strictEqual(res[2].id, 10); // unverified last

console.log("[PASS] UserMgmt sorting unit tests passed!");


// --- 3. Test Verifications Sorting & Search ---
const Verifications = {
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
    }
};

const mockVerifs = [
    { id: 1, full_name: 'David Lee', created_at: '2026-06-01', license_expiry: '2026-08-01', license_number: 'N01-22-123456' },
    { id: 2, full_name: 'Brenda Cruz', created_at: '2026-06-05', license_expiry: '2027-12-31', license_number: 'N02-23-654321' },
    { id: 3, full_name: 'Carl Santos', created_at: '2026-06-03', license_expiry: '2026-07-15', license_number: 'N03-24-789012' }
];

// Test expiry soonest
res = Verifications.sortList(mockVerifs, 'expiry_asc');
assert.strictEqual(res[0].full_name, 'Carl Santos'); // July 15 is soonest
assert.strictEqual(res[2].full_name, 'Brenda Cruz'); // Dec 31 2027 is furthest

// Test date FIFO (oldest first)
res = Verifications.sortList(mockVerifs, 'date_asc');
assert.strictEqual(res[0].id, 1); // 2026-06-01
assert.strictEqual(res[2].id, 2); // 2026-06-05

console.log("[PASS] Verifications sorting unit tests passed!");
console.log("=== ALL UNIT TESTS COMPLETED 100% SUCCESSFULLY! ===");
