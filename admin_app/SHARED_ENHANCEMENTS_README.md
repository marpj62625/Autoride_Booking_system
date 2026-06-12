# Shared Enhancements Documentation

## Overview

This document describes the shared CSS enhancements and utility functions available for all Autoride Admin Panel pages. These enhancements provide consistent styling, improved typography, and reusable JavaScript utilities across the application.

## Files

- **`shared-enhancements.css`** - Shared CSS styles including enhanced typography, modal overlays, toast notifications, and utility classes
- **`shared-utils.js`** - Shared JavaScript utility functions for common operations
- **`test-shared-enhancements.html`** - Test page demonstrating all shared enhancements

## Usage

### Including in HTML Pages

Add the following to your HTML `<head>` section:

```html
<!-- Base styles (booking-management.css or similar) -->
<link rel="stylesheet" href="booking-management.css">

<!-- Shared enhancements -->
<link rel="stylesheet" href="shared-enhancements.css">

<!-- Shared utilities -->
<script src="shared-utils.js"></script>
```

## CSS Enhancements

### 1. Enhanced Typography

Apply the `enhanced-text` class to containers for improved readability with 15%+ font size increases.

**Usage:**
```html
<div class="enhanced-text">
    <h3>Booking Details</h3>
    <div class="info-grid">
        <div class="info-item">
            <span class="info-label">Customer:</span>
            <span class="info-value">Juan Dela Cruz</span>
        </div>
    </div>
</div>
```

**Font Sizes:**
- `.info-label`: 1.05rem (23.5% increase from 0.85rem)
- `.info-value`: 1.1rem (15.8% increase from 0.95rem)
- `h3`: 1.44rem (20% increase from 1.2rem)
- `h4`: 1.08rem (20% increase from 0.9rem)

**Responsive Breakpoints:**
- Desktop (>1024px): Full enhanced sizes
- Tablet (768px-1024px): Slightly reduced sizes
- Mobile (<768px): Further reduced for optimal mobile viewing
- Small mobile (<480px): Minimum readable sizes

### 2. Modal Overlays

Pre-styled modal components with backdrop blur and animations.

**Usage:**
```html
<div class="modal-overlay hidden" id="myModal">
    <div class="modal-card">
        <header class="modal-header">
            <h3>Modal Title</h3>
            <button class="close-btn" onclick="closeModal()">?</button>
        </header>
        <div class="modal-body">
            <!-- Modal content -->
        </div>
        <div class="modal-footer">
            <button class="btn">Close</button>
        </div>
    </div>
</div>
```

**Features:**
- Backdrop blur effect
- Fade-in animation (0.2s)
- Slide-up animation for modal card (0.3s)
- Responsive sizing (max-width: 600px, max-height: 90vh)
- Sticky header and footer
- Custom scrollbar styling

### 3. Toast Notifications

Styled toast notifications for user feedback.

**CSS Classes:**
- `.toast` - Base toast container
- `.toast.success` - Success notification (green)
- `.toast.error` - Error notification (red)
- `.toast.warning` - Warning notification (amber)
- `.toast.info` - Info notification (blue)

**Usage with JavaScript:**
```javascript
showToast('success', 'Operation completed successfully!');
showToast('error', 'An error occurred');
showToast('warning', 'Please check your input');
showToast('info', 'New update available');
```

### 4. Status Badges

Pre-styled status badges for booking and payment statuses.

**Usage:**
```html
<span class="status-badge status-pending">Pending</span>
<span class="status-badge status-approved">Approved</span>
<span class="status-badge status-rejected">Rejected</span>
<span class="status-badge status-completed">Completed</span>
<span class="status-badge status-cancelled">Cancelled</span>

<!-- Payment status -->
<span class="payment-status paid">Paid</span>
<span class="payment-status unpaid">Unpaid</span>
<span class="payment-status refund-pending">Refund Pending</span>
<span class="payment-status refunded">Refunded</span>
```

### 5. Loading States

**Spinner:**
```html
<div class="loading-container">
    <div class="spinner"></div>
    <p>Loading data...</p>
</div>
```

**Empty State:**
```html
<div class="empty-state">
    <div class="empty-state-icon">??</div>
    <h3>No Results Found</h3>
    <p>Try adjusting your search criteria</p>
</div>
```

### 6. Utility Classes

**Spacing:**
- `.mt-1` to `.mt-4` - Margin top (0.5rem to 2rem)
- `.mb-1` to `.mb-4` - Margin bottom (0.5rem to 2rem)
- `.p-1` to `.p-4` - Padding (0.5rem to 2rem)

**Layout:**
- `.flex` - Display flex
- `.flex-col` - Flex direction column
- `.items-center` - Align items center
- `.justify-between` - Justify content space-between
- `.gap-1` to `.gap-3` - Gap (0.5rem to 1.5rem)

**Misc:**
- `.w-full` - Width 100%
- `.hidden` - Display none (with !important)
- `.text-center`, `.text-left`, `.text-right` - Text alignment

## JavaScript Utilities

### HTML & Security

#### `escapeHtml(str)`
Escapes HTML special characters to prevent XSS attacks.

```javascript
const safe = escapeHtml('<script>alert("XSS")</script>');
// Returns: &lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;
```

### Date Formatting

#### `formatDate(dateStr, options)`
Formats a date string into readable format.

```javascript
formatDate('2024-01-15');
// Returns: "Jan 15, 2024"

formatDate('2024-01-15', { month: 'long', day: 'numeric', year: 'numeric' });
// Returns: "January 15, 2024"
```

#### `formatDateTime(dateStr)`
Formats date with time.

```javascript
formatDateTime('2024-01-15T14:30:00');
// Returns: "Jan 15, 2024, 02:30 PM"
```

#### `formatTime(dateStr)`
Formats time only.

```javascript
formatTime('2024-01-15T14:30:00');
// Returns: "02:30 PM"
```

#### `formatRentalDates(startDate, endDate)`
Formats a date range.

```javascript
formatRentalDates('2024-01-15', '2024-01-20');
// Returns: "Jan 15, 2024 - Jan 20, 2024"
```

#### `daysBetween(startDate, endDate)`
Calculates days between two dates.

```javascript
daysBetween('2024-01-15', '2024-01-20');
// Returns: 5
```

### Price Formatting

#### `formatPrice(price, currency)`
Formats price with Philippine Peso formatting.

```javascript
formatPrice(5500);
// Returns: "?5,500.00"

formatPrice(5500, '$');
// Returns: "$5,500.00"
```

#### `formatNumber(num)`
Formats number with thousand separators.

```javascript
formatNumber(1234567);
// Returns: "1,234,567"
```

### Toast Notifications

#### `showToast(type, message, duration)`
Shows a toast notification.

```javascript
showToast('success', 'Booking approved successfully!');
showToast('error', 'Failed to load data', 5000);
showToast('warning', 'License expires soon');
showToast('info', 'New feature available');
```

**Parameters:**
- `type`: 'success', 'error', 'warning', or 'info'
- `message`: The message to display
- `duration`: Duration in milliseconds (default: 4000)

#### `hideToast()`
Hides the toast immediately.

```javascript
hideToast();
```

### String Utilities

#### `truncateString(str, maxLength)`
Truncates a string with ellipsis.

```javascript
truncateString('This is a very long string', 15);
// Returns: "This is a very..."
```

#### `capitalize(str)`
Capitalizes first letter.

```javascript
capitalize('hello world');
// Returns: "Hello world"
```

#### `toTitleCase(str)`
Converts to title case.

```javascript
toTitleCase('hello world from autoride');
// Returns: "Hello World From Autoride"
```

### Validation

#### `isValidEmail(email)`
Validates email address.

```javascript
isValidEmail('test@example.com');
// Returns: true

isValidEmail('invalid-email');
// Returns: false
```

#### `isValidPhone(phone)`
Validates Philippine phone number.

```javascript
isValidPhone('09123456789');
// Returns: true

isValidPhone('+639123456789');
// Returns: true

isValidPhone('12345');
// Returns: false
```

### Array Utilities

#### `groupBy(array, key)`
Groups array of objects by a key.

```javascript
const bookings = [
    { id: 1, status: 'Pending' },
    { id: 2, status: 'Approved' },
    { id: 3, status: 'Pending' }
];

groupBy(bookings, 'status');
// Returns: {
//   Pending: [{ id: 1, status: 'Pending' }, { id: 3, status: 'Pending' }],
//   Approved: [{ id: 2, status: 'Approved' }]
// }
```

#### `sortBy(array, key, order)`
Sorts array of objects by a key.

```javascript
const bookings = [
    { id: 3, name: 'Charlie' },
    { id: 1, name: 'Alice' },
    { id: 2, name: 'Bob' }
];

sortBy(bookings, 'name', 'asc');
// Returns: [{ id: 1, name: 'Alice' }, { id: 2, name: 'Bob' }, { id: 3, name: 'Charlie' }]
```

### Performance

#### `debounce(func, wait)`
Creates a debounced function.

```javascript
const searchBookings = debounce((query) => {
    // Search logic here
}, 300);

searchInput.addEventListener('input', (e) => {
    searchBookings(e.target.value);
});
```

### Local Storage

#### `getLocalStorage(key, defaultValue)`
Safely gets item from localStorage.

```javascript
const filters = getLocalStorage('bookingFilters', { status: 'all' });
```

#### `setLocalStorage(key, value)`
Safely sets item in localStorage.

```javascript
setLocalStorage('bookingFilters', { status: 'Pending' });
```

#### `removeLocalStorage(key)`
Removes item from localStorage.

```javascript
removeLocalStorage('bookingFilters');
```

### URL Utilities

#### `getUrlParam(param)`
Gets URL parameter value.

```javascript
// URL: ?id=123&status=pending
getUrlParam('id');
// Returns: "123"
```

#### `setUrlParam(param, value)`
Sets URL parameter without reload.

```javascript
setUrlParam('status', 'approved');
// URL becomes: ?status=approved
```

### UI Helpers

#### `statusBadge(status)`
Generates status badge HTML.

```javascript
statusBadge('Approved');
// Returns: '<span class="status-badge status-approved">Approved</span>'
```

#### `toggleLoading(element, show)`
Shows or hides loading state.

```javascript
toggleLoading(loadingElement, true);  // Show
toggleLoading(loadingElement, false); // Hide
```

#### `createLoadingSpinner(message)`
Creates a loading spinner element.

```javascript
const spinner = createLoadingSpinner('Loading bookings...');
container.appendChild(spinner);
```

#### `escapeRegex(str)`
Escapes special regex characters.

```javascript
escapeRegex('test.com');
// Returns: "test\\.com"
```

## Testing

Open `test-shared-enhancements.html` in a browser to test all shared enhancements:

1. Enhanced typography with different font sizes
2. All utility functions with sample inputs and outputs
3. Toast notifications (success, error, warning, info)
4. Modal overlay with animations
5. Status badges
6. Loading spinner
7. Empty state

## Browser Support

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (with -webkit- prefixes for backdrop-filter)
- Mobile browsers: Full support with responsive adjustments

## CSS Variables Used

The shared enhancements use the following CSS variables defined in the base styles:

```css
--bg-primary:    #0b0f1a
--bg-secondary:  #111827
--bg-glass:      rgba(255, 255, 255, 0.04)
--border-glass:  rgba(255, 255, 255, 0.08)
--text-primary:  #f1f5f9
--text-secondary:#94a3b8
--text-muted:    #64748b
--accent:        #6366f1
--accent-glow:   rgba(99, 102, 241, 0.35)
--green:         #22c55e
--green-bg:      rgba(34, 197, 94, 0.12)
--amber:         #f59e0b
--amber-bg:      rgba(245, 158, 11, 0.12)
--red:           #ef4444
--red-bg:        rgba(239, 68, 68, 0.12)
--blue:          #3b82f6
--blue-bg:       rgba(59, 130, 246, 0.12)
--radius:        12px
--radius-sm:     8px
--transition:    0.25s cubic-bezier(.4,0,.2,1)
```

## Best Practices

1. **Always escape user input** using `escapeHtml()` before displaying
2. **Use toast notifications** for user feedback instead of alerts
3. **Apply enhanced-text class** to modal content for better readability
4. **Use debounce** for search inputs and filter changes
5. **Validate data** using provided validation functions
6. **Use status badges** for consistent status display
7. **Handle loading states** with spinner and empty state components

## Migration Guide

If you have existing pages, follow these steps to integrate shared enhancements:

1. Add `shared-enhancements.css` and `shared-utils.js` to your HTML
2. Replace inline utility functions with shared utilities
3. Add `enhanced-text` class to modal content
4. Replace custom toast implementations with `showToast()`
5. Use status badge classes for status display
6. Test responsive behavior on mobile devices

## Support

For issues or questions about shared enhancements, contact the development team or refer to the design document in `.kiro/specs/admin-panel-ui-improvements/design.md`.
