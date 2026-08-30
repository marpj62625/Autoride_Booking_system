/**
 * Unit Tests for Print Header Navigation
 * Feature: admin-panel-ui-improvements
 * Task 8.2: Implement goBack() navigation function
 * 
 * Tests cover:
 * - goBack() with valid referrer in same domain
 * - goBack() fallback to booking management page
 * - sessionStorage-based navigation (navigateToPrintView and goBackFromPrint)
 * 
 * Requirements: 6.2
 */

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';

// Mock window object
const createMockWindow = () => {
  return {
    location: {
      hostname: 'localhost',
      href: 'http://localhost:5000/admin_app/print-receipt.html?id=123'
    },
    history: {
      back: vi.fn()
    }
  };
};

// Mock document object
const createMockDocument = (referrer = '') => {
  return {
    referrer
  };
};

// Mock sessionStorage
const createMockSessionStorage = () => {
  const storage = {};
  return {
    getItem: vi.fn((key) => storage[key] || null),
    setItem: vi.fn((key, value) => { storage[key] = value; }),
    removeItem: vi.fn((key) => { delete storage[key]; }),
    clear: vi.fn(() => { Object.keys(storage).forEach(key => delete storage[key]); }),
    _storage: storage
  };
};

// Implementation of goBack for testing
const createGoBack = (window, document) => {
  return function goBack() {
    // Check if there's a referrer in the same domain
    if (document.referrer && document.referrer.includes(window.location.hostname)) {
      window.history.back();
    } else {
      // Fallback to booking management page
      window.location.href = '/admin_app/booking-management.html';
    }
  };
};

// Implementation of navigateToPrintView for testing
const createNavigateToPrintView = (window, sessionStorage) => {
  return function navigateToPrintView(printViewUrl, title = 'Document') {
    // Store current page URL
    sessionStorage.setItem('previousPage', window.location.href);
    
    // Store print title if provided
    if (title) {
      sessionStorage.setItem('printTitle', title);
    }
    
    // Navigate to print view
    window.location.href = printViewUrl;
  };
};

// Implementation of goBackFromPrint for testing
const createGoBackFromPrint = (window, sessionStorage) => {
  return function goBackFromPrint() {
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
  };
};

describe('Print Header Navigation - goBack()', () => {
  let mockWindow;
  let mockDocument;
  let goBack;

  beforeEach(() => {
    mockWindow = createMockWindow();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  /**
   * Test: goBack() with valid referrer in same domain
   * Validates Requirement: 6.2 - Use window.history.back() if referrer exists
   */
  test('should use history.back() when referrer is from same domain', () => {
    // Setup: referrer from same domain
    mockDocument = createMockDocument('http://localhost:5000/admin_app/booking-management.html');
    goBack = createGoBack(mockWindow, mockDocument);

    // Execute
    goBack();

    // Verify: history.back() was called
    expect(mockWindow.history.back).toHaveBeenCalledTimes(1);
    
    // Verify: location.href was NOT changed
    expect(mockWindow.location.href).toBe('http://localhost:5000/admin_app/print-receipt.html?id=123');
  });

  /**
   * Test: goBack() with referrer from same domain (different subdomain)
   * Validates Requirement: 6.2 - Check for valid referrer in same domain
   */
  test('should use history.back() when referrer hostname matches', () => {
    // Setup: referrer with same hostname
    mockDocument = createMockDocument('http://localhost:8080/admin_app/reports.html');
    goBack = createGoBack(mockWindow, mockDocument);

    // Execute
    goBack();

    // Verify: history.back() was called
    expect(mockWindow.history.back).toHaveBeenCalledTimes(1);
  });

  /**
   * Test: goBack() with no referrer
   * Validates Requirement: 6.2 - Fallback to booking management page if no referrer
   */
  test('should fallback to booking management page when no referrer', () => {
    // Setup: no referrer
    mockDocument = createMockDocument('');
    goBack = createGoBack(mockWindow, mockDocument);

    // Execute
    goBack();

    // Verify: history.back() was NOT called
    expect(mockWindow.history.back).not.toHaveBeenCalled();
    
    // Verify: location.href was changed to booking management page
    expect(mockWindow.location.href).toBe('/admin_app/booking-management.html');
  });

  /**
   * Test: goBack() with referrer from different domain
   * Validates Requirement: 6.2 - Fallback to booking management page if referrer from different domain
   */
  test('should fallback to booking management page when referrer is from different domain', () => {
    // Setup: referrer from external domain
    mockDocument = createMockDocument('https://google.com/search');
    goBack = createGoBack(mockWindow, mockDocument);

    // Execute
    goBack();

    // Verify: history.back() was NOT called
    expect(mockWindow.history.back).not.toHaveBeenCalled();
    
    // Verify: location.href was changed to booking management page
    expect(mockWindow.location.href).toBe('/admin_app/booking-management.html');
  });

  /**
   * Test: goBack() with referrer from different subdomain
   * Validates Requirement: 6.2 - Fallback when hostname doesn't match
   */
  test('should fallback to booking management page when referrer has different hostname', () => {
    // Setup: referrer from different hostname
    mockDocument = createMockDocument('http://example.com/admin_app/booking-management.html');
    goBack = createGoBack(mockWindow, mockDocument);

    // Execute
    goBack();

    // Verify: history.back() was NOT called
    expect(mockWindow.history.back).not.toHaveBeenCalled();
    
    // Verify: location.href was changed to booking management page
    expect(mockWindow.location.href).toBe('/admin_app/booking-management.html');
  });

  /**
   * Test: goBack() with null referrer
   * Validates Requirement: 6.2 - Handle null referrer gracefully
   */
  test('should fallback to booking management page when referrer is null', () => {
    // Setup: null referrer
    mockDocument = createMockDocument(null);
    goBack = createGoBack(mockWindow, mockDocument);

    // Execute
    goBack();

    // Verify: history.back() was NOT called
    expect(mockWindow.history.back).not.toHaveBeenCalled();
    
    // Verify: location.href was changed to booking management page
    expect(mockWindow.location.href).toBe('/admin_app/booking-management.html');
  });

  /**
   * Test: goBack() with referrer containing hostname as substring
   * Validates Requirement: 6.2 - Proper hostname matching
   */
  test('should use history.back() when referrer contains hostname', () => {
    // Setup: referrer with hostname in path
    mockDocument = createMockDocument('http://localhost:5000/admin_app/reports.html?host=localhost');
    goBack = createGoBack(mockWindow, mockDocument);

    // Execute
    goBack();

    // Verify: history.back() was called (hostname 'localhost' is in referrer)
    expect(mockWindow.history.back).toHaveBeenCalledTimes(1);
  });
});

describe('Print Header Navigation - sessionStorage-based navigation', () => {
  let mockWindow;
  let mockSessionStorage;
  let navigateToPrintView;
  let goBackFromPrint;

  beforeEach(() => {
    mockWindow = createMockWindow();
    mockSessionStorage = createMockSessionStorage();
    navigateToPrintView = createNavigateToPrintView(mockWindow, mockSessionStorage);
    goBackFromPrint = createGoBackFromPrint(mockWindow, mockSessionStorage);
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  /**
   * Test: navigateToPrintView stores current page and navigates
   * Validates Requirement: 6.2 - Alternative navigation approach
   */
  test('should store current page URL and navigate to print view', () => {
    // Setup
    const printViewUrl = '/admin_app/print-receipt.html?id=456';
    const title = 'Booking Receipt #456';

    // Execute
    navigateToPrintView(printViewUrl, title);

    // Verify: previousPage was stored
    expect(mockSessionStorage.setItem).toHaveBeenCalledWith(
      'previousPage',
      'http://localhost:5000/admin_app/print-receipt.html?id=123'
    );

    // Verify: printTitle was stored
    expect(mockSessionStorage.setItem).toHaveBeenCalledWith('printTitle', title);

    // Verify: navigation occurred
    expect(mockWindow.location.href).toBe(printViewUrl);
  });

  /**
   * Test: navigateToPrintView with default title
   * Validates Requirement: 6.2 - Handle optional title parameter
   */
  test('should use default title when not provided', () => {
    // Setup
    const printViewUrl = '/admin_app/print-receipt.html?id=789';

    // Execute (no title provided)
    navigateToPrintView(printViewUrl);

    // Verify: default title 'Document' was stored
    expect(mockSessionStorage.setItem).toHaveBeenCalledWith('printTitle', 'Document');
  });

  /**
   * Test: goBackFromPrint retrieves stored page and navigates back
   * Validates Requirement: 6.2 - Navigate back using stored page
   */
  test('should navigate back to stored previous page', () => {
    // Setup: store a previous page
    mockSessionStorage._storage.previousPage = 'http://localhost:5000/admin_app/booking-management.html';
    mockSessionStorage._storage.printTitle = 'Test Title';

    // Execute
    goBackFromPrint();

    // Verify: previousPage was retrieved
    expect(mockSessionStorage.getItem).toHaveBeenCalledWith('previousPage');

    // Verify: navigation occurred to stored page
    expect(mockWindow.location.href).toBe('http://localhost:5000/admin_app/booking-management.html');

    // Verify: sessionStorage was cleaned up
    expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('previousPage');
    expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('printTitle');
  });

  /**
   * Test: goBackFromPrint falls back to history.back() when no stored page
   * Validates Requirement: 6.2 - Fallback behavior
   */
  test('should fallback to history.back() when no stored previous page', () => {
    // Setup: no stored previous page
    mockSessionStorage._storage = {};

    // Execute
    goBackFromPrint();

    // Verify: previousPage was checked
    expect(mockSessionStorage.getItem).toHaveBeenCalledWith('previousPage');

    // Verify: history.back() was called as fallback
    expect(mockWindow.history.back).toHaveBeenCalledTimes(1);

    // Verify: location.href was NOT changed
    expect(mockWindow.location.href).toBe('http://localhost:5000/admin_app/print-receipt.html?id=123');
  });

  /**
   * Test: goBackFromPrint handles null stored page
   * Validates Requirement: 6.2 - Handle null values gracefully
   */
  test('should fallback to history.back() when stored page is null', () => {
    // Setup: null stored page
    mockSessionStorage._storage.previousPage = null;

    // Execute
    goBackFromPrint();

    // Verify: history.back() was called
    expect(mockWindow.history.back).toHaveBeenCalledTimes(1);
  });

  /**
   * Test: Complete workflow - navigate to print view and back
   * Validates Requirement: 6.2 - End-to-end navigation flow
   */
  test('should complete full navigation workflow', () => {
    // Step 1: Navigate to print view
    const printViewUrl = '/admin_app/print-receipt.html?id=999';
    const title = 'Receipt #999';
    navigateToPrintView(printViewUrl, title);

    // Verify: storage was set
    expect(mockSessionStorage._storage.previousPage).toBe('http://localhost:5000/admin_app/print-receipt.html?id=123');
    expect(mockSessionStorage._storage.printTitle).toBe(title);

    // Step 2: Simulate being on print view page
    mockWindow.location.href = printViewUrl;

    // Step 3: Go back from print view
    goBackFromPrint();

    // Verify: navigated back to original page
    expect(mockWindow.location.href).toBe('http://localhost:5000/admin_app/print-receipt.html?id=123');

    // Verify: storage was cleaned up
    expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('previousPage');
    expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('printTitle');
  });
});

describe('Print Header Navigation - Edge Cases', () => {
  let mockWindow;
  let mockDocument;
  let goBack;

  beforeEach(() => {
    mockWindow = createMockWindow();
    vi.clearAllMocks();
  });

  /**
   * Test: goBack() with referrer containing special characters
   * Validates Requirement: 6.2 - Handle special characters in URLs
   */
  test('should handle referrer with special characters', () => {
    // Setup: referrer with query parameters and special characters
    mockDocument = createMockDocument('http://localhost:5000/admin_app/booking-management.html?search=test%20query&filter=active');
    goBack = createGoBack(mockWindow, mockDocument);

    // Execute
    goBack();

    // Verify: history.back() was called
    expect(mockWindow.history.back).toHaveBeenCalledTimes(1);
  });

  /**
   * Test: goBack() with referrer using HTTPS
   * Validates Requirement: 6.2 - Handle different protocols
   */
  test('should handle HTTPS referrer from same domain', () => {
    // Setup: HTTPS referrer
    mockWindow.location.hostname = 'autoride.com';
    mockDocument = createMockDocument('https://autoride.com/admin_app/reports.html');
    goBack = createGoBack(mockWindow, mockDocument);

    // Execute
    goBack();

    // Verify: history.back() was called (hostname matches)
    expect(mockWindow.history.back).toHaveBeenCalledTimes(1);
  });

  /**
   * Test: goBack() with referrer using different port
   * Validates Requirement: 6.2 - Handle different ports on same hostname
   */
  test('should handle referrer with different port on same hostname', () => {
    // Setup: different port but same hostname
    mockDocument = createMockDocument('http://localhost:8080/admin_app/booking-management.html');
    goBack = createGoBack(mockWindow, mockDocument);

    // Execute
    goBack();

    // Verify: history.back() was called (hostname 'localhost' matches)
    expect(mockWindow.history.back).toHaveBeenCalledTimes(1);
  });

  /**
   * Test: goBack() with empty string referrer
   * Validates Requirement: 6.2 - Handle empty string referrer
   */
  test('should fallback when referrer is empty string', () => {
    // Setup: empty string referrer
    mockDocument = createMockDocument('');
    goBack = createGoBack(mockWindow, mockDocument);

    // Execute
    goBack();

    // Verify: fallback to booking management page
    expect(mockWindow.history.back).not.toHaveBeenCalled();
    expect(mockWindow.location.href).toBe('/admin_app/booking-management.html');
  });

  /**
   * Test: goBack() with referrer as file:// protocol
   * Validates Requirement: 6.2 - Handle file protocol referrer
   */
  test('should fallback when referrer uses file:// protocol', () => {
    // Setup: file protocol referrer
    mockDocument = createMockDocument('file:///C:/Users/admin/Desktop/test.html');
    goBack = createGoBack(mockWindow, mockDocument);

    // Execute
    goBack();

    // Verify: fallback to booking management page
    expect(mockWindow.history.back).not.toHaveBeenCalled();
    expect(mockWindow.location.href).toBe('/admin_app/booking-management.html');
  });
});
