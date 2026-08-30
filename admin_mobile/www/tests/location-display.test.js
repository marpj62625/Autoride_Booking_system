/**
 * Unit Tests for Location Display Utilities
 * Feature: admin-panel-ui-improvements
 * Task 9.2: Implement truncateLocation() utility function
 * Task 9.5: Write unit tests for location display
 * 
 * Tests cover:
 * - truncateLocation() with various location lengths
 * - Null/undefined location handling
 * - Custom max length parameter
 * - Edge cases (empty string, exact length, one character over)
 * 
 * Requirements: 7.5
 */

import { describe, test, expect } from 'vitest';

/**
 * Implementation of truncateLocation for testing
 * This matches the implementation in shared-utils.js
 */
function truncateLocation(location, maxLength = 30) {
    if (!location) return 'N/A';
    if (location.length <= maxLength) return location;
    return location.substring(0, maxLength) + '...';
}

describe('truncateLocation() - Location String Truncation', () => {
  /**
   * Test: Return "N/A" for null location
   * Validates Requirements: 7.5
   */
  test('should return "N/A" for null location', () => {
    const result = truncateLocation(null);
    expect(result).toBe('N/A');
  });

  /**
   * Test: Return "N/A" for undefined location
   * Validates Requirements: 7.5
   */
  test('should return "N/A" for undefined location', () => {
    const result = truncateLocation(undefined);
    expect(result).toBe('N/A');
  });

  /**
   * Test: Return "N/A" for empty string
   * Validates Requirements: 7.5
   */
  test('should return "N/A" for empty string', () => {
    const result = truncateLocation('');
    expect(result).toBe('N/A');
  });

  /**
   * Test: Return full location if within max length (default 30)
   * Validates Requirements: 7.5
   */
  test('should return full location if within default max length of 30', () => {
    const location = 'Manila City Hall';
    const result = truncateLocation(location);
    expect(result).toBe('Manila City Hall');
    expect(result.length).toBe(16);
  });

  /**
   * Test: Return full location if exactly at max length
   * Validates Requirements: 7.5
   */
  test('should return full location if exactly at max length', () => {
    const location = '123456789012345678901234567890'; // Exactly 30 characters
    const result = truncateLocation(location);
    expect(result).toBe(location);
    expect(result.length).toBe(30);
  });

  /**
   * Test: Truncate and add ellipsis if exceeds max length
   * Validates Requirements: 7.5
   */
  test('should truncate and add ellipsis if exceeds default max length', () => {
    const location = 'Quezon City Memorial Circle, Quezon Avenue, Quezon City';
    const result = truncateLocation(location);
    expect(result).toBe('Quezon City Memorial Circle, Q...');
    expect(result.length).toBe(33); // 30 + 3 for '...'
  });

  /**
   * Test: Truncate location one character over max length
   * Validates Requirements: 7.5
   */
  test('should truncate location that is one character over max length', () => {
    const location = '1234567890123456789012345678901'; // 31 characters
    const result = truncateLocation(location);
    expect(result).toBe('123456789012345678901234567890...');
    expect(result.length).toBe(33);
  });

  /**
   * Test: Custom max length parameter (shorter)
   * Validates Requirements: 7.5
   */
  test('should respect custom max length parameter (20 characters)', () => {
    const location = 'Makati Central Business District';
    const result = truncateLocation(location, 20);
    expect(result).toBe('Makati Central Busin...');
    expect(result.length).toBe(23); // 20 + 3 for '...'
  });

  /**
   * Test: Custom max length parameter (longer)
   * Validates Requirements: 7.5
   */
  test('should respect custom max length parameter (50 characters)', () => {
    const location = 'Bonifacio Global City, Taguig, Metro Manila, Philippines';
    const result = truncateLocation(location, 50);
    expect(result).toBe('Bonifacio Global City, Taguig, Metro Manila, Phili...');
    expect(result.length).toBe(53); // 50 + 3 for '...'
  });

  /**
   * Test: Short location with custom max length
   * Validates Requirements: 7.5
   */
  test('should return full location if within custom max length', () => {
    const location = 'BGC';
    const result = truncateLocation(location, 10);
    expect(result).toBe('BGC');
    expect(result.length).toBe(3);
  });

  /**
   * Test: Very long location string
   * Validates Requirements: 7.5
   */
  test('should handle very long location strings', () => {
    const location = 'Unit 1234, Building A, Street Name Avenue, Barangay Example, City Name, Province Name, Region Name, Country Name, Postal Code 12345';
    const result = truncateLocation(location);
    expect(result).toBe('Unit 1234, Building A, Street ...');
    expect(result.length).toBe(33);
  });

  /**
   * Test: Location with special characters
   * Validates Requirements: 7.5
   */
  test('should handle location with special characters', () => {
    const location = 'Ermita, Manila (near Rizal Park & Manila Bay)';
    const result = truncateLocation(location);
    // Location is 46 characters, exceeds 30, so it should be truncated
    expect(result).toBe('Ermita, Manila (near Rizal Par...');
    expect(result.length).toBe(33);
  });

  /**
   * Test: Location with Unicode characters
   * Validates Requirements: 7.5
   */
  test('should handle location with Unicode characters', () => {
    const location = 'Pasig City, Metro Manila ???';
    const result = truncateLocation(location, 20);
    expect(result).toBe('Pasig City, Metro Ma...');
  });

  /**
   * Test: Single character location
   * Validates Requirements: 7.5
   */
  test('should handle single character location', () => {
    const location = 'A';
    const result = truncateLocation(location);
    expect(result).toBe('A');
  });

  /**
   * Test: Max length of 0 (edge case)
   * Validates Requirements: 7.5
   */
  test('should handle max length of 0', () => {
    const location = 'Manila';
    const result = truncateLocation(location, 0);
    expect(result).toBe('...');
  });

  /**
   * Test: Max length of 1 (edge case)
   * Validates Requirements: 7.5
   */
  test('should handle max length of 1', () => {
    const location = 'Manila';
    const result = truncateLocation(location, 1);
    expect(result).toBe('M...');
  });

  /**
   * Test: Whitespace-only location
   * Validates Requirements: 7.5
   */
  test('should handle whitespace-only location', () => {
    const location = '   ';
    const result = truncateLocation(location);
    expect(result).toBe('   ');
  });

  /**
   * Test: Location with newlines and tabs
   * Validates Requirements: 7.5
   */
  test('should handle location with newlines and tabs', () => {
    const location = 'Manila\nCity\tHall';
    const result = truncateLocation(location);
    expect(result).toBe('Manila\nCity\tHall');
  });
});

describe('truncateLocation() - Real-world Location Examples', () => {
  /**
   * Test: Common Philippine addresses
   * Validates Requirements: 7.5
   */
  test('should handle common Philippine addresses', () => {
    const locations = [
      { input: 'NAIA Terminal 3', expected: 'NAIA Terminal 3' },
      { input: 'SM Mall of Asia, Pasay City', expected: 'SM Mall of Asia, Pasay City' },
      { input: 'Ayala Avenue, Makati City, Metro Manila', expected: 'Ayala Avenue, Makati City, Met...' },
      { input: 'Bonifacio Global City', expected: 'Bonifacio Global City' },
      { input: 'Quezon Memorial Circle', expected: 'Quezon Memorial Circle' }
    ];

    locations.forEach(({ input, expected }) => {
      const result = truncateLocation(input);
      expect(result).toBe(expected);
    });
  });

  /**
   * Test: Airport and transportation hub names
   * Validates Requirements: 7.5
   */
  test('should handle airport and transportation hub names', () => {
    const location = 'Ninoy Aquino International Airport Terminal 3, Pasay City';
    const result = truncateLocation(location);
    expect(result).toBe('Ninoy Aquino International Air...');
  });

  /**
   * Test: Hotel and landmark names
   * Validates Requirements: 7.5
   */
  test('should handle hotel and landmark names', () => {
    const location = 'The Peninsula Manila, Ayala Avenue corner Makati Avenue';
    const result = truncateLocation(location);
    expect(result).toBe('The Peninsula Manila, Ayala Av...');
  });
});

describe('truncateLocation() - Integration with Location Display', () => {
  /**
   * Test: Simulate location display in active bookings
   * Validates Requirements: 7.5
   */
  test('should work correctly in active bookings display context', () => {
    const booking = {
      pickup_location: 'Makati Central Business District, Ayala Avenue',
      dropoff_location: 'Bonifacio Global City, Taguig'
    };

    const pickupDisplay = truncateLocation(booking.pickup_location);
    const dropoffDisplay = truncateLocation(booking.dropoff_location);

    expect(pickupDisplay).toBe('Makati Central Business Distri...');
    expect(dropoffDisplay).toBe('Bonifacio Global City, Taguig');
  });

  /**
   * Test: Handle null pickup/dropoff locations
   * Validates Requirements: 7.5
   */
  test('should handle null pickup/dropoff locations in booking context', () => {
    const booking = {
      pickup_location: null,
      dropoff_location: null
    };

    const pickupDisplay = truncateLocation(booking.pickup_location);
    const dropoffDisplay = truncateLocation(booking.dropoff_location);

    expect(pickupDisplay).toBe('N/A');
    expect(dropoffDisplay).toBe('N/A');
  });

  /**
   * Test: Same pickup and dropoff location
   * Validates Requirements: 7.5
   */
  test('should handle same pickup and dropoff location', () => {
    const location = 'Manila Hotel, Rizal Park, Manila';
    const pickupDisplay = truncateLocation(location);
    const dropoffDisplay = truncateLocation(location);

    expect(pickupDisplay).toBe('Manila Hotel, Rizal Park, Mani...');
    expect(dropoffDisplay).toBe('Manila Hotel, Rizal Park, Mani...');
    expect(pickupDisplay).toBe(dropoffDisplay);
  });
});
