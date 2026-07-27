/**
 * utils.js  -  Pure utility functions for the Autoride Customer Mobile App.
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

function showInlineError(inputElement, errorMessage) {
  if (!inputElement) return;
  var errSpan = inputElement.nextElementSibling;
  if (!errSpan || !errSpan.classList.contains('inline-error-msg')) {
    errSpan = document.createElement('span');
    errSpan.className = 'inline-error-msg';
    errSpan.style.color = 'var(--danger, #f87171)';
    errSpan.style.fontSize = '0.75rem';
    errSpan.style.marginTop = '4px';
    errSpan.style.display = 'block';
    inputElement.parentNode.insertBefore(errSpan, inputElement.nextSibling);
  }
  errSpan.textContent = errorMessage;
  inputElement.style.borderColor = 'var(--danger, #f87171)';
  inputElement.focus();
}

function clearInlineError(inputElement) {
  if (!inputElement) return;
  var errSpan = inputElement.nextElementSibling;
  if (errSpan && errSpan.classList.contains('inline-error-msg')) {
    errSpan.textContent = '';
  }
  inputElement.style.borderColor = 'var(--border, #e5e7eb)';
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
  return '&#8369;' + num.toLocaleString('en-PH', {
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
 * Formats a 'YYYY-MM-DD' string into a readable date like "Jun 17, 2026".
 * @param {string} dateStr - YYYY-MM-DD
 * @returns {string}
 */
function formatDateDisplay(dateStr) {
  if (!dateStr) return '';
  var parts = dateStr.split('T')[0].split('-');
  if (parts.length < 3) return dateStr;
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var y = parseInt(parts[0]), m = parseInt(parts[1]) - 1, d = parseInt(parts[2]);
  return months[m] + ' ' + d + ', ' + y;
}

/**
 * Validates a file for upload: must be JPEG or PNG and ? 5 MB.
 * Property 7: File validation  -  format and size.
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
 * @param {string} startDate  -  'YYYY-MM-DD'
 * @param {string} endDate    -  'YYYY-MM-DD'
 * @returns {{ valid: boolean, error?: string }}
 */
function validateDateRange(startDate, endDate, pickupTime) {
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

  // If start date is TODAY, validate pickup time is at least 1 hour from now
  if (start.getTime() === today.getTime() && pickupTime) {
    const [hh, mm] = pickupTime.split(':').map(Number);
    const pickupDateTime = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hh, mm);
    const minAllowed = new Date(now.getTime() + 60 * 60 * 1000); // +1 hour from now
    if (pickupDateTime < minAllowed) {
      const minH = minAllowed.getHours().toString().padStart(2, '0');
      const minM = minAllowed.getMinutes() >= 30 ? '30' : '00';
      const ampm = minAllowed.getHours() < 12 ? 'AM' : 'PM';
      const h12 = minAllowed.getHours() === 0 ? 12 : minAllowed.getHours() > 12 ? minAllowed.getHours() - 12 : minAllowed.getHours();
      return {
        valid: false,
        error: 'Pickup time must be at least 1 hour from now. Please choose a time after ' + h12 + ':' + minM + ' ' + ampm + '.'
      };
    }
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
 * @param {string} startDate  -  'YYYY-MM-DD'
 * @param {string} endDate    -  'YYYY-MM-DD'
 * @param {Array<{price: number}>} addons  -  array of add-on objects with a price field
 * @param {number} insurancePrice
 * @param {number} longTermDiscountDays  -  minimum days to qualify for long-term discount
 * @param {number} longTermDiscountPercent  -  discount percentage (e.g. 10 for 10%)
 * @param {number} couponPercent  -  coupon discount percentage (0 if none)
 * @param {number} pointsRedeemed  -  loyalty points to redeem (10 points = PHP 1)
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
  const pointsValue = pts / 10; // 10 points = PHP 1
  
  // LIMIT: Points can only cover max 50% of subtotal (after coupon)
  const maxPointsDiscount = (subtotal - couponDiscount) * 0.50;
  const pointsDiscount = Math.min(pointsValue, maxPointsDiscount);

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
  if (!dateStr) return ' - ';
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

/**
 * Compresses an image file using canvas before uploading.
 * Returns a Promise that resolves with a compressed File object (or original file if compression fails/unsupported).
 */
function compressImage(file, maxW, maxH, quality) {
  return new Promise(function(resolve) {
    if (!file || !file.type || !file.type.match(/image.*/)) {
      resolve(file);
      return;
    }
    
    var reader = new FileReader();
    reader.onload = function(readerEvent) {
      var image = new Image();
      image.onload = function() {
        var width = image.width;
        var height = image.height;
        
        if (width > height) {
          if (width > maxW) {
            height *= maxW / width;
            width = maxW;
          }
        } else {
          if (height > maxH) {
            width *= maxH / height;
            height = maxH;
          }
        }
        
        var canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        
        var ctx = canvas.getContext('2d');
        ctx.drawImage(image, 0, 0, width, height);
        
        canvas.toBlob(function(blob) {
          if (blob) {
            var compressedFile = new File([blob], file.name || 'image.jpg', {
              type: 'image/jpeg',
              lastModified: Date.now()
            });
            resolve(compressedFile);
          } else {
            resolve(file);
          }
        }, 'image/jpeg', quality);
      };
      image.onerror = function() {
        resolve(file);
      };
      image.src = readerEvent.target.result;
    };
    reader.onerror = function() {
      resolve(file);
    };
    reader.readAsDataURL(file);
  });
}

// Remove ES module export for browser/WebView compatibility
// All functions are available globally in this file
