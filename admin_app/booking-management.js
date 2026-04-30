/* ============================================================
   Autoride Admin — Booking Management JS
   Handles fetching, filtering, approving, and rejecting bookings
   ============================================================ */

const API_BASE = "/api";

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
            <td class="price-cell">₱${formatPrice(b.total_price)}</td>
            <td>${statusBadge(b.status)}</td>
            <td class="actions-cell">
                <button class="btn-details" onclick="viewDetails(${b.id})" title="View full details">👁 View</button>
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
    detailsContent.innerHTML = `
        <div class="info-grid">
            <div class="info-item"><strong>Customer:</strong> ${escapeHtml(b.customer_name)}</div>
            <div class="info-item"><strong>Vehicle:</strong> ${escapeHtml(b.car)}</div>
            <div class="info-item"><strong>Period:</strong> ${formatRentalDates(b.start_date, b.end_date)}</div>
            <div class="info-item"><strong>Total:</strong> ₱${formatPrice(b.total_price)}</div>
            <div class="info-item"><strong>Status:</strong> ${statusBadge(b.status)}</div>
            <div class="info-item"><strong>Payment:</strong> <span class="payment-status ${b.payment_status?.toLowerCase()}">${b.payment_status || 'Unpaid'}</span></div>
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
                <span>📍 ${insp.mileage} km</span>
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

// ==================== TOAST ====================
let _toastTimeout = null;

function showToast(type, message) {
    const toast = document.getElementById('toast');
    const toastIcon = document.getElementById('toastIcon');
    const toastMsg  = document.getElementById('toastMsg');

    toast.className = `toast ${type}`;
    toastIcon.textContent = type === 'success' ? '✅' : '❌';
    toastMsg.textContent = message;

    clearTimeout(_toastTimeout);
    _toastTimeout = setTimeout(() => toast.classList.add('hidden'), 4000);
}

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
        icon: '⚠️',
        title: 'Cancel Approved Booking',
        message: `Are you sure you want to cancel booking <strong>#${id}</strong>? Status will be changed to Rejected and a refund will be required if already paid.`,
        confirmClass: 'danger',
        onConfirm: () => updateBookingStatus(id, 'cancel')
    });
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatRentalDates(startDate, endDate) {
    return `${formatDate(startDate)} - ${formatDate(endDate)}`;
}

function formatPrice(price) {
    if (price == null) return '0.00';
    return parseFloat(price).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Pop-in animation for stats (CSS)
const styleTag = document.createElement('style');
styleTag.textContent = `@keyframes popIn { 0% { transform: scale(0.8); opacity: 0.5; } 100% { transform: scale(1); opacity: 1; } }`;
document.head.appendChild(styleTag);
