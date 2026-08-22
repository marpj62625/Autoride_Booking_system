/* ============================================================
   Autoride Admin — Booking Management JS
   Handles fetching, filtering, approving, and rejecting bookings
   ============================================================ */

// Using global API_BASE from index.html

// DOM references
const bookingsBody  = document.getElementById('bookingsBody');
const searchInput   = document.getElementById('searchInput');
const statusFilter  = document.getElementById('statusFilter');
const btnRefresh    = document.getElementById('btnRefresh');
const loadingState  = document.getElementById('loadingState');
const emptyState    = document.getElementById('emptyState');
const bookingsTable = document.getElementById('bookingsTable');

// Stats
const statTotal    = document.getElementById('statTotal');
const statPending  = document.getElementById('statPending');
const statApproved = document.getElementById('statApproved');
const statRejected = document.getElementById('statRejected');

// Modal
const confirmModal = document.getElementById('confirmModal');
const modalIcon    = document.getElementById('modalIcon');
const modalTitle   = document.getElementById('modalTitle');
const modalMessage = document.getElementById('modalMessage');
const modalConfirm = document.getElementById('modalConfirm');
const modalCancel  = document.getElementById('modalCancel');

// Details Modal
const detailsModal     = document.getElementById('detailsModal');
const detailsContent   = document.getElementById('detailsContent');
const inspectionsList  = document.getElementById('inspectionsList');
const detailsClose     = document.getElementById('detailsClose');
const detailsCloseBtn  = document.getElementById('detailsCloseBtn');

// Inspection Form elements
const btnAddInspection = document.getElementById('btnAddInspection');
const inspectionForm   = document.getElementById('inspectionForm');
const btnCancelInsp    = document.getElementById('btnCancelInsp');
const btnSaveInsp      = document.getElementById('btnSaveInsp');

// Sidebar toggle
const sidebar    = document.getElementById('sidebar');
const menuToggle = document.getElementById('menuToggle');

// State
let allBookings = [];

// ==================== INIT ====================
document.addEventListener('DOMContentLoaded', () => {
    fetchBookings();
    updateClock();
    setInterval(updateClock, 1000);

    searchInput.addEventListener('input', applyFilters);
    statusFilter.addEventListener('change', applyFilters);
    btnRefresh.addEventListener('click', fetchBookings);
    modalCancel.addEventListener('click', closeModal);
    detailsClose.addEventListener('click', closeDetails);
    detailsCloseBtn.addEventListener('click', closeDetails);
    
    // Tabs and search filters initialization
    initTabs();
    initCancelledBookingsHandlers();
    initPastBookingsHandlers();
    
    document.getElementById('searchActiveInput').addEventListener('input', applyActiveFilters);
    document.getElementById('btnActiveRefresh').addEventListener('click', fetchActiveBookings);
    
    document.getElementById('searchPastInput').addEventListener('input', applyPastFilters);
    document.getElementById('btnPastRefresh').addEventListener('click', loadPastBookings);
    
    document.getElementById('searchCancelledInput').addEventListener('input', applyCancelledFilters);
    document.getElementById('btnCancelledRefresh').addEventListener('click', loadCancelledBookings);
    
    btnAddInspection.addEventListener('click', () => {
        inspectionForm.classList.remove('hidden');
        btnAddInspection.classList.add('hidden');
    });

    btnCancelInsp.addEventListener('click', () => {
        inspectionForm.classList.add('hidden');
        btnAddInspection.classList.remove('hidden');
    });

    btnSaveInsp.addEventListener('click', saveInspection);

    menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));

    // Close sidebar on outside click (mobile)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 &&
            sidebar.classList.contains('open') &&
            !sidebar.contains(e.target) &&
            e.target !== menuToggle) {
            sidebar.classList.remove('open');
        }
    });
});

// ==================== CLOCK ====================
function updateClock() {
    const el = document.getElementById('headerTime');
    if (!el) return;
    const now = new Date();
    el.textContent = now.toLocaleString('en-US', {
        weekday: 'short', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
}

// ==================== FETCH BOOKINGS ====================
async function fetchBookings() {
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/bookings`);
        if (!res.ok) throw new Error(`Server error ${res.status}`);
        allBookings = await res.json();
        updateStats();
        applyFilters();
    } catch (err) {
        console.error('Failed to fetch bookings:', err);
        showToast('error', 'Failed to load bookings. Is the backend running?');
        allBookings = [];
        renderTable([]);
    } finally {
        showLoading(false);
    }
}

// ==================== RENDER TABLE ====================
function renderTable(bookings) {
    bookingsBody.innerHTML = '';

    if (bookings.length === 0) {
        bookingsTable.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }

    bookingsTable.classList.remove('hidden');
    emptyState.classList.add('hidden');

    bookings.forEach(b => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="id-cell">#${b.id}</td>
            <td class="customer-cell">${escapeHtml(b.customer_name)}</td>
            <td>${escapeHtml(b.car)}</td>
            <td>${formatRentalDates(b.start_date, b.end_date)}</td>
            <td class="price-cell">₱${formatPriceNum(b.total_price)}</td>
            <td>${statusBadge(b.status)}</td>
            <td class="actions-cell">
                <button class="btn-details" onclick="viewDetails(${b.id})" title="View full details">👝 View</button>
                ${actionButtons(b)}
            </td>
        `;
        bookingsBody.appendChild(tr);
    });
}

// ==================== FILTERS ====================
function applyFilters() {
    const search = searchInput.value.toLowerCase().trim();
    const status = statusFilter.value;

    let filtered = allBookings;

    if (status !== 'all') {
        filtered = filtered.filter(b => b.status === status);
    }

    if (search) {
        filtered = filtered.filter(b =>
            (b.customer_name || '').toLowerCase().includes(search) ||
            (b.car || '').toLowerCase().includes(search)
        );
    }

    renderTable(filtered);
}

// ==================== STATS ====================
function updateStats() {
    statTotal.textContent    = allBookings.length;
    statPending.textContent  = allBookings.filter(b => b.status === 'Pending').length;
    statApproved.textContent = allBookings.filter(b => b.status === 'Approved').length;
    statRejected.textContent = allBookings.filter(b => b.status === 'Rejected').length;

    // Animate stat numbers
    document.querySelectorAll('.stat-value').forEach(el => {
        el.style.animation = 'none';
        el.offsetHeight; // trigger reflow
        el.style.animation = 'popIn 0.35s ease';
    });
}

// ==================== APPROVE / REJECT ====================
function approveBooking(id) {
    openModal({
        icon: '✅',
        title: 'Approve Booking',
        message: `Are you sure you want to approve booking <strong>#${id}</strong>? The customer will be notified.`,
        confirmClass: 'success',
        onConfirm: () => updateBookingStatus(id, 'approve')
    });
}

function rejectBooking(id) {
    openModal({
        icon: '🚫',
        title: 'Reject Booking',
        message: `Are you sure you want to reject booking <strong>#${id}</strong>? This action cannot be undone.`,
        confirmClass: 'danger',
        onConfirm: () => updateBookingStatus(id, 'reject')
    });
}

async function updateBookingStatus(id, action) {
    closeModal();
    try {
        const res = await fetch(`${API_BASE}/bookings/${id}/${action}`, { method: 'PUT' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Operation failed');
        showToast('success', data.message || `Booking #${id} ${action}d`);
        fetchBookings(); // Refresh
    } catch (err) {
        showToast('error', err.message);
    }
}

// ==================== MODAL ====================
let _modalOnConfirm = null;

function openModal({ icon, title, message, confirmClass, onConfirm }) {
    modalIcon.textContent = icon;
    modalTitle.textContent = title;
    modalMessage.innerHTML = message;
    modalConfirm.className = `btn btn-confirm ${confirmClass || ''}`;
    _modalOnConfirm = onConfirm;
    modalConfirm.onclick = () => { if (_modalOnConfirm) _modalOnConfirm(); };
    confirmModal.classList.remove('hidden');
}

function closeModal() {
    confirmModal.classList.add('hidden');
    _modalOnConfirm = null;
}

// ==================== DETAILS MODAL ====================
async function viewDetails(id) {
    const b = allBookings.find(x => x.id === id);
    if (!b) return;

    detailsModal.dataset.bookingId = id; // Store for form
    inspectionForm.classList.add('hidden');
    btnAddInspection.classList.remove('hidden');
    const startTimeStr = b.start_time ? ` (${b.start_time})` : '';
    const endTimeStr = b.end_time ? ` (${b.end_time})` : '';
    detailsContent.innerHTML = `
        <div class="info-grid enhanced-text" role="list">
            <div class="info-item" role="listitem">
                <strong class="info-label">Customer:</strong> 
                <span class="info-value">${escapeHtml(b.customer_name)}</span>
                <button class="btn-view-profile" onclick="viewCustomerProfile(${b.user_id})" aria-label="View ${escapeHtml(b.customer_name)}'s profile">
                    👁 View Profile
                </button>
            </div>
            <div class="info-item" role="listitem"><strong class="info-label">Vehicle:</strong> <span class="info-value">${escapeHtml(b.car)}</span></div>
            <div class="info-item" role="listitem"><strong class="info-label">Period:</strong> <span class="info-value">${formatRentalDates(b.start_date, b.end_date)}${startTimeStr} to ${endTimeStr}</span></div>
            <div class="info-item" role="listitem"><strong class="info-label">Total:</strong> <span class="info-value">₱${formatPriceNum(b.total_price)}</span></div>
            <div class="info-item" role="listitem"><strong class="info-label">Status:</strong> ${statusBadge(b.status)}</div>
            <div class="info-item" role="listitem"><strong class="info-label">Payment:</strong> <span class="payment-status ${b.payment_status?.toLowerCase()}">${b.payment_status || 'Unpaid'}</span></div>
        </div>
    `;

    // Fetch inspections
    inspectionsList.innerHTML = '<div class="loading-mini">Checking for inspection photos...</div>';
    detailsModal.classList.remove('hidden');

    // Add Refund Section if needed
    if (b.payment_status === 'Refund Pending') {
        detailsContent.innerHTML += `
            <div class="refund-upload-box" style="margin-top: 15px; padding: 15px; background: rgba(239, 68, 68, 0.1); border: 1px dashed #ef4444; border-radius: 12px;">
                <h4 style="color: #ef4444; margin-bottom: 10px; font-size: 0.9rem;"><i class="fas fa-undo"></i> Action Required: Upload Refund Proof</h4>
                <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 12px;">This booking was cancelled. Upload the refund receipt to mark it as Refunded.</p>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <input type="file" id="refundProofFile" accept="image/*" style="font-size: 0.8rem; flex: 1;">
                    <button class="btn-approve" onclick="uploadRefundProof(${id})" style="background: #ef4444; border: none; padding: 8px 15px;">Submit Proof</button>
                </div>
            </div>
        `;
    } else if (b.payment_status === 'Refunded') {
        detailsContent.innerHTML += `
            <div style="margin-top: 15px; padding: 10px; background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 8px; font-size: 0.85rem; color: #10b981; display: flex; align-items: center; justify-content: space-between;">
                <span><i class="fas fa-check-circle"></i> Refund Completed</span>
                <button onclick="window.open('${API_BASE}${b.refund_proof_url}', '_blank')" style="background: none; border: none; color: #10b981; text-decoration: underline; cursor: pointer; font-size: 0.75rem;">View Receipt</button>
            </div>
        `;
    }

    try {
        const res = await fetch(`${API_BASE}/api/inspections/${id}`);
        if (!res.ok) throw new Error('Failed to load inspections');
        const inspections = await res.json();
        renderInspections(inspections);
    } catch (err) {
        inspectionsList.innerHTML = '<div class="info-msg">No inspection photos recorded for this booking yet.</div>';
    }
}

function renderInspections(list) {
    if (list.length === 0) {
        inspectionsList.innerHTML = '<div class="info-msg">No inspection photos recorded yet.</div>';
        return;
    }

    inspectionsList.innerHTML = '';
    list.forEach(insp => {
        const div = document.createElement('div');
        div.className = `inspection-card ${insp.inspection_type}`;
        
        let photosHtml = '';
        const photos = JSON.parse(insp.photos || '[]');
        photos.forEach(url => {
            photosHtml += `<img src="${API_BASE}${url}" class="insp-img" onclick="window.open('${API_BASE}${url}', '_blank')">`;
        });

        div.innerHTML = `
            <div class="insp-header">
                <span class="type-badge">${insp.inspection_type.toUpperCase()}</span>
                <span class="insp-date">${new Date(insp.created_at).toLocaleString()}</span>
            </div>
            <div class="insp-stats">
                <span>📝 ${insp.mileage} km</span>
                <span>⛽ ${insp.fuel_level}</span>
            </div>
            <div class="insp-photos">${photosHtml || '<i>No photos</i>'}</div>
            <div class="insp-notes">${insp.notes ? `<strong>Notes:</strong> ${insp.notes}` : ''}</div>
        `;
        inspectionsList.appendChild(div);
    });
}

function closeDetails() {
    detailsModal.classList.add('hidden');
}

async function saveInspection() {
    const bookingId = detailsModal.dataset.bookingId;
    const type = document.getElementById('inspType').value;
    const mileage = document.getElementById('inspMileage').value;
    const fuel = document.getElementById('inspFuel').value;
    const photos = document.getElementById('inspPhotos').files;
    const notes = document.getElementById('inspNotes').value;

    if (!mileage) {
        showToast('error', 'Please enter mileage');
        return;
    }

    const formData = new FormData();
    formData.append('booking_id', bookingId);
    formData.append('type', type);
    formData.append('mileage', mileage);
    formData.append('fuel_level', fuel);
    formData.append('notes', notes);
    formData.append('admin_id', 1); // Mock admin_id for now

    for (let i = 0; i < photos.length; i++) {
        formData.append('photos', photos[i]);
    }

    btnSaveInsp.disabled = true;
    btnSaveInsp.textContent = 'Saving...';

    try {
        const res = await fetch(`${API_BASE}/api/inspections/submit`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to save inspection');

        showToast('success', 'Inspection saved successfully');
        inspectionForm.classList.add('hidden');
        btnAddInspection.classList.remove('hidden');
        
        // Refresh the list
        viewDetails(parseInt(bookingId));
    } catch (err) {
        showToast('error', err.message);
    } finally {
        btnSaveInsp.disabled = false;
        btnSaveInsp.textContent = 'Save Inspection';
    }
}

async function uploadRefundProof(bookingId) {
    const fileInput = document.getElementById('refundProofFile');
    if (!fileInput.files.length) {
        showToast('error', 'Please select a proof image first');
        return;
    }

    const formData = new FormData();
    formData.append('booking_id', bookingId);
    formData.append('admin_id', 1); // Mock admin_id
    formData.append('proof', fileInput.files[0]);

    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Uploading...';

    try {
        const res = await fetch(`${API_BASE}/api/admin/upload-refund-proof`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Upload failed');

        showToast('success', 'Refund proof uploaded successfully!');
        fetchBookings(); // Refresh main list
        viewDetails(bookingId); // Refresh modal
    } catch (err) {
        showToast('error', err.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Submit Proof';
    }
}

// ==================== HELPERS ====================
// ==================== HELPERS ====================
function showLoading(show) {
    loadingState.classList.toggle('hidden', !show);
    if (show) {
        bookingsTable.classList.add('hidden');
        emptyState.classList.add('hidden');
    }
}

function statusBadge(status) {
    const cls = (status || 'pending').toLowerCase();
    return `<span class="status-badge status-${cls}">${status || 'Unknown'}</span>`;
}

function actionButtons(booking) {
    if (booking.status === 'Pending') {
        return `
            <button class="btn-approve" onclick="approveBooking(${booking.id})" title="Approve booking">
                ✓ Approve
            </button>
            <button class="btn-reject" onclick="rejectBooking(${booking.id})" title="Reject booking">
                ✕ Reject
            </button>
        `;
    } else if (booking.status === 'Approved') {
        return `
            <button class="btn-reject" onclick="cancelBooking(${booking.id})" style="background: #64748b;" title="Cancel approved booking">
                ✕ Cancel
            </button>
        `;
    }
    return `<span class="no-action">—</span>`;
}

function cancelBooking(id) {
    openModal({
        icon: '⚠︝',
        title: 'Cancel Approved Booking',
        message: `Are you sure you want to cancel booking <strong>#${id}</strong>? Status will be changed to Rejected and a refund will be required if already paid.`,
        confirmClass: 'danger',
        onConfirm: () => updateBookingStatus(id, 'cancel')
    });
}



function formatPriceNum(price) {
    if (price == null) return '0.00';
    return parseFloat(price).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// Pop-in animation for stats (CSS)
const styleTag = document.createElement('style');
styleTag.textContent = `@keyframes popIn { 0% { transform: scale(0.8); opacity: 0.5; } 100% { transform: scale(1); opacity: 1; } }`;
document.head.appendChild(styleTag);

// ==================== CANCELLED BOOKINGS ====================

// State for cancelled bookings
let cancelledBookings = [];
let cancelledPagination = {
    page: 1,
    page_size: 25,
    total: 0,
    total_pages: 0
};
let cancelledSortBy = 'cancellation_date_desc';

async function loadCancelledBookings() {
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
}

function renderCancelledBookingsTable() {
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
                <button class="btn-details" onclick="viewDetails(${b.id})" title="View full details">👁 View</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function updateCancelledPaginationControls() {
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
}

// Event handlers for cancelled bookings (to be attached when tab is created)
function initCancelledBookingsHandlers() {
    const sortSelect = document.getElementById('cancelledSortBy');
    const pageSizeSelect = document.getElementById('cancelledPageSize');
    const prevBtn = document.getElementById('cancelledPrevPage');
    const nextBtn = document.getElementById('cancelledNextPage');
    
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            cancelledSortBy = e.target.value;
            cancelledPagination.page = 1;
            loadCancelledBookings();
        });
    }
    
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', (e) => {
            cancelledPagination.page_size = parseInt(e.target.value);
            cancelledPagination.page = 1;
            loadCancelledBookings();
        });
    }
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (cancelledPagination.page > 1) {
                cancelledPagination.page--;
                loadCancelledBookings();
            }
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (cancelledPagination.page < cancelledPagination.total_pages) {
                cancelledPagination.page++;
                loadCancelledBookings();
            }
        });
    }
}

// ==================== CUSTOMER PROFILE PREVIEW ====================

// Helper function to get initials from a name
function getInitials(name) {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length === 1) {
        return parts[0].charAt(0).toUpperCase();
    }
    return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

async function viewCustomerProfile(userId) {
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
                    expiryElement.innerHTML += ' <span class="warning-badge">⚠️ EXPIRED</span>';
                } else if (daysUntilExpiry <= 30) {
                    expiryElement.classList.add('expiring-soon');
                    expiryElement.innerHTML += ` <span class="warning-badge expiring">⚠️ Expires in ${daysUntilExpiry} days</span>`;
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
}

// Close profile modal handler
document.getElementById('profileClose').addEventListener('click', () => {
    document.getElementById('customerProfileModal').classList.add('hidden');
});

// Close profile modal on overlay click
document.getElementById('customerProfileModal').addEventListener('click', (e) => {
    if (e.target.id === 'customerProfileModal') {
        document.getElementById('customerProfileModal').classList.add('hidden');
    }
});

// Close profile modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const profileModal = document.getElementById('customerProfileModal');
        if (profileModal && !profileModal.classList.contains('hidden')) {
            profileModal.classList.add('hidden');
        }
    }
});

// ==================== TABS SWITCHING ====================
let activeTab = 'all';

function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            tabButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.add('hidden'));
            
            btn.classList.add('active');
            const targetTab = btn.getAttribute('data-tab');
            activeTab = targetTab;
            
            const targetContent = document.getElementById(`tab${targetTab.charAt(0).toUpperCase() + targetTab.slice(1)}`);
            if (targetContent) {
                targetContent.classList.remove('hidden');
            }
            
            // Fetch/render appropriate data
            if (targetTab === 'all') {
                fetchBookings();
            } else if (targetTab === 'active') {
                fetchActiveBookings();
            } else if (targetTab === 'past') {
                loadPastBookings();
            } else if (targetTab === 'cancelled') {
                loadCancelledBookings();
            }
        });
    });
}

// ==================== ACTIVE BOOKINGS ====================
let activeBookings = [];

function fetchActiveBookings() {
    const loadingEl = document.getElementById('activeLoadingState');
    const tableEl = document.getElementById('activeBookingsTable');
    const emptyEl = document.getElementById('activeEmptyState');
    
    if (loadingEl) loadingEl.classList.remove('hidden');
    if (tableEl) tableEl.classList.add('hidden');
    if (emptyEl) emptyEl.classList.add('hidden');
    
    // Active rentals are either Approved or Active
    activeBookings = allBookings.filter(b => b.status === 'Approved' || b.status === 'Active');
    
    renderActiveBookingsTable();
    
    if (loadingEl) loadingEl.classList.add('hidden');
}

function renderActiveBookingsTable() {
    const tbody = document.getElementById('activeBookingsBody');
    const tableEl = document.getElementById('activeBookingsTable');
    const emptyEl = document.getElementById('activeEmptyState');
    
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (activeBookings.length === 0) {
        if (tableEl) tableEl.classList.add('hidden');
        if (emptyEl) emptyEl.classList.remove('hidden');
        return;
    }
    
    if (tableEl) tableEl.classList.remove('hidden');
    if (emptyEl) emptyEl.classList.add('hidden');
    
    activeBookings.forEach(b => {
        const tr = document.createElement('tr');
        tr.className = 'booking-row active-booking';
        
        const locationDisplay = b.dropoff_location && b.dropoff_location !== b.pickup_location
            ? `<span class="pickup-location" title="${escapeHtml(b.pickup_location)}">${truncateLocation(b.pickup_location)}</span>
               <span class="location-separator">➔</span>
               <span class="dropoff-location" title="${escapeHtml(b.dropoff_location)}">${truncateLocation(b.dropoff_location)}</span>`
            : `<span class="pickup-location" title="${escapeHtml(b.pickup_location || '')}">${truncateLocation(b.pickup_location)}</span>`;
        
        tr.innerHTML = `
            <td class="id-cell">#${b.id}</td>
            <td class="customer-cell">${escapeHtml(b.customer_name)}</td>
            <td>${escapeHtml(b.car)}</td>
            <td class="location-cell">
                <div class="location-info">
                    <span class="location-icon">📝</span>
                    <div class="location-text">${locationDisplay}</div>
                </div>
            </td>
            <td>${formatRentalDates(b.start_date, b.end_date)}</td>
            <td class="price-cell">₱${formatPriceNum(b.total_price)}</td>
            <td>${statusBadge(b.status)}</td>
            <td class="actions-cell">
                <button class="btn-details" onclick="viewDetails(${b.id})" title="View full details">👝 View</button>
                ${actionButtons(b)}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function applyActiveFilters() {
    const search = document.getElementById('searchActiveInput').value.toLowerCase().trim();
    if (!search) {
        renderActiveBookingsTable();
        return;
    }
    
    const filtered = activeBookings.filter(b => 
        (b.customer_name || '').toLowerCase().includes(search) ||
        (b.car || '').toLowerCase().includes(search) ||
        (b.pickup_location || '').toLowerCase().includes(search) ||
        (b.dropoff_location || '').toLowerCase().includes(search) ||
        String(b.id).includes(search)
    );
    
    const tbody = document.getElementById('activeBookingsBody');
    const tableEl = document.getElementById('activeBookingsTable');
    const emptyEl = document.getElementById('activeEmptyState');
    
    tbody.innerHTML = '';
    
    if (filtered.length === 0) {
        tableEl.classList.add('hidden');
        emptyEl.classList.remove('hidden');
        return;
    }
    
    tableEl.classList.remove('hidden');
    emptyEl.classList.add('hidden');
    
    filtered.forEach(b => {
        const tr = document.createElement('tr');
        tr.className = 'booking-row active-booking';
        
        const locationDisplay = b.dropoff_location && b.dropoff_location !== b.pickup_location
            ? `<span class="pickup-location" title="${escapeHtml(b.pickup_location)}">${truncateLocation(b.pickup_location)}</span>
               <span class="location-separator">➔</span>
               <span class="dropoff-location" title="${escapeHtml(b.dropoff_location)}">${truncateLocation(b.dropoff_location)}</span>`
            : `<span class="pickup-location" title="${escapeHtml(b.pickup_location || '')}">${truncateLocation(b.pickup_location)}</span>`;
            
        tr.innerHTML = `
            <td class="id-cell">#${b.id}</td>
            <td class="customer-cell">${escapeHtml(b.customer_name)}</td>
            <td>${escapeHtml(b.car)}</td>
            <td class="location-cell">
                <div class="location-info">
                    <span class="location-icon">📝</span>
                    <div class="location-text">${locationDisplay}</div>
                </div>
            </td>
            <td>${formatRentalDates(b.start_date, b.end_date)}</td>
            <td class="price-cell">₱${formatPriceNum(b.total_price)}</td>
            <td>${statusBadge(b.status)}</td>
            <td class="actions-cell">
                <button class="btn-details" onclick="viewDetails(${b.id})" title="View full details">👝 View</button>
                ${actionButtons(b)}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// ==================== PAST BOOKINGS ====================
let pastBookings = [];
let pastPagination = {
    page: 1,
    page_size: 25,
    total: 0,
    total_pages: 0
};
let pastSortBy = 'completion_date_desc';

async function loadPastBookings() {
    const loadingEl = document.getElementById('loadingPastState');
    const tableEl = document.getElementById('pastBookingsTable');
    const emptyEl = document.getElementById('emptyPastState');
    
    if (loadingEl) loadingEl.classList.remove('hidden');
    if (tableEl) tableEl.classList.add('hidden');
    if (emptyEl) emptyEl.classList.add('hidden');
    
    try {
        const params = new URLSearchParams({
            page: pastPagination.page,
            page_size: pastPagination.page_size,
            sort_by: pastSortBy
        });
        
        const res = await fetch(`${API_BASE}/api/bookings/past?${params}`);
        if (!res.ok) throw new Error(`Server error ${res.status}`);
        
        const data = await res.json();
        pastBookings = data.bookings || [];
        pastPagination = data.pagination || {
            page: data.page || 1,
            page_size: data.page_size || 25,
            total: data.total || 0,
            total_pages: data.total_pages || 1
        };
        
        renderPastBookingsTable();
        updatePastPaginationControls();
    } catch (err) {
        console.error('Failed to fetch past bookings:', err);
        showToast('error', 'Failed to load past bookings');
        pastBookings = [];
        renderPastBookingsTable();
    } finally {
        if (loadingEl) loadingEl.classList.add('hidden');
    }
}

function renderPastBookingsTable() {
    const tbody = document.getElementById('pastBookingsBody');
    const tableEl = document.getElementById('pastBookingsTable');
    const emptyEl = document.getElementById('emptyPastState');
    
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (pastBookings.length === 0) {
        if (tableEl) tableEl.classList.add('hidden');
        if (emptyEl) emptyEl.classList.remove('hidden');
        return;
    }
    
    if (tableEl) tableEl.classList.remove('hidden');
    if (emptyEl) emptyEl.classList.add('hidden');
    
    pastBookings.forEach(b => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="id-cell">#${b.id}</td>
            <td class="customer-cell">${escapeHtml(b.customer_name)}</td>
            <td>${escapeHtml(b.car)}</td>
            <td>${formatRentalDates(b.start_date, b.end_date)}</td>
            <td>${formatDate(b.completion_date)}</td>
            <td class="price-cell">₱${formatPriceNum(b.total_price)}</td>
            <td class="actions-cell">
                <button class="btn-details" onclick="viewDetails(${b.id})" title="View full details">👝 View</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function updatePastPaginationControls() {
    const pageInfo = document.getElementById('pastPageInfo');
    const prevBtn = document.getElementById('btnPastPrev');
    const nextBtn = document.getElementById('btnPastNext');
    
    if (pageInfo) {
        pageInfo.textContent = `Page ${pastPagination.page} of ${pastPagination.total_pages || 1}`;
    }
    
    if (prevBtn) {
        prevBtn.disabled = pastPagination.page <= 1;
    }
    
    if (nextBtn) {
        nextBtn.disabled = pastPagination.page >= pastPagination.total_pages;
    }
}

function applyPastFilters() {
    const search = document.getElementById('searchPastInput').value.toLowerCase().trim();
    if (!search) {
        renderPastBookingsTable();
        return;
    }
    
    const filtered = pastBookings.filter(b => 
        (b.customer_name || '').toLowerCase().includes(search) ||
        (b.car || '').toLowerCase().includes(search) ||
        String(b.id).includes(search)
    );
    
    const tbody = document.getElementById('pastBookingsBody');
    const tableEl = document.getElementById('pastBookingsTable');
    const emptyEl = document.getElementById('emptyPastState');
    
    tbody.innerHTML = '';
    
    if (filtered.length === 0) {
        tableEl.classList.add('hidden');
        emptyEl.classList.remove('hidden');
        return;
    }
    
    tableEl.classList.remove('hidden');
    emptyEl.classList.add('hidden');
    
    filtered.forEach(b => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="id-cell">#${b.id}</td>
            <td class="customer-cell">${escapeHtml(b.customer_name)}</td>
            <td>${escapeHtml(b.car)}</td>
            <td>${formatRentalDates(b.start_date, b.end_date)}</td>
            <td>${formatDate(b.completion_date)}</td>
            <td class="price-cell">₱${formatPriceNum(b.total_price)}</td>
            <td class="actions-cell">
                <button class="btn-details" onclick="viewDetails(${b.id})" title="View full details">👝 View</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function initPastBookingsHandlers() {
    const sortSelect = document.getElementById('sortPastBy');
    const pageSizeSelect = document.getElementById('pageSizePast');
    const prevBtn = document.getElementById('btnPastPrev');
    const nextBtn = document.getElementById('btnPastNext');
    
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            pastSortBy = e.target.value;
            pastPagination.page = 1;
            loadPastBookings();
        });
    }
    
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', (e) => {
            pastPagination.page_size = parseInt(e.target.value);
            pastPagination.page = 1;
            loadPastBookings();
        });
    }
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (pastPagination.page > 1) {
                pastPagination.page--;
                loadPastBookings();
            }
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (pastPagination.page < pastPagination.total_pages) {
                pastPagination.page++;
                loadPastBookings();
            }
        });
    }
}

// ==================== CANCELLED BOOKINGS SEARCH ====================
function applyCancelledFilters() {
    const search = document.getElementById('searchCancelledInput').value.toLowerCase().trim();
    if (!search) {
        renderCancelledBookingsTable();
        return;
    }
    
    const filtered = cancelledBookings.filter(b => 
        (b.customer_name || '').toLowerCase().includes(search) ||
        (b.car || '').toLowerCase().includes(search) ||
        (b.cancellation_reason || '').toLowerCase().includes(search) ||
        String(b.id).includes(search)
    );
    
    const tbody = document.getElementById('cancelledBookingsBody');
    const tableEl = document.getElementById('cancelledBookingsTable');
    const emptyEl = document.getElementById('cancelledEmptyState');
    
    tbody.innerHTML = '';
    
    if (filtered.length === 0) {
        tableEl.classList.add('hidden');
        emptyEl.classList.remove('hidden');
        return;
    }
    
    tableEl.classList.remove('hidden');
    emptyEl.classList.add('hidden');
    
    filtered.forEach(b => {
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
                <button class="btn-details" onclick="viewDetails(${b.id})" title="View full details">👝 View</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}


