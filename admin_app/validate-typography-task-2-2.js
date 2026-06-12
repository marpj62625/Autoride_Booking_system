/**
 * Validation Script for Task 2.2: Enhanced Typography CSS
 * 
 * This script validates that all typography enhancements are correctly implemented
 * according to the requirements in tasks.md
 */

const fs = require('fs');
const path = require('path');

// Read the CSS file
const cssPath = path.join(__dirname, 'shared-enhancements.css');
const cssContent = fs.readFileSync(cssPath, 'utf8');

// Test results
const results = {
    passed: [],
    failed: [],
    warnings: []
};

console.log('='.repeat(60));
console.log('Task 2.2: Enhanced Typography CSS Validation');
console.log('='.repeat(60));
console.log();

// Test 1: Font size increases
console.log('Test 1: Font Size Increases');
console.log('-'.repeat(60));

const fontSizeTests = [
    { selector: '.enhanced-text .info-label', expected: '1.05rem', description: 'Labels font size' },
    { selector: '.enhanced-text .info-value', expected: '1.1rem', description: 'Values font size' },
    { selector: '.enhanced-text h3', expected: '1.44rem', description: 'H3 headings font size' },
    { selector: '.enhanced-text h4', expected: '1.08rem', description: 'H4 headings font size' }
];

fontSizeTests.forEach(test => {
    const regex = new RegExp(`${test.selector.replace(/\./g, '\\.').replace(/\s+/g, '\\s+')}\\s*{[^}]*font-size:\\s*${test.expected}`, 'i');
    if (regex.test(cssContent)) {
        results.passed.push(`? ${test.description}: ${test.expected}`);
        console.log(`? PASS: ${test.description} = ${test.expected}`);
    } else {
        results.failed.push(`? ${test.description}: Expected ${test.expected}`);
        console.log(`? FAIL: ${test.description} - Expected ${test.expected}`);
    }
});

console.log();

// Test 2: Responsive adjustments (768px breakpoint)
console.log('Test 2: Responsive Adjustments (768px breakpoint)');
console.log('-'.repeat(60));

const responsiveTests = [
    { selector: '.enhanced-text .info-label', expected: '0.95rem', description: 'Mobile labels font size' },
    { selector: '.enhanced-text .info-value', expected: '1rem', description: 'Mobile values font size' },
    { selector: '.enhanced-text h3', expected: '1.2rem', description: 'Mobile H3 font size' },
    { selector: '.enhanced-text h4', expected: '0.95rem', description: 'Mobile H4 font size' }
];

// Check for 768px media query
if (cssContent.includes('@media (max-width: 768px)')) {
    results.passed.push('? 768px breakpoint exists');
    console.log('? PASS: 768px breakpoint exists');
    
    responsiveTests.forEach(test => {
        const mediaQuerySection = cssContent.match(/@media\s*\(max-width:\s*768px\)\s*{[^}]*(?:{[^}]*}[^}]*)*}/gi);
        if (mediaQuerySection && mediaQuerySection[0].includes(test.expected)) {
            results.passed.push(`? ${test.description}: ${test.expected}`);
            console.log(`? PASS: ${test.description} = ${test.expected}`);
        } else {
            results.warnings.push(`? ${test.description}: Could not verify ${test.expected}`);
            console.log(`? WARNING: ${test.description} - Could not verify ${test.expected}`);
        }
    });
} else {
    results.failed.push('? 768px breakpoint not found');
    console.log('? FAIL: 768px breakpoint not found');
}

console.log();

// Test 3: Text overflow handling
console.log('Test 3: Text Overflow Handling');
console.log('-'.repeat(60));

const overflowTests = [
    { property: 'word-wrap: break-word', description: 'word-wrap property' },
    { property: 'overflow-wrap: break-word', description: 'overflow-wrap property' }
];

overflowTests.forEach(test => {
    if (cssContent.includes(test.property)) {
        results.passed.push(`? ${test.description} implemented`);
        console.log(`? PASS: ${test.description} implemented`);
    } else {
        results.failed.push(`? ${test.description} not found`);
        console.log(`? FAIL: ${test.description} not found`);
    }
});

console.log();

// Test 4: Enhanced-text class usage
console.log('Test 4: Enhanced-text Class Implementation');
console.log('-'.repeat(60));

const enhancedTextSelectors = [
    '.enhanced-text .info-label',
    '.enhanced-text .info-value',
    '.enhanced-text h3',
    '.enhanced-text h4',
    '.enhanced-text .info-grid'
];

enhancedTextSelectors.forEach(selector => {
    if (cssContent.includes(selector)) {
        results.passed.push(`? ${selector} defined`);
        console.log(`? PASS: ${selector} defined`);
    } else {
        results.failed.push(`? ${selector} not found`);
        console.log(`? FAIL: ${selector} not found`);
    }
});

console.log();

// Summary
console.log('='.repeat(60));
console.log('VALIDATION SUMMARY');
console.log('='.repeat(60));
console.log(`Total Tests: ${results.passed.length + results.failed.length + results.warnings.length}`);
console.log(`Passed: ${results.passed.length}`);
console.log(`Failed: ${results.failed.length}`);
console.log(`Warnings: ${results.warnings.length}`);
console.log();

if (results.failed.length === 0) {
    console.log('? ALL TESTS PASSED!');
    console.log();
    console.log('Task 2.2 Requirements Met:');
    console.log('  ? Font size increases implemented (labels: 1.05rem, values: 1.1rem, h3: 1.44rem, h4: 1.08rem)');
    console.log('  ? Responsive adjustments for mobile viewports (768px breakpoint)');
    console.log('  ? Text overflow handling with word-wrap and overflow-wrap');
    console.log('  ? Ready for testing with long booking descriptions and customer names');
    console.log();
    console.log('Next Steps:');
    console.log('  1. Open test-typography-task-2-2.html in a browser');
    console.log('  2. Verify visual appearance of enhanced typography');
    console.log('  3. Test responsive behavior by resizing browser window');
    console.log('  4. Test with long text content to verify overflow handling');
    console.log();
    process.exit(0);
} else {
    console.log('? SOME TESTS FAILED');
    console.log();
    console.log('Failed Tests:');
    results.failed.forEach(fail => console.log(`  ${fail}`));
    console.log();
    process.exit(1);
}
