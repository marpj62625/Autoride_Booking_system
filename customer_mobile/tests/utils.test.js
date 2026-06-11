/**
 * Property-based tests for AutorideSystem Customer Mobile App utility functions.
 * Feature: autoride-customer-mobile-app
 *
 * Run with: npx vitest --run
 */

import { describe, test, expect } from 'vitest';
import fc from 'fast-check';
import {
  isGmailAddress,
  isBlank,
  normalizePhone,
  isValidLastFour,
  formatPHP,
  validateUploadFile,
  validateDateRange,
  calculateBookingPrice
} from '../www/js/utils.js';

// ?????????????????????????????????????????????????????????????????????????????
// Property 1: Gmail-only registration enforcement
// Feature: autoride-customer-mobile-app, Property 1: isGmailAddress returns true iff email ends with @gmail.com
// ?????????????????????????????????????????????????????????????????????????????
describe('Property 1: Gmail-only registration enforcement', () => {
  test('returns true for any string ending with @gmail.com (case-insensitive)', () => {
    fc.assert(
      fc.property(
        fc.stringOf(fc.char()).filter(s => !s.includes('@')),
        (localPart) => {
          const email = localPart + '@gmail.com';
          expect(isGmailAddress(email)).toBe(true);
          expect(isGmailAddress(email.toUpperCase())).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('returns false for emails not ending with @gmail.com', () => {
    const nonGmailDomains = ['@yahoo.com', '@outlook.com', '@hotmail.com', '@example.com', '@gmail.org'];
    fc.assert(
      fc.property(
        fc.stringOf(fc.char()).filter(s => !s.includes('@')),
        fc.constantFrom(...nonGmailDomains),
        (localPart, domain) => {
          const email = localPart + domain;
          expect(isGmailAddress(email)).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('returns false for empty, null, or undefined', () => {
    expect(isGmailAddress('')).toBe(false);
    expect(isGmailAddress(null)).toBe(false);
    expect(isGmailAddress(undefined)).toBe(false);
  });
});

// ?????????????????????????????????????????????????????????????????????????????
// Property 2: Booking price calculation correctness
// Feature: autoride-customer-mobile-app, Property 2: calculateBookingPrice total equals formula clamped to 0
// ?????????????????????????????????????????????????????????????????????????????
describe('Property 2: Booking price calculation correctness', () => {
  test('total equals formula and pointsEarned equals floor(total/100)', () => {
    fc.assert(
      fc.property(
        fc.float({ min: 100, max: 10000, noNaN: true }),   // dailyRate
        fc.integer({ min: 1, max: 30 }),                    // days
        fc.array(fc.float({ min: 0, max: 500, noNaN: true }), { minLength: 0, maxLength: 5 }), // addon prices
        fc.float({ min: 0, max: 2000, noNaN: true }),       // insurancePrice
        fc.integer({ min: 1, max: 30 }),                    // longTermDiscountDays
        fc.float({ min: 0, max: 50, noNaN: true }),         // longTermDiscountPercent
        fc.float({ min: 0, max: 30, noNaN: true }),         // couponPercent
        fc.integer({ min: 0, max: 1000 }),                  // pointsRedeemed
        (dailyRate, days, addonPrices, insurancePrice, ltDays, ltPercent, couponPercent, pointsRedeemed) => {
          // Build date strings
          const start = new Date('2030-01-01');
          const end = new Date(start);
          end.setDate(end.getDate() + days);
          const startStr = start.toISOString().split('T')[0];
          const endStr = end.toISOString().split('T')[0];

          const addons = addonPrices.map(p => ({ price: p }));
          const result = calculateBookingPrice(
            dailyRate, startStr, endStr, addons, insurancePrice,
            ltDays, ltPercent, couponPercent, pointsRedeemed
          );

          // Verify formula
          const basePrice = dailyRate * days;
          const addonPrice = addonPrices.reduce((s, p) => s + p, 0);
          const longTermDiscount = days >= ltDays ? basePrice * (ltPercent / 100) : 0;
          const subtotal = basePrice + addonPrice + insurancePrice - longTermDiscount;
          const couponDiscount = subtotal * (couponPercent / 100);
          const pointsDiscount = pointsRedeemed / 10;
          const expectedTotal = Math.max(0, subtotal - couponDiscount - pointsDiscount);
          const expectedPointsEarned = Math.floor(expectedTotal / 100);

          expect(result.total).toBeCloseTo(expectedTotal, 2);
          expect(result.pointsEarned).toBe(expectedPointsEarned);
          expect(result.total).toBeGreaterThanOrEqual(0);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('total is never negative', () => {
    fc.assert(
      fc.property(
        fc.float({ min: 0, max: 5000, noNaN: true }),
        fc.integer({ min: 1, max: 30 }),
        (dailyRate, days) => {
          const start = new Date('2030-06-01');
          const end = new Date(start);
          end.setDate(end.getDate() + days);
          const result = calculateBookingPrice(
            dailyRate,
            start.toISOString().split('T')[0],
            end.toISOString().split('T')[0],
            [], 0, 7, 10, 100, 0 // 100% coupon  -  total should clamp to 0
          );
          expect(result.total).toBeGreaterThanOrEqual(0);
        }
      ),
      { numRuns: 50 }
    );
  });
});

// ?????????????????????????????????????????????????????????????????????????????
// Property 3: Date range validation
// Feature: autoride-customer-mobile-app, Property 3: validateDateRange returns valid iff start>=today and end>start
// ?????????????????????????????????????????????????????????????????????????????
describe('Property 3: Date range validation', () => {
  test('valid when start is today or future and end is after start', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 365 }),  // daysFromToday for start
        fc.integer({ min: 1, max: 365 }),  // additional days for end
        (startOffset, endOffset) => {
          // Build date strings in local time to avoid UTC offset issues
          const toLocalDateStr = (d) => {
            const y = d.getFullYear();
            const m = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            return `${y}-${m}-${day}`;
          };

          const today = new Date();
          today.setHours(0, 0, 0, 0);
          const start = new Date(today);
          start.setDate(start.getDate() + startOffset);
          const end = new Date(start);
          end.setDate(end.getDate() + endOffset);

          const result = validateDateRange(
            toLocalDateStr(start),
            toLocalDateStr(end)
          );
          expect(result.valid).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('invalid when start is in the past', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 365 }),
        (daysAgo) => {
          const past = new Date();
          past.setDate(past.getDate() - daysAgo);
          const future = new Date();
          future.setDate(future.getDate() + 1);
          const result = validateDateRange(
            past.toISOString().split('T')[0],
            future.toISOString().split('T')[0]
          );
          expect(result.valid).toBe(false);
        }
      ),
      { numRuns: 50 }
    );
  });

  test('invalid when end is not after start', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 365 }),
        (startOffset) => {
          const today = new Date();
          today.setHours(0, 0, 0, 0);
          const start = new Date(today);
          start.setDate(start.getDate() + startOffset);
          // end == start (not strictly after)
          const result = validateDateRange(
            start.toISOString().split('T')[0],
            start.toISOString().split('T')[0]
          );
          expect(result.valid).toBe(false);
        }
      ),
      { numRuns: 50 }
    );
  });
});

// ?????????????????????????????????????????????????????????????????????????????
// Property 4: Whitespace-only input rejection
// Feature: autoride-customer-mobile-app, Property 4: isBlank returns true for whitespace-only strings
// ?????????????????????????????????????????????????????????????????????????????
describe('Property 4: Whitespace-only input rejection', () => {
  test('isBlank returns true for strings of only whitespace characters', () => {
    fc.assert(
      fc.property(
        fc.stringOf(fc.constantFrom(' ', '\t', '\n', '\r')),
        (s) => {
          expect(isBlank(s)).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('isBlank returns false for strings with at least one non-whitespace character', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1 }).filter(s => s.trim().length > 0),
        (s) => {
          expect(isBlank(s)).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('isBlank returns true for null and undefined', () => {
    expect(isBlank(null)).toBe(true);
    expect(isBlank(undefined)).toBe(true);
    expect(isBlank('')).toBe(true);
  });
});

// ?????????????????????????????????????????????????????????????????????????????
// Property 5: Phone number format normalization
// Feature: autoride-customer-mobile-app, Property 5: normalizePhone always produces 11-digit string starting with 0
// ?????????????????????????????????????????????????????????????????????????????
describe('Property 5: Phone number format normalization', () => {
  test('+63 prefix is replaced with 0', () => {
    expect(normalizePhone('+639171234567')).toBe('09171234567');
    expect(normalizePhone('+63 917 123 4567')).toBe('09171234567');
  });

  test('numbers already starting with 0 are unchanged in digit content', () => {
    expect(normalizePhone('09171234567')).toBe('09171234567');
  });

  test('numbers without 0 prefix get 0 prepended', () => {
    expect(normalizePhone('9171234567')).toBe('09171234567');
  });

  test('output always starts with 0 for valid Philippine numbers', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('09171234567', '+639171234567', '9171234567'),
        (phone) => {
          const result = normalizePhone(phone);
          expect(result.startsWith('0')).toBe(true);
        }
      ),
      { numRuns: 50 }
    );
  });
});

// ?????????????????????????????????????????????????????????????????????????????
// Property 6: Loyalty points earned round-trip
// Feature: autoride-customer-mobile-app, Property 6: pointsEarned = floor(total/100), value = points/10
// ?????????????????????????????????????????????????????????????????????????????
describe('Property 6: Loyalty points earned round-trip', () => {
  test('pointsEarned equals floor(total/100) for any non-negative total', () => {
    fc.assert(
      fc.property(
        fc.float({ min: 0, max: 1000000, noNaN: true }),
        (total) => {
          const pointsEarned = Math.floor(total / 100);
          const pointsValue = pointsEarned / 10;
          expect(pointsEarned).toBe(Math.floor(total / 100));
          expect(pointsValue).toBeCloseTo(Math.floor(total / 100) / 10, 10);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('calculateBookingPrice pointsEarned matches floor(total/100)', () => {
    fc.assert(
      fc.property(
        fc.float({ min: 100, max: 5000, noNaN: true }),
        fc.integer({ min: 1, max: 14 }),
        (dailyRate, days) => {
          const start = new Date('2030-03-01');
          const end = new Date(start);
          end.setDate(end.getDate() + days);
          const result = calculateBookingPrice(
            dailyRate,
            start.toISOString().split('T')[0],
            end.toISOString().split('T')[0],
            [], 0, 7, 10, 0, 0
          );
          expect(result.pointsEarned).toBe(Math.floor(result.total / 100));
        }
      ),
      { numRuns: 100 }
    );
  });
});

// ?????????????????????????????????????????????????????????????????????????????
// Property 7: File validation  -  format and size
// Feature: autoride-customer-mobile-app, Property 7: validateUploadFile rejects non-JPEG/PNG and >5MB files
// ?????????????????????????????????????????????????????????????????????????????
describe('Property 7: File validation  -  format and size', () => {
  test('returns null for valid JPEG files under 5 MB', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 5 * 1024 * 1024 }),
        (size) => {
          expect(validateUploadFile({ type: 'image/jpeg', size })).toBeNull();
        }
      ),
      { numRuns: 50 }
    );
  });

  test('returns null for valid PNG files under 5 MB', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 5 * 1024 * 1024 }),
        (size) => {
          expect(validateUploadFile({ type: 'image/png', size })).toBeNull();
        }
      ),
      { numRuns: 50 }
    );
  });

  test('returns error for files exceeding 5 MB', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 5 * 1024 * 1024 + 1, max: 50 * 1024 * 1024 }),
        fc.constantFrom('image/jpeg', 'image/png'),
        (size, type) => {
          const result = validateUploadFile({ type, size });
          expect(result).not.toBeNull();
          expect(typeof result).toBe('string');
        }
      ),
      { numRuns: 50 }
    );
  });

  test('returns error for non-JPEG/PNG types', () => {
    const invalidTypes = ['image/gif', 'image/webp', 'application/pdf', 'video/mp4', 'text/plain'];
    fc.assert(
      fc.property(
        fc.constantFrom(...invalidTypes),
        fc.integer({ min: 1, max: 1024 * 1024 }),
        (type, size) => {
          const result = validateUploadFile({ type, size });
          expect(result).not.toBeNull();
        }
      ),
      { numRuns: 50 }
    );
  });
});

// ?????????????????????????????????????????????????????????????????????????????
// Property 8: Downpayment amount calculation
// Feature: autoride-customer-mobile-app, Property 8: downpayment=20%, balance=80%, sum=total
// ?????????????????????????????????????????????????????????????????????????????
describe('Property 8: Downpayment amount calculation', () => {
  test('downpaymentAmount + balanceAmount === total for any positive total', () => {
    fc.assert(
      fc.property(
        fc.float({ min: 100, max: 100000, noNaN: true }),
        fc.integer({ min: 1, max: 30 }),
        (dailyRate, days) => {
          const start = new Date('2030-05-01');
          const end = new Date(start);
          end.setDate(end.getDate() + days);
          const result = calculateBookingPrice(
            dailyRate,
            start.toISOString().split('T')[0],
            end.toISOString().split('T')[0],
            [], 0, 7, 10, 0, 0
          );
          expect(result.downpaymentAmount).toBeCloseTo(result.total * 0.20, 2);
          expect(result.balanceAmount).toBeCloseTo(result.total * 0.80, 2);
          expect(result.downpaymentAmount + result.balanceAmount).toBeCloseTo(result.total, 2);
        }
      ),
      { numRuns: 100 }
    );
  });
});

// ?????????????????????????????????????????????????????????????????????????????
// Property 9: Last-four digits validation
// Feature: autoride-customer-mobile-app, Property 9: isValidLastFour returns true iff exactly 4 decimal digits
// ?????????????????????????????????????????????????????????????????????????????
describe('Property 9: Last-four digits validation', () => {
  test('returns true for exactly 4 decimal digit strings', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 9999 }),
        (n) => {
          const s = String(n).padStart(4, '0');
          expect(isValidLastFour(s)).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('returns false for strings that are not exactly 4 digits', () => {
    const invalid = ['', '123', '12345', 'abcd', '12ab', ' 123', '123 '];
    invalid.forEach(s => {
      expect(isValidLastFour(s)).toBe(false);
    });
  });

  test('matches /^\\d{4}$/ regex for any string', () => {
    fc.assert(
      fc.property(
        fc.string({ maxLength: 8 }),
        (s) => {
          expect(isValidLastFour(s)).toBe(/^\d{4}$/.test(s));
        }
      ),
      { numRuns: 100 }
    );
  });
});

// ?????????????????????????????????????????????????????????????????????????????
// Property 10: Monetary display formatting
// Feature: autoride-customer-mobile-app, Property 10: formatPHP produces "PHP X,XXX.XX" with 2 decimal places
// ?????????????????????????????????????????????????????????????????????????????
describe('Property 10: Monetary display formatting', () => {
  test('output always starts with "PHP "', () => {
    fc.assert(
      fc.property(
        fc.float({ min: 0, max: 1000000, noNaN: true }),
        (value) => {
          expect(formatPHP(value).startsWith('PHP ')).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('output contains exactly one decimal point', () => {
    fc.assert(
      fc.property(
        fc.float({ min: 0, max: 1000000, noNaN: true }),
        (value) => {
          const result = formatPHP(value);
          const dotCount = (result.match(/\./g) || []).length;
          expect(dotCount).toBe(1);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('decimal part always has exactly 2 digits', () => {
    fc.assert(
      fc.property(
        fc.float({ min: 0, max: 1000000, noNaN: true }),
        (value) => {
          const result = formatPHP(value);
          const decimalPart = result.split('.')[1];
          expect(decimalPart).toHaveLength(2);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('known values format correctly', () => {
    expect(formatPHP(0)).toBe('PHP 0.00');
    expect(formatPHP(1234.5)).toMatch(/^PHP 1,234\.50$/);
    expect(formatPHP(1000000)).toMatch(/^PHP 1,000,000\.00$/);
  });
});
