# Design Document: Admin Panel UI/UX Improvements

## Overview

This design document outlines the technical implementation for UI/UX improvements across the Autoride Admin Panel. The improvements focus on enhancing readability, accessibility, and usability through larger fonts, customer profile previews, expandable charts with filters, live chat search, improved print views, location fields in active bookings, dedicated list views for past and cancelled bookings, and removal of the recent booking section from the customer mobile app.

The admin panel is a web-based interface built with vanilla JavaScript, HTML, and CSS. The backend is a Flask Python API with PostgreSQL database. The customer mobile app is built using Capacitor (Ionic framework) for cross-platform deployment.

### Goals

- Improve readability of booking details through larger font sizes
- Provide quick access to customer identity verification through profile previews
- Enable deeper data analysis through expandable charts with interactive filters
- Streamline chat conversation discovery through search functionality
- Improve navigation in print views with dedicated back buttons
- Enhance active booking visibility with location information
- Provide dedicated views for historical booking data (past and cancelled)
- Simplify customer mobile interface by removing redundant sections

### Non-Goals

- Complete redesign of the admin panel layout
- Backend performance optimization
- Mobile app feature additions beyond removal of recent booking section
- Real-time collaboration features
- Advanced analytics or machine learning insights

## Architecture

### System Components


```
???????????????????????????????????????????????????????????????
?                     Admin Web Interface                      ?
?  (HTML/CSS/JS - booking-management.html, reports.html, etc) ?
???????????????????????????????????????????????????????????????
                       ? HTTP/REST API
                       ?
???????????????????????????????????????????????????????????????
?                    Flask Backend (app.py)                    ?
?  - Booking Routes                                            ?
?  - User/Customer Routes                                      ?
?  - Report Routes                                             ?
?  - Chat Routes                                               ?
???????????????????????????????????????????????????????????????
                       ? SQL Queries
                       ?
???????????????????????????????????????????????????????????????
?                  PostgreSQL Database                         ?
?  - bookings table                                            ?
?  - users table (customers)                                   ?
?  - chat_messages table                                       ?
?  - vehicle_inspections table                                 ?
????????????????????????????????????????????????????????????????

???????????????????????????????????????????????????????????????
?              Customer Mobile App (Capacitor)                 ?
?  - Ionic/Angular/React components                            ?
?  - Recent booking section (TO BE REMOVED)                    ?
???????????????????????????????????????????????????????????????
```

### Technology Stack

- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Backend**: Flask (Python), PostgreSQL
- **Mobile**: Capacitor framework
- **Charts**: Chart.js library (already integrated)
- **File Storage**: Local uploads folder + Supabase (for images)


### Design Patterns

- **Modal Pattern**: Used for booking details, customer profile preview, and chart popups
- **Progressive Enhancement**: Base functionality works without JavaScript, enhanced with JS
- **Responsive Design**: Mobile-first approach with breakpoints at 768px and 1024px
- **Component-Based CSS**: Modular CSS classes for reusability
- **Event Delegation**: Efficient event handling for dynamically generated content

## Components and Interfaces

### 1. Enhanced Booking Details Modal

**Component**: `detailsModal` in `booking-management.html`

**Current Implementation**:
- Modal displays booking information with standard font sizes
- Uses CSS variables for text sizing

**Enhanced Implementation**:

```javascript
// booking-management.js - Enhanced viewDetails function
async function viewDetails(id) {
    const b = allBookings.find(x => x.id === id);
    if (!b) return;

    detailsModal.dataset.bookingId = id;
    detailsContent.innerHTML = `
        <div class="info-grid enhanced-text">
            <div class="info-item">
                <strong class="info-label">Customer:</strong> 
                <span class="info-value">${escapeHtml(b.customer_name)}</span>
                <button class="btn-view-profile" onclick="viewCustomerProfile(${b.user_id})">
                    ?? View Profile
                </button>
            </div>
            <!-- Additional fields with enhanced typography -->
        </div>
    `;
    detailsModal.classList.remove('hidden');
}
```


**CSS Enhancements**:

```css
/* Enhanced text sizing for booking details modal */
.details-card.enhanced-text .info-label {
    font-size: 1.05rem; /* Increased from 0.85rem - 23.5% increase */
    font-weight: 600;
    color: var(--text-secondary);
}

.details-card.enhanced-text .info-value {
    font-size: 1.1rem; /* Increased from 0.95rem - 15.8% increase */
    color: var(--text-primary);
    line-height: 1.6;
}

.details-card h3 {
    font-size: 1.44rem; /* Increased from 1.2rem - 20% increase */
    margin-bottom: 1rem;
}

.details-card h4 {
    font-size: 1.08rem; /* Increased from 0.9rem - 20% increase */
}

/* Ensure no text overflow */
.info-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
    overflow-wrap: break-word;
    word-wrap: break-word;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .details-card.enhanced-text .info-label {
        font-size: 0.95rem;
    }
    .details-card.enhanced-text .info-value {
        font-size: 1rem;
    }
}
```


### 2. Customer Profile Preview Modal

**Component**: New `customerProfileModal` component

**HTML Structure**:

```html
<!-- Add to booking-management.html -->
<div class="modal-overlay hidden" id="customerProfileModal">
    <div class="modal-card profile-preview-card">
        <header class="modal-header">
            <h3>Customer Profile</h3>
            <button class="close-btn" id="profileClose">?</button>
        </header>
        <div class="profile-content" id="profileContent">
            <div class="profile-avatar-section">
                <img id="profileAvatar" class="profile-avatar-img" alt="Customer Avatar">
            </div>
            <div class="profile-info-section">
                <h4 id="profileName"></h4>
                <p id="profileEmail"></p>
                <p id="profilePhone"></p>
            </div>
            <div class="license-section">
                <h4>License Information</h4>
                <div class="license-image-container">
                    <img id="licenseImage" class="license-img" alt="License">
                </div>
                <div class="license-details">
                    <div class="license-field">
                        <span class="license-label">License Number:</span>
                        <span id="licenseNumber"></span>
                    </div>
                    <div class="license-field">
                        <span class="license-label">Type:</span>
                        <span id="licenseType"></span>
                    </div>
                    <div class="license-field">
                        <span class="license-label">Expiry Date:</span>
                        <span id="licenseExpiry" class="expiry-date"></span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```


**JavaScript Implementation**:

```javascript
// booking-management.js - Customer profile preview
async function viewCustomerProfile(userId) {
    try {
        const res = await fetch(`${API_BASE}/users/${userId}`);
        if (!res.ok) throw new Error('Failed to load customer profile');
        
        const customer = await res.json();
        
        // Populate modal
        document.getElementById('profileAvatar').src = customer.profile_picture_url || '/default-avatar.png';
        document.getElementById('profileName').textContent = customer.full_name;
        document.getElementById('profileEmail').textContent = customer.email;
        document.getElementById('profilePhone').textContent = customer.phone || 'N/A';
        
        // License information
        if (customer.license_image_url) {
            document.getElementById('licenseImage').src = `${API_BASE}${customer.license_image_url}`;
            document.getElementById('licenseNumber').textContent = customer.license_number || 'N/A';
            document.getElementById('licenseType').textContent = customer.license_type || 'N/A';
            
            const expiryElement = document.getElementById('licenseExpiry');
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
                expiryElement.innerHTML += ` <span class="warning-badge">?? Expires in ${daysUntilExpiry} days</span>`;
            }
        } else {
            document.querySelector('.license-section').innerHTML = '<p class="no-license">No license information available</p>';
        }
        
        document.getElementById('customerProfileModal').classList.remove('hidden');
    } catch (err) {
        showToast('error', 'Failed to load customer profile');
        console.error(err);
    }
}

// Close handler
document.getElementById('profileClose').addEventListener('click', () => {
    document.getElementById('customerProfileModal').classList.add('hidden');
});
```


**CSS Styling**:

```css
.profile-preview-card {
    max-width: 600px;
    max-height: 90vh;
    overflow-y: auto;
}

.profile-avatar-section {
    text-align: center;
    margin-bottom: 1.5rem;
}

.profile-avatar-img {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid var(--accent);
}

.profile-info-section {
    text-align: center;
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border-glass);
}

.license-section {
    margin-top: 1.5rem;
}

.license-section h4 {
    font-size: 1.1rem;
    margin-bottom: 1rem;
    color: var(--text-primary);
}

.license-image-container {
    margin-bottom: 1rem;
    text-align: center;
}

.license-img {
    max-width: 100%;
    max-height: 300px;
    border-radius: 8px;
    border: 1px solid var(--border-glass);
    cursor: pointer;
}

.license-img:hover {
    opacity: 0.9;
}

.license-details {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.license-field {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 6px;
}

.license-label {
    font-weight: 600;
    color: var(--text-secondary);
}

.expiry-date.expired {
    color: var(--red);
    font-weight: 700;
}

.expiry-date.expiring-soon {
    color: var(--amber);
    font-weight: 700;
}

.warning-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    background: rgba(239, 68, 68, 0.2);
    color: var(--red);
}

.no-license {
    text-align: center;
    color: var(--text-muted);
    font-style: italic;
}
```


### 3. Expandable Dashboard Charts with Filters

**Component**: Chart popup modal in `reports.html`

**HTML Structure**:

```html
<!-- Add to reports.html -->
<div class="modal-overlay hidden" id="chartPopupModal">
    <div class="modal-card chart-popup-card">
        <header class="modal-header">
            <h3 id="chartPopupTitle">Chart Details</h3>
            <button class="close-btn" id="chartPopupClose">?</button>
        </header>
        <div class="chart-filters">
            <div class="filter-group">
                <label for="filterStartDate">Start Date:</label>
                <input type="date" id="filterStartDate" class="filter-input">
            </div>
            <div class="filter-group">
                <label for="filterEndDate">End Date:</label>
                <input type="date" id="filterEndDate" class="filter-input">
            </div>
            <div class="filter-group">
                <label for="filterStatus">Status:</label>
                <select id="filterStatus" class="filter-input">
                    <option value="all">All Statuses</option>
                    <option value="Pending">Pending</option>
                    <option value="Approved">Approved</option>
                    <option value="Completed">Completed</option>
                    <option value="Cancelled">Cancelled</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="filterVehicleType">Vehicle Type:</label>
                <select id="filterVehicleType" class="filter-input">
                    <option value="all">All Types</option>
                    <option value="sedan">Sedan</option>
                    <option value="suv">SUV</option>
                    <option value="van">Van</option>
                </select>
            </div>
            <button class="btn-reset-filters" id="btnResetFilters">?? Reset Filters</button>
        </div>
        <div class="chart-popup-body">
            <canvas id="popupChartCanvas"></canvas>
        </div>
    </div>
</div>
```


**JavaScript Implementation**:

```javascript
// reports.js - Chart expansion and filtering
let currentPopupChart = null;
let currentChartData = null;
let currentChartType = null;

// Make charts clickable
function makeChartClickable(chartElement, chartInstance, chartType) {
    chartElement.style.cursor = 'pointer';
    chartElement.addEventListener('click', () => {
        openChartPopup(chartInstance, chartType);
    });
}

async function openChartPopup(chartInstance, chartType) {
    currentChartType = chartType;
    currentChartData = {
        labels: chartInstance.data.labels,
        datasets: chartInstance.data.datasets
    };
    
    document.getElementById('chartPopupTitle').textContent = getChartTitle(chartType);
    document.getElementById('chartPopupModal').classList.remove('hidden');
    
    // Initialize filters with current date range
    const today = new Date().toISOString().split('T')[0];
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    document.getElementById('filterStartDate').value = thirtyDaysAgo;
    document.getElementById('filterEndDate').value = today;
    
    renderPopupChart();
}

function renderPopupChart() {
    const canvas = document.getElementById('popupChartCanvas');
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    if (currentPopupChart) {
        currentPopupChart.destroy();
    }
    
    // Create enlarged chart (150% of original)
    currentPopupChart = new Chart(ctx, {
        type: currentChartType,
        data: currentChartData,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#f1f5f9',
                        font: { size: 14 }
                    }
                }
            },
            scales: currentChartType !== 'doughnut' ? {
                y: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(255,255,255,0.1)' }
                },
                x: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(255,255,255,0.1)' }
                }
            } : {}
        }
    });
}

// Filter handlers
async function applyChartFilters() {
    const startDate = document.getElementById('filterStartDate').value;
    const endDate = document.getElementById('filterEndDate').value;
    const status = document.getElementById('filterStatus').value;
    const vehicleType = document.getElementById('filterVehicleType').value;
    
    try {
        const res = await fetch(`${API_BASE}/reports/filtered?start=${startDate}&end=${endDate}&status=${status}&vehicle_type=${vehicleType}`);
        if (!res.ok) throw new Error('Failed to fetch filtered data');
        
        const data = await res.json();
        currentChartData = transformDataForChart(data, currentChartType);
        renderPopupChart();
    } catch (err) {
        showToast('error', 'Failed to apply filters');
        console.error(err);
    }
}

// Debounced filter application
let filterTimeout;
['filterStartDate', 'filterEndDate', 'filterStatus', 'filterVehicleType'].forEach(id => {
    document.getElementById(id).addEventListener('change', () => {
        clearTimeout(filterTimeout);
        filterTimeout = setTimeout(applyChartFilters, 500);
    });
});

document.getElementById('btnResetFilters').addEventListener('click', () => {
    const today = new Date().toISOString().split('T')[0];
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    document.getElementById('filterStartDate').value = thirtyDaysAgo;
    document.getElementById('filterEndDate').value = today;
    document.getElementById('filterStatus').value = 'all';
    document.getElementById('filterVehicleType').value = 'all';
    applyChartFilters();
});

document.getElementById('chartPopupClose').addEventListener('click', () => {
    document.getElementById('chartPopupModal').classList.add('hidden');
    if (currentPopupChart) {
        currentPopupChart.destroy();
        currentPopupChart = null;
    }
});
```


**CSS Styling**:

```css
.chart-popup-card {
    max-width: 1200px;
    width: 95vw;
    max-height: 90vh;
}

.chart-filters {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 8px;
    margin-bottom: 1.5rem;
}

.filter-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.filter-group label {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
}

.filter-input {
    padding: 0.5rem;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid var(--border-glass);
    border-radius: 6px;
    color: var(--text-primary);
    font-size: 0.9rem;
}

.btn-reset-filters {
    grid-column: span 1;
    padding: 0.5rem 1rem;
    background: var(--bg-glass);
    border: 1px solid var(--border-glass);
    color: var(--text-primary);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-reset-filters:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: var(--accent);
}

.chart-popup-body {
    padding: 1rem;
    min-height: 400px;
}

@media (max-width: 768px) {
    .chart-filters {
        grid-template-columns: 1fr;
    }
}
```


### 4. Live Chat Search Functionality

**Component**: Chat search in admin panel (likely in `index.html` or separate chat page)

**HTML Structure**:

```html
<!-- Add to chat interface -->
<div class="chat-search-container">
    <div class="search-box">
        <span class="search-icon">??</span>
        <input type="text" id="chatSearchInput" placeholder="Search conversations by name, email, or message..." autocomplete="off">
        <button class="clear-search hidden" id="clearSearch">?</button>
    </div>
    <div class="search-results-count hidden" id="searchResultsCount">
        <span id="resultsText"></span>
    </div>
</div>
```

**JavaScript Implementation**:

```javascript
// Live chat search functionality
let allConversations = [];
let filteredConversations = [];

async function loadConversations() {
    try {
        const res = await fetch(`${API_BASE}/chat/conversations`);
        if (!res.ok) throw new Error('Failed to load conversations');
        allConversations = await res.json();
        filteredConversations = [...allConversations];
        renderConversations(filteredConversations);
    } catch (err) {
        console.error('Failed to load conversations:', err);
        showToast('error', 'Failed to load chat conversations');
    }
}

function searchConversations(query) {
    const searchTerm = query.toLowerCase().trim();
    
    if (!searchTerm) {
        filteredConversations = [...allConversations];
        document.getElementById('searchResultsCount').classList.add('hidden');
        document.getElementById('clearSearch').classList.add('hidden');
        renderConversations(filteredConversations);
        return;
    }
    
    document.getElementById('clearSearch').classList.remove('hidden');
    
    filteredConversations = allConversations.filter(conv => {
        // Search in customer name
        if (conv.customer_name && conv.customer_name.toLowerCase().includes(searchTerm)) {
            return true;
        }
        // Search in email
        if (conv.customer_email && conv.customer_email.toLowerCase().includes(searchTerm)) {
            return true;
        }
        // Search in last message content
        if (conv.last_message && conv.last_message.toLowerCase().includes(searchTerm)) {
            return true;
        }
        return false;
    });
    
    // Show results count
    const resultsCount = document.getElementById('searchResultsCount');
    const resultsText = document.getElementById('resultsText');
    resultsText.textContent = `${filteredConversations.length} conversation${filteredConversations.length !== 1 ? 's' : ''} found`;
    resultsCount.classList.remove('hidden');
    
    renderConversations(filteredConversations);
}

function renderConversations(conversations) {
    const container = document.getElementById('conversationsContainer');
    
    if (conversations.length === 0) {
        container.innerHTML = '<div class="no-results">No conversations found</div>';
        return;
    }
    
    container.innerHTML = conversations.map(conv => {
        const searchTerm = document.getElementById('chatSearchInput').value.toLowerCase();
        const highlightedName = highlightText(conv.customer_name, searchTerm);
        const highlightedMessage = highlightText(conv.last_message, searchTerm);
        
        return `
            <div class="conversation-item" onclick="openConversation(${conv.user_id})">
                <div class="conv-avatar">${conv.customer_name.charAt(0).toUpperCase()}</div>
                <div class="conv-info">
                    <div class="conv-name">${highlightedName}</div>
                    <div class="conv-preview">${highlightedMessage}</div>
                </div>
                <div class="conv-meta">
                    <span class="conv-time">${formatTime(conv.last_message_time)}</span>
                    ${conv.unread_count > 0 ? `<span class="unread-badge">${conv.unread_count}</span>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

function highlightText(text, searchTerm) {
    if (!text || !searchTerm) return text || '';
    const regex = new RegExp(`(${escapeRegex(searchTerm)})`, 'gi');
    return text.replace(regex, '<mark class="search-highlight">$1</mark>');
}

function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Event listeners
document.getElementById('chatSearchInput').addEventListener('input', (e) => {
    searchConversations(e.target.value);
});

document.getElementById('clearSearch').addEventListener('click', () => {
    document.getElementById('chatSearchInput').value = '';
    searchConversations('');
});
```


**CSS Styling**:

```css
.chat-search-container {
    margin-bottom: 1rem;
}

.search-box {
    position: relative;
    display: flex;
    align-items: center;
}

.search-box .search-icon {
    position: absolute;
    left: 12px;
    font-size: 1.2rem;
    color: var(--text-muted);
}

#chatSearchInput {
    width: 100%;
    padding: 0.75rem 2.5rem 0.75rem 2.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-glass);
    border-radius: 8px;
    color: var(--text-primary);
    font-size: 0.95rem;
}

#chatSearchInput:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
}

.clear-search {
    position: absolute;
    right: 8px;
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition: all 0.2s ease;
}

.clear-search:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
}

.search-results-count {
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: rgba(99, 102, 241, 0.1);
    border-radius: 6px;
    text-align: center;
}

#resultsText {
    font-size: 0.85rem;
    color: var(--accent);
    font-weight: 600;
}

.search-highlight {
    background: rgba(245, 158, 11, 0.3);
    color: var(--amber);
    padding: 2px 4px;
    border-radius: 3px;
    font-weight: 600;
}

.no-results {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-muted);
    font-size: 0.95rem;
}
```


### 5. Print View Navigation

**Component**: Print view pages (booking receipts, reports, etc.)

**HTML Structure**:

```html
<!-- Add to print view pages -->
<div class="print-header no-print">
    <button class="btn-back" id="btnBackToPrevious" onclick="goBack()">
        <span class="back-icon">?</span>
        <span class="back-text">Back</span>
    </button>
    <h1 class="print-title">Booking Receipt</h1>
    <button class="btn-print" onclick="window.print()">
        <span class="print-icon">???</span>
        <span class="print-text">Print</span>
    </button>
</div>
```

**JavaScript Implementation**:

```javascript
// Print view navigation
function goBack() {
    // Check if there's a referrer in the same domain
    if (document.referrer && document.referrer.includes(window.location.hostname)) {
        window.history.back();
    } else {
        // Fallback to booking management page
        window.location.href = '/admin_app/booking-management.html';
    }
}

// Alternative: Store previous page in sessionStorage
function navigateToPrintView(bookingId) {
    sessionStorage.setItem('previousPage', window.location.href);
    window.location.href = `/admin_app/print-receipt.html?id=${bookingId}`;
}

function goBackFromPrint() {
    const previousPage = sessionStorage.getItem('previousPage');
    if (previousPage) {
        window.location.href = previousPage;
        sessionStorage.removeItem('previousPage');
    } else {
        window.history.back();
    }
}
```

**CSS Styling**:

```css
.print-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-glass);
    position: sticky;
    top: 0;
    z-index: 100;
}

.btn-back {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    background: var(--bg-glass);
    border: 1px solid var(--border-glass);
    border-radius: 8px;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.95rem;
    font-weight: 500;
}

.btn-back:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: var(--accent);
    transform: translateX(-3px);
}

.back-icon {
    font-size: 1.2rem;
}

.print-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
}

.btn-print {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    background: var(--accent);
    border: none;
    border-radius: 8px;
    color: white;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.95rem;
    font-weight: 600;
}

.btn-print:hover {
    background: #5558dd;
    box-shadow: 0 0 20px var(--accent-glow);
}

/* Hide navigation elements when printing */
@media print {
    .no-print {
        display: none !important;
    }
    
    .print-header {
        display: none !important;
    }
}
```


### 6. Location Field in Active Bookings

**Component**: Active bookings tab in booking management

**HTML Structure**:

```html
<!-- Modified booking card/row for active bookings -->
<tr class="booking-row active-booking">
    <td class="id-cell">#${b.id}</td>
    <td class="customer-cell">${escapeHtml(b.customer_name)}</td>
    <td class="car-cell">${escapeHtml(b.car)}</td>
    <td class="location-cell">
        <div class="location-info">
            <span class="location-icon">??</span>
            <div class="location-text">
                <span class="pickup-location" title="${escapeHtml(b.pickup_location)}">
                    ${truncateLocation(b.pickup_location)}
                </span>
                ${b.dropoff_location && b.dropoff_location !== b.pickup_location ? 
                    `<span class="location-separator">?</span>
                     <span class="dropoff-location" title="${escapeHtml(b.dropoff_location)}">
                        ${truncateLocation(b.dropoff_location)}
                     </span>` : ''}
            </div>
        </div>
    </td>
    <td class="dates-cell">${formatRentalDates(b.start_date, b.end_date)}</td>
    <td class="price-cell">?${formatPrice(b.total_price)}</td>
    <td class="status-cell">${statusBadge(b.status)}</td>
    <td class="actions-cell">
        <button class="btn-details" onclick="viewDetails(${b.id})">??? View</button>
    </td>
</tr>
```

**JavaScript Implementation**:

```javascript
// Location handling functions
function truncateLocation(location, maxLength = 30) {
    if (!location) return 'N/A';
    if (location.length <= maxLength) return location;
    return location.substring(0, maxLength) + '...';
}

// Modify renderTable to include location for active bookings
function renderActiveBookingsTable(bookings) {
    const tbody = document.getElementById('activeBookingsBody');
    tbody.innerHTML = '';
    
    if (bookings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-cell">No active bookings</td></tr>';
        return;
    }
    
    bookings.forEach(b => {
        const tr = document.createElement('tr');
        tr.className = 'booking-row active-booking';
        
        const locationDisplay = b.dropoff_location && b.dropoff_location !== b.pickup_location
            ? `<span class="pickup-location" title="${escapeHtml(b.pickup_location)}">${truncateLocation(b.pickup_location)}</span>
               <span class="location-separator">?</span>
               <span class="dropoff-location" title="${escapeHtml(b.dropoff_location)}">${truncateLocation(b.dropoff_location)}</span>`
            : `<span class="pickup-location" title="${escapeHtml(b.pickup_location)}">${truncateLocation(b.pickup_location)}</span>`;
        
        tr.innerHTML = `
            <td class="id-cell">#${b.id}</td>
            <td class="customer-cell">${escapeHtml(b.customer_name)}</td>
            <td class="car-cell">${escapeHtml(b.car)}</td>
            <td class="location-cell">
                <div class="location-info">
                    <span class="location-icon">??</span>
                    <div class="location-text">${locationDisplay}</div>
                </div>
            </td>
            <td class="dates-cell">${formatRentalDates(b.start_date, b.end_date)}</td>
            <td class="price-cell">?${formatPrice(b.total_price)}</td>
            <td class="status-cell">${statusBadge(b.status)}</td>
            <td class="actions-cell">
                <button class="btn-details" onclick="viewDetails(${b.id})">??? View</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}
```


**CSS Styling**:

```css
.location-cell {
    min-width: 200px;
    max-width: 300px;
}

.location-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.location-icon {
    font-size: 1.1rem;
    flex-shrink: 0;
}

.location-text {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    overflow: hidden;
}

.pickup-location,
.dropoff-location {
    font-size: 0.9rem;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    cursor: help;
}

.pickup-location {
    font-weight: 600;
}

.dropoff-location {
    font-weight: 500;
    color: var(--text-secondary);
}

.location-separator {
    margin: 0 0.25rem;
    color: var(--text-muted);
    font-size: 0.8rem;
}

/* Tooltip on hover for full location */
.pickup-location:hover,
.dropoff-location:hover {
    color: var(--accent);
}

@media (max-width: 768px) {
    .location-cell {
        min-width: 150px;
    }
    
    .location-text {
        font-size: 0.85rem;
    }
}
```


### 7. Past Bookings List View

**Component**: New tab in booking management

**HTML Structure**:

```html
<!-- Add to booking-management.html -->
<section class="tabs-container">
    <button class="tab-button active" data-tab="all">All Bookings</button>
    <button class="tab-button" data-tab="active">Active Now</button>
    <button class="tab-button" data-tab="past">Past Bookings</button>
    <button class="tab-button" data-tab="cancelled">Cancelled</button>
</section>

<div class="tab-content active" id="tabAll">
    <!-- Existing all bookings content -->
</div>

<div class="tab-content" id="tabPast">
    <section class="toolbar">
        <div class="search-box">
            <span class="search-icon">??</span>
            <input type="text" id="searchPastInput" placeholder="Search past bookings..." autocomplete="off">
        </div>
        <div class="filter-group">
            <select id="sortPastBy">
                <option value="completion_date_desc">Completion Date (Newest)</option>
                <option value="completion_date_asc">Completion Date (Oldest)</option>
                <option value="customer_name">Customer Name</option>
                <option value="total_price_desc">Total Price (High to Low)</option>
                <option value="total_price_asc">Total Price (Low to High)</option>
            </select>
            <select id="pageSizePast">
                <option value="10">10 per page</option>
                <option value="25" selected>25 per page</option>
                <option value="50">50 per page</option>
                <option value="100">100 per page</option>
            </select>
        </div>
    </section>
    
    <section class="table-container">
        <div class="table-scroll">
            <table class="bookings-table" id="pastBookingsTable">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Customer</th>
                        <th>Vehicle</th>
                        <th>Rental Dates</th>
                        <th>Completion Date</th>
                        <th>Total Price</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="pastBookingsBody">
                    <!-- Dynamically populated -->
                </tbody>
            </table>
        </div>
        
        <div class="pagination-controls" id="pastPagination">
            <button class="btn-page" id="btnPastPrev">? Previous</button>
            <span class="page-info" id="pastPageInfo">Page 1 of 1</span>
            <button class="btn-page" id="btnPastNext">Next ?</button>
        </div>
        
        <div class="empty-state hidden" id="emptyPastState">
            <div class="empty-icon">??</div>
            <h3>No past bookings found</h3>
            <p>Completed bookings will appear here.</p>
        </div>
        
        <div class="loading-state hidden" id="loadingPastState">
            <div class="spinner"></div>
            <p>Loading past bookings...</p>
        </div>
    </section>
</div>
```



## Data Models

This section describes the data structures used across the admin panel UI improvements.

### Booking Record

The core booking entity with enhanced display fields:

```typescript
interface Booking {
    id: number;
    user_id: number;
    customer_name: string;
    customer_email: string;
    customer_phone: string;
    car: string;
    vehicle_type: 'sedan' | 'suv' | 'van';
    pickup_location: string;
    dropoff_location: string;
    start_date: string; // ISO 8601 format
    end_date: string; // ISO 8601 format
    completion_date?: string; // ISO 8601 format (for past bookings)
    cancellation_date?: string; // ISO 8601 format (for cancelled bookings)
    cancellation_reason?: string;
    cancelled_by?: 'customer' | 'admin';
    total_price: number;
    status: 'Pending' | 'Approved' | 'Active' | 'Completed' | 'Cancelled';
    created_at: string;
    updated_at: string;
}
```

### Customer Profile

Extended customer information for profile preview:

```typescript
interface CustomerProfile {
    id: number;
    full_name: string;
    email: string;
    phone: string;
    profile_picture_url?: string;
    license_number?: string;
    license_type?: string;
    license_expiry?: string; // ISO 8601 format
    license_image_url?: string;
    created_at: string;
    total_bookings: number;
    account_status: 'active' | 'suspended' | 'inactive';
}
```

### Chat Conversation

Chat conversation metadata for search functionality:

```typescript
interface ChatConversation {
    user_id: number;
    customer_name: string;
    customer_email: string;
    last_message: string;
    last_message_time: string; // ISO 8601 format
    unread_count: number;
    conversation_status: 'active' | 'archived';
}
```

### Chart Data

Data structure for dashboard charts with filter support:

```typescript
interface ChartData {
    labels: string[];
    datasets: ChartDataset[];
}

interface ChartDataset {
    label: string;
    data: number[];
    backgroundColor: string | string[];
    borderColor: string | string[];
    borderWidth: number;
}

interface ChartFilters {
    startDate: string; // ISO 8601 format
    endDate: string; // ISO 8601 format
    status: 'all' | 'Pending' | 'Approved' | 'Completed' | 'Cancelled';
    vehicleType: 'all' | 'sedan' | 'suv' | 'van';
}
```

### Pagination State

Pagination configuration for list views:

```typescript
interface PaginationState {
    currentPage: number;
    pageSize: number;
    totalRecords: number;
    totalPages: number;
    sortBy: string;
    sortOrder: 'asc' | 'desc';
}
```



## Correctness Properties

**Property-based testing is not applicable for this feature.**

This feature consists primarily of UI/UX improvements including:
- Visual enhancements (larger fonts, modal displays, chart expansions)
- Navigation improvements (back buttons, search functionality)
- Display logic (list views, pagination, filtering)

These improvements fall into categories where property-based testing is not appropriate:

1. **UI Rendering and Layout**: Font size changes, modal positioning, and visual styling are best verified through snapshot tests and visual regression testing, not property-based tests.

2. **Simple Display Logic**: Showing filtered lists, pagination, and search results are deterministic operations that work with specific UI states. These are better tested with example-based unit tests.

3. **User Interaction Handlers**: Click handlers, navigation flows, and form interactions are specific scenarios that don't benefit from randomized input generation.

Instead, this feature will use **unit tests** for component logic, **integration tests** for user workflows, and **visual regression tests** for UI consistency. See the Testing Strategy section below for the complete testing approach.



## Error Handling

This section outlines error handling strategies for the admin panel UI improvements.

### Frontend Error Handling

#### API Request Failures

All API requests should implement consistent error handling:

```javascript
async function fetchWithErrorHandling(url, options = {}) {
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            // Handle HTTP errors
            if (response.status === 401) {
                // Unauthorized - redirect to login
                window.location.href = '/login.html';
                throw new Error('Session expired. Please log in again.');
            } else if (response.status === 403) {
                showToast('error', 'You do not have permission to perform this action');
                throw new Error('Forbidden');
            } else if (response.status === 404) {
                showToast('error', 'Resource not found');
                throw new Error('Not found');
            } else if (response.status >= 500) {
                showToast('error', 'Server error. Please try again later.');
                throw new Error('Server error');
            } else {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.message || 'Request failed';
                showToast('error', errorMessage);
                throw new Error(errorMessage);
            }
        }
        
        return await response.json();
    } catch (error) {
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            // Network error
            showToast('error', 'Network error. Please check your connection.');
        }
        throw error;
    }
}
```

#### Modal and UI Component Errors

Handle errors in modal operations gracefully:

```javascript
// Customer profile preview error handling
async function viewCustomerProfile(userId) {
    const modal = document.getElementById('customerProfileModal');
    const content = document.getElementById('profileContent');
    
    try {
        // Show loading state
        content.innerHTML = '<div class="loading-spinner">Loading...</div>';
        modal.classList.remove('hidden');
        
        const customer = await fetchWithErrorHandling(`${API_BASE}/users/${userId}`);
        
        // Populate modal with data
        populateCustomerProfile(customer);
        
    } catch (error) {
        // Show error state in modal
        content.innerHTML = `
            <div class="error-state">
                <div class="error-icon">??</div>
                <h4>Failed to Load Profile</h4>
                <p>${error.message}</p>
                <button class="btn-retry" onclick="viewCustomerProfile(${userId})">
                    Retry
                </button>
            </div>
        `;
        console.error('Profile load error:', error);
    }
}
```



#### Chart Rendering Errors

Handle Chart.js rendering failures:

```javascript
function renderChartSafely(canvasId, chartConfig) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');
    
    try {
        return new Chart(ctx, chartConfig);
    } catch (error) {
        console.error('Chart rendering error:', error);
        
        // Display error message in canvas container
        const container = canvas.parentElement;
        container.innerHTML = `
            <div class="chart-error">
                <p>Unable to display chart</p>
                <button onclick="location.reload()">Refresh Page</button>
            </div>
        `;
        
        showToast('error', 'Failed to render chart');
        return null;
    }
}
```

#### Search and Filter Errors

Handle search failures gracefully:

```javascript
function searchConversations(query) {
    try {
        const searchTerm = query.toLowerCase().trim();
        
        if (!allConversations || !Array.isArray(allConversations)) {
            throw new Error('Conversation data not loaded');
        }
        
        // Perform search
        filteredConversations = allConversations.filter(conv => {
            // Safe property access with fallbacks
            const name = (conv.customer_name || '').toLowerCase();
            const email = (conv.customer_email || '').toLowerCase();
            const message = (conv.last_message || '').toLowerCase();
            
            return name.includes(searchTerm) || 
                   email.includes(searchTerm) || 
                   message.includes(searchTerm);
        });
        
        renderConversations(filteredConversations);
        
    } catch (error) {
        console.error('Search error:', error);
        showToast('error', 'Search failed. Please try again.');
        
        // Reset to show all conversations
        filteredConversations = [...allConversations];
        renderConversations(filteredConversations);
    }
}
```

### Backend Error Handling

#### Flask Route Error Responses

Consistent error response format:

```python
from flask import jsonify

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'status': 404
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status': 500
    }), 500

# Route-specific error handling
@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': f'User with ID {user_id} not found'
            }), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        app.logger.error(f'Error fetching user {user_id}: {str(e)}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to retrieve user data'
        }), 500
```



#### Database Query Error Handling

Handle database errors with proper logging:

```python
from sqlalchemy.exc import SQLAlchemyError

@app.route('/api/bookings/past')
def get_past_bookings():
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 25, type=int)
        sort_by = request.args.get('sort_by', 'completion_date_desc')
        
        # Validate page_size
        if page_size not in [10, 25, 50, 100]:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid page_size. Must be 10, 25, 50, or 100'
            }), 400
        
        query = Booking.query.filter_by(status='Completed')
        
        # Apply sorting
        if sort_by == 'completion_date_desc':
            query = query.order_by(Booking.completion_date.desc())
        elif sort_by == 'completion_date_asc':
            query = query.order_by(Booking.completion_date.asc())
        # ... other sort options
        
        # Paginate
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        
        return jsonify({
            'bookings': [b.to_dict() for b in pagination.items],
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'total_pages': pagination.pages
        }), 200
        
    except SQLAlchemyError as e:
        app.logger.error(f'Database error in get_past_bookings: {str(e)}')
        return jsonify({
            'error': 'Database Error',
            'message': 'Failed to retrieve bookings'
        }), 500
    except Exception as e:
        app.logger.error(f'Unexpected error in get_past_bookings: {str(e)}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
```

### User-Facing Error Messages

Error messages should be:
- **Clear**: Explain what went wrong in plain language
- **Actionable**: Suggest what the user can do next
- **Non-technical**: Avoid exposing technical details or stack traces
- **Consistent**: Use the same toast/notification system throughout

Examples:
- ? "Failed to load customer profile. Please try again."
- ? "Network error. Please check your connection."
- ? "Session expired. Please log in again."
- ? "TypeError: Cannot read property 'name' of undefined"
- ? "500 Internal Server Error"



## Testing Strategy

### Overview

This feature focuses on UI/UX improvements including visual enhancements (larger fonts, modals, charts), navigation improvements (back buttons, search), and display logic (list views, pagination). **Property-based testing is not applicable** for this feature because:

1. **UI Rendering**: Font size changes, modal displays, and visual layouts are best tested with snapshot tests and visual regression testing
2. **Simple Display Logic**: Showing lists, filtering, and pagination are deterministic operations best verified with example-based tests
3. **User Interactions**: Click handlers, navigation, and search are specific scenarios that don't benefit from randomized input testing

Instead, we will use **unit tests** for component logic and **integration tests** for end-to-end user flows.

### Testing Approach

#### 1. Unit Tests

Unit tests will verify individual functions and component behavior:

**Font Size Enhancements (Requirement 1)**
- Test that CSS classes apply correct font size increases (15%+ from baseline)
- Test responsive font size adjustments for mobile viewports
- Test text overflow handling with long content

**Customer Profile Preview (Requirement 2)**
- Test `viewCustomerProfile()` function with valid user data
- Test license expiry warning logic (expired, expiring within 30 days, valid)
- Test modal open/close behavior
- Test error handling when customer data is missing
- Test default avatar display when profile picture is unavailable

**Chart Expansion and Filtering (Requirements 3, 4)**
- Test `openChartPopup()` function with different chart types
- Test filter application logic (date range, status, vehicle type)
- Test filter reset functionality
- Test chart data transformation for different filter combinations
- Test debounced filter updates (500ms delay)

**Live Chat Search (Requirement 5)**
- Test `searchConversations()` with various search terms
- Test search matching against customer name, email, and message content
- Test search highlighting logic
- Test empty search results handling
- Test search term escaping for regex safety

**Print View Navigation (Requirement 6)**
- Test `goBack()` function with valid referrer
- Test fallback navigation when no referrer exists
- Test sessionStorage-based navigation tracking

**Location Display (Requirement 7)**
- Test `truncateLocation()` function with various location lengths
- Test location display with matching pickup/dropoff
- Test location display with different pickup/dropoff
- Test tooltip display on hover

**Pagination Logic (Requirements 8, 9)**
- Test page calculation with different page sizes (10, 25, 50, 100)
- Test sorting logic for different sort options
- Test pagination state updates
- Test edge cases (empty results, single page, last page)

#### 2. Integration Tests

Integration tests will verify end-to-end user workflows:

**Booking Details Flow**
- Navigate to booking management page
- Click on a booking to open details modal
- Verify enhanced font sizes are applied
- Click "View Profile" button
- Verify customer profile modal opens with correct data
- Verify license expiry warnings display correctly
- Close modals and verify state cleanup

**Dashboard Charts Flow**
- Navigate to reports/dashboard page
- Click on a chart to expand it
- Verify chart popup displays at 150% size
- Apply date range filter
- Verify chart updates with filtered data
- Apply status and vehicle type filters
- Verify combined filter results
- Reset filters and verify default state restored
- Close chart popup

**Chat Search Flow**
- Navigate to live chat interface
- Type search query in search box
- Verify conversations filter in real-time
- Verify search term highlighting in results
- Verify results count display
- Clear search and verify all conversations shown
- Test search with no results

**Print View Navigation Flow**
- Navigate to booking details
- Click print/view receipt button
- Verify print view displays with back button
- Click back button
- Verify navigation returns to previous page
- Verify back button hidden in print mode

**Active Bookings Location Display**
- Navigate to "Active Now" tab
- Verify location column displays for all active bookings
- Verify pickup location shown prominently
- Verify dropoff location shown when different from pickup
- Hover over truncated location
- Verify full location shown in tooltip

**Past Bookings List View**
- Navigate to "Past Bookings" tab
- Verify completed bookings displayed
- Change page size to 50
- Verify pagination updates correctly
- Sort by completion date (newest first)
- Verify sort order applied
- Search for specific customer
- Verify filtered results
- Click on a past booking
- Verify details modal opens

**Cancelled Bookings List View**
- Navigate to "Cancelled Bookings" tab
- Verify cancelled bookings displayed with cancellation details
- Sort by cancellation date
- Verify sort order applied
- Change page size to 100
- Verify pagination updates
- Click on a cancelled booking
- Verify details modal shows cancellation reason and cancelled_by field

#### 3. API Integration Tests

Test backend endpoints that support the UI improvements:

**Customer Profile Endpoint**
- `GET /api/users/{user_id}` returns complete customer profile
- Verify license information included in response
- Test 404 response for non-existent user
- Test error handling for database failures

**Filtered Reports Endpoint**
- `GET /api/reports/filtered` with date range, status, vehicle type filters
- Verify correct data returned for filter combinations
- Test validation of filter parameters
- Test empty results handling

**Chat Conversations Endpoint**
- `GET /api/chat/conversations` returns all conversations
- Verify conversation metadata (last message, unread count)
- Test sorting by last message time

**Past Bookings Endpoint**
- `GET /api/bookings/past` with pagination and sorting
- Verify only completed bookings returned
- Test page size validation (10, 25, 50, 100)
- Test sorting options (completion_date, customer_name, total_price)

**Cancelled Bookings Endpoint**
- `GET /api/bookings/cancelled` with pagination and sorting
- Verify only cancelled bookings returned
- Verify cancellation_reason and cancelled_by fields included

#### 4. Visual Regression Tests

Use snapshot testing or visual regression tools to verify UI consistency:

- Capture screenshots of booking details modal with enhanced fonts
- Capture customer profile preview modal
- Capture expanded chart popup with filters
- Capture print view layout
- Capture active bookings table with location column
- Capture past and cancelled bookings list views
- Compare against baseline screenshots to detect unintended visual changes

#### 5. Accessibility Tests

Verify WCAG compliance for UI improvements:

- Test keyboard navigation through modals (Tab, Escape, Enter)
- Test screen reader compatibility for new UI elements
- Test color contrast ratios for text (minimum 4.5:1 for normal text)
- Test focus indicators on interactive elements
- Test ARIA labels for icons and buttons

#### 6. Mobile Responsiveness Tests

Test UI improvements on different viewport sizes:

- Test font size adjustments on mobile (768px and below)
- Test modal layouts on small screens
- Test chart popup responsiveness
- Test table scrolling on mobile
- Test location column display on narrow viewports

### Test Environment Setup

**Frontend Testing**
- Framework: Jest + Testing Library (or Vitest for Vite projects)
- Browser automation: Playwright or Cypress for integration tests
- Visual regression: Percy or Chromatic

**Backend Testing**
- Framework: pytest
- Database: PostgreSQL test database with fixtures
- API testing: requests library or httpx

**Test Data**
- Create fixtures for bookings (active, past, cancelled)
- Create fixtures for customers with various license states (valid, expiring, expired)
- Create fixtures for chat conversations
- Create fixtures for chart data with different date ranges

### Test Coverage Goals

- **Unit test coverage**: Minimum 80% for JavaScript functions
- **Integration test coverage**: All critical user workflows covered
- **API endpoint coverage**: 100% of new/modified endpoints tested
- **Visual regression**: All new UI components captured

### Continuous Integration

- Run unit tests on every commit
- Run integration tests on pull requests
- Run visual regression tests on staging deployments
- Generate coverage reports and fail builds below 80% coverage threshold

