# Print Header Component

## Overview

The Print Header component provides a consistent navigation interface for print views in the Autoride Admin Panel. It includes a back button for easy navigation, a customizable title, and a print button.

**Requirements Implemented:**
- 6.1: Print view displays back button in top-left corner
- 6.2: Back button navigates to previous page
- 6.3: Back button visible on screen but hidden when printing
- 6.4: Back button includes icon and label for clarity

## Files

- `print-header.html` - HTML structure for the print header
- `print-header.css` - Styling for the print header component
- `print-header.js` - Navigation functions for the print header
- `print-receipt.html` - Example implementation of a print view page

## Features

### 1. Back Button
- **Icon**: Left arrow (?)
- **Text**: "Back"
- **Behavior**: Navigates to the previous page in the application
- **Fallback**: If no referrer exists, navigates to booking management page
- **Responsive**: Text hidden on mobile devices, icon-only display

### 2. Print Title
- **Customizable**: Can be set dynamically via JavaScript
- **Centered**: Positioned in the center of the header
- **Responsive**: Font size adjusts for mobile devices

### 3. Print Button
- **Icon**: Printer emoji (??)
- **Text**: "Print"
- **Behavior**: Triggers the browser's print dialog
- **Styling**: Accent color with hover effects
- **Responsive**: Text hidden on mobile devices, icon-only display

### 4. Print Media Query
- **Automatic hiding**: The entire header is hidden when printing to paper or PDF
- **Class**: Uses `.no-print` class for easy identification

## Usage

### Basic Implementation

1. **Include the CSS file** in your HTML `<head>`:
```html
<link rel="stylesheet" href="print-header.css">
```

2. **Add the HTML structure** at the top of your page body:
```html
<div class="print-header no-print">
    <button class="btn-back" id="btnBackToPrevious" onclick="goBack()">
        <span class="back-icon">?</span>
        <span class="back-text">Back</span>
    </button>
    <h1 class="print-title" id="printTitle">Document Title</h1>
    <button class="btn-print" onclick="window.print()">
        <span class="print-icon">??</span>
        <span class="print-text">Print</span>
    </button>
</div>
```

3. **Include the JavaScript file** before the closing `</body>` tag:
```html
<script src="print-header.js"></script>
```

### Setting a Custom Title

#### Method 1: Direct HTML
```html
<h1 class="print-title" id="printTitle">Booking Receipt</h1>
```

#### Method 2: JavaScript (Dynamic)
```javascript
setPrintTitle('Booking Receipt #12345');
```

#### Method 3: SessionStorage (When navigating from another page)
```javascript
// From the source page (e.g., booking-management.html)
navigateToPrintView('/admin_app/print-receipt.html?id=12345', 'Booking Receipt #12345');
```

## Navigation Methods

### Method 1: Standard History Navigation (Default)

The `goBack()` function uses browser history:

```javascript
function goBack() {
    if (document.referrer && document.referrer.includes(window.location.hostname)) {
        window.history.back();
    } else {
        window.location.href = '/admin_app/booking-management.html';
    }
}
```

**Pros:**
- Simple and straightforward
- Works with browser back button
- No storage required

**Cons:**
- May not work if user opens print view directly
- Fallback URL is hardcoded

### Method 2: SessionStorage Navigation (Alternative)

Use `navigateToPrintView()` and `goBackFromPrint()`:

```javascript
// From source page
navigateToPrintView('/admin_app/print-receipt.html?id=123', 'Receipt #123');

// In print view, update the back button
<button class="btn-back" onclick="goBackFromPrint()">
```

**Pros:**
- More reliable navigation
- Stores exact previous page URL
- Can pass title along with navigation

**Cons:**
- Requires updating source pages
- Uses sessionStorage

## Example: Booking Receipt Print View

See `print-receipt.html` for a complete example implementation.

### Key Features:
1. Print header with back button, title, and print button
2. Responsive layout that adapts to mobile devices
3. Print-friendly styling (removes shadows, adjusts margins)
4. Dynamic data loading from URL parameters
5. Clean, professional receipt layout

## Styling Customization

### CSS Variables

The print header uses CSS variables for easy theming:

```css
:root {
    --bg-secondary: #f8fafc;
    --border-glass: #e2e8f0;
    --bg-glass: rgba(255, 255, 255, 0.8);
    --text-primary: #1e293b;
    --accent: #6366f1;
}
```

### Dark Theme Support

The component includes dark theme support:

```css
[data-theme="dark"] .print-header {
    background: #1e293b;
    border-bottom-color: rgba(255, 255, 255, 0.1);
}
```

### Mobile Responsive

Breakpoint at 768px:
- Reduced padding
- Smaller font sizes
- Text labels hidden (icon-only buttons)
- Larger icons for better touch targets

## Integration with Existing Pages

### Reports Page

To add print functionality to the reports page:

1. Add the print header CSS to `reports.html`:
```html
<link rel="stylesheet" href="print-header.css">
```

2. Add the print header HTML at the top of the reports content

3. Update the existing print button to use the new navigation:
```javascript
function printReport() {
    navigateToPrintView('/admin_app/print-receipt.html', 'Revenue Report');
}
```

### Booking Management Page

To add print functionality for booking receipts:

1. Create a print view page (e.g., `print-booking.html`)
2. Add a "Print Receipt" button to the booking details modal:
```html
<button onclick="printBooking(bookingId)">Print Receipt</button>
```

3. Implement the navigation function:
```javascript
function printBooking(id) {
    navigateToPrintView(`/admin_app/print-receipt.html?id=${id}`, `Booking Receipt #${id}`);
}
```

## Browser Compatibility

- **Chrome/Edge**: Full support
- **Firefox**: Full support
- **Safari**: Full support
- **Mobile browsers**: Full support with responsive adjustments

## Print Media Query

The component automatically hides when printing:

```css
@media print {
    .no-print {
        display: none !important;
    }
}
```

This ensures that:
- Navigation buttons don't appear in printed documents
- Print button doesn't appear in printed documents
- Only the actual content is printed

## Accessibility

- **Keyboard navigation**: All buttons are keyboard accessible
- **Screen readers**: Buttons have descriptive text
- **Focus indicators**: Visible focus states for keyboard navigation
- **Touch targets**: Minimum 44x44px touch targets on mobile

## Testing

To test the print header component:

1. **Visual test**: Open `print-receipt.html` in a browser
2. **Back button**: Click the back button and verify navigation
3. **Print button**: Click the print button and verify print dialog opens
4. **Print preview**: Use browser print preview to verify header is hidden
5. **Mobile**: Test on mobile device or use browser dev tools
6. **Dark theme**: Toggle dark theme and verify styling

## Future Enhancements

Potential improvements for future versions:

1. **Export to PDF**: Add a "Save as PDF" button
2. **Email**: Add an "Email" button to send the document
3. **Share**: Add social sharing options
4. **Templates**: Multiple print templates (receipt, invoice, report)
5. **Customization**: User preferences for print layout
6. **Batch printing**: Print multiple documents at once

## Support

For issues or questions about the print header component, please refer to:
- Design document: `.kiro/specs/admin-panel-ui-improvements/design.md`
- Requirements: `.kiro/specs/admin-panel-ui-improvements/requirements.md`
- Task list: `.kiro/specs/admin-panel-ui-improvements/tasks.md`
