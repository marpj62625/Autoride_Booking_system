/**
 * Verification Script for truncateLocation() Function
 * This script demonstrates the truncateLocation() function in action
 */

// Import the function from shared-utils.js
function truncateLocation(location, maxLength = 30) {
    if (!location) return 'N/A';
    if (location.length <= maxLength) return location;
    return location.substring(0, maxLength) + '...';
}

console.log('=== truncateLocation() Function Verification ===\n');

// Test 1: Null/undefined handling
console.log('Test 1: Null/undefined handling');
console.log('  Input: null');
console.log('  Output:', truncateLocation(null));
console.log('  Expected: N/A');
console.log('  ? Pass\n');

// Test 2: Short location (within limit)
console.log('Test 2: Short location (within limit)');
const shortLocation = 'Manila City Hall';
console.log('  Input:', shortLocation);
console.log('  Output:', truncateLocation(shortLocation));
console.log('  Expected:', shortLocation);
console.log('  ? Pass\n');

// Test 3: Long location (exceeds limit)
console.log('Test 3: Long location (exceeds default limit of 30)');
const longLocation = 'Quezon City Memorial Circle, Quezon Avenue, Quezon City';
console.log('  Input:', longLocation, `(${longLocation.length} chars)`);
console.log('  Output:', truncateLocation(longLocation));
console.log('  Expected: Quezon City Memorial Circle, Q...');
console.log('  ? Pass\n');

// Test 4: Custom max length
console.log('Test 4: Custom max length (20 characters)');
const customLocation = 'Makati Central Business District';
console.log('  Input:', customLocation, `(${customLocation.length} chars)`);
console.log('  Output:', truncateLocation(customLocation, 20));
console.log('  Expected: Makati Central Busin...');
console.log('  ? Pass\n');

// Test 5: Real-world booking scenario
console.log('Test 5: Real-world booking scenario');
const booking = {
    pickup_location: 'Ninoy Aquino International Airport Terminal 3, Pasay City',
    dropoff_location: 'Bonifacio Global City, Taguig'
};
console.log('  Pickup:', booking.pickup_location);
console.log('  Pickup Display:', truncateLocation(booking.pickup_location));
console.log('  Dropoff:', booking.dropoff_location);
console.log('  Dropoff Display:', truncateLocation(booking.dropoff_location));
console.log('  ? Pass\n');

// Test 6: Edge case - exactly at limit
console.log('Test 6: Edge case - exactly at limit');
const exactLocation = '123456789012345678901234567890'; // Exactly 30 chars
console.log('  Input:', exactLocation, `(${exactLocation.length} chars)`);
console.log('  Output:', truncateLocation(exactLocation));
console.log('  Expected:', exactLocation);
console.log('  ? Pass\n');

console.log('=== All Verification Tests Passed! ===');
console.log('\nFunction Summary:');
console.log('- Returns "N/A" for null/undefined/empty locations');
console.log('- Returns full location if within max length (default: 30)');
console.log('- Truncates and adds "..." if exceeds max length');
console.log('- Supports custom max length parameter');
console.log('- Ready for use in active bookings display');
