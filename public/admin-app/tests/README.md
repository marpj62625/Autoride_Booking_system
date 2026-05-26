# Admin App Unit Tests

This directory contains unit tests for the Autoride Admin Panel web application.

## Test Framework

- **Vitest**: Fast unit test framework with Jest-compatible API
- **jsdom**: DOM environment for testing browser-based JavaScript
- **fast-check**: Property-based testing library (available for future use)

## Running Tests

```bash
# Run all tests once
npm test

# Run tests in watch mode (re-runs on file changes)
npm test:watch

# Run tests with UI
npm test:ui

# Run tests with coverage report
npm test:coverage
```

## Test Files

### `customer-profile-preview.test.js`

Tests for the customer profile preview modal functionality (Task 3.6).

**Coverage:**
- ? viewCustomerProfile() with valid user data (Requirements 2.2, 2.3, 2.4, 2.5)
- ? License expiry warning logic - EXPIRED (Requirement 2.6)
- ? License expiry warning logic - EXPIRING SOON (within 30 days) (Requirement 2.6)
- ? License expiry warning logic - VALID (more than 30 days) (Requirement 2.6)
- ? Modal open behavior (Requirement 2.2)
- ? Error handling for missing customer data (Requirement 2.2)
- ? Default avatar display with initials (Requirement 2.3)
- ? Missing license information handling (Requirements 2.4, 2.5)
- ? Missing expiry date handling (Requirements 2.5, 2.6)
- ? Missing phone number handling (Requirement 2.2)
- ? Single-name customer initials (Requirement 2.3)
- ? Modal close button functionality (Requirement 2.7)
- ? Modal close on overlay click (Requirement 2.7)
- ? Modal close on Escape key (Requirement 2.7)
- ? getInitials helper function

**Test Results:**
```
? Customer Profile Preview Modal - viewCustomerProfile() (11 tests)
? Customer Profile Preview Modal - Close Handlers (3 tests)
? Helper Functions (1 test)

Total: 15 tests passed
```

## Test Structure

Each test file follows this structure:

1. **Imports**: Vitest functions and any dependencies
2. **Mock Setup**: DOM elements, API calls, and helper functions
3. **Test Suites**: Organized by feature/component
4. **Individual Tests**: Each test validates a specific behavior

## Writing New Tests

When adding new tests:

1. Create a new `.test.js` file in the `tests/` directory
2. Import necessary Vitest functions: `describe`, `test`, `expect`, `beforeEach`, `afterEach`, `vi`
3. Set up mocks for DOM elements and external dependencies
4. Write descriptive test names that explain what is being tested
5. Include requirement references in test comments
6. Run tests to verify they pass

Example:

```javascript
import { describe, test, expect, beforeEach, vi } from 'vitest';

describe('Feature Name', () => {
  beforeEach(() => {
    // Setup code
  });

  test('should do something specific', () => {
    // Arrange
    const input = 'test';
    
    // Act
    const result = functionUnderTest(input);
    
    // Assert
    expect(result).toBe('expected');
  });
});
```

## Mocking Guidelines

### DOM Elements
Use `vi.fn()` to mock DOM methods:

```javascript
const mockElement = {
  classList: {
    add: vi.fn(),
    remove: vi.fn(),
    contains: vi.fn(() => false)
  },
  textContent: '',
  innerHTML: ''
};
```

### Fetch API
Mock fetch responses:

```javascript
const mockFetch = vi.fn(() => Promise.resolve({
  ok: true,
  status: 200,
  json: () => Promise.resolve({ data: 'value' })
}));
```

### Event Listeners
Test event handlers directly:

```javascript
const handler = vi.fn(() => {
  // Handler logic
});

handler(); // Simulate event
expect(handler).toHaveBeenCalled();
```

## Coverage

To generate a coverage report:

```bash
npm run test:coverage
```

This will create an HTML coverage report in the `coverage/` directory.

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    cd admin_app
    npm install
    npm test
```

## Troubleshooting

### Tests fail with "Cannot find module"
- Ensure all dependencies are installed: `npm install`
- Check that file paths in imports are correct

### DOM-related errors
- Verify `jsdom` is installed and configured in `vitest.config.js`
- Check that `environment: 'jsdom'` is set in the config

### Mock not working
- Ensure mocks are set up in `beforeEach()` hooks
- Clear mocks between tests with `vi.clearAllMocks()`
- Restore original implementations with `vi.restoreAllMocks()` in `afterEach()`

## Future Enhancements

Potential areas for additional testing:

1. **Booking Management Tests**
   - Approve/reject booking functionality
   - Booking details modal
   - Inspection form submission

2. **Reports Tests**
   - Chart rendering
   - Filter functionality
   - Data export

3. **Vehicle Management Tests**
   - Vehicle CRUD operations
   - Status updates
   - Image uploads

4. **Integration Tests**
   - API integration tests
   - End-to-end user flows

5. **Property-Based Tests**
   - Use fast-check for testing properties across many inputs
   - Validate data transformations
   - Test edge cases automatically
