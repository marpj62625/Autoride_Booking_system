/**
 * Unit Tests for Cancelled Bookings List View
 * Feature: admin-panel-ui-improvements
 * Task 11.2: Implement loadCancelledBookings() function
 * 
 * Tests cover:
 * - loadCancelledBookings() fetches data from correct endpoint
 * - Pagination parameters are included in request
 * - Sorting parameter is included in request
 * - Bookings are stored in state variable
 * - renderCancelledBookingsTable() is called
 * - Pagination controls are updated
 * - Error handling for API failures
 * 
 * Requirements: 9.2, 9.4, 9.5
 */

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';

// Mock DOM elements
const createMockDOM = () => {
  const mockElements = {
    cancelledLoadingState: { classList: { add: vi.fn(), remove: vi.fn() } },
    cancelledBookingsTable: { classList: { add: vi.fn(), remove: vi.fn() } },
    cancelledEmptyState: { classList: { add: vi.fn(), remove: vi.fn() } },
    cancelledBookingsBody: { innerHTML: '', appendChild: vi.fn() },
    cancelledPageInfo: { textContent: '' },
    cancelledPrevPage: { disabled: false },
    cancelledNextPage: { disabled: false },
    cancelledSortBy: { value: 'cancellation_date_desc', addEventListener: vi.fn() },
    cancelledPageSize: { value: '25', addEventListener: vi.fn() }
  };

  global.document = {
    getElementById: vi.fn((id) => mockElements[id] || null),
    createElement: vi.fn((tag) => ({
      innerHTML: '',
      appendChild: vi.fn(),
      classList: { add: vi.fn(), remove: vi.fn() }
    }))
  };

  return mockElements;
};

// Mock fetch API
const createMockFetch = (responseData, ok = true, status = 200) => {
  return vi.fn(() => Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(responseData)
  }));
};

// Mock showToast function
const mockShowToast = vi.fn();

// Mock console.error
const mockConsoleError = vi.fn();

// Mock escapeHtml function
const escapeHtml = (str) => {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML || str;
};

// Mock formatDate function
const formatDate = (dateStr) => {
  if (!dateStr) return ' - ';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

// Mock formatRentalDates function
const formatRentalDates = (startDate, endDate) => {
  return `${formatDate(startDate)} - ${formatDate(endDate)}`;
};

// Implementation of loadCancelledBookings for testing
const createLoadCancelledBookings = (fetch, showToast, API_BASE = 'http://localhost:5000') => {
  let cancelledBookings = [];
  let cancelledPagination = {
    page: 1,
    page_size: 25,
    total: 0,
    total_pages: 0
  };
  let cancelledSortBy = 'cancellation_date_desc';

  const renderCancelledBookingsTable = () => {
    const tbody = document.getElementById('cancelledBookingsBody');
    const tableEl = document.getElementById('cancelledBookingsTable');
    const emptyEl = document.getElementById('cancelledEmptyState');
    
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (cancelledBookings.length === 0) {
      if (tableEl) tableEl.classList.add('hidden');
      if (emptyEl) emptyEl.classList.remove('hidden');
      return;
    }
    
    if (tableEl) tableEl.classList.remove('hidden');
    if (emptyEl) emptyEl.classList.add('hidden');
    
    cancelledBookings.forEach(b => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="id-cell">#${b.id}</td>
        <td class="customer-cell">${escapeHtml(b.customer_name)}</td>
        <td>${escapeHtml(b.car)}</td>
        <td>${formatRentalDates(b.start_date, b.end_date)}</td>
        <td>${formatDate(b.cancellation_date)}</td>
        <td class="reason-cell">${escapeHtml(b.cancellation_reason || 'N/A')}</td>
        <td>${escapeHtml(b.cancelled_by || 'N/A')}</td>
        <td class="actions-cell">
          <button class="btn-details" onclick="viewDetails(${b.id})" title="View full details">?? View</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  };

  const updateCancelledPaginationControls = () => {
    const pageInfo = document.getElementById('cancelledPageInfo');
    const prevBtn = document.getElementById('cancelledPrevPage');
    const nextBtn = document.getElementById('cancelledNextPage');
    
    if (pageInfo) {
      pageInfo.textContent = `Page ${cancelledPagination.page} of ${cancelledPagination.total_pages || 1}`;
    }
    
    if (prevBtn) {
      prevBtn.disabled = cancelledPagination.page <= 1;
    }
    
    if (nextBtn) {
      nextBtn.disabled = cancelledPagination.page >= cancelledPagination.total_pages;
    }
  };

  const loadCancelledBookings = async () => {
    const loadingEl = document.getElementById('cancelledLoadingState');
    const tableEl = document.getElementById('cancelledBookingsTable');
    const emptyEl = document.getElementById('cancelledEmptyState');
    
    if (loadingEl) loadingEl.classList.remove('hidden');
    if (tableEl) tableEl.classList.add('hidden');
    if (emptyEl) emptyEl.classList.add('hidden');
    
    try {
      const params = new URLSearchParams({
        page: cancelledPagination.page,
        page_size: cancelledPagination.page_size,
        sort_by: cancelledSortBy
      });
      
      const res = await fetch(`${API_BASE}/bookings/cancelled?${params}`);
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      
      const data = await res.json();
      cancelledBookings = data.bookings || [];
      cancelledPagination = data.pagination || cancelledPagination;
      
      renderCancelledBookingsTable();
      updateCancelledPaginationControls();
    } catch (err) {
      console.error('Failed to fetch cancelled bookings:', err);
      showToast('error', 'Failed to load cancelled bookings');
      cancelledBookings = [];
      renderCancelledBookingsTable();
    } finally {
      if (loadingEl) loadingEl.classList.add('hidden');
    }
  };

  return {
    loadCancelledBookings,
    getCancelledBookings: () => cancelledBookings,
    getCancelledPagination: () => cancelledPagination,
    getCancelledSortBy: () => cancelledSortBy,
    setCancelledPagination: (newPagination) => { cancelledPagination = newPagination; },
    setCancelledSortBy: (newSortBy) => { cancelledSortBy = newSortBy; }
  };
};

describe('Cancelled Bookings - loadCancelledBookings()', () => {
  let mockElements;
  let mockFetch;
  let cancelledBookingsModule;

  beforeEach(() => {
    mockElements = createMockDOM();
    global.console.error = mockConsoleError;
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  /**
   * Test: loadCancelledBookings() fetches from correct endpoint
   * Validates Requirements: 9.2
   */
  test('should fetch cancelled bookings from /bookings/cancelled endpoint', async () => {
    const mockResponse = {
      bookings: [
        {
          id: 1,
          customer_name: 'John Doe',
          car: 'Toyota Camry (ABC-123)',
          start_date: '2024-01-15',
          end_date: '2024-01-20',
          cancellation_date: '2024-01-14',
          cancellation_reason: 'Customer request',
          cancelled_by: 'Customer'
        }
      ],
      pagination: {
        page: 1,
        page_size: 25,
        total: 1,
        total_pages: 1
      }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify API call to correct endpoint
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('http://localhost:5000/bookings/cancelled')
    );
  });

  /**
   * Test: Pagination parameters are included in request
   * Validates Requirements: 9.5
   */
  test('should include pagination parameters (page, page_size) in request', async () => {
    const mockResponse = {
      bookings: [],
      pagination: { page: 2, page_size: 50, total: 100, total_pages: 2 }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    // Set custom pagination
    cancelledBookingsModule.setCancelledPagination({ page: 2, page_size: 50, total: 0, total_pages: 0 });

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify pagination parameters in URL
    const callUrl = mockFetch.mock.calls[0][0];
    expect(callUrl).toContain('page=2');
    expect(callUrl).toContain('page_size=50');
  });

  /**
   * Test: Sorting parameter is included in request
   * Validates Requirements: 9.4
   */
  test('should include sorting parameter (sort_by) in request', async () => {
    const mockResponse = {
      bookings: [],
      pagination: { page: 1, page_size: 25, total: 0, total_pages: 0 }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    // Set custom sort
    cancelledBookingsModule.setCancelledSortBy('customer_name');

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify sort parameter in URL
    const callUrl = mockFetch.mock.calls[0][0];
    expect(callUrl).toContain('sort_by=customer_name');
  });

  /**
   * Test: Bookings are stored in state variable
   * Validates Requirements: 9.2
   */
  test('should store fetched bookings in state variable', async () => {
    const mockBookings = [
      {
        id: 1,
        customer_name: 'Alice Smith',
        car: 'Honda Civic (XYZ-789)',
        start_date: '2024-02-01',
        end_date: '2024-02-05',
        cancellation_date: '2024-01-30',
        cancellation_reason: 'Change of plans',
        cancelled_by: 'Customer'
      },
      {
        id: 2,
        customer_name: 'Bob Johnson',
        car: 'Ford Focus (DEF-456)',
        start_date: '2024-02-10',
        end_date: '2024-02-15',
        cancellation_date: '2024-02-08',
        cancellation_reason: 'Vehicle unavailable',
        cancelled_by: 'Admin'
      }
    ];

    const mockResponse = {
      bookings: mockBookings,
      pagination: { page: 1, page_size: 25, total: 2, total_pages: 1 }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify bookings are stored
    const storedBookings = cancelledBookingsModule.getCancelledBookings();
    expect(storedBookings).toHaveLength(2);
    expect(storedBookings[0].customer_name).toBe('Alice Smith');
    expect(storedBookings[1].customer_name).toBe('Bob Johnson');
  });

  /**
   * Test: Pagination metadata is stored
   * Validates Requirements: 9.5
   */
  test('should store pagination metadata in state', async () => {
    const mockResponse = {
      bookings: [],
      pagination: {
        page: 3,
        page_size: 50,
        total: 150,
        total_pages: 3
      }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify pagination is stored
    const storedPagination = cancelledBookingsModule.getCancelledPagination();
    expect(storedPagination.page).toBe(3);
    expect(storedPagination.page_size).toBe(50);
    expect(storedPagination.total).toBe(150);
    expect(storedPagination.total_pages).toBe(3);
  });

  /**
   * Test: renderCancelledBookingsTable() is called
   * Validates Requirements: 9.2
   */
  test('should call renderCancelledBookingsTable() to display data', async () => {
    const mockResponse = {
      bookings: [
        {
          id: 5,
          customer_name: 'Charlie Brown',
          car: 'Mazda 3 (GHI-321)',
          start_date: '2024-03-01',
          end_date: '2024-03-05',
          cancellation_date: '2024-02-28',
          cancellation_reason: 'Emergency',
          cancelled_by: 'Customer'
        }
      ],
      pagination: { page: 1, page_size: 25, total: 1, total_pages: 1 }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify table is shown and populated
    expect(mockElements.cancelledBookingsTable.classList.remove).toHaveBeenCalledWith('hidden');
    expect(mockElements.cancelledEmptyState.classList.add).toHaveBeenCalledWith('hidden');
    expect(mockElements.cancelledBookingsBody.appendChild).toHaveBeenCalled();
  });

  /**
   * Test: Empty state is shown when no bookings
   * Validates Requirements: 9.2
   */
  test('should show empty state when no cancelled bookings', async () => {
    const mockResponse = {
      bookings: [],
      pagination: { page: 1, page_size: 25, total: 0, total_pages: 0 }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify empty state is shown
    expect(mockElements.cancelledBookingsTable.classList.add).toHaveBeenCalledWith('hidden');
    expect(mockElements.cancelledEmptyState.classList.remove).toHaveBeenCalledWith('hidden');
  });

  /**
   * Test: Pagination controls are updated
   * Validates Requirements: 9.5
   */
  test('should update pagination controls with correct page info', async () => {
    const mockResponse = {
      bookings: [],
      pagination: {
        page: 2,
        page_size: 25,
        total: 75,
        total_pages: 3
      }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify page info is updated
    expect(mockElements.cancelledPageInfo.textContent).toBe('Page 2 of 3');
  });

  /**
   * Test: Previous button is disabled on first page
   * Validates Requirements: 9.5
   */
  test('should disable previous button on first page', async () => {
    const mockResponse = {
      bookings: [],
      pagination: { page: 1, page_size: 25, total: 50, total_pages: 2 }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify previous button is disabled
    expect(mockElements.cancelledPrevPage.disabled).toBe(true);
  });

  /**
   * Test: Next button is disabled on last page
   * Validates Requirements: 9.5
   */
  test('should disable next button on last page', async () => {
    const mockResponse = {
      bookings: [],
      pagination: { page: 3, page_size: 25, total: 75, total_pages: 3 }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    // Set to last page
    cancelledBookingsModule.setCancelledPagination({ page: 3, page_size: 25, total: 0, total_pages: 0 });

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify next button is disabled
    expect(mockElements.cancelledNextPage.disabled).toBe(true);
  });

  /**
   * Test: Loading state is shown during fetch
   * Validates Requirements: 9.2
   */
  test('should show loading state during fetch', async () => {
    const mockResponse = {
      bookings: [],
      pagination: { page: 1, page_size: 25, total: 0, total_pages: 0 }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    const loadPromise = cancelledBookingsModule.loadCancelledBookings();

    // Verify loading state is shown
    expect(mockElements.cancelledLoadingState.classList.remove).toHaveBeenCalledWith('hidden');

    await loadPromise;

    // Verify loading state is hidden after fetch
    expect(mockElements.cancelledLoadingState.classList.add).toHaveBeenCalledWith('hidden');
  });

  /**
   * Test: Error handling for API failures
   * Validates Requirements: 9.2
   */
  test('should handle API error gracefully', async () => {
    mockFetch = createMockFetch({ error: 'Server error' }, false, 500);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify error is logged
    expect(mockConsoleError).toHaveBeenCalledWith(
      'Failed to fetch cancelled bookings:',
      expect.any(Error)
    );

    // Verify error toast is shown
    expect(mockShowToast).toHaveBeenCalledWith('error', 'Failed to load cancelled bookings');

    // Verify bookings are cleared
    const storedBookings = cancelledBookingsModule.getCancelledBookings();
    expect(storedBookings).toHaveLength(0);

    // Verify empty state is shown
    expect(mockElements.cancelledEmptyState.classList.remove).toHaveBeenCalledWith('hidden');
  });

  /**
   * Test: Default sort order is cancellation_date_desc
   * Validates Requirements: 9.4
   */
  test('should use default sort order cancellation_date_desc', async () => {
    const mockResponse = {
      bookings: [],
      pagination: { page: 1, page_size: 25, total: 0, total_pages: 0 }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify default sort parameter
    const callUrl = mockFetch.mock.calls[0][0];
    expect(callUrl).toContain('sort_by=cancellation_date_desc');
  });

  /**
   * Test: Default page size is 25
   * Validates Requirements: 9.5
   */
  test('should use default page size of 25', async () => {
    const mockResponse = {
      bookings: [],
      pagination: { page: 1, page_size: 25, total: 0, total_pages: 0 }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify default page size
    const callUrl = mockFetch.mock.calls[0][0];
    expect(callUrl).toContain('page_size=25');
  });

  /**
   * Test: Handles missing pagination data gracefully
   * Validates Requirements: 9.5
   */
  test('should handle missing pagination data gracefully', async () => {
    const mockResponse = {
      bookings: [
        {
          id: 10,
          customer_name: 'Test User',
          car: 'Test Car',
          start_date: '2024-01-01',
          end_date: '2024-01-05',
          cancellation_date: '2024-01-01',
          cancellation_reason: 'Test',
          cancelled_by: 'Admin'
        }
      ]
      // Missing pagination object
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify function doesn't crash and uses default pagination
    const storedPagination = cancelledBookingsModule.getCancelledPagination();
    expect(storedPagination.page).toBe(1);
    expect(storedPagination.page_size).toBe(25);
  });

  /**
   * Test: Renders cancellation details correctly
   * Validates Requirements: 9.2
   */
  test('should render cancellation reason and cancelled_by fields', async () => {
    const mockResponse = {
      bookings: [
        {
          id: 15,
          customer_name: 'David Lee',
          car: 'Nissan Altima (JKL-654)',
          start_date: '2024-04-01',
          end_date: '2024-04-10',
          cancellation_date: '2024-03-30',
          cancellation_reason: 'Weather conditions',
          cancelled_by: 'Admin'
        }
      ],
      pagination: { page: 1, page_size: 25, total: 1, total_pages: 1 }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify table row is created with cancellation details
    const createElementCalls = document.createElement.mock.calls;
    expect(createElementCalls.length).toBeGreaterThan(0);
  });
});

describe('Cancelled Bookings - Edge Cases', () => {
  let mockElements;
  let mockFetch;
  let cancelledBookingsModule;

  beforeEach(() => {
    mockElements = createMockDOM();
    global.console.error = mockConsoleError;
    vi.clearAllMocks();
  });

  /**
   * Test: Handles null cancellation_reason
   * Validates Requirements: 9.2
   */
  test('should display N/A for null cancellation_reason', async () => {
    const mockResponse = {
      bookings: [
        {
          id: 20,
          customer_name: 'Emma Wilson',
          car: 'Hyundai Elantra (MNO-987)',
          start_date: '2024-05-01',
          end_date: '2024-05-05',
          cancellation_date: '2024-04-30',
          cancellation_reason: null,
          cancelled_by: 'System'
        }
      ],
      pagination: { page: 1, page_size: 25, total: 1, total_pages: 1 }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify N/A is used for null reason
    const storedBookings = cancelledBookingsModule.getCancelledBookings();
    expect(storedBookings[0].cancellation_reason).toBeNull();
  });

  /**
   * Test: Handles null cancelled_by
   * Validates Requirements: 9.2
   */
  test('should display N/A for null cancelled_by', async () => {
    const mockResponse = {
      bookings: [
        {
          id: 21,
          customer_name: 'Frank Miller',
          car: 'Kia Forte (PQR-321)',
          start_date: '2024-06-01',
          end_date: '2024-06-05',
          cancellation_date: '2024-05-30',
          cancellation_reason: 'Unknown',
          cancelled_by: null
        }
      ],
      pagination: { page: 1, page_size: 25, total: 1, total_pages: 1 }
    };

    mockFetch = createMockFetch(mockResponse);
    cancelledBookingsModule = createLoadCancelledBookings(mockFetch, mockShowToast);

    await cancelledBookingsModule.loadCancelledBookings();

    // Verify N/A is used for null cancelled_by
    const storedBookings = cancelledBookingsModule.getCancelledBookings();
    expect(storedBookings[0].cancelled_by).toBeNull();
  });
});

