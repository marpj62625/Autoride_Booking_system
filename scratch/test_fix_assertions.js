const assert = require('assert');

console.log("Verifying fixed pickup & return logic...");

const Bookings = {
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
    },

    sortBookings(list, sortKey) {
        const copy = [...list];
        switch (sortKey) {
            case 'pickup_asc':
                return copy.sort((a, b) => {
                    const isA_waiting = ['confirmed', 'approved', 'pending'].includes((a.status || '').toLowerCase());
                    const isB_waiting = ['confirmed', 'approved', 'pending'].includes((b.status || '').toLowerCase());
                    if (isA_waiting && !isB_waiting) return -1;
                    if (!isA_waiting && isB_waiting) return 1;
                    return this.getPickupTime(a) - this.getPickupTime(b);
                });
            case 'return_asc':
                return copy.sort((a, b) => {
                    const isA_active = ['picked up', 'ongoing'].includes((a.status || '').toLowerCase());
                    const isB_active = ['picked up', 'ongoing'].includes((b.status || '').toLowerCase());
                    if (isA_active && !isB_active) return -1;
                    if (!isA_active && isB_active) return 1;
                    return this.getReturnTime(a) - this.getReturnTime(b);
                });
            default:
                return copy;
        }
    }
};

// Scenario matching the user's exact screenshot:
const mockData = [
    { id: 694, customer_name: 'Julius Sensida Labrador', car: 'Innova (CCK 1126)', status: 'Picked Up', start_date: '2026-10-01', end_date: '2026-10-30' },
    { id: 699, customer_name: 'Eliezer Cadarit Amador', car: 'Innova (NHN 5388)', status: 'Picked Up', start_date: '2026-10-12', end_date: '2026-10-19' },
    { id: 701, customer_name: 'Michael Ortega Jarina', car: 'Vios (DBJ 9483)', status: 'Confirmed', start_date: '2026-10-15', end_date: '2026-10-16' },
    { id: 702, customer_name: 'Pedro Ramos', car: 'Fortuner', status: 'Confirmed', start_date: '2026-10-20', end_date: '2026-10-25' }
];

// Test 1: pickup_asc sort
// Confirmed bookings waiting for pickup MUST be ranked BEFORE Picked Up bookings!
const byPickup = Bookings.sortBookings(mockData, 'pickup_asc');
console.log("Sort by pickup_asc top 2:", byPickup.slice(0, 2).map(b => `${b.id} ${b.customer_name} (${b.status})`));
assert.strictEqual(byPickup[0].id, 701); // Michael (Confirmed, Oct 15)
assert.strictEqual(byPickup[1].id, 702); // Pedro (Confirmed, Oct 20)
assert.strictEqual(byPickup[2].status, 'Picked Up'); // Julius & Eliezer go to bottom

// Test 2: return_asc sort
// Picked Up bookings waiting to be returned MUST be ranked BEFORE Confirmed bookings!
const byReturn = Bookings.sortBookings(mockData, 'return_asc');
console.log("Sort by return_asc top 2:", byReturn.slice(0, 2).map(b => `${b.id} ${b.customer_name} (${b.status})`));
assert.strictEqual(byReturn[0].id, 699); // Eliezer (Picked Up, end Oct 19 - due sooner than Oct 30)
assert.strictEqual(byReturn[1].id, 694); // Julius (Picked Up, end Oct 30)
assert.strictEqual(byReturn[2].status, 'Confirmed'); // Michael & Pedro go to bottom

// Test 3: pickup_soon filter
const pickupSoonList = mockData.filter(b => ['confirmed', 'approved', 'pending'].includes((b.status || '').toLowerCase()));
assert.strictEqual(pickupSoonList.length, 2);
assert(!pickupSoonList.some(b => b.status === 'Picked Up')); // NO ongoing bookings!

// Test 4: return_soon filter
const returnSoonList = mockData.filter(b => ['picked up', 'ongoing'].includes((b.status || '').toLowerCase()));
assert.strictEqual(returnSoonList.length, 2);
assert(!returnSoonList.some(b => b.status === 'Confirmed')); // NO unpicked-up bookings!

console.log("=== ALL LOGIC ASSERTIONS PASSED 100%! ===");
