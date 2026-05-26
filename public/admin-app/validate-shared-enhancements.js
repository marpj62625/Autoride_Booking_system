/* ============================================================
   Validation Script for Shared Enhancements
   Checks that all required functions and CSS are available
   ============================================================ */

// Color codes for console output
const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m'
};

console.log(`${colors.cyan}========================================`);
console.log(`Shared Enhancements Validation`);
console.log(`========================================${colors.reset}\n`);

let passCount = 0;
let failCount = 0;

// Helper function to test
function test(name, fn) {
    try {
        const result = fn();
        if (result) {
            console.log(`${colors.green}?${colors.reset} ${name}`);
            passCount++;
        } else {
            console.log(`${colors.red}?${colors.reset} ${name}`);
            failCount++;
        }
    } catch (error) {
        console.log(`${colors.red}?${colors.reset} ${name} - Error: ${error.message}`);
        failCount++;
    }
}

console.log(`${colors.blue}Testing Utility Functions:${colors.reset}`);

// Test HTML escaping
test('escapeHtml() exists', () => typeof escapeHtml === 'function');
test('escapeHtml() works correctly', () => {
    const result = escapeHtml('<script>alert("test")</script>');
    return result.includes('&lt;') && result.includes('&gt;');
});

// Test date formatting
test('formatDate() exists', () => typeof formatDate === 'function');
test('formatDate() works correctly', () => {
    const result = formatDate('2024-01-15');
    return result.includes('Jan') && result.includes('15') && result.includes('2024');
});

test('formatDateTime() exists', () => typeof formatDateTime === 'function');
test('formatTime() exists', () => typeof formatTime === 'function');
test('formatRentalDates() exists', () => typeof formatRentalDates === 'function');
test('daysBetween() exists', () => typeof daysBetween === 'function');
test('daysBetween() calculates correctly', () => {
    const days = daysBetween('2024-01-01', '2024-01-06');
    return days === 5;
});

// Test price formatting
test('formatPrice() exists', () => typeof formatPrice === 'function');
test('formatPrice() works correctly', () => {
    const result = formatPrice(5500);
    return result.includes('?') && result.includes('5,500.00');
});

test('formatNumber() exists', () => typeof formatNumber === 'function');
test('formatNumber() works correctly', () => {
    const result = formatNumber(1234567);
    return result.includes('1,234,567');
});

// Test toast notifications
test('showToast() exists', () => typeof showToast === 'function');
test('hideToast() exists', () => typeof hideToast === 'function');

// Test string utilities
test('truncateString() exists', () => typeof truncateString === 'function');
test('truncateString() works correctly', () => {
    const result = truncateString('This is a very long string', 15);
    return result.length <= 18 && result.includes('...');
});

test('capitalize() exists', () => typeof capitalize === 'function');
test('capitalize() works correctly', () => {
    const result = capitalize('hello world');
    return result === 'Hello world';
});

test('toTitleCase() exists', () => typeof toTitleCase === 'function');
test('toTitleCase() works correctly', () => {
    const result = toTitleCase('hello world');
    return result === 'Hello World';
});

// Test validation
test('isValidEmail() exists', () => typeof isValidEmail === 'function');
test('isValidEmail() validates correctly', () => {
    return isValidEmail('test@example.com') === true && 
           isValidEmail('invalid-email') === false;
});

test('isValidPhone() exists', () => typeof isValidPhone === 'function');
test('isValidPhone() validates correctly', () => {
    return isValidPhone('09123456789') === true && 
           isValidPhone('12345') === false;
});

// Test array utilities
test('groupBy() exists', () => typeof groupBy === 'function');
test('groupBy() works correctly', () => {
    const arr = [{ id: 1, type: 'A' }, { id: 2, type: 'B' }, { id: 3, type: 'A' }];
    const result = groupBy(arr, 'type');
    return result.A.length === 2 && result.B.length === 1;
});

test('sortBy() exists', () => typeof sortBy === 'function');
test('sortBy() works correctly', () => {
    const arr = [{ id: 3 }, { id: 1 }, { id: 2 }];
    const result = sortBy(arr, 'id', 'asc');
    return result[0].id === 1 && result[2].id === 3;
});

// Test performance utilities
test('debounce() exists', () => typeof debounce === 'function');

// Test local storage utilities
test('getLocalStorage() exists', () => typeof getLocalStorage === 'function');
test('setLocalStorage() exists', () => typeof setLocalStorage === 'function');
test('removeLocalStorage() exists', () => typeof removeLocalStorage === 'function');

// Test URL utilities
test('getUrlParam() exists', () => typeof getUrlParam === 'function');
test('setUrlParam() exists', () => typeof setUrlParam === 'function');

// Test UI helpers
test('statusBadge() exists', () => typeof statusBadge === 'function');
test('statusBadge() generates HTML', () => {
    const result = statusBadge('Approved');
    return result.includes('status-badge') && result.includes('Approved');
});

test('toggleLoading() exists', () => typeof toggleLoading === 'function');
test('createLoadingSpinner() exists', () => typeof createLoadingSpinner === 'function');
test('escapeRegex() exists', () => typeof escapeRegex === 'function');

// Summary
console.log(`\n${colors.cyan}========================================`);
console.log(`Validation Summary`);
console.log(`========================================${colors.reset}`);
console.log(`${colors.green}Passed: ${passCount}${colors.reset}`);
console.log(`${colors.red}Failed: ${failCount}${colors.reset}`);

if (failCount === 0) {
    console.log(`\n${colors.green}? All tests passed! Shared enhancements are working correctly.${colors.reset}\n`);
} else {
    console.log(`\n${colors.yellow}? Some tests failed. Please review the implementation.${colors.reset}\n`);
}

// Check CSS file existence (browser only)
if (typeof document !== 'undefined') {
    console.log(`\n${colors.blue}Checking CSS:${colors.reset}`);
    
    const cssFiles = Array.from(document.styleSheets).map(sheet => {
        try {
            return sheet.href || 'inline';
        } catch (e) {
            return 'unknown';
        }
    });
    
    const hasSharedCSS = cssFiles.some(file => file.includes('shared-enhancements.css'));
    
    if (hasSharedCSS) {
        console.log(`${colors.green}?${colors.reset} shared-enhancements.css is loaded`);
    } else {
        console.log(`${colors.yellow}?${colors.reset} shared-enhancements.css not found in stylesheets`);
    }
}
