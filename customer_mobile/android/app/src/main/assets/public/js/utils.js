/**
 * utils.js  -  Pure utility functions for the Autoride Customer Mobile App.
 * All functions are side-effect-free and fully testable without DOM or Capacitor.
 *
 * Feature: autoride-customer-mobile-app
 */

/**
 * Disposable/temporary email domains list for fraud & burner account prevention.
 */
var DISPOSABLE_EMAIL_DOMAINS = [
  'mailinator.com', 'yopmail.com', 'guerrillamail.com', 'guerrillamail.net', 'guerrillamail.org',
  'guerrillamail.biz', 'guerrillamailblock.com', 'sharklasers.com', 'grr.la', 'pokemail.net', 'spam4.me',
  'temp-mail.org', 'temp-mail.io', 'tempmail.com', 'tempmail.net', 'tempmailo.com', 'mytempmail.com',
  'mytempmail.net', 'tempreceive.com', 'tempail.com', 'tempinbox.com', 'tempinbox.co.uk', 'tempmail24.net',
  '10minutemail.com', '10minutemail.net', '10minutemail.org', 'minutemail.com', 'minuteinbox.com',
  'throwawaymail.com', 'throwaway.email', 'trashmail.com', 'trashmail.net', 'trashmail.me', 'trashmail.org',
  'trashmail.at', 'trashmail.de', 'trash-mail.com', 'dispostable.com', 'disposablemail.com', 'disposable.email',
  'getairmail.com', 'mohmal.com', 'mohmal.in', 'fakemailgenerator.com', 'generator.email', 'mytemp.email',
  'nada.ltd', 'getnada.com', 'inboxkitten.com', 'crazymailing.com', 'crazymail.com', 'dropmail.me',
  'emailondeck.com', 'burnermail.io', 'tmpmail.org', 'tmpmail.net', 'internalmail.net', 'maildrop.cc',
  'harakirimail.com', 'boun.cr', 'byom.de', 'mailcatch.com', 'fakeinbox.com', 'trashinbox.com',
  'mailnesia.com', 'luxusmail.org', 'spamgourmet.com', 'incognitomail.com', 'anonymbox.com',
  'armyspy.com', 'cuvox.de', 'dayrep.com', 'fleckens.hu', 'gustr.com', 'jourrapide.com',
  'rhyta.com', 'superrito.com', 'teleworm.us', 'tinypm.com', 'fakemail.net', 'filzmail.com',
  'hidemail.de', 'jetable.org', 'kasmail.com', 'meltmail.com', 'no-spam.ws', 'noclickemail.com',
  'nomail.xl.cx', 'nospam.ze.tc', 'safersignup.de', 'shortmail.net', 'spambox.us', 'spamfree24.org',
  'wegwerfadresse.de', 'wegwerfemail.de', 'whyspam.me', 'yapped.net', 'zippymail.info', 'zoemail.org',
  'tmail.ws', 'tempmailaddress.com', 'instant-mail.de', 'disposableaddress.com', 'burneremail.com',
  'getnada.edu', 'inboxproxy.com', 'tempmailer.com', 'throwawayemail.com', 'fake-box.com', 'trashbox.eu'
];

var DISPOSABLE_EMAIL_KEYWORDS = [
  'tempmail', 'temp-mail', 'disposable', 'throwaway', '10minutemail', 'fakemail',
  'trashmail', 'mailinator', 'yopmail', 'guerrillamail', 'burnermail', 'dropmail',
  'getnada', 'fakeinbox'
];

/**
 * Returns true if the email is from a known temporary/disposable email provider.
 * @param {string} email
 * @returns {boolean}
 */
function isDisposableEmail(email) {
  if (!email || typeof email !== 'string') return false;
  var clean = email.trim().toLowerCase();
  var parts = clean.split('@');
  if (parts.length !== 2) return false;
  var domain = parts[1];
  for (var i = 0; i < DISPOSABLE_EMAIL_DOMAINS.length; i++) {
    if (domain === DISPOSABLE_EMAIL_DOMAINS[i] || domain.endsWith('.' + DISPOSABLE_EMAIL_DOMAINS[i])) {
      return true;
    }
  }
  for (var k = 0; k < DISPOSABLE_EMAIL_KEYWORDS.length; k++) {
    if (domain.indexOf(DISPOSABLE_EMAIL_KEYWORDS[k]) !== -1) {
      return true;
    }
  }
  return false;
}

/**
 * Returns true if the email has a valid format (standard RFC-compliant structure, max 60 chars).
 * @param {string} email
 * @returns {boolean}
 */
function isValidEmailFormat(email) {
  if (!email || typeof email !== 'string') return false;
  var clean = email.trim();
  if (clean.length < 5 || clean.length > 60) return false;
  var emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return emailRegex.test(clean);
}

/**
 * Validates an email address for registration, login, and profile updates.
 * Supports standard providers (Gmail, Outlook, Yahoo, iCloud, custom domains, etc.)
 * but strictly rejects temporary/disposable mail providers.
 * @param {string} email
 * @returns {{valid: boolean, error?: string, email?: string}}
 */
function validateEmailAddress(email) {
  if (!email || typeof email !== 'string' || !email.trim()) {
    return { valid: false, error: 'Email address is required.' };
  }
  var clean = email.trim().toLowerCase();
  if (!isValidEmailFormat(clean)) {
    return { valid: false, error: 'Please enter a valid email address (e.g. name@outlook.com, name@gmail.com).' };
  }
  if (isDisposableEmail(clean)) {
    return { valid: false, error: 'Temporary/disposable email addresses are not supported. Please use a valid email (e.g. Gmail, Outlook, Yahoo, iCloud).' };
  }
  return { valid: true, email: clean };
}

/**
 * Legacy helper for checking @gmail.com
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
 * Formats a driver's license number as LNN-YY-NNNNNN (13 chars total).
 * Strictly enforces 1 uppercase letter followed by 10 digits.
 * Auto-corrects common letter/digit lookalikes in digit positions (O->0, I/L->1).
 * @param {string} value
 * @returns {string}
 */
function formatLicenseNumberInput(value) {
  if (!value) return '';
  var raw = String(value).toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (!raw) return '';

  // Position 0 must be a letter A-Z
  var firstLetterIdx = raw.search(/[A-Z]/);
  if (firstLetterIdx === -1) return '';
  var letter = raw.charAt(firstLetterIdx);
  var rest = raw.slice(firstLetterIdx + 1);

  // Positions 1..10 must be digits (convert O->0, I/L->1, strip other letters)
  var digits = rest
    .replace(/O/g, '0')
    .replace(/[IL]/g, '1')
    .replace(/[^0-9]/g, '')
    .substring(0, 10);

  var cleaned = letter + digits;
  var formatted = cleaned.substring(0, 3);
  if (cleaned.length > 3) {
    formatted += '-' + cleaned.substring(3, 5);
  }
  if (cleaned.length > 5) {
    formatted += '-' + cleaned.substring(5, 11);
  }
  return formatted;
}

/**
 * Validates a person's name (First Name, Middle Name, Last Name, Full Name, Emergency Contact Name).
 * Blocks character spam (e.g., "aaaa..."), excessive length, digits/symbols, and single-word full names.
 * @param {string} value
 * @param {string} fieldLabel
 * @param {{ required?: boolean, minLen?: number, maxLen?: number, requireFullName?: boolean, isMiddleName?: boolean }} [options]
 * @returns {{ valid: boolean, error?: string, cleaned?: string }}
 */
function validatePersonName(value, fieldLabel, options) {
  options = options || {};
  var label = fieldLabel || 'Name';
  var required = options.required !== false;
  var isMiddle = Boolean(options.isMiddleName);
  var requireFull = Boolean(options.requireFullName);
  var minLen = options.minLen || (isMiddle ? 1 : (requireFull ? 5 : 2));
  var maxLen = options.maxLen || (requireFull ? 70 : 40);

  var trimmed = (value || '').trim().replace(/\s+/g, ' ');
  if (!trimmed) {
    if (required) return { valid: false, error: label + ' is required.' };
    return { valid: true, cleaned: '' };
  }

  if (trimmed.length < minLen) {
    return { valid: false, error: label + ' must be at least ' + minLen + ' characters.' };
  }
  if (trimmed.length > maxLen) {
    return { valid: false, error: label + ' cannot exceed ' + maxLen + ' characters.' };
  }

  // Only letters (including Ñ/ñ and accented chars), spaces, hyphens, apostrophes, periods
  if (!/^[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF\u00D1\u00F1\s.'-]+$/.test(trimmed)) {
    return { valid: false, error: label + ' may only contain letters, spaces, hyphens, and periods (no numbers or symbols).' };
  }

  // Must start with a letter
  if (!/^[A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF\u00D1\u00F1]/.test(trimmed)) {
    return { valid: false, error: label + ' must start with a valid letter.' };
  }

  // Block 3 or more identical consecutive letters (e.g. "aaa", "bbbb", "xxxx")
  if (/([A-Za-z\u00D1\u00F1])\1\1/i.test(trimmed)) {
    return { valid: false, error: label + ' contains invalid repeating characters (e.g., "aaa"). Please enter a real name.' };
  }

  // Block repeated 2-letter patterns 3+ times (e.g. "ababab", "asdasd")
  var lettersOnly = trimmed.replace(/[^A-Za-z]/g, '').toLowerCase();
  if (/(..)\1\1/.test(lettersOnly) || /(...)\1\1/.test(lettersOnly)) {
    return { valid: false, error: label + ' appears to contain repetitive or gibberish text. Please enter a real name.' };
  }

  var words = trimmed.split(' ').filter(Boolean);
  for (var i = 0; i < words.length; i++) {
    var w = words[i].replace(/[.'-]/g, '');
    if (w.length > 20) {
      return { valid: false, error: 'Each word in ' + label + ' cannot exceed 20 characters.' };
    }
    // Any word of 4+ letters must contain at least one vowel (a, e, i, o, u, y) and not be 5+ vowels only
    if (w.length >= 4 && !/[aeiouyAEIOUY\u00C0-\u00FF]/.test(w)) {
      return { valid: false, error: label + ' contains an unrecognizable word ("' + words[i] + '"). Please enter a valid name.' };
    }
    if (w.length >= 5 && /^[aeiouAEIOU]+$/.test(w)) {
      return { valid: false, error: label + ' contains an invalid vowel sequence ("' + words[i] + '"). Please enter a valid name.' };
    }
  }

  if (requireFull) {
    var meaningfulWords = words.filter(function(w) { return w.replace(/[^A-Za-z]/g, '').length >= 2; });
    if (words.length < 2 || meaningfulWords.length < 2) {
      return { valid: false, error: 'Please enter both First Name and Last Name for ' + label + '.' };
    }
    if (words.length >= 2 && words.every(function(w) { return w.toLowerCase() === words[0].toLowerCase(); })) {
      return { valid: false, error: label + ' cannot have identical first and last names.' };
    }
  }

  return { valid: true, cleaned: trimmed };
}

/**
 * Validates a Philippine mobile phone number (09XXXXXXXXX).
 * Rejects dummy/repeating numbers such as 09999999999, 09000000000, 09123456789.
 * @param {string} phone
 * @param {string} [fieldLabel]
 * @returns {{ valid: boolean, error?: string, cleaned?: string }}
 */
function validatePhonePH(phone, fieldLabel) {
  var label = fieldLabel || 'Phone number';
  var raw = (phone || '').trim();
  if (!raw) {
    return { valid: false, error: label + ' is required.' };
  }
  var cleaned = raw.replace(/\s|-/g, '');
  if (cleaned.indexOf('+639') === 0 && cleaned.length === 13) {
    cleaned = '0' + cleaned.slice(3);
  } else if (cleaned.indexOf('639') === 0 && cleaned.length === 12) {
    cleaned = '0' + cleaned.slice(2);
  }

  if (!/^09\d{9}$/.test(cleaned)) {
    return { valid: false, error: label + ' must be an 11-digit Philippine mobile number starting with 09 (e.g., 09171234567).' };
  }

  // Reject 5+ identical consecutive digits (e.g., 09999999999, 09111111111, 09170000000)
  if (/(\d)\1{4,}/.test(cleaned)) {
    return { valid: false, error: 'Invalid ' + label.toLowerCase() + '. Repeating or dummy numbers (like ' + cleaned + ') are not allowed.' };
  }

  // Reject sequential dummy digits
  var sub = cleaned.slice(2);
  if (sub === '123456789' || sub === '987654321' || sub === '012345678' || /(..)\1{3,}/.test(sub) || /(\d{3})\1{2}/.test(sub)) {
    return { valid: false, error: 'Invalid ' + label.toLowerCase() + '. Please enter an active, real mobile number.' };
  }

  return { valid: true, cleaned: cleaned };
}

/**
 * Validates a Philippine LTO Driver's License Number (LNN-YY-NNNNNN).
 * Position 1 must be a letter (A-Z), followed by 2 digits, hyphen, 2 digits, hyphen, 6 digits.
 * @param {string} licenseNum
 * @returns {{ valid: boolean, error?: string, cleaned?: string }}
 */
function validateLtoLicenseNumber(licenseNum) {
  var cleaned = (licenseNum || '').trim().toUpperCase();
  if (!cleaned) {
    return { valid: false, error: 'License Number is required.' };
  }
  if (!/^[A-Z]\d{2}-\d{2}-\d{6}$/.test(cleaned)) {
    return {
      valid: false,
      error: 'Invalid LTO License format. Must be 1 letter + 2 digits - 2 digits - 6 digits (e.g., N01-23-456789).'
    };
  }
  var parts = cleaned.split('-');
  var officeDigits = parts[0].slice(1);
  var serial = parts[2];
  if (officeDigits === '00') {
    return { valid: false, error: 'Invalid LTO agency code (' + parts[0] + '). Cannot be 00.' };
  }
  if (/^(\d)\1{5}$/.test(serial) || serial === '123456' || serial === '654321' || serial === '012345') {
    return { valid: false, error: 'Invalid LTO serial number (' + serial + '). Dummy or repeating numbers are not allowed.' };
  }
  return { valid: true, cleaned: cleaned };
}

/**
 * Validates Driver's License Date of Birth.
 * Must be a valid date and driver age must be between 18 and 75 years old.
 * @param {string} dobStr - YYYY-MM-DD
 * @returns {{ valid: boolean, error?: string }}
 */
function validateDriverDob(dobStr) {
  if (!dobStr) {
    return { valid: false, error: 'Date of Birth is required.' };
  }
  var parts = String(dobStr).split('T')[0].split('-').map(Number);
  if (parts.length !== 3 || !parts[0] || !parts[1] || !parts[2]) {
    return { valid: false, error: 'Invalid Date of Birth format.' };
  }
  var dob = new Date(parts[0], parts[1] - 1, parts[2]);
  if (isNaN(dob.getTime()) || dob.getFullYear() !== parts[0] || (dob.getMonth() + 1) !== parts[1] || dob.getDate() !== parts[2]) {
    return { valid: false, error: 'Invalid Date of Birth.' };
  }
  var today = new Date();
  var age = today.getFullYear() - dob.getFullYear();
  var m = today.getMonth() - dob.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
    age--;
  }
  if (age < 18) {
    return { valid: false, error: 'You must be at least 18 years old to rent or drive a vehicle.' };
  }
  if (age > 75 || parts[0] < (today.getFullYear() - 75)) {
    return { valid: false, error: 'Invalid Date of Birth (' + parts[0] + '). Driver age must be between 18 and 75 years old.' };
  }
  return { valid: true };
}

/**
 * Validates Driver's License Expiry Date.
 * Must not be expired and must not exceed 10 years from today (LTO max validity).
 * @param {string} expiryStr - YYYY-MM-DD
 * @returns {{ valid: boolean, error?: string }}
 */
function validateLicenseExpiry(expiryStr) {
  if (!expiryStr) {
    return { valid: false, error: 'License Expiry Date is required.' };
  }
  var parts = String(expiryStr).split('T')[0].split('-').map(Number);
  if (parts.length !== 3 || !parts[0] || !parts[1] || !parts[2]) {
    return { valid: false, error: 'Invalid Expiry Date format.' };
  }
  var exp = new Date(parts[0], parts[1] - 1, parts[2]);
  if (isNaN(exp.getTime()) || exp.getFullYear() !== parts[0] || (exp.getMonth() + 1) !== parts[1] || exp.getDate() !== parts[2]) {
    return { valid: false, error: 'Invalid Expiry Date.' };
  }
  var now = new Date();
  var todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  if (exp <= todayStart) {
    return { valid: false, error: 'Your driver\'s license is expired. Please provide an active, unexpired license.' };
  }
  var maxExpiry = new Date(now.getFullYear() + 11, now.getMonth(), now.getDate());
  if (exp > maxExpiry) {
    return {
      valid: false,
      error: 'Invalid Expiry Date (' + parts[0] + '). LTO driver\'s licenses are valid for up to 10 years only (max year ' + (now.getFullYear() + 10) + ').'
    };
  }
  return { valid: true };
}

/**
 * Validates an Address or Destination text field against character spam and length bounds.
 * @param {string} value
 * @param {string} fieldLabel
 * @param {number} [minLen]
 * @param {number} [maxLen]
 * @returns {{ valid: boolean, error?: string, cleaned?: string }}
 */
function validateAddressOrPlace(value, fieldLabel, minLen, maxLen) {
  var label = fieldLabel || 'Address';
  minLen = minLen || 4;
  maxLen = maxLen || 150;
  var trimmed = (value || '').trim().replace(/\s+/g, ' ');
  if (!trimmed) {
    return { valid: false, error: label + ' is required.' };
  }
  if (trimmed.length < minLen) {
    return { valid: false, error: label + ' must be at least ' + minLen + ' characters.' };
  }
  if (trimmed.length > maxLen) {
    return { valid: false, error: label + ' cannot exceed ' + maxLen + ' characters.' };
  }
  if (!/[A-Za-z]{2,}/.test(trimmed)) {
    return { valid: false, error: 'Please enter a valid ' + label.toLowerCase() + ' containing letters.' };
  }
  if (/([A-Za-z])\1\1/i.test(trimmed) || /(.)\1{4,}/.test(trimmed)) {
    return { valid: false, error: label + ' contains invalid repeating characters. Please enter a real location.' };
  }
  var words = trimmed.split(' ');
  for (var i = 0; i < words.length; i++) {
    if (words[i].length > 28) {
      return { valid: false, error: label + ' contains an unusually long word. Please enter a valid address or place.' };
    }
  }
  return { valid: true, cleaned: trimmed };
}



/**
 * Compresses an image file client-side using an HTML5 Canvas to prevent payload errors.
 * Fits within maxWidth/maxHeight and outputs JPEG blob.
 * @param {File|Blob} file
 * @param {number} maxWidth
 * @param {number} maxHeight
 * @param {number} quality
 * @returns {Promise<File>}
 */
function compressImageFile(file, maxWidth, maxHeight, quality) {
  maxWidth = maxWidth || 1200;
  maxHeight = maxHeight || 1200;
  quality = quality || 0.82;

  if (!file || !file.type || !file.type.startsWith('image/')) {
    return Promise.resolve(file);
  }

  // If already under 350KB and is jpeg/png, no compression needed
  if (file.size && file.size < 350 * 1024) {
    return Promise.resolve(file);
  }

  return new Promise(function(resolve) {
    try {
      var reader = new FileReader();
      reader.onload = function(e) {
        var img = new Image();
        img.onload = function() {
          try {
            var width = img.width;
            var height = img.height;

            if (width > maxWidth || height > maxHeight) {
              if (width > height) {
                height = Math.round((height * maxWidth) / width);
                width = maxWidth;
              } else {
                width = Math.round((width * maxHeight) / height);
                maxHeight = maxHeight;
                height = Math.round((height * maxHeight) / img.height);
              }
            }

            var canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);

            canvas.toBlob(function(blob) {
              if (blob && blob.size < file.size) {
                var fileName = (file.name || 'photo.jpg').replace(/\.[^/.]+$/, '.jpg');
                var compressedFile = new File([blob], fileName, { type: 'image/jpeg' });
                console.log('[ImageCompress] Compressed from ' + Math.round(file.size/1024) + 'KB down to ' + Math.round(compressedFile.size/1024) + 'KB');
                resolve(compressedFile);
              } else {
                resolve(file); // Keep original if blob conversion didn't reduce size
              }
            }, 'image/jpeg', quality);
          } catch(canvasErr) {
            console.warn('[ImageCompress] Canvas compression error:', canvasErr);
            resolve(file);
          }
        };
        img.onerror = function() {
          resolve(file);
        };
        img.src = e.target.result;
      };
      reader.onerror = function() {
        resolve(file);
      };
      reader.readAsDataURL(file);
    } catch(err) {
      console.warn('[ImageCompress] Compression setup error:', err);
      resolve(file);
    }
  });
}
if (typeof window !== 'undefined') window.compressImageFile = compressImageFile;

/**
 * Validates a file for upload: must be an image and <= 15 MB before compression.
 * @param {{ type: string, size: number }} file
 * @returns {string|null} Error message string, or null if valid.
 */
function validateUploadFile(file) {
  if (!file) return 'No file selected.';
  var type = (file.type || '').toLowerCase();
  var isImage = type.indexOf('image/') === 0 || /\.(jpe?g|png|webp|gif|heic|heif)$/i.test(file.name || '');
  if (!isImage) {
    return 'Only image files (JPG, PNG, WebP) are accepted.';
  }
  var maxRawSize = 15 * 1024 * 1024; // 15 MB raw camera limit before client compression
  if (file.size > maxRawSize) {
    return 'Image file is too large (over 15 MB). Please select a smaller photo.';
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

  const maxBookingDays = (typeof appSettings !== 'undefined' && Number(appSettings.max_booking_duration_days)) || 730;
  const bookingDays = Math.round((end - start) / (1000 * 60 * 60 * 24));
  if (bookingDays > maxBookingDays) {
    return {
      valid: false,
      error: 'Booking duration exceeds the maximum limit of ' + maxBookingDays + ' days (' + Math.round(maxBookingDays / 365) + ' years).'
    };
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
  pointsRedeemed,
  deliveryFee,
  driverFee = 0
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
  const drvFee = Number(driverFee) || 0;

  const ltDays = Number(longTermDiscountDays) || 7;
  const ltPercent = Number(longTermDiscountPercent) || 10;
  const longTermDiscount = days >= ltDays ? basePrice * (ltPercent / 100) : 0;

  const subtotal = basePrice + addonPrice + insPrice + drvFee - longTermDiscount;

  const cpPercent = Number(couponPercent) || 0;
  const couponDiscount = subtotal * (cpPercent / 100);

  // Fetch dynamic loyalty configurations
  const spendRatio = (typeof appSettings !== 'undefined' && Number(appSettings.loyalty_points_spend_ratio)) || 100;
  const pointsValRate = (typeof appSettings !== 'undefined' && Number(appSettings.loyalty_points_value)) || 0.1;
  const maxDiscountPct = (typeof appSettings !== 'undefined' && Number(appSettings.loyalty_max_discount_percent)) || 50;

  const pts = Number(pointsRedeemed) || 0;
  const pointsValue = pts * pointsValRate;
  
  // LIMIT: Points can only cover configurable max percentage of subtotal (after coupon)
  const maxPointsDiscount = (subtotal - couponDiscount) * (maxDiscountPct / 100);
  const pointsDiscount = Math.min(pointsValue, maxPointsDiscount);

  const delFee = Number(deliveryFee) || 0;
  const total = Math.max(0, subtotal - couponDiscount - pointsDiscount) + delFee;
  const pointsEarned = Math.floor(total / spendRatio);

  const downpaymentAmount = total * 0.20;
  const balanceAmount = total * 0.80;

  return {
    days,
    basePrice,
    addonPrice,
    insurancePrice: insPrice,
    driverFee: drvFee,
    longTermDiscount,
    couponDiscount,
    pointsDiscount,
    deliveryFee: delFee,
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
            console.log('Compressed image from ' + (file.size / 1024 / 1024).toFixed(2) + 'MB to ' + (compressedFile.size / 1024).toFixed(2) + 'KB');
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
