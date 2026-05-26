/* ============================================================
   Autoride Admin – Shared Utility Functions
   Reusable utility functions for all admin pages
   ============================================================ */

// API Base URL - can be overridden by individual pages
const API_BASE = window.API_BASE || 'http://localhost:5000';

/* ==================== HTML ESCAPING ==================== */

/**
 * Escapes HTML special characters to prevent XSS attacks
 * @param {string} str - The string to escape
 * @returns {string} - The escaped string
 */
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/* ==================== DATE FORMATTING ==================== */

/**
 * Formats a date string into a readable format
 * @param {string} dateStr - ISO date string or date-compatible string
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} - Formatted date string
 */
function formatDate(dateStr, options = null) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    
    // Check if date is valid
    if (isNaN(d.getTime())) return '—';
    
    const defaultOptions = { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
    };
    
    return d.toLocaleDateString('en-US', options || defaultOptions);
}

/**
 * Formats a date string with time
 * @param {string} dateStr - ISO date string or date-compatible string
 * @returns {string} - Formatted date and time string
 */
function formatDateTime(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    
    if (isNaN(d.getTime())) return '—';
    
    return d.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Formats a time string
 * @param {string} dateStr - ISO date string or date-compatible string
 * @returns {string} - Formatted time string
 */
function formatTime(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    
    if (isNaN(d.getTime())) return '—';
    
    return d.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Formats rental date range
 * @param {string} startDate - Start date string
 * @param {string} endDate - End date string
 * @returns {string} - Formatted date range
 */
function formatRentalDates(startDate, endDate) {
    return `${formatDate(startDate)} - ${formatDate(endDate)}`;
}

/**
 * Calculates days between two dates
 * @param {string} startDate - Start date string
 * @param {string} endDate - End date string
 * @returns {number} - Number of days
 */
function daysBetween(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

/* ==================== PRICE FORMATTING ==================== */

/**
 * Formats a price value with Philippine Peso formatting
 * @param {number|string} price - The price value
 * @param {string} currency - Currency symbol (default: ?)
 * @returns {string} - Formatted price string
 */
function formatPrice(price, currency = '?') {
    if (price == null || price === '') return `${currency}0.00`;
    
    const numPrice = parseFloat(price);
    
    if (isNaN(numPrice)) return `${currency}0.00`;
    
    return `${currency}${numPrice.toLocaleString('en-PH', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
    })}`;
}

/**
 * Formats a number with thousand separators
 * @param {number|string} num - The number to format
 * @returns {string} - Formatted number string
 */
function formatNumber(num) {
    if (num == null || num === '') return '0';
    
    const numValue = parseFloat(num);
    
    if (isNaN(numValue)) return '0';
    
    return numValue.toLocaleString('en-PH');
}

/* ==================== TOAST NOTIFICATIONS ==================== */

let _toastTimeout = null;
let _toastElement = null;

/**
 * Shows a toast notification
 * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
 * @param {string} message - The message to display
 * @param {number} duration - Duration in milliseconds (default: 4000)
 */
function showToast(type, message, duration = 4000) {
    // Get or create toast element
    if (!_toastElement) {
        _toastElement = document.getElementById('toast');
        
        // If toast doesn't exist in DOM, create it
        if (!_toastElement) {
            _toastElement = document.createElement('div');
            _toastElement.id = 'toast';
            _toastElement.className = 'toast hidden';
            _toastElement.innerHTML = `
                <span class="toast-icon" id="toastIcon"></span>
                <span class="toast-msg" id="toastMsg"></span>
            `;
            document.body.appendChild(_toastElement);
        }
    }
    
    const toastIcon = document.getElementById('toastIcon');
    const toastMsg = document.getElementById('toastMsg');
    
    // Set icon based on type
    const icons = {
        success: '?',
        error: '?',
        warning: '??',
        info: '??'
    };
    
    _toastElement.className = `toast ${type}`;
    toastIcon.textContent = icons[type] || icons.info;
    toastMsg.textContent = message;
    
    // Show toast
    _toastElement.classList.remove('hidden');
    
    // Clear existing timeout
    clearTimeout(_toastTimeout);
    
    // Auto-hide after duration
    _toastTimeout = setTimeout(() => {
        _toastElement.classList.add('hidden');
    }, duration);
}

/**
 * Hides the toast notification immediately
 */
function hideToast() {
    if (_toastElement) {
        _toastElement.classList.add('hidden');
        clearTimeout(_toastTimeout);
    }
}

/* ==================== STRING UTILITIES ==================== */

/**
 * Truncates a string to a maximum length with ellipsis
 * @param {string} str - The string to truncate
 * @param {number} maxLength - Maximum length (default: 50)
 * @returns {string} - Truncated string
 */
function truncateString(str, maxLength = 50) {
    if (!str) return '';
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength) + '...';
}

/**
 * Truncates a location string to a maximum length with ellipsis
 * Returns "N/A" for null/undefined locations
 * @param {string} location - The location string to truncate
 * @param {number} maxLength - Maximum length (default: 30)
 * @returns {string} - Truncated location string or "N/A"
 */
function truncateLocation(location, maxLength = 30) {
    if (!location) return 'N/A';
    if (location.length <= maxLength) return location;
    return location.substring(0, maxLength) + '...';
}

/**
 * Capitalizes the first letter of a string
 * @param {string} str - The string to capitalize
 * @returns {string} - Capitalized string
 */
function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Converts a string to title case
 * @param {string} str - The string to convert
 * @returns {string} - Title case string
 */
function toTitleCase(str) {
    if (!str) return '';
    return str.toLowerCase().split(' ').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

/* ==================== VALIDATION UTILITIES ==================== */

/**
 * Validates an email address
 * @param {string} email - The email to validate
 * @returns {boolean} - True if valid, false otherwise
 */
function isValidEmail(email) {
    if (!email) return false;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validates a phone number (Philippine format)
 * @param {string} phone - The phone number to validate
 * @returns {boolean} - True if valid, false otherwise
 */
function isValidPhone(phone) {
    if (!phone) return false;
    // Accepts formats: 09123456789, +639123456789, 9123456789
    const phoneRegex = /^(\+63|0)?9\d{9}$/;
    return phoneRegex.test(phone.replace(/[\s-]/g, ''));
}

/* ==================== ARRAY UTILITIES ==================== */

/**
 * Groups an array of objects by a key
 * @param {Array} array - The array to group
 * @param {string} key - The key to group by
 * @returns {Object} - Grouped object
 */
function groupBy(array, key) {
    return array.reduce((result, item) => {
        const groupKey = item[key];
        if (!result[groupKey]) {
            result[groupKey] = [];
        }
        result[groupKey].push(item);
        return result;
    }, {});
}

/**
 * Sorts an array of objects by a key
 * @param {Array} array - The array to sort
 * @param {string} key - The key to sort by
 * @param {string} order - Sort order: 'asc' or 'desc' (default: 'asc')
 * @returns {Array} - Sorted array
 */
function sortBy(array, key, order = 'asc') {
    return [...array].sort((a, b) => {
        const aVal = a[key];
        const bVal = b[key];
        
        if (aVal < bVal) return order === 'asc' ? -1 : 1;
        if (aVal > bVal) return order === 'asc' ? 1 : -1;
        return 0;
    });
}

/* ==================== DEBOUNCE UTILITY ==================== */

/**
 * Creates a debounced function that delays execution
 * @param {Function} func - The function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} - Debounced function
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/* ==================== LOCAL STORAGE UTILITIES ==================== */

/**
 * Safely gets an item from localStorage
 * @param {string} key - The key to retrieve
 * @param {*} defaultValue - Default value if key doesn't exist
 * @returns {*} - The stored value or default
 */
function getLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Error reading from localStorage:', error);
        return defaultValue;
    }
}

/**
 * Safely sets an item in localStorage
 * @param {string} key - The key to set
 * @param {*} value - The value to store
 * @returns {boolean} - True if successful, false otherwise
 */
function setLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        console.error('Error writing to localStorage:', error);
        return false;
    }
}

/**
 * Removes an item from localStorage
 * @param {string} key - The key to remove
 */
function removeLocalStorage(key) {
    try {
        localStorage.removeItem(key);
    } catch (error) {
        console.error('Error removing from localStorage:', error);
    }
}

/* ==================== URL UTILITIES ==================== */

/**
 * Gets a URL parameter value
 * @param {string} param - The parameter name
 * @returns {string|null} - The parameter value or null
 */
function getUrlParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

/**
 * Sets a URL parameter without reloading the page
 * @param {string} param - The parameter name
 * @param {string} value - The parameter value
 */
function setUrlParam(param, value) {
    const url = new URL(window.location);
    url.searchParams.set(param, value);
    window.history.pushState({}, '', url);
}

/* ==================== STATUS BADGE HELPER ==================== */

/**
 * Generates a status badge HTML
 * @param {string} status - The status text
 * @returns {string} - HTML string for status badge
 */
function statusBadge(status) {
    const cls = (status || 'pending').toLowerCase().replace(/\s+/g, '-');
    return `<span class="status-badge status-${cls}">${escapeHtml(status) || 'Unknown'}</span>`;
}

/* ==================== LOADING STATE HELPERS ==================== */

/**
 * Shows or hides a loading spinner
 * @param {HTMLElement} element - The element to show/hide
 * @param {boolean} show - True to show, false to hide
 */
function toggleLoading(element, show) {
    if (!element) return;
    element.classList.toggle('hidden', !show);
}

/**
 * Creates a loading spinner element
 * @param {string} message - Optional loading message
 * @returns {HTMLElement} - The loading element
 */
function createLoadingSpinner(message = 'Loading...') {
    const container = document.createElement('div');
    container.className = 'loading-container';
    container.innerHTML = `
        <div class="spinner"></div>
        <p>${escapeHtml(message)}</p>
    `;
    return container;
}

/* ==================== REGEX ESCAPE UTILITY ==================== */

/**
 * Escapes special regex characters in a string
 * @param {string} str - The string to escape
 * @returns {string} - Escaped string
 */
function escapeRegex(str) {
    if (!str) return '';
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/* ==================== EXPORT FOR MODULE USAGE (if needed) ==================== */

// If using ES6 modules, uncomment the following:
// export {
//     escapeHtml,
//     formatDate,
//     formatDateTime,
//     formatTime,
//     formatRentalDates,
//     daysBetween,
//     formatPrice,
//     formatNumber,
//     showToast,
//     hideToast,
//     truncateString,
//     capitalize,
//     toTitleCase,
//     isValidEmail,
//     isValidPhone,
//     groupBy,
//     sortBy,
//     debounce,
//     getLocalStorage,
//     setLocalStorage,
//     removeLocalStorage,
//     getUrlParam,
//     setUrlParam,
//     statusBadge,
//     toggleLoading,
//     createLoadingSpinner,
//     escapeRegex
// };
