/**
 * Print Header Navigation Functions
 * Requirements: 6.2 - Back button navigation functionality
 */

/**
 * Navigate back to the previous page
 * Requirement 6.2: Back button navigates to previous page in application
 */
function goBack() {
    // Check if there's a referrer in the same domain
    if (document.referrer && document.referrer.includes(window.location.hostname)) {
        window.history.back();
    } else {
        // Fallback to booking management page
        window.location.href = '/admin_app/booking-management.html';
    }
}

/**
 * Alternative navigation using sessionStorage
 * This approach stores the previous page URL before navigating to print view
 */

/**
 * Navigate to print view and store the current page
 * @param {string} printViewUrl - URL of the print view page
 * @param {string} title - Title to display in the print header
 */
function navigateToPrintView(printViewUrl, title = 'Document') {
    // Store current page URL
    sessionStorage.setItem('previousPage', window.location.href);
    
    // Store print title if provided
    if (title) {
        sessionStorage.setItem('printTitle', title);
    }
    
    // Navigate to print view
    window.location.href = printViewUrl;
}

/**
 * Go back from print view using stored previous page
 * This is an alternative to the standard goBack() function
 */
function goBackFromPrint() {
    const previousPage = sessionStorage.getItem('previousPage');
    
    if (previousPage) {
        window.location.href = previousPage;
        // Clean up sessionStorage
        sessionStorage.removeItem('previousPage');
        sessionStorage.removeItem('printTitle');
    } else {
        // Fallback to history.back()
        window.history.back();
    }
}

/**
 * Initialize print header on page load
 * Sets the title from sessionStorage if available
 */
function initializePrintHeader() {
    const storedTitle = sessionStorage.getItem('printTitle');
    const titleElement = document.getElementById('printTitle');
    
    if (storedTitle && titleElement) {
        titleElement.textContent = storedTitle;
    }
}

// Initialize print header when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePrintHeader);
} else {
    initializePrintHeader();
}

/**
 * Utility function to set print title dynamically
 * @param {string} title - Title to display in the print header
 */
function setPrintTitle(title) {
    const titleElement = document.getElementById('printTitle');
    if (titleElement) {
        titleElement.textContent = title;
    }
}
