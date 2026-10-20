const assert = require('assert');

console.log("Testing pickup_asc and return_asc sorting...");

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
                return copy.sort((a, b) => this.getPickupTime(a) - this.getPickupTime(b));
            case 'return_asc':
                return copy.sort((a, b) => this.getReturnTime(a) - this.getReturnTime(b));
            default:
                return copy;
        }
    }
};

const bookings = [
    { id: 101, car: 'Innova', start_date: '2026-10-25', start_time: '10:00', end_date: '2026-10-30', end_time: '17:00' },
    { id: 102, car: 'Vios', start_date: '2026-10-16', start_time: '08:00', end_date: '2026-10-18', end_time: '17:00' },
    { id: 103, car: 'Fortuner', start_date: '2026-10-20', start_time: '14:00', end_date: '2026-10-22', end_time: '17:00' }
];

// Test pickup_asc: Soonest pickup first
const byPickup = Bookings.sortBookings(bookings, 'pickup_asc');
assert.strictEqual(byPickup[0].id, 102); // Oct 16
assert.strictEqual(byPickup[1].id, 103); // Oct 20
assert.strictEqual(byPickup[2].id, 101); // Oct 25

// Test return_asc: Soonest return first
const byReturn = Bookings.sortBookings(bookings, 'return_asc');
assert.strictEqual(byReturn[0].id, 102); // Oct 18
assert.strictEqual(byReturn[1].id, 103); // Oct 22
assert.strictEqual(byReturn[2].id, 101); // Oct 30

console.log("[PASS] Pickup and Return unit test assertions passed!");
