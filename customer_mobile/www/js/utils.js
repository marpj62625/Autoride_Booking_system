/**
 * utils.js — Pure utility functions for the Autoride Customer Mobile App.
 * All functions are side-effect-free and fully testable without DOM or Capacitor.
 *
 * Feature: autoride-customer-mobile-app
 */

/**
 * Returns true if the email ends with @gmail.com (case-insensitive).
 * Property 1: Gmail-only registration enforcement.
 * @param {string} email
 * @returns {boolean}
 */
function isGmailAddress(email) {
  if (!email || typeof email !== 'string') return false;
  return email.toLowerCase().endsWith('@gmail.com');
}

/**
 * Returns true if the value is null, undefined, or a string whose trimmed form is empty.
 * Property 4: Whitespace-only input rejection.
 * @param {*} str
 * @returns {boolean}
 */
function isBlank(str) {
  if (str === null || str === undefined) return true;
  return String(str).trim() === '';
}

/**
 * Normalizes a Philippine phone number to the 11-digit local format (09XXXXXXXXX).
 * - Strips all non-digit characters except a leading +
 * - Replaces leading +63 with 0
 * - Prepends 0 if the number doesn't already start with 0
 * Property 5: Phone number format normalization.
 * @param {string} phone
 * @returns {string}
 */
function normalizePhone(phone) {
  if (!phone || typeof phone !== 'string') return '';
  let cleaned = phone.trim();
  // Replace +63 prefix with 0
  if (cleaned.startsWith('+63')) {
    cleaned = '0' + cleaned.slice(3);
  }
  // Strip all non-digit characters
  cleaned = cleaned.replace(/\D/g, '');
  // Prepend 0 if not already starting with 0
  if (!cleaned.startsWith('0')) {
    cleaned = '0' + cleaned;
  }
  return cleaned;
}

/**
 * Returns true if the string is exactly 4 decimal digits.
 * Property 9: Last-four digits validation.
 * @param {string} s
 * @returns {boolean}
 */
function isValidLastFour(s) {
  if (!s || typeof s !== 'string') return false;
  return /^\d{4}$/.test(s);
}

/**
 * Formats a numeric value as Philippine Peso currency string.
 * Example: 1234.5 ? "PHP 1,234.50"
 * Property 10: Monetary display formatting.
 * @param {number} value
 * @returns {string}
 */
function formatPHP(value) {
  // Ensure value is a valid number, default to 0 if not
  const num = (value !== null && value !== undefined && !isNaN(Number(value))) ? Number(value) : 0;
  return 'PHP ' + num.toLocaleString('en-PH', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

function formatTime12h(time24) {
  if (!time24) return '';
  var parts = time24.split(':');
  var h = parseInt(parts[0]);
  var m = parts[1] || '00';
  var ampm = h < 12 ? 'AM' : 'PM';
  var h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
  return String(h12).padStart(2, '0') + ':' + m + ' ' + ampm;
}

/**
 * Validates a file for upload: must be JPEG or PNG and ? 5 MB.
 * Property 7: File validation — format and size.
 * @param {{ type: string, size: number }} file
 * @returns {string|null} Error message string, or null if valid.
 */
function validateUploadFile(file) {
  if (!file) return 'No file selected.';
  const allowedTypes = ['image/jpeg', 'image/png'];
  if (!allowedTypes.includes(file.type)) {
    return 'Only JPEG and PNG images are accepted.';
  }
  const maxSize = 5 * 1024 * 1024; // 5 MB
  if (file.size > maxSize) {
    return 'File size must not exceed 5 MB.';
  }
  return null;
}

/**
 * Validates a booking date range.
 * - startDate must be today or a future date
 * - endDate must be strictly after startDate
 * Property 3: Date range validation.
 * @param {string} startDate — 'YYYY-MM-DD'
 * @param {string} endDate   — 'YYYY-MM-DD'
 * @returns {{ valid: boolean, error?: string }}
 */
function validateDateRange(startDate, endDate) {
  if (!startDate || !endDate) {
    return { valid: false, error: 'Both start and end dates are required.' };
  }
  // Build today's date in local time (no UTC offset shift)
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  // Parse date strings as local time by splitting manually
  const parseLocal = (str) => {
    const [y, m, d] = str.split('-').map(Number);
    if (!y || !m || !d) return null;
    return new Date(y, m - 1, d);
  };

  const start = parseLocal(startDate);
  const end = parseLocal(endDate);

  if (!start || !end) {
    return { valid: false, error: 'Invalid date format.' };
  }
  if (start < today) {
    return { valid: false, error: 'Start date must be today or a future date.' };
  }
  if (end <= start) {
    return { valid: false, error: 'End date must be after the start date.' };
  }
  return { valid: true };
}

/**
 * Calculates the full booking price breakdown.
 * Property 2: Booking price calculation correctness.
 * Property 8: Downpayment amount calculation.
 * Property 6: Loyalty points earned round-trip.
 *
 * @param {number} dailyRate
 * @param {string} startDate — 'YYYY-MM-DD'
 * @param {string} endDate   — 'YYYY-MM-DD'
 * @param {Array<{price: number}>} addons — array of add-on objects with a price field
 * @param {number} insurancePrice
 * @param {number} longTermDiscountDays — minimum days to qualify for long-term discount
 * @param {number} longTermDiscountPercent — discount percentage (e.g. 10 for 10%)
 * @param {number} couponPercent — coupon discount percentage (0 if none)
 * @param {number} pointsRedeemed — loyalty points to redeem (10 points = PHP 1)
 * @returns {{
 *   days: number,
 *   basePrice: number,
 *   addonPrice: number,
 *   insurancePrice: number,
 *   longTermDiscount: number,
 *   couponDiscount: number,
 *   pointsDiscount: number,
 *   total: number,
 *   pointsEarned: number,
 *   downpaymentAmount: number,
 *   balanceAmount: number
 * }}
 */
function calculateBookingPrice(
  dailyRate,
  startDate,
  endDate,
  addons,
  insurancePrice,
  longTermDiscountDays,
  longTermDiscountPercent,
  couponPercent,
  pointsRedeemed
) {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const days = Math.max(1, Math.round((end - start) / (1000 * 60 * 60 * 24)));

  const rate = Number(dailyRate) || 0;
  const basePrice = rate * days;

  const addonPrice = Array.isArray(addons)
    ? addons.reduce((sum, a) => sum + (Number(a.price) || 0), 0)
    : 0;

  const insPrice = Number(insurancePrice) || 0;

  const ltDays = Number(longTermDiscountDays) || 7;
  const ltPercent = Number(longTermDiscountPercent) || 10;
  const longTermDiscount = days >= ltDays ? basePrice * (ltPercent / 100) : 0;

  const subtotal = basePrice + addonPrice + insPrice - longTermDiscount;

  const cpPercent = Number(couponPercent) || 0;
  const couponDiscount = subtotal * (cpPercent / 100);

  const pts = Number(pointsRedeemed) || 0;
  const pointsDiscount = pts / 10; // 10 points = PHP 1

  const total = Math.max(0, subtotal - couponDiscount - pointsDiscount);
  const pointsEarned = Math.floor(total / 100);

  const downpaymentAmount = total * 0.20;
  const balanceAmount = total * 0.80;

  return {
    days,
    basePrice,
    addonPrice,
    insurancePrice: insPrice,
    longTermDiscount,
    couponDiscount,
    pointsDiscount,
    total,
    pointsEarned,
    downpaymentAmount,
    balanceAmount
  };
}

/**
 * Formats a booking date string into a clean, human-readable format.
 * Handles ISO strings, RFC strings (e.g. "Tue, 12 May 2026 00:00:00 GMT"),
 * and YYYY-MM-DD strings.
 * Example: "2026-05-12" ? "May 12, 2026"
 * @param {string} dateStr
 * @returns {string}
 */
function formatBookingDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString('en-PH', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

/**
 * Sanitizes a string by stripping characters that could be used for
 * HTML/script injection: < > " ' ` and backslash.
 * @param {string} str
 * @returns {string}
 */
function sanitizeInput(str) {
  if (!str || typeof str !== 'string') return '';
  return str.replace(/[<>"'`\\]/g, '');
}

// Remove ES module export for browser/WebView compatibility
// All functions are available globally in this file
