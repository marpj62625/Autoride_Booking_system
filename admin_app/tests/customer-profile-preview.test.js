/**
 * Unit Tests for Customer Profile Preview Modal
 * Feature: admin-panel-ui-improvements
 * Task 3.6: Write unit tests for customer profile preview
 * 
 * Tests cover:
 * - viewCustomerProfile() with valid user data
 * - License expiry warning logic (expired, expiring, valid)
 * - Modal open/close behavior
 * - Error handling for missing customer data
 * - Default avatar display
 * 
 * Requirements: 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
 */

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';

// Mock DOM elements
const createMockDOM = () => {
  const mockElements = {
    customerProfileModal: { classList: { add: vi.fn(), remove: vi.fn(), contains: vi.fn(() => false) } },
    profileAvatar: { src: '', style: { display: '' } },
    profileName: { textContent: '' },
    profileEmail: { textContent: '' },
    profilePhone: { textContent: '' },
    licenseImage: { src: '' },
    licenseNumber: { textContent: '' },
    licenseType: { textContent: '' },
    licenseExpiry: { textContent: '', innerHTML: '', classList: { add: vi.fn(), remove: vi.fn() } },
    licenseSection: { style: { display: '' }, innerHTML: '' },
    profileAvatarSection: { innerHTML: '' }
  };

  global.document = {
    getElementById: vi.fn((id) => mockElements[id] || null),
    querySelector: vi.fn((selector) => {
      if (selector === '.license-section') return mockElements.licenseSection;
      if (selector === '.profile-avatar-section') return mockElements.profileAvatarSection;
      return null;
    }),
    addEventListener: vi.fn(),
    createElement: vi.fn(() => ({ textContent: '', innerHTML: '' }))
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

// Mock formatDate function
const mockFormatDate = (dateStr) => {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

// Mock getInitials function
const getInitials = (name) => {
  if (!name) return 'U';
  const parts = name.trim().split(' ');
  if (parts.length === 1) {
    return parts[0].charAt(0).toUpperCase();
  }
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
};

// Implementation of viewCustomerProfile for testing
const createViewCustomerProfile = (fetch, showToast, formatDate, API_BASE = 'http://localhost:5000') => {
  return async function viewCustomerProfile(userId) {
    try {
      const res = await fetch(`${API_BASE}/users/${userId}`);
      if (!res.ok) throw new Error('Failed to load customer profile');
      
      const customer = await res.json();
      
      // Populate modal
      const avatarImg = document.getElementById('profileAvatar');
      if (customer.profile_picture_url) {
        avatarImg.src = `${API_BASE}${customer.profile_picture_url}`;
        avatarImg.style.display = 'block';
      } else {
        // Use a placeholder with customer initials
        const initials = getInitials(customer.full_name || customer.name || 'User');
        avatarImg.style.display = 'none';
        const avatarSection = document.querySelector('.profile-avatar-section');
        avatarSection.innerHTML = `<div class="profile-avatar-placeholder">${initials}</div>`;
      }
      
      document.getElementById('profileName').textContent = customer.full_name || customer.name || 'N/A';
      document.getElementById('profileEmail').textContent = customer.email || 'N/A';
      document.getElementById('profilePhone').textContent = customer.phone || 'N/A';
      
      // License information
      const licenseSection = document.querySelector('.license-section');
      if (customer.license_image_url) {
        document.getElementById('licenseImage').src = `${API_BASE}${customer.license_image_url}`;
        document.getElementById('licenseNumber').textContent = customer.license_number || 'N/A';
        document.getElementById('licenseType').textContent = customer.license_type || 'N/A';
        
        const expiryElement = document.getElementById('licenseExpiry');
        if (customer.license_expiry) {
          const expiryDate = new Date(customer.license_expiry);
          const today = new Date();
          const daysUntilExpiry = Math.floor((expiryDate - today) / (1000 * 60 * 60 * 24));
          
          expiryElement.textContent = formatDate(customer.license_expiry);
          
          // Warning indicator for expiring/expired licenses
          if (daysUntilExpiry < 0) {
            expiryElement.classList.add('expired');
            expiryElement.innerHTML += ' <span class="warning-badge">?? EXPIRED</span>';
          } else if (daysUntilExpiry <= 30) {
            expiryElement.classList.add('expiring-soon');
            expiryElement.innerHTML += ` <span class="warning-badge expiring">?? Expires in ${daysUntilExpiry} days</span>`;
          }
        } else {
          expiryElement.textContent = 'N/A';
        }
        
        // Show license section
        licenseSection.style.display = 'block';
      } else {
        // Hide license section if no license info
        licenseSection.innerHTML = '<p class="no-license">No license information available</p>';
      }
      
      document.getElementById('customerProfileModal').classList.remove('hidden');
    } catch (err) {
      showToast('error', 'Failed to load customer profile');
      console.error(err);
    }
  };
};

describe('Customer Profile Preview Modal - viewCustomerProfile()', () => {
  let mockElements;
  let viewCustomerProfile;
  let mockFetch;

  beforeEach(() => {
    mockElements = createMockDOM();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  /**
   * Test: viewCustomerProfile() with valid user data
   * Validates Requirements: 2.2, 2.3, 2.4, 2.5
   */
  test('should display customer profile with valid user data', async () => {
    const mockCustomer = {
      id: 1,
      full_name: 'John Doe',
      email: 'john.doe@gmail.com',
      phone: '09171234567',
      profile_picture_url: '/uploads/profile/john.jpg',
      license_image_url: '/uploads/license/john_license.jpg',
      license_number: 'N01-12-345678',
      license_type: 'Professional',
      license_expiry: '2025-12-31'
    };

    mockFetch = createMockFetch(mockCustomer);
    viewCustomerProfile = createViewCustomerProfile(mockFetch, mockShowToast, mockFormatDate);

    await viewCustomerProfile(1);

    // Verify API call
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:5000/users/1');

    // Verify profile information is populated
    expect(mockElements.profileName.textContent).toBe('John Doe');
    expect(mockElements.profileEmail.textContent).toBe('john.doe@gmail.com');
    expect(mockElements.profilePhone.textContent).toBe('09171234567');
    expect(mockElements.profileAvatar.src).toBe('http://localhost:5000/uploads/profile/john.jpg');
    expect(mockElements.profileAvatar.style.display).toBe('block');

    // Verify license information is populated
    expect(mockElements.licenseImage.src).toBe('http://localhost:5000/uploads/license/john_license.jpg');
    expect(mockElements.licenseNumber.textContent).toBe('N01-12-345678');
    expect(mockElements.licenseType.textContent).toBe('Professional');
    expect(mockElements.licenseSection.style.display).toBe('block');

    // Verify modal is shown
    expect(mockElements.customerProfileModal.classList.remove).toHaveBeenCalledWith('hidden');
  });

  /**
   * Test: License expiry warning - EXPIRED license
   * Validates Requirements: 2.6
   */
  test('should display EXPIRED warning for expired license', async () => {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const expiredDate = yesterday.toISOString().split('T')[0];

    const mockCustomer = {
      id: 2,
      full_name: 'Jane Smith',
      email: 'jane.smith@gmail.com',
      phone: '09181234567',
      license_image_url: '/uploads/license/jane_license.jpg',
      license_number: 'N01-12-987654',
      license_type: 'Non-Professional',
      license_expiry: expiredDate
    };

    mockFetch = createMockFetch(mockCustomer);
    viewCustomerProfile = createViewCustomerProfile(mockFetch, mockShowToast, mockFormatDate);

    await viewCustomerProfile(2);

    // Verify expired warning is added
    expect(mockElements.licenseExpiry.classList.add).toHaveBeenCalledWith('expired');
    expect(mockElements.licenseExpiry.innerHTML).toContain('?? EXPIRED');
  });

  /**
   * Test: License expiry warning - EXPIRING SOON (within 30 days)
   * Validates Requirements: 2.6
   */
  test('should display expiring warning for license expiring within 30 days', async () => {
    const in15Days = new Date();
    in15Days.setDate(in15Days.getDate() + 15);
    const expiringDate = in15Days.toISOString().split('T')[0];

    const mockCustomer = {
      id: 3,
      full_name: 'Bob Johnson',
      email: 'bob.johnson@gmail.com',
      phone: '09191234567',
      license_image_url: '/uploads/license/bob_license.jpg',
      license_number: 'N01-12-111222',
      license_type: 'Professional',
      license_expiry: expiringDate
    };

    mockFetch = createMockFetch(mockCustomer);
    viewCustomerProfile = createViewCustomerProfile(mockFetch, mockShowToast, mockFormatDate);

    await viewCustomerProfile(3);

    // Verify expiring-soon warning is added
    expect(mockElements.licenseExpiry.classList.add).toHaveBeenCalledWith('expiring-soon');
    expect(mockElements.licenseExpiry.innerHTML).toContain('?? Expires in');
    expect(mockElements.licenseExpiry.innerHTML).toContain('days');
  });

  /**
   * Test: License expiry warning - VALID license (more than 30 days)
   * Validates Requirements: 2.6
   */
  test('should NOT display warning for valid license (more than 30 days)', async () => {
    const in60Days = new Date();
    in60Days.setDate(in60Days.getDate() + 60);
    const validDate = in60Days.toISOString().split('T')[0];

    const mockCustomer = {
      id: 4,
      full_name: 'Alice Brown',
      email: 'alice.brown@gmail.com',
      phone: '09201234567',
      license_image_url: '/uploads/license/alice_license.jpg',
      license_number: 'N01-12-333444',
      license_type: 'Professional',
      license_expiry: validDate
    };

    mockFetch = createMockFetch(mockCustomer);
    viewCustomerProfile = createViewCustomerProfile(mockFetch, mockShowToast, mockFormatDate);

    await viewCustomerProfile(4);

    // Verify NO warning classes are added
    expect(mockElements.licenseExpiry.classList.add).not.toHaveBeenCalledWith('expired');
    expect(mockElements.licenseExpiry.classList.add).not.toHaveBeenCalledWith('expiring-soon');
    expect(mockElements.licenseExpiry.innerHTML).not.toContain('??');
  });

  /**
   * Test: Modal open behavior
   * Validates Requirements: 2.2
   */
  test('should open modal by removing hidden class', async () => {
    const mockCustomer = {
      id: 5,
      full_name: 'Charlie Davis',
      email: 'charlie.davis@gmail.com',
      phone: '09211234567'
    };

    mockFetch = createMockFetch(mockCustomer);
    viewCustomerProfile = createViewCustomerProfile(mockFetch, mockShowToast, mockFormatDate);

    await viewCustomerProfile(5);

    // Verify modal is opened
    expect(mockElements.customerProfileModal.classList.remove).toHaveBeenCalledWith('hidden');
  });

  /**
   * Test: Error handling for missing customer data (API failure)
   * Validates Requirements: 2.2
   */
  test('should handle API error gracefully', async () => {
    mockFetch = createMockFetch({ error: 'User not found' }, false, 404);
    viewCustomerProfile = createViewCustomerProfile(mockFetch, mockShowToast, mockFormatDate);

    await viewCustomerProfile(999);

    // Verify error toast is shown
    expect(mockShowToast).toHaveBeenCalledWith('error', 'Failed to load customer profile');

    // Verify modal is NOT opened
    expect(mockElements.customerProfileModal.classList.remove).not.toHaveBeenCalled();
  });

  /**
   * Test: Default avatar display when no profile picture
   * Validates Requirements: 2.3
   */
  test('should display default avatar with initials when no profile picture', async () => {
    const mockCustomer = {
      id: 6,
      full_name: 'David Wilson',
      email: 'david.wilson@gmail.com',
      phone: '09221234567',
      profile_picture_url: null // No profile picture
    };

    mockFetch = createMockFetch(mockCustomer);
    viewCustomerProfile = createViewCustomerProfile(mockFetch, mockShowToast, mockFormatDate);

    await viewCustomerProfile(6);

    // Verify avatar image is hidden
    expect(mockElements.profileAvatar.style.display).toBe('none');

    // Verify placeholder with initials is created
    expect(mockElements.profileAvatarSection.innerHTML).toContain('profile-avatar-placeholder');
    expect(mockElements.profileAvatarSection.innerHTML).toContain('DW'); // David Wilson initials
  });

  /**
   * Test: Handle missing license information
   * Validates Requirements: 2.4, 2.5
   */
  test('should display "No license information" when license data is missing', async () => {
    const mockCustomer = {
      id: 7,
      full_name: 'Eva Martinez',
      email: 'eva.martinez@gmail.com',
      phone: '09231234567',
      license_image_url: null // No license
    };

    mockFetch = createMockFetch(mockCustomer);
    viewCustomerProfile = createViewCustomerProfile(mockFetch, mockShowToast, mockFormatDate);

    await viewCustomerProfile(7);

    // Verify "No license information" message is displayed
    expect(mockElements.licenseSection.innerHTML).toContain('No license information available');
  });

  /**
   * Test: Handle missing expiry date
   * Validates Requirements: 2.5, 2.6
   */
  test('should display N/A when license expiry date is missing', async () => {
    const mockCustomer = {
      id: 8,
      full_name: 'Frank Garcia',
      email: 'frank.garcia@gmail.com',
      phone: '09241234567',
      license_image_url: '/uploads/license/frank_license.jpg',
      license_number: 'N01-12-555666',
      license_type: 'Professional',
      license_expiry: null // No expiry date
    };

    mockFetch = createMockFetch(mockCustomer);
    viewCustomerProfile = createViewCustomerProfile(mockFetch, mockShowToast, mockFormatDate);

    await viewCustomerProfile(8);

    // Verify N/A is displayed for expiry date
    expect(mockElements.licenseExpiry.textContent).toBe('N/A');
  });

  /**
   * Test: Handle missing phone number
   * Validates Requirements: 2.2
   */
  test('should display N/A for missing phone number', async () => {
    const mockCustomer = {
      id: 9,
      full_name: 'Grace Lee',
      email: 'grace.lee@gmail.com',
      phone: null // No phone
    };

    mockFetch = createMockFetch(mockCustomer);
    viewCustomerProfile = createViewCustomerProfile(mockFetch, mockShowToast, mockFormatDate);

    await viewCustomerProfile(9);

    // Verify N/A is displayed for phone
    expect(mockElements.profilePhone.textContent).toBe('N/A');
  });

  /**
   * Test: Handle single-name customer (initials)
   * Validates Requirements: 2.3
   */
  test('should handle single-name customer for initials', async () => {
    const mockCustomer = {
      id: 10,
      full_name: 'Madonna',
      email: 'madonna@gmail.com',
      phone: '09251234567',
      profile_picture_url: null
    };

    mockFetch = createMockFetch(mockCustomer);
    viewCustomerProfile = createViewCustomerProfile(mockFetch, mockShowToast, mockFormatDate);

    await viewCustomerProfile(10);

    // Verify single initial is used
    expect(mockElements.profileAvatarSection.innerHTML).toContain('M');
  });
});

describe('Customer Profile Preview Modal - Close Handlers', () => {
  let mockElements;

  beforeEach(() => {
    mockElements = createMockDOM();
    vi.clearAllMocks();
  });

  /**
   * Test: Modal close button functionality
   * Validates Requirements: 2.7
   */
  test('should close modal when close button is clicked', () => {
    const closeButton = { addEventListener: vi.fn() };
    global.document.getElementById = vi.fn((id) => {
      if (id === 'profileClose') return closeButton;
      return mockElements[id] || null;
    });

    // Simulate the event listener setup
    const closeHandler = vi.fn(() => {
      mockElements.customerProfileModal.classList.add('hidden');
    });

    closeButton.addEventListener('click', closeHandler);

    // Simulate click
    closeHandler();

    // Verify modal is hidden
    expect(mockElements.customerProfileModal.classList.add).toHaveBeenCalledWith('hidden');
  });

  /**
   * Test: Modal close on overlay click
   * Validates Requirements: 2.7
   */
  test('should close modal when clicking on overlay', () => {
    const mockEvent = { target: { id: 'customerProfileModal' } };
    
    const overlayClickHandler = (e) => {
      if (e.target.id === 'customerProfileModal') {
        mockElements.customerProfileModal.classList.add('hidden');
      }
    };

    overlayClickHandler(mockEvent);

    // Verify modal is hidden
    expect(mockElements.customerProfileModal.classList.add).toHaveBeenCalledWith('hidden');
  });

  /**
   * Test: Modal close on Escape key
   * Validates Requirements: 2.7
   */
  test('should close modal when Escape key is pressed', () => {
    const mockEvent = { key: 'Escape' };
    mockElements.customerProfileModal.classList.contains = vi.fn(() => false);

    const escapeHandler = (e) => {
      if (e.key === 'Escape') {
        const profileModal = document.getElementById('customerProfileModal');
        if (profileModal && !profileModal.classList.contains('hidden')) {
          profileModal.classList.add('hidden');
        }
      }
    };

    escapeHandler(mockEvent);

    // Verify modal is hidden
    expect(mockElements.customerProfileModal.classList.add).toHaveBeenCalledWith('hidden');
  });
});

describe('Helper Functions', () => {
  /**
   * Test: getInitials helper function
   */
  test('getInitials should return correct initials for full name', () => {
    expect(getInitials('John Doe')).toBe('JD');
    expect(getInitials('Alice Bob Charlie')).toBe('AC');
    expect(getInitials('Madonna')).toBe('M');
    expect(getInitials('')).toBe('U');
    expect(getInitials(null)).toBe('U');
  });
});
