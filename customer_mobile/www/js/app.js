/**
 * Autoride Customer Mobile App — Main Application Script
 * All screens, API calls, and business logic live here.
 * Import utils.js for pure utility functions.
 */

// ??? CONFIG ??????????????????????????????????????????????????????????????????
const API_BASE = 'https://autoride-booking-system.vercel.app';

// ??? IMPORTS ?????????????????????????????????????????????????????????????????
import {
  isGmailAddress, isBlank, normalizePhone, isValidLastFour,
  formatPHP, validateUploadFile, validateDateRange,
  calculateBookingPrice, sanitizeInput
} from './utils.js';

// ??? STATE ???????????????????????????????????????????????????????????????????
let currentUser = { id: null, fullName: '', isVerified: 0 };
let allVehicles = [];
let currentVehicleDetail = null;
let activeBookingId = null;
let activeBookingData = null;
let gpsRefreshInterval = null;
let profilePicBlob = null;
let licenseBlob = null;
let inspectionPhotos = [];
let chatHistory = [];
let pendingOtpEmail = '';
let pendingOtpPhone = '';
let appSettings = { mileage_limit: '250', long_term_discount_days: '7', long_term_discount_percent: '10', rental_terms: '' };
let couponData = null;
let selectedAddons = [];
let selectedInsurance = { type: 'Basic', price: 0 };
let bookingFormVehicle = null;

// ??? CAPACITOR PLUGINS ???????????????????????????????????????????????????????
const { Preferences } = window.Capacitor?.Plugins || {};
const { Camera, CameraResultType, CameraSource } = window.Capacitor?.Plugins || {};

// ??? SESSION ?????????????????????????????????????????????????????????????????
const Session = {
  async save(user) {
    if (Preferences) {
      await Preferences.set({ key: 'user', value: JSON.stringify(user) });
    } else {
      localStorage.setItem('user', JSON.stringify(user));
    }
  },
  async load() {
    try {
      if (Preferences) {
        const { value } = await Preferences.get({ key: 'user' });
        return value ? JSON.parse(value) : null;
      }
      const v = localStorage.getItem('user');
      return v ? JSON.parse(v) : null;
    } catch { return null; }
  },
  async clear() {
    if (Preferences) {
      await Preferences.remove({ key: 'user' });
    } else {
      localStorage.removeItem('user');
    }
  }
};

// ??? NOTIFICATIONS STORE ?????????????????????????????????????????????????????
const NotifStore = {
  async getAll() {
    try {
      if (Preferences) {
        const { value } = await Preferences.get({ key: 'notifications' });
        return value ? JSON.parse(value) : [];
      }
      const v = localStorage.getItem('notifications');
      return v ? JSON.parse(v) : [];
    } catch { return []; }
  },
  async add(msg) {
    const all = await this.getAll();
    all.unshift({ msg, ts: new Date().toISOString(), read: false });
    const store = Preferences || { set: (o) => localStorage.setItem(o.key, o.value) };
    await store.set({ key: 'notifications', value: JSON.stringify(all.slice(0, 50)) });
    updateNotifBadge();
  },
  async markAllRead() {
    const all = await this.getAll();
    all.forEach(n => n.read = true);
    const store = Preferences || { set: (o) => localStorage.setItem(o.key, o.value) };
    await store.set({ key: 'notifications', value: JSON.stringify(all) });
    updateNotifBadge();
  }
};

// ??? API HELPERS ?????????????????????????????????????????????????????????????
async function apiCall(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options
    });
    const data = await res.json();
    if (!res.ok) {
      if ((res.status === 401 || res.status === 403) && !data.verification_required && !data.reason) {
        await Session.clear();
        showPage('page-login');
      }
      throw { status: res.status, message: data.error || data.message || 'Request failed' };
    }
    return data;
  } catch (err) {
    if (err.status) throw err;
    throw { status: 0, message: 'Network error. Please check your connection.' };
  }
}

async function uploadFile(endpoint, formData) {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok) throw { status: res.status, message: data.error || 'Upload failed' };
    return data;
  } catch (err) {
    if (err.status) throw err;
    throw { status: 0, message: 'Network error during upload.' };
  }
}

// ??? UI HELPERS ??????????????????????????????????????????????????????????????
function showLoading(show) {
  document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'info') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = message;
  document.body.appendChild(t);
  requestAnimationFrame(() => { t.classList.add('show'); });
  setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 300); }, 3000);
}

const AUTH_PAGES = ['page-splash','page-login','page-register','page-otp-verify','page-phone-login'];
const MAIN_PAGES = ['page-home','page-vehicles','page-bookings','page-profile','page-more'];
const NAV_MAP = { 'page-home':'nav-home','page-vehicles':'nav-vehicles','page-bookings':'nav-bookings','page-profile':'nav-profile','page-more':'nav-more' };

function showPage(id) {
  // Hide all pages
  document.querySelectorAll('.page, .auth-page').forEach(p => {
    p.classList.remove('active');
    p.style.display = 'none';
  });
  // Show target
  const target = document.getElementById(id);
  if (!target) return;
  if (target.classList.contains('auth-page')) {
    target.style.display = 'flex';
  } else {
    target.style.display = 'block';
  }
  target.classList.add('active');
  // Bottom nav
  const nav = document.getElementById('bottomNav');
  if (MAIN_PAGES.includes(id)) {
    nav.classList.remove('hidden');
    Object.values(NAV_MAP).forEach(n => document.getElementById(n)?.classList.remove('active'));
    if (NAV_MAP[id]) document.getElementById(NAV_MAP[id])?.classList.add('active');
  } else {
    nav.classList.add('hidden');
  }
  // Trigger page load hooks
  if (id === 'page-home') loadHome();
  if (id === 'page-vehicles') loadVehicles();
  if (id === 'page-bookings') loadBookings();
  if (id === 'page-profile') loadProfile();
}

function showOverlay(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.add('active');
  el.style.display = 'block';
  // Trigger overlay load hooks
  if (id === 'page-notifications') loadNotifications();
  if (id === 'page-favorites') loadFavorites();
  if (id === 'page-saved-payments') loadSavedPayments();
  if (id === 'page-license-upload') openLicenseUpload();
  if (id === 'page-split-payment') loadSplitPayment();
  if (id === 'page-support') loadSupport();
  if (id === 'page-chatbot') loadChatbot();
  if (id === 'page-newsletter') loadNewsletter();
}

function closeOverlay(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.remove('active');
  el.style.display = 'none';
  if (id === 'page-gps-map') stopGpsPolling();
}

function statusPill(status) {
  const map = {
    'Pending':'pill-pending','Confirmed':'pill-confirmed','Approved':'pill-approved',
    'Picked Up':'pill-picked-up','Completed':'pill-completed','Cancelled':'pill-cancelled',
    'Rejected':'pill-rejected','Unpaid':'pill-unpaid','Partially Paid':'pill-partially-paid',
    'Paid':'pill-paid','Refund Pending':'pill-refund-pending','Refunded':'pill-refunded'
  };
  return `<span class="pill ${map[status]||''}">${status||'—'}</span>`;
}

async function updateNotifBadge() {
  const all = await NotifStore.getAll();
  const unread = all.filter(n => !n.read).length;
  const badge = document.getElementById('notifBadge');
  if (badge) {
    badge.textContent = unread;
    badge.classList.toggle('hidden', unread === 0);
  }
}

// ??? STARTUP ?????????????????????????????????????????????????????????????????
async function initApp() {
  showPage('page-splash');
  try {
    const user = await Session.load();
    if (user && user.id) {
      currentUser = user;
      // Fetch public settings
      try {
        const s = await apiCall('/public/settings');
        Object.assign(appSettings, s);
      } catch {}
      showPage('page-home');
    } else {
      showPage('page-login');
    }
  } catch {
    showPage('page-login');
  }
  updateNotifBadge();
}

document.addEventListener('DOMContentLoaded', initApp);
document.addEventListener('deviceready', initApp);

// ??? AUTH: LOGIN ?????????????????????????????????????????????????????????????
async function doLogin() {
  const email = sanitizeInput(document.getElementById('loginEmail').value.trim());
  const password = document.getElementById('loginPassword').value;
  document.getElementById('loginEmailErr').textContent = '';
  document.getElementById('loginPasswordErr').textContent = '';
  document.getElementById('loginErr').textContent = '';

  if (isBlank(email)) { document.getElementById('loginEmailErr').textContent = 'Email is required.'; return; }
  if (!isGmailAddress(email)) { document.getElementById('loginEmailErr').textContent = 'Only @gmail.com emails are allowed.'; return; }
  if (isBlank(password)) { document.getElementById('loginPasswordErr').textContent = 'Password is required.'; return; }

  showLoading(true);
  try {
    const data = await apiCall('/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    currentUser = { id: data.user_id, fullName: data.full_name, isVerified: data.is_verified || 0 };
    await Session.save(currentUser);
    try { const s = await apiCall('/public/settings'); Object.assign(appSettings, s); } catch {}
    showPage('page-home');
  } catch (err) {
    if (err.status === 403 && err.message === 'Account Frozen') {
      document.getElementById('loginErr').textContent = err.reason || 'Your account has been suspended.';
    } else if (err.status === 403) {
      pendingOtpEmail = email;
      document.getElementById('otpEmailDisplay').textContent = email;
      showPage('page-otp-verify');
    } else {
      document.getElementById('loginErr').textContent = err.message || 'Invalid credentials.';
    }
  } finally { showLoading(false); }
}

async function doGoogleLogin() {
  showToast('Google Sign-In requires native Capacitor setup. Use email login for now.', 'info');
}

async function doLogout() {
  await Session.clear();
  currentUser = { id: null, fullName: '', isVerified: 0 };
  showPage('page-login');
}

// ??? AUTH: REGISTER ??????????????????????????????????????????????????????????
async function doRegister() {
  const name = sanitizeInput(document.getElementById('regName').value.trim());
  const email = sanitizeInput(document.getElementById('regEmail').value.trim());
  const password = document.getElementById('regPassword').value;
  ['regNameErr','regEmailErr','regPasswordErr','regErr'].forEach(id => document.getElementById(id).textContent = '');

  if (isBlank(name)) { document.getElementById('regNameErr').textContent = 'Full name is required.'; return; }
  if (!isGmailAddress(email)) { document.getElementById('regEmailErr').textContent = 'Only @gmail.com emails are allowed for registration.'; return; }
  if (isBlank(password) || password.length < 8) { document.getElementById('regPasswordErr').textContent = 'Password must be at least 8 characters.'; return; }

  showLoading(true);
  try {
    await apiCall('/register', { method: 'POST', body: JSON.stringify({ name, email, password }) });
    pendingOtpEmail = email;
    document.getElementById('otpEmailDisplay').textContent = email;
    showToast('Verification code sent to your email!', 'success');
    showPage('page-otp-verify');
  } catch (err) {
    if (err.status === 409) {
      document.getElementById('regEmailErr').textContent = 'Email already registered.';
    } else {
      document.getElementById('regErr').textContent = err.message || 'Registration failed.';
    }
  } finally { showLoading(false); }
}

// ??? AUTH: OTP ???????????????????????????????????????????????????????????????
function otpNext(el, nextIdx) {
  if (el.value.length >= 1 && nextIdx >= 0) {
    document.getElementById(`otp${nextIdx}`)?.focus();
  }
}

function getOtpValue(prefix) {
  return [0,1,2,3,4,5].map(i => document.getElementById(`${prefix}${i}`)?.value || '').join('');
}

async function doVerifyEmail() {
  const otp = getOtpValue('otp');
  document.getElementById('otpErr').textContent = '';
  if (otp.length < 6) { document.getElementById('otpErr').textContent = 'Please enter the full 6-digit code.'; return; }
  showLoading(true);
  try {
    await apiCall('/auth/verify-email', { method: 'POST', body: JSON.stringify({ email: pendingOtpEmail, otp }) });
    showToast('Email verified! Please log in.', 'success');
    showPage('page-login');
  } catch (err) {
    document.getElementById('otpErr').textContent = err.message || 'Invalid or expired verification code.';
  } finally { showLoading(false); }
}

async function resendOtp() {
  if (!pendingOtpEmail) return;
  showToast('Resending code...', 'info');
  try {
    await apiCall('/register', { method: 'POST', body: JSON.stringify({ email: pendingOtpEmail, name: 'resend', password: 'resend' }) });
  } catch {}
  showToast('A new code has been sent.', 'success');
}

// ??? AUTH: PHONE OTP ?????????????????????????????????????????????????????????
function otpNextSms(el, nextIdx) {
  if (el.value.length >= 1 && nextIdx >= 0) {
    document.getElementById(`smsOtp${nextIdx}`)?.focus();
  }
}

async function doRequestOtp() {
  const raw = document.getElementById('phoneNumber').value.trim();
  document.getElementById('phoneErr').textContent = '';
  if (isBlank(raw)) { document.getElementById('phoneErr').textContent = 'Phone number is required.'; return; }
  const phone = normalizePhone(raw);
  pendingOtpPhone = phone;
  showLoading(true);
  try {
    await apiCall('/auth/request-otp', { method: 'POST', body: JSON.stringify({ phone }) });
    document.getElementById('phoneStep1').classList.add('hidden');
    document.getElementById('phoneStep2').classList.remove('hidden');
    showToast('OTP sent to your phone!', 'success');
  } catch (err) {
    document.getElementById('phoneErr').textContent = err.message || 'Failed to send OTP.';
  } finally { showLoading(false); }
}

async function doVerifyPhone() {
  const otp = getOtpValue('smsOtp');
  document.getElementById('smsOtpErr').textContent = '';
  if (otp.length < 6) { document.getElementById('smsOtpErr').textContent = 'Please enter the full 6-digit code.'; return; }
  showLoading(true);
  try {
    const data = await apiCall('/auth/verify-otp', { method: 'POST', body: JSON.stringify({ phone: pendingOtpPhone, otp }) });
    currentUser = { id: data.user_id, fullName: data.full_name, isVerified: 0 };
    await Session.save(currentUser);
    showPage('page-home');
  } catch (err) {
    document.getElementById('smsOtpErr').textContent = err.message || 'Invalid or expired OTP.';
  } finally { showLoading(false); }
}

// ??? HOME ????????????????????????????????????????????????????????????????????
async function loadHome() {
  document.getElementById('homeUserName').textContent = currentUser.fullName || 'there';
  try {
    const pts = await apiCall(`/user/points?user_id=${currentUser.id}`);
    document.getElementById('homePoints').textContent = pts.points || 0;
    currentUser.loyaltyPoints = pts.points || 0;
  } catch {}
  try {
    const bookings = await apiCall(`/user-bookings?user_id=${currentUser.id}`);
    const recent = bookings.slice(0, 3);
    const el = document.getElementById('recentBookings');
    if (!recent.length) {
      el.innerHTML = '<div class="empty-state"><i class="fas fa-calendar-times"></i><p>No bookings yet</p></div>';
    } else {
      el.innerHTML = recent.map(b => `
        <div class="booking-item" onclick="openBookingDetail(${b.id})">
          <h4>${b.brand || ''} ${b.model || ''}</h4>
          <div class="booking-meta">${b.start_date} ? ${b.end_date}</div>
          <div class="booking-footer">${statusPill(b.status)} ${statusPill(b.payment_status)}</div>
        </div>`).join('');
    }
  } catch {}
  updateNotifBadge();
}

// ??? VEHICLES ????????????????????????????????????????????????????????????????
async function loadVehicles() {
  showLoading(true);
  try {
    const data = await apiCall('/vehicles/categories');
    allVehicles = data;
    renderVehicles(data);
  } catch (err) {
    document.getElementById('vehicleGrid').innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${err.message}</p></div>`;
  } finally { showLoading(false); }
}

function renderVehicles(list) {
  const grid = document.getElementById('vehicleGrid');
  const available = list.filter(v => (v.available_units || 0) > 0);
  if (!available.length) {
    grid.innerHTML = '<div class="empty-state"><i class="fas fa-car"></i><p>No vehicles available</p></div>';
    return;
  }
  grid.innerHTML = available.map(v => `
    <div class="vehicle-card" onclick="openVehicleDetail(${v.id || v.representative_id})">
      <div class="vehicle-img-wrap">
        <img src="${v.vehicle_image ? API_BASE + '/' + v.vehicle_image : 'https://via.placeholder.com/400x200?text=No+Image'}" alt="${v.brand} ${v.model}" onerror="this.src='https://via.placeholder.com/400x200?text=No+Image'">
        <span class="badge-available">${v.available_units || 0} available</span>
        <button class="fav-btn" style="position:absolute;top:8px;left:10px;" onclick="event.stopPropagation();toggleFav(${v.id || v.representative_id},this)">
          <i class="fas fa-heart"></i>
        </button>
      </div>
      <div class="vehicle-info">
        <h3>${v.brand} ${v.model}</h3>
        <div class="vehicle-meta"><i class="fas fa-car-side"></i> ${v.vehicle_type || '—'} &nbsp; <i class="fas fa-cog"></i> ${v.transmission || '—'} &nbsp; <i class="fas fa-gas-pump"></i> ${v.fuel_type || '—'}</div>
        <div class="vehicle-meta"><i class="fas fa-users"></i> ${v.seats || '—'} seats</div>
        <div class="vehicle-location"><i class="fas fa-map-marker-alt"></i> ${v.location || '—'}</div>
        <div class="vehicle-rate">${formatPHP(v.daily_rate)} <span>/ day</span></div>
      </div>
    </div>`).join('');
}

function filterVehicles(filter, chipEl) {
  document.querySelectorAll('#vehicleFilters .chip').forEach(c => c.classList.remove('active'));
  chipEl.classList.add('active');
  if (filter === 'all') { renderVehicles(allVehicles); return; }
  const filtered = allVehicles.filter(v =>
    v.vehicle_type === filter || v.transmission === filter || v.fuel_type === filter
  );
  renderVehicles(filtered);
}

async function toggleFav(vehicleId, btn) {
  if (!currentUser.id) { showToast('Please log in first.', 'error'); return; }
  try {
    const data = await apiCall('/toggle-favorite', { method: 'POST', body: JSON.stringify({ user_id: currentUser.id, vehicle_id: vehicleId }) });
    btn.classList.toggle('active', data.is_favorite);
    showToast(data.message, 'success');
  } catch (err) { showToast(err.message, 'error'); }
}

async function openVehicleDetail(vehicleId) {
  showLoading(true);
  try {
    const v = await apiCall(`/vehicle/${vehicleId}?user_id=${currentUser.id || ''}`);
    currentVehicleDetail = v;
    renderVehicleDetail(v);
    showOverlay('page-vehicle-detail');
  } catch (err) { showToast(err.message, 'error'); }
  finally { showLoading(false); }
}

function renderVehicleDetail(v) {
  const ltDays = parseInt(appSettings.long_term_discount_days) || 7;
  const ltPct = parseInt(appSettings.long_term_discount_percent) || 10;
  const mileage = appSettings.mileage_limit || '250';
  const canBook = currentUser.isVerified === 2 || currentUser.isVerified === '2';
  const el = document.getElementById('vehicleDetailContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-vehicle-detail')"><i class="fas fa-arrow-left"></i></button>
      <h2>${v.brand} ${v.model}</h2>
      <button class="fav-btn ${v.is_favorite ? 'active' : ''}" onclick="toggleFav(${v.id},this)"><i class="fas fa-heart"></i></button>
    </div>
    <div class="gallery-scroll">
      ${(v.gallery && v.gallery.length ? v.gallery : [v.vehicle_image]).filter(Boolean).map(img =>
        `<img class="gallery-img" src="${API_BASE}/${img}" onerror="this.src='https://via.placeholder.com/200x130?text=No+Image'" alt="Vehicle">`
      ).join('')}
    </div>
    <div class="scroll-content">
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <div class="vehicle-rate">${formatPHP(v.daily_rate)} <span>/ day</span></div>
          <div style="color:#ffc107;font-size:0.9rem;">? ${(v.avg_rating||0).toFixed(1)} (${(v.reviews||[]).length})</div>
        </div>
        <div class="vehicle-meta"><i class="fas fa-car-side"></i> ${v.vehicle_type||'—'} &nbsp; <i class="fas fa-cog"></i> ${v.transmission||'—'} &nbsp; <i class="fas fa-gas-pump"></i> ${v.fuel_type||'—'} &nbsp; <i class="fas fa-users"></i> ${v.seats||'—'} seats</div>
        <div class="vehicle-meta" style="margin-top:6px;"><i class="fas fa-map-marker-alt"></i> ${v.location||'—'}</div>
        ${v.plate_number ? `<div class="vehicle-meta"><i class="fas fa-id-card"></i> ${v.plate_number}</div>` : ''}
        <div style="background:#fff3cd;border-radius:var(--radius-sm);padding:10px;margin-top:10px;font-size:0.8rem;color:#856404;">
          <i class="fas fa-tag"></i> Rentals of ${ltDays}+ days get a <strong>${ltPct}% discount</strong>!
        </div>
        <div style="background:#e8f4fd;border-radius:var(--radius-sm);padding:10px;margin-top:8px;font-size:0.8rem;color:#084298;">
          <i class="fas fa-tachometer-alt"></i> Daily mileage limit: <strong>${mileage} km</strong>
        </div>
      </div>
      ${(v.pickup_instructions||[]).length ? `
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:10px;">Pickup Requirements</h4>
        ${v.pickup_instructions.map(i => `<div style="font-size:0.875rem;padding:6px 0;border-bottom:1px solid var(--border);"><i class="fas fa-check-circle" style="color:var(--success);margin-right:8px;"></i>${i}</div>`).join('')}
      </div>` : ''}
      ${canBook
        ? `<button class="btn-primary" onclick="openBookingForm(${v.id})"><i class="fas fa-calendar-plus"></i> Book Now</button>`
        : `<div style="background:#f8d7da;border-radius:var(--radius-sm);padding:12px;text-align:center;font-size:0.875rem;color:#842029;margin-bottom:12px;"><i class="fas fa-lock"></i> License verification required before booking.</div>`
      }
      <div style="margin-top:20px;">
        <h4 style="font-weight:700;margin-bottom:12px;">Customer Reviews</h4>
        ${(v.reviews||[]).length ? v.reviews.map(r => `
          <div class="review-item">
            <div class="reviewer">
              ${r.profile_picture ? `<img src="${r.profile_picture}" alt="">` : `<div class="avatar-placeholder">${(r.full_name||'?')[0]}</div>`}
              <div><strong style="font-size:0.875rem;">${r.full_name||'Customer'}</strong><br><span class="review-stars">${'?'.repeat(r.rating||0)}${'?'.repeat(5-(r.rating||0))}</span></div>
            </div>
            ${r.comment ? `<p style="font-size:0.875rem;color:var(--text-secondary);">${r.comment}</p>` : ''}
            <small style="color:var(--text-muted);">${r.created_at ? new Date(r.created_at).toLocaleDateString() : ''}</small>
          </div>`).join('')
          : '<div class="empty-state" style="padding:20px 0;"><i class="fas fa-star"></i><p>No reviews yet</p></div>'
        }
      </div>
    </div>`;
}

// ??? BOOKING FORM ????????????????????????????????????????????????????????????
function openBookingForm(vehicleId) {
  bookingFormVehicle = currentVehicleDetail;
  couponData = null;
  selectedAddons = [];
  selectedInsurance = { type: 'Basic', price: 0 };
  const today = new Date().toISOString().split('T')[0];
  const el = document.getElementById('bookingFormContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-booking-form')"><i class="fas fa-arrow-left"></i></button>
      <h2>Book ${bookingFormVehicle?.brand} ${bookingFormVehicle?.model}</h2>
    </div>
    <div class="scroll-content">
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:14px;">Rental Period</h4>
        <div class="form-group"><label>Start Date</label><input type="date" id="bfStartDate" min="${today}" onchange="updateBookingPrice()"><span class="field-error" id="bfStartErr"></span></div>
        <div class="form-group"><label>End Date</label><input type="date" id="bfEndDate" min="${today}" onchange="updateBookingPrice()"><span class="field-error" id="bfEndErr"></span></div>
      </div>
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:14px;">Pickup Location</h4>
        <div class="form-group"><label>Province</label><input type="text" id="bfPickupProvince" placeholder="e.g. Metro Manila"></div>
        <div class="form-group"><label>Municipality / City</label><input type="text" id="bfPickupMunicipality" placeholder="e.g. Quezon City"></div>
        <div class="form-group"><label>Barangay</label><input type="text" id="bfPickupBarangay" placeholder="e.g. Diliman"></div>
      </div>
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:14px;">Return Location</h4>
        <div class="form-group"><label>Province</label><input type="text" id="bfReturnProvince" placeholder="e.g. Metro Manila"></div>
        <div class="form-group"><label>Municipality / City</label><input type="text" id="bfReturnMunicipality" placeholder="e.g. Quezon City"></div>
        <div class="form-group"><label>Barangay</label><input type="text" id="bfReturnBarangay" placeholder="e.g. Diliman"></div>
      </div>
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:14px;">Rental Type</h4>
        <div class="toggle-group">
          <button id="btnSelfDrive" class="active" onclick="setRentalType('Self-Drive')">Self-Drive</button>
          <button id="btnWithDriver" onclick="setRentalType('With Driver')">With Driver</button>
        </div>
        <input type="hidden" id="bfRentalType" value="Self-Drive">
      </div>
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:14px;">Insurance</h4>
        <div class="option-card selected" onclick="selectInsurance('Basic',0,this)"><input type="radio" name="insurance" checked> <div><strong>Basic</strong><br><small style="color:var(--text-secondary);">Included — PHP 0.00</small></div></div>
        <div class="option-card" onclick="selectInsurance('Comprehensive',500,this)"><input type="radio" name="insurance"> <div><strong>Comprehensive</strong><br><small style="color:var(--text-secondary);">PHP 500.00 / booking</small></div></div>
      </div>
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:14px;">Payment Type</h4>
        <div class="toggle-group">
          <button id="btnFull" class="active" onclick="setPaymentType('Full')">Full Payment</button>
          <button id="btnDown" onclick="setPaymentType('Downpayment')">20% Downpayment</button>
        </div>
        <input type="hidden" id="bfPaymentType" value="Full">
      </div>
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:14px;">Coupon Code</h4>
        <div class="coupon-row">
          <input type="text" id="bfCoupon" placeholder="Enter coupon code">
          <button onclick="applyCoupon()">Apply</button>
        </div>
        <div id="couponMsg" style="font-size:0.8rem;margin-top:6px;"></div>
      </div>
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:14px;">Loyalty Points</h4>
        <p style="font-size:0.875rem;color:var(--text-secondary);margin-bottom:8px;">Available: <strong>${currentUser.loyaltyPoints || 0} pts</strong> (${formatPHP((currentUser.loyaltyPoints||0)/10)} value)</p>
        <div class="form-group"><label>Points to Redeem</label><input type="number" id="bfPoints" min="0" max="${currentUser.loyaltyPoints||0}" value="0" onchange="updateBookingPrice()"></div>
      </div>
      <div class="card" id="priceBreakdown">
        <h4 style="font-weight:700;margin-bottom:14px;">Price Breakdown</h4>
        <p style="color:var(--text-muted);font-size:0.875rem;">Select dates to see pricing</p>
      </div>
      <div style="background:#e8f4fd;border-radius:var(--radius-sm);padding:12px;margin-bottom:12px;font-size:0.8rem;color:#084298;">
        <i class="fas fa-tachometer-alt"></i> Daily mileage limit: <strong>${appSettings.mileage_limit||250} km</strong>
      </div>
      ${appSettings.rental_terms ? `<div class="card"><h4 style="font-weight:700;margin-bottom:8px;">Rental Terms</h4><p style="font-size:0.8rem;color:var(--text-secondary);">${appSettings.rental_terms}</p></div>` : ''}
      <span class="field-error" id="bfErr" style="display:block;margin-bottom:12px;text-align:center;"></span>
      <button class="btn-primary" onclick="submitBooking()"><i class="fas fa-check"></i> Confirm Booking</button>
    </div>`;
  showOverlay('page-booking-form');
}

function setRentalType(type) {
  document.getElementById('bfRentalType').value = type;
  document.getElementById('btnSelfDrive').classList.toggle('active', type === 'Self-Drive');
  document.getElementById('btnWithDriver').classList.toggle('active', type === 'With Driver');
}

function setPaymentType(type) {
  document.getElementById('bfPaymentType').value = type;
  document.getElementById('btnFull').classList.toggle('active', type === 'Full');
  document.getElementById('btnDown').classList.toggle('active', type === 'Downpayment');
  updateBookingPrice();
}

function selectInsurance(type, price, el) {
  selectedInsurance = { type, price };
  document.querySelectorAll('#bookingFormContent .option-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  updateBookingPrice();
}

function updateBookingPrice() {
  const start = document.getElementById('bfStartDate')?.value;
  const end = document.getElementById('bfEndDate')?.value;
  if (!start || !end) return;
  const v = bookingFormVehicle;
  if (!v) return;
  const pts = parseInt(document.getElementById('bfPoints')?.value) || 0;
  const cpPct = couponData ? couponData.discount_percent : 0;
  const result = calculateBookingPrice(
    v.daily_rate, start, end, selectedAddons, selectedInsurance.price,
    parseInt(appSettings.long_term_discount_days)||7,
    parseInt(appSettings.long_term_discount_percent)||10,
    cpPct, pts
  );
  const payType = document.getElementById('bfPaymentType')?.value || 'Full';
  const nowDue = payType === 'Downpayment' ? result.downpaymentAmount : result.total;
  const el = document.getElementById('priceBreakdown');
  el.innerHTML = `
    <h4 style="font-weight:700;margin-bottom:14px;">Price Breakdown</h4>
    <div class="price-row"><span>Base (${result.days} days × ${formatPHP(v.daily_rate)})</span><span>${formatPHP(result.basePrice)}</span></div>
    ${result.addonPrice > 0 ? `<div class="price-row"><span>Add-ons</span><span>${formatPHP(result.addonPrice)}</span></div>` : ''}
    <div class="price-row"><span>Insurance (${selectedInsurance.type})</span><span>${formatPHP(result.insurancePrice)}</span></div>
    ${result.longTermDiscount > 0 ? `<div class="price-row" style="color:var(--success);"><span>Long-term Discount (${appSettings.long_term_discount_percent}%)</span><span>-${formatPHP(result.longTermDiscount)}</span></div>` : ''}
    ${result.couponDiscount > 0 ? `<div class="price-row" style="color:var(--success);"><span>Coupon Discount</span><span>-${formatPHP(result.couponDiscount)}</span></div>` : ''}
    ${result.pointsDiscount > 0 ? `<div class="price-row" style="color:var(--success);"><span>Points Discount</span><span>-${formatPHP(result.pointsDiscount)}</span></div>` : ''}
    <div class="price-row total"><span>Total</span><span>${formatPHP(result.total)}</span></div>
    ${payType === 'Downpayment' ? `<div class="price-row" style="color:var(--primary);"><span>Due Now (20%)</span><span>${formatPHP(nowDue)}</span></div><div class="price-row"><span>Balance (80%)</span><span>${formatPHP(result.balanceAmount)}</span></div>` : ''}
    <div style="font-size:0.78rem;color:var(--text-muted);margin-top:8px;"><i class="fas fa-star" style="color:#ffc107;"></i> You'll earn <strong>${result.pointsEarned} pts</strong> from this booking</div>`;
}

async function applyCoupon() {
  const code = document.getElementById('bfCoupon').value.trim().toUpperCase();
  const msg = document.getElementById('couponMsg');
  if (!code) { msg.innerHTML = '<span style="color:var(--danger);">Enter a coupon code.</span>'; return; }
  try {
    const data = await apiCall('/coupons/verify', { method: 'POST', body: JSON.stringify({ code }) });
    couponData = data;
    msg.innerHTML = `<span style="color:var(--success);"><i class="fas fa-check"></i> ${data.discount_percent}% discount applied!</span>`;
    updateBookingPrice();
  } catch (err) {
    couponData = null;
    msg.innerHTML = `<span style="color:var(--danger);">${err.message}</span>`;
    updateBookingPrice();
  }
}

async function submitBooking() {
  const start = document.getElementById('bfStartDate').value;
  const end = document.getElementById('bfEndDate').value;
  document.getElementById('bfStartErr').textContent = '';
  document.getElementById('bfEndErr').textContent = '';
  document.getElementById('bfErr').textContent = '';

  const dateCheck = validateDateRange(start, end);
  if (!dateCheck.valid) {
    if (dateCheck.error.includes('Start')) document.getElementById('bfStartErr').textContent = dateCheck.error;
    else document.getElementById('bfEndErr').textContent = dateCheck.error;
    return;
  }
  const pts = parseInt(document.getElementById('bfPoints').value) || 0;
  const cpPct = couponData ? couponData.discount_percent : 0;
  const result = calculateBookingPrice(
    bookingFormVehicle.daily_rate, start, end, selectedAddons, selectedInsurance.price,
    parseInt(appSettings.long_term_discount_days)||7,
    parseInt(appSettings.long_term_discount_percent)||10,
    cpPct, pts
  );
  const payType = document.getElementById('bfPaymentType').value;
  const payload = {
    user_id: currentUser.id,
    vehicle_id: bookingFormVehicle.id,
    start_date: start, end_date: end,
    pickup_location: [document.getElementById('bfPickupProvince').value, document.getElementById('bfPickupMunicipality').value, document.getElementById('bfPickupBarangay').value].filter(Boolean).join(', '),
    pickup_province: sanitizeInput(document.getElementById('bfPickupProvince').value),
    pickup_municipality: sanitizeInput(document.getElementById('bfPickupMunicipality').value),
    pickup_barangay: sanitizeInput(document.getElementById('bfPickupBarangay').value),
    return_province: sanitizeInput(document.getElementById('bfReturnProvince').value),
    return_municipality: sanitizeInput(document.getElementById('bfReturnMunicipality').value),
    return_barangay: sanitizeInput(document.getElementById('bfReturnBarangay').value),
    rental_type: document.getElementById('bfRentalType').value,
    addons: selectedAddons.map(a => a.name),
    insurance_type: selectedInsurance.type,
    insurance_price: selectedInsurance.price,
    base_price: result.basePrice,
    addon_price: result.addonPrice,
    total_price: result.total,
    payment_type: payType,
    applied_coupon_id: couponData?.coupon_id || null,
    discount_amount: result.couponDiscount + result.longTermDiscount,
    points_redeemed: pts,
    points_earned: result.pointsEarned
  };
  showLoading(true);
  try {
    const data = await apiCall('/book', { method: 'POST', body: JSON.stringify(payload) });
    activeBookingId = data.booking_id;
    closeOverlay('page-booking-form');
    closeOverlay('page-vehicle-detail');
    await NotifStore.add(`Booking #${data.booking_id} received! Our team will review it shortly.`);
    openPaymentScreen(data.booking_id, result, payType);
  } catch (err) {
    document.getElementById('bfErr').textContent = err.message || 'Booking failed. Please try again.';
  } finally { showLoading(false); }
}

// ??? PAYMENT ?????????????????????????????????????????????????????????????????
function openPaymentScreen(bookingId, priceResult, payType) {
  const nowDue = payType === 'Downpayment' ? priceResult.downpaymentAmount : priceResult.total;
  const el = document.getElementById('paymentContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-payment')"><i class="fas fa-arrow-left"></i></button>
      <h2>Payment</h2>
    </div>
    <div class="scroll-content">
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:10px;">Booking #${bookingId}</h4>
        <div class="price-row"><span>Total Amount</span><span>${formatPHP(priceResult.total)}</span></div>
        <div class="price-row total"><span>Amount Due Now</span><span>${formatPHP(nowDue)}</span></div>
        ${payType === 'Downpayment' ? `<div class="price-row"><span>Remaining Balance</span><span>${formatPHP(priceResult.balanceAmount)}</span></div>` : ''}
      </div>
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:14px;">Payment Method</h4>
        <div class="form-group">
          <label>Method</label>
          <select id="payMethod">
            <option value="GCash">GCash</option>
            <option value="Credit Card">Credit Card</option>
            <option value="Debit Card">Debit Card</option>
            <option value="Cash (Over the counter)">Cash (Over the counter)</option>
          </select>
        </div>
        <div class="form-group">
          <label>Reference Number</label>
          <input type="text" id="payRef" placeholder="Transaction reference number">
        </div>
        <div class="form-group">
          <label>Payment Proof (optional)</label>
          <button class="btn-secondary" onclick="pickPaymentProof()"><i class="fas fa-upload"></i> Upload Proof</button>
          <img id="payProofPreview" style="width:100%;border-radius:var(--radius-sm);margin-top:8px;display:none;">
          <span class="field-error" id="payProofErr"></span>
        </div>
      </div>
      <div class="card">
        <button class="btn-outline" onclick="showOverlay('page-split-payment')"><i class="fas fa-users"></i> Split Payment</button>
      </div>
      <span class="field-error" id="payErr" style="display:block;margin-bottom:12px;text-align:center;"></span>
      <button class="btn-primary" onclick="submitPayment(${bookingId},${nowDue})"><i class="fas fa-lock"></i> Pay ${formatPHP(nowDue)}</button>
    </div>`;
  showOverlay('page-payment');
}

let paymentProofBlob = null;
async function pickPaymentProof() {
  try {
    if (window.Capacitor?.Plugins?.Camera) {
      const photo = await Camera.getPhoto({ resultType: CameraResultType.Base64, source: CameraSource.Photos, quality: 80 });
      const res = await fetch(`data:image/jpeg;base64,${photo.base64String}`);
      paymentProofBlob = await res.blob();
      const url = URL.createObjectURL(paymentProofBlob);
      const preview = document.getElementById('payProofPreview');
      preview.src = url; preview.style.display = 'block';
    } else {
      const input = document.createElement('input');
      input.type = 'file'; input.accept = 'image/jpeg,image/png';
      input.onchange = (e) => {
        const file = e.target.files[0];
        const err = validateUploadFile(file);
        if (err) { document.getElementById('payProofErr').textContent = err; return; }
        paymentProofBlob = file;
        const preview = document.getElementById('payProofPreview');
        preview.src = URL.createObjectURL(file); preview.style.display = 'block';
      };
      input.click();
    }
  } catch {}
}

async function submitPayment(bookingId, amount) {
  const method = document.getElementById('payMethod').value;
  const ref = sanitizeInput(document.getElementById('payRef').value.trim());
  document.getElementById('payErr').textContent = '';
  showLoading(true);
  try {
    let data;
    if (paymentProofBlob) {
      const fd = new FormData();
      fd.append('booking_id', bookingId);
      fd.append('amount', amount);
      fd.append('method', method);
      fd.append('reference_number', ref);
      fd.append('payment_proof', paymentProofBlob, 'proof.jpg');
      data = await uploadFile('/legacy-payment', fd);
    } else {
      data = await apiCall('/payment', { method: 'POST', body: JSON.stringify({ booking_id: bookingId, amount, method, reference_number: ref }) });
    }
    closeOverlay('page-payment');
    await NotifStore.add(`Payment confirmed for Booking #${bookingId}!`);
    showReceipt(bookingId, data);
  } catch (err) {
    document.getElementById('payErr').textContent = err.message || 'Payment failed. Please try again.';
  } finally { showLoading(false); }
}

function showReceipt(bookingId, data) {
  const receipt = data.receipt || {};
  const el = document.getElementById('receiptContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-receipt');showPage('page-bookings')"><i class="fas fa-arrow-left"></i></button>
      <h2>Receipt</h2>
    </div>
    <div class="receipt-card">
      <div class="receipt-header">
        <i class="fas fa-check-circle"></i>
        <h2>Payment Successful!</h2>
        <p style="color:var(--text-secondary);font-size:0.875rem;">Your booking is confirmed</p>
      </div>
      <div class="receipt-row"><span>Booking ID</span><strong>#${bookingId}</strong></div>
      ${receipt.brand ? `<div class="receipt-row"><span>Vehicle</span><strong>${receipt.brand} ${receipt.model}</strong></div>` : ''}
      ${receipt.start_date ? `<div class="receipt-row"><span>Period</span><strong>${receipt.start_date} ? ${receipt.end_date}</strong></div>` : ''}
      ${receipt.amount ? `<div class="receipt-row"><span>Amount Paid</span><strong>${formatPHP(receipt.amount)}</strong></div>` : ''}
      ${receipt.reference_number ? `<div class="receipt-row"><span>Reference</span><strong>${receipt.reference_number}</strong></div>` : ''}
      ${receipt.method ? `<div class="receipt-row"><span>Method</span><strong>${receipt.method}</strong></div>` : ''}
      <div style="margin-top:16px;">
        <button class="btn-primary" onclick="downloadReceipt(${bookingId})"><i class="fas fa-download"></i> Download PDF Receipt</button>
      </div>
    </div>`;
  showOverlay('page-receipt');
}

async function downloadReceipt(bookingId) {
  showToast('Downloading receipt...', 'info');
  window.open(`${API_BASE}/bookings/${bookingId}/receipt`, '_blank');
}

// ??? BOOKINGS ????????????????????????????????????????????????????????????????
async function loadBookings() {
  showLoading(true);
  try {
    const data = await apiCall(`/user-bookings?user_id=${currentUser.id}`);
    const el = document.getElementById('bookingsList');
    if (!data.length) {
      el.innerHTML = '<div class="empty-state"><i class="fas fa-calendar-times"></i><p>No bookings yet</p></div>';
    } else {
      el.innerHTML = data.map(b => `
        <div class="booking-item" onclick="openBookingDetail(${b.id})">
          <h4>${b.brand||''} ${b.model||''} ${b.plate_number ? '('+b.plate_number+')' : ''}</h4>
          <div class="booking-meta"><i class="fas fa-calendar"></i> ${b.start_date} ? ${b.end_date}</div>
          <div class="booking-meta"><i class="fas fa-money-bill"></i> ${formatPHP(b.total_price)}</div>
          <div class="booking-footer">${statusPill(b.status)} ${statusPill(b.payment_status)}</div>
        </div>`).join('');
    }
  } catch (err) {
    document.getElementById('bookingsList').innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${err.message}</p></div>`;
  } finally { showLoading(false); }
}

async function openBookingDetail(bookingId) {
  showLoading(true);
  try {
    const bookings = await apiCall(`/user-bookings?user_id=${currentUser.id}`);
    const b = bookings.find(x => x.id === bookingId);
    if (!b) { showToast('Booking not found.', 'error'); return; }
    activeBookingData = b;
    renderBookingDetail(b);
    showOverlay('page-booking-detail');
  } catch (err) { showToast(err.message, 'error'); }
  finally { showLoading(false); }
}

function renderBookingDetail(b) {
  const canCancel = ['Pending','Confirmed'].includes(b.status);
  const canModify = ['Pending','Confirmed'].includes(b.status);
  const canPreInspect = ['Confirmed','Approved'].includes(b.status);
  const canPostInspect = b.status === 'Picked Up';
  const canTrack = b.status === 'Picked Up';
  const canReview = b.status === 'Completed';
  const canPayBalance = b.payment_status === 'Partially Paid';
  const el = document.getElementById('bookingDetailContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-booking-detail')"><i class="fas fa-arrow-left"></i></button>
      <h2>Booking #${b.id}</h2>
    </div>
    <div class="scroll-content">
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
          <h4 style="font-weight:700;">${b.brand||''} ${b.model||''}</h4>
          ${statusPill(b.status)}
        </div>
        <div class="price-row"><span>Rental Period</span><span>${b.start_date} ? ${b.end_date}</span></div>
        <div class="price-row"><span>Rental Type</span><span>${b.rental_type||'—'}</span></div>
        <div class="price-row"><span>Pickup</span><span>${[b.pickup_barangay,b.pickup_municipality,b.pickup_province].filter(Boolean).join(', ')||b.pickup_location||'—'}</span></div>
        <div class="price-row"><span>Return</span><span>${[b.return_barangay,b.return_municipality,b.return_province].filter(Boolean).join(', ')||'—'}</span></div>
        <div class="price-row"><span>Insurance</span><span>${b.insurance_type||'Basic'}</span></div>
        ${b.addons ? `<div class="price-row"><span>Add-ons</span><span>${b.addons}</span></div>` : ''}
      </div>
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:10px;">Payment</h4>
        <div class="price-row"><span>Total</span><span>${formatPHP(b.total_price)}</span></div>
        <div class="price-row"><span>Paid</span><span>${formatPHP(b.amount_paid)}</span></div>
        ${b.balance_amount > 0 ? `<div class="price-row"><span>Balance</span><span style="color:var(--danger);">${formatPHP(b.balance_amount)}</span></div>` : ''}
        <div class="price-row"><span>Payment Status</span><span>${statusPill(b.payment_status)}</span></div>
        <div class="price-row"><span>Payment Type</span><span>${b.payment_type||'Full'}</span></div>
      </div>
      ${b.cancellation_reason ? `<div class="card" style="border-left:4px solid var(--danger);"><p style="font-size:0.875rem;"><strong>Cancellation Reason:</strong> ${b.cancellation_reason}</p></div>` : ''}
      <div class="action-btn-grid">
        ${canPayBalance ? `<button class="btn-primary btn-sm" onclick="openPayBalanceScreen(${b.id},${b.balance_amount})"><i class="fas fa-money-bill"></i> Pay Balance</button>` : ''}
        ${canCancel ? `<button class="btn-danger btn-sm" onclick="promptCancelBooking(${b.id})"><i class="fas fa-times"></i> Cancel</button>` : ''}
        ${canModify ? `<button class="btn-secondary btn-sm" onclick="openModifyBooking(${b.id})"><i class="fas fa-edit"></i> Modify Dates</button>` : ''}
        ${canPreInspect ? `<button class="btn-secondary btn-sm" onclick="openInspection(${b.id},'pickup')"><i class="fas fa-clipboard-check"></i> Pre-Rental Check</button>` : ''}
        ${canPostInspect ? `<button class="btn-secondary btn-sm" onclick="openInspection(${b.id},'return')"><i class="fas fa-clipboard-check"></i> Post-Rental Check</button>` : ''}
        ${canTrack ? `<button class="btn-outline btn-sm" onclick="openGpsMap(${b.vehicle_id})"><i class="fas fa-map-marker-alt"></i> Track Vehicle</button>` : ''}
        ${canReview ? `<button class="btn-outline btn-sm" onclick="openReviewForm(${b.vehicle_id})"><i class="fas fa-star"></i> Leave Review</button>` : ''}
        <button class="btn-secondary btn-sm" onclick="downloadReceipt(${b.id})"><i class="fas fa-download"></i> Receipt PDF</button>
      </div>
    </div>`;
}

async function promptCancelBooking(bookingId) {
  const reason = prompt('Please provide a reason for cancellation:');
  if (!reason) return;
  showLoading(true);
  try {
    await apiCall('/cancel-booking', { method: 'POST', body: JSON.stringify({ booking_id: bookingId, user_id: currentUser.id, reason }) });
    showToast('Booking cancelled successfully.', 'success');
    await NotifStore.add(`Booking #${bookingId} has been cancelled.`);
    closeOverlay('page-booking-detail');
    loadBookings();
  } catch (err) { showToast(err.message, 'error'); }
  finally { showLoading(false); }
}

function openPayBalanceScreen(bookingId, balance) {
  const el = document.getElementById('paymentContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-payment')"><i class="fas fa-arrow-left"></i></button>
      <h2>Pay Balance</h2>
    </div>
    <div class="scroll-content">
      <div class="card">
        <div class="price-row total"><span>Balance Due</span><span>${formatPHP(balance)}</span></div>
      </div>
      <div class="card">
        <div class="form-group"><label>Method</label><select id="balMethod"><option>GCash</option><option>Credit Card</option><option>Cash (Over the counter)</option></select></div>
        <div class="form-group"><label>Reference Number</label><input type="text" id="balRef" placeholder="Reference number"></div>
      </div>
      <span class="field-error" id="balErr" style="display:block;margin-bottom:12px;text-align:center;"></span>
      <button class="btn-primary" onclick="submitBalancePayment(${bookingId},${balance})">Pay ${formatPHP(balance)}</button>
    </div>`;
  showOverlay('page-payment');
}

async function submitBalancePayment(bookingId, amount) {
  const method = document.getElementById('balMethod').value;
  const ref = sanitizeInput(document.getElementById('balRef').value.trim());
  showLoading(true);
  try {
    await apiCall(`/bookings/${bookingId}/pay-balance`, { method: 'POST', body: JSON.stringify({ amount, method, reference_number: ref }) });
    showToast('Balance paid successfully!', 'success');
    closeOverlay('page-payment');
    closeOverlay('page-booking-detail');
    loadBookings();
  } catch (err) { document.getElementById('balErr').textContent = err.message; }
  finally { showLoading(false); }
}

async function openModifyBooking(bookingId) {
  const newStart = prompt('New start date (YYYY-MM-DD):');
  const newEnd = prompt('New end date (YYYY-MM-DD):');
  if (!newStart || !newEnd) return;
  const check = validateDateRange(newStart, newEnd);
  if (!check.valid) { showToast(check.error, 'error'); return; }
  showLoading(true);
  try {
    const data = await apiCall('/modify-booking', { method: 'POST', body: JSON.stringify({ booking_id: bookingId, user_id: currentUser.id, start_date: newStart, end_date: newEnd }) });
    showToast(`Dates updated! New total: ${formatPHP(data.new_total)}`, 'success');
    closeOverlay('page-booking-detail');
    loadBookings();
  } catch (err) { showToast(err.message, 'error'); }
  finally { showLoading(false); }
}

// ??? INSPECTION ??????????????????????????????????????????????????????????????
function openInspection(bookingId, type) {
  inspectionPhotos = [];
  const el = document.getElementById('inspectionContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-inspection')"><i class="fas fa-arrow-left"></i></button>
      <h2>${type === 'pickup' ? 'Pre-Rental' : 'Post-Rental'} Inspection</h2>
    </div>
    <div class="scroll-content">
      <div class="card">
        <div class="form-group"><label>Mileage Reading (km) *</label><input type="number" id="inspMileage" placeholder="e.g. 12500"><span class="field-error" id="inspMileageErr"></span></div>
        <div class="form-group"><label>Fuel Level</label><select id="inspFuel"><option>Full</option><option>3/4</option><option>1/2</option><option>1/4</option><option>Empty</option></select></div>
        <div class="form-group"><label>Condition Notes</label><textarea id="inspNotes" placeholder="Describe vehicle condition..."></textarea></div>
      </div>
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:10px;">Photos</h4>
        <button class="btn-secondary" onclick="addInspectionPhoto()"><i class="fas fa-camera"></i> Take / Add Photo</button>
        <div class="photo-thumbs" id="inspPhotoThumbs"></div>
      </div>
      <span class="field-error" id="inspErr" style="display:block;margin-bottom:12px;text-align:center;"></span>
      <button class="btn-primary" onclick="submitInspection(${bookingId},'${type}')"><i class="fas fa-check"></i> Submit Inspection</button>
      <div style="margin-top:20px;" id="pastInspectionsWrap"></div>
    </div>`;
  showOverlay('page-inspection');
  loadPastInspections(bookingId);
}

async function addInspectionPhoto() {
  try {
    let blob;
    if (window.Capacitor?.Plugins?.Camera) {
      const photo = await Camera.getPhoto({ resultType: CameraResultType.Base64, source: CameraSource.Camera, quality: 70 });
      const res = await fetch(`data:image/jpeg;base64,${photo.base64String}`);
      blob = await res.blob();
    } else {
      await new Promise((resolve) => {
        const input = document.createElement('input');
        input.type = 'file'; input.accept = 'image/*';
        input.onchange = (e) => { blob = e.target.files[0]; resolve(); };
        input.click();
      });
    }
    if (!blob) return;
    const err = validateUploadFile(blob);
    if (err) { showToast(err, 'error'); return; }
    inspectionPhotos.push(blob);
    const thumbs = document.getElementById('inspPhotoThumbs');
    const img = document.createElement('img');
    img.className = 'photo-thumb';
    img.src = URL.createObjectURL(blob);
    thumbs.appendChild(img);
  } catch {}
}

async function submitInspection(bookingId, type) {
  const mileage = document.getElementById('inspMileage').value;
  document.getElementById('inspMileageErr').textContent = '';
  document.getElementById('inspErr').textContent = '';
  if (isBlank(mileage)) { document.getElementById('inspMileageErr').textContent = 'Mileage reading is required.'; return; }
  const fd = new FormData();
  fd.append('booking_id', bookingId);
  fd.append('inspection_type', type);
  fd.append('mileage', mileage);
  fd.append('fuel_level', document.getElementById('inspFuel').value);
  fd.append('notes', sanitizeInput(document.getElementById('inspNotes').value));
  fd.append('inspector_id', currentUser.id);
  inspectionPhotos.forEach((p, i) => fd.append(`photo_${i}`, p, `photo_${i}.jpg`));
  showLoading(true);
  try {
    await uploadFile('/inspections/submit', fd);
    showToast('Inspection submitted successfully!', 'success');
    closeOverlay('page-inspection');
  } catch (err) { document.getElementById('inspErr').textContent = err.message; }
  finally { showLoading(false); }
}

async function loadPastInspections(bookingId) {
  try {
    const data = await apiCall(`/inspections/${bookingId}`);
    if (!data.length) return;
    const el = document.getElementById('pastInspectionsWrap');
    el.innerHTML = `<h4 style="font-weight:700;margin-bottom:10px;">Past Inspections</h4>` +
      data.map(i => `
        <div class="card" style="margin-bottom:10px;">
          <div style="display:flex;justify-content:space-between;"><strong>${i.inspection_type === 'pickup' ? 'Pre-Rental' : 'Post-Rental'}</strong><small>${new Date(i.created_at).toLocaleDateString()}</small></div>
          <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:6px;">Mileage: ${i.mileage} km | Fuel: ${i.fuel_level}</div>
          ${i.notes ? `<div style="font-size:0.8rem;margin-top:4px;">${i.notes}</div>` : ''}
          ${(i.photos||[]).length ? `<div class="photo-thumbs">${i.photos.map(p => `<img class="photo-thumb" src="${p}">`).join('')}</div>` : ''}
        </div>`).join('');
  } catch {}
}

// ??? GPS MAP ?????????????????????????????????????????????????????????????????
let gpsMap = null;
let gpsMarker = null;

async function openGpsMap(vehicleId) {
  showOverlay('page-gps-map');
  const el = document.getElementById('gpsMapContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-gps-map')"><i class="fas fa-arrow-left"></i></button>
      <h2>Track Vehicle</h2>
    </div>
    <div class="scroll-content" style="padding:16px;">
      <div id="map"></div>
      <div id="gpsTimestamp" style="font-size:0.8rem;color:var(--text-muted);margin-top:8px;text-align:center;"></div>
      <button class="btn-secondary" style="margin-top:10px;" onclick="centerGpsMap()"><i class="fas fa-crosshairs"></i> Center on Vehicle</button>
    </div>`;
  setTimeout(() => {
    if (!gpsMap) {
      gpsMap = L.map('map').setView([14.5995, 120.9842], 13);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(gpsMap);
    }
    fetchVehicleLocation(vehicleId);
    startGpsPolling(vehicleId);
  }, 300);
}

async function fetchVehicleLocation(vehicleId) {
  try {
    const data = await apiCall(`/vehicles/${vehicleId}/location?user_id=${currentUser.id}`);
    if (data.latitude && data.longitude) {
      const latlng = [data.latitude, data.longitude];
      if (gpsMarker) { gpsMarker.setLatLng(latlng); }
      else { gpsMarker = L.marker(latlng).addTo(gpsMap).bindPopup('Vehicle Location').openPopup(); }
      gpsMap.setView(latlng, 15);
      const ts = document.getElementById('gpsTimestamp');
      if (ts) ts.textContent = `Last updated: ${data.last_gps_update ? new Date(data.last_gps_update).toLocaleString() : 'Unknown'}`;
    } else {
      const ts = document.getElementById('gpsTimestamp');
      if (ts) ts.textContent = 'Live tracking is currently unavailable for this vehicle.';
    }
  } catch {}
}

function centerGpsMap() { if (gpsMarker && gpsMap) gpsMap.setView(gpsMarker.getLatLng(), 15); }
function startGpsPolling(vehicleId) { gpsRefreshInterval = setInterval(() => fetchVehicleLocation(vehicleId), 30000); }
function stopGpsPolling() { if (gpsRefreshInterval) { clearInterval(gpsRefreshInterval); gpsRefreshInterval = null; } if (gpsMap) { gpsMap.remove(); gpsMap = null; gpsMarker = null; } }

// ??? REVIEW ??????????????????????????????????????????????????????????????????
let selectedRating = 0;
function openReviewForm(vehicleId) {
  selectedRating = 0;
  const el = document.getElementById('reviewContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-review')"><i class="fas fa-arrow-left"></i></button>
      <h2>Leave a Review</h2>
    </div>
    <div class="scroll-content">
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:14px;">Rate your experience</h4>
        <div class="star-rating" id="starRating">
          ${[1,2,3,4,5].map(n => `<i class="fas fa-star" onclick="setRating(${n})" data-val="${n}"></i>`).join('')}
        </div>
        <span class="field-error" id="ratingErr" style="margin-top:8px;display:block;"></span>
        <div class="form-group" style="margin-top:16px;"><label>Comment (optional)</label><textarea id="reviewComment" placeholder="Share your experience..."></textarea></div>
        <span class="field-error" id="reviewErr" style="display:block;margin-bottom:12px;"></span>
        <button class="btn-primary" onclick="submitReview(${vehicleId})"><i class="fas fa-paper-plane"></i> Submit Review</button>
      </div>
    </div>`;
  showOverlay('page-review');
}

function setRating(val) {
  selectedRating = val;
  document.querySelectorAll('#starRating i').forEach(s => {
    s.classList.toggle('active', parseInt(s.dataset.val) <= val);
  });
}

async function submitReview(vehicleId) {
  document.getElementById('ratingErr').textContent = '';
  document.getElementById('reviewErr').textContent = '';
  if (!selectedRating) { document.getElementById('ratingErr').textContent = 'Please select a rating before submitting.'; return; }
  const comment = sanitizeInput(document.getElementById('reviewComment').value.trim());
  showLoading(true);
  try {
    await apiCall('/review', { method: 'POST', body: JSON.stringify({ user_id: currentUser.id, vehicle_id: vehicleId, rating: selectedRating, comment }) });
    showToast('Review submitted! Thank you.', 'success');
    closeOverlay('page-review');
  } catch (err) { document.getElementById('reviewErr').textContent = err.message; }
  finally { showLoading(false); }
}

// ??? PROFILE ?????????????????????????????????????????????????????????????????
async function loadProfile() {
  showLoading(true);
  try {
    const [profile, pts, verif] = await Promise.all([
      apiCall(`/profile?user_id=${currentUser.id}`),
      apiCall(`/user/points?user_id=${currentUser.id}`),
      apiCall(`/user/verify-status?user_id=${currentUser.id}`)
    ]);
    document.getElementById('profileName').textContent = profile.full_name || '';
    document.getElementById('profileEmail').textContent = profile.email || '';
    document.getElementById('editName').value = profile.full_name || '';
    document.getElementById('editPhone').value = profile.phone || '';
    document.getElementById('profilePoints').textContent = pts.points || 0;
    currentUser.loyaltyPoints = pts.points || 0;
    currentUser.isVerified = verif.is_verified ?? profile.is_verified ?? 0;
    await Session.save(currentUser);
    const badge = document.getElementById('profileVerifyBadge');
    const labels = { 0: 'Not Verified', 1: 'Pending Review', 2: 'Verified' };
    badge.textContent = labels[currentUser.isVerified] || 'Not Verified';
    badge.className = `verify-badge verify-${currentUser.isVerified}`;
    const avatarWrap = document.getElementById('profileAvatarWrap');
    if (profile.profile_picture) {
      avatarWrap.innerHTML = `<img class="profile-avatar" src="${profile.profile_picture}" alt="Avatar">`;
    } else {
      document.getElementById('profileAvatarPlaceholder').textContent = (profile.full_name||'?')[0].toUpperCase();
    }
    if (verif.license_image_url) {
      const licEl = document.getElementById('licenseCurrentImg');
      if (licEl) { licEl.src = verif.license_image_url; licEl.style.display = 'block'; }
    }
  } catch (err) { showToast(err.message, 'error'); }
  finally { showLoading(false); }
}

async function pickProfilePicture() {
  try {
    if (window.Capacitor?.Plugins?.Camera) {
      const photo = await Camera.getPhoto({ resultType: CameraResultType.Base64, source: CameraSource.Photos, quality: 80 });
      const res = await fetch(`data:image/jpeg;base64,${photo.base64String}`);
      profilePicBlob = await res.blob();
    } else {
      await new Promise(resolve => {
        const input = document.createElement('input');
        input.type = 'file'; input.accept = 'image/jpeg,image/png';
        input.onchange = (e) => {
          const file = e.target.files[0];
          const err = validateUploadFile(file);
          if (err) { showToast(err, 'error'); resolve(); return; }
          profilePicBlob = file; resolve();
        };
        input.click();
      });
    }
    if (profilePicBlob) {
      const preview = document.getElementById('profilePicPreview');
      preview.src = URL.createObjectURL(profilePicBlob);
      preview.style.display = 'block';
    }
  } catch {}
}

async function doUpdateProfile() {
  const name = sanitizeInput(document.getElementById('editName').value.trim());
  const phone = document.getElementById('editPhone').value.trim();
  document.getElementById('editPhoneErr').textContent = '';
  if (phone && (!/^\d+$/.test(phone) || phone.length < 10 || phone.length > 11)) {
    document.getElementById('editPhoneErr').textContent = 'Phone must be 10–11 digits.'; return;
  }
  const fd = new FormData();
  fd.append('user_id', currentUser.id);
  fd.append('full_name', name);
  fd.append('phone', phone);
  if (profilePicBlob) fd.append('profile_picture', profilePicBlob, 'avatar.jpg');
  showLoading(true);
  try {
    await uploadFile('/update-profile', fd);
    currentUser.fullName = name;
    await Session.save(currentUser);
    showToast('Profile updated successfully!', 'success');
    loadProfile();
  } catch (err) { showToast(err.message, 'error'); }
  finally { showLoading(false); }
}

// ??? LICENSE UPLOAD ??????????????????????????????????????????????????????????
async function openLicenseUpload() {
  const el = document.getElementById('licenseUploadContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-license-upload')"><i class="fas fa-arrow-left"></i></button>
      <h2>Upload License</h2>
    </div>
    <div class="scroll-content">
      <div class="card">
        <p style="font-size:0.875rem;color:var(--text-secondary);margin-bottom:14px;">Upload a clear photo of your driver's license. Accepted: JPEG, PNG. Max size: 5 MB.</p>
        ${currentUser.isVerified === 0 ? '<div style="background:#f8d7da;border-radius:var(--radius-sm);padding:10px;margin-bottom:12px;font-size:0.8rem;color:#842029;"><i class="fas fa-exclamation-circle"></i> Please re-upload a valid document.</div>' : ''}
        <img id="licenseCurrentImg" style="width:100%;border-radius:var(--radius-sm);margin-bottom:12px;display:none;">
        <button class="btn-secondary" onclick="pickLicense()"><i class="fas fa-id-card"></i> Choose License Photo</button>
        <img id="licensePreview" style="width:100%;border-radius:var(--radius-sm);margin-top:10px;display:none;">
        <span class="field-error" id="licenseErr" style="display:block;margin-top:8px;"></span>
        <button class="btn-primary" style="margin-top:14px;" onclick="submitLicense()"><i class="fas fa-upload"></i> Submit for Verification</button>
      </div>
    </div>`;
  showOverlay('page-license-upload');
  // Load current license
  try {
    const v = await apiCall(`/user/verify-status?user_id=${currentUser.id}`);
    if (v.license_image_url) {
      const img = document.getElementById('licenseCurrentImg');
      img.src = v.license_image_url; img.style.display = 'block';
    }
  } catch {}
}

async function pickLicense() {
  try {
    if (window.Capacitor?.Plugins?.Camera) {
      const photo = await Camera.getPhoto({ resultType: CameraResultType.Base64, source: CameraSource.Photos, quality: 90 });
      const res = await fetch(`data:image/jpeg;base64,${photo.base64String}`);
      licenseBlob = await res.blob();
    } else {
      await new Promise(resolve => {
        const input = document.createElement('input');
        input.type = 'file'; input.accept = 'image/jpeg,image/png';
        input.onchange = (e) => {
          const file = e.target.files[0];
          const err = validateUploadFile(file);
          if (err) { document.getElementById('licenseErr').textContent = err; resolve(); return; }
          licenseBlob = file; resolve();
        };
        input.click();
      });
    }
    if (licenseBlob) {
      const preview = document.getElementById('licensePreview');
      preview.src = URL.createObjectURL(licenseBlob); preview.style.display = 'block';
    }
  } catch {}
}

async function submitLicense() {
  document.getElementById('licenseErr').textContent = '';
  if (!licenseBlob) { document.getElementById('licenseErr').textContent = 'Please select a license image first.'; return; }
  const fd = new FormData();
  fd.append('user_id', currentUser.id);
  fd.append('license', licenseBlob, 'license.jpg');
  showLoading(true);
  try {
    await uploadFile('/user/upload-license', fd);
    currentUser.isVerified = 1;
    await Session.save(currentUser);
    showToast('Your license has been submitted for review.', 'success');
    await NotifStore.add('Your license has been submitted for review. We will notify you once approved.');
    closeOverlay('page-license-upload');
    loadProfile();
  } catch (err) { document.getElementById('licenseErr').textContent = err.message; }
  finally { showLoading(false); }
}

// ??? SAVED PAYMENTS ??????????????????????????????????????????????????????????
async function loadSavedPayments() {
  showLoading(true);
  try {
    const data = await apiCall(`/saved-payments?user_id=${currentUser.id}`);
    const el = document.getElementById('savedPaymentsContent');
    const listHtml = data.length
      ? data.map(p => `<div class="payment-card-item"><div class="payment-card-icon"><i class="fas fa-credit-card"></i></div><div><strong>${p.card_type}</strong><br><small style="color:var(--text-secondary);">•••• ${p.last_four} — ${p.provider}</small></div></div>`).join('')
      : '<div class="empty-state"><i class="fas fa-credit-card"></i><p>No saved payment methods</p></div>';
    el.innerHTML = `
      <div class="page-header">
        <button class="back-btn" onclick="closeOverlay('page-saved-payments')"><i class="fas fa-arrow-left"></i></button>
        <h2>Saved Payments</h2>
      </div>
      <div class="scroll-content">
        ${listHtml}
        <div class="card" style="margin-top:16px;">
          <h4 style="font-weight:700;margin-bottom:14px;">Add Payment Method</h4>
          <div class="form-group"><label>Card Type</label><select id="newCardType"><option>Visa</option><option>Mastercard</option><option>GCash</option><option>Maya</option></select></div>
          <div class="form-group"><label>Last 4 Digits</label><input type="text" id="newLastFour" maxlength="4" placeholder="1234"><span class="field-error" id="lastFourErr"></span></div>
          <div class="form-group"><label>Provider</label><input type="text" id="newProvider" placeholder="e.g. BDO, BPI, GCash"></div>
          <button class="btn-primary" onclick="addSavedPayment()"><i class="fas fa-plus"></i> Add Method</button>
        </div>
      </div>`;
  } catch (err) { showToast(err.message, 'error'); }
  finally { showLoading(false); }
}

async function addSavedPayment() {
  const cardType = document.getElementById('newCardType').value;
  const lastFour = document.getElementById('newLastFour').value.trim();
  const provider = sanitizeInput(document.getElementById('newProvider').value.trim());
  document.getElementById('lastFourErr').textContent = '';
  if (!isValidLastFour(lastFour)) { document.getElementById('lastFourErr').textContent = 'Must be exactly 4 digits.'; return; }
  showLoading(true);
  try {
    await apiCall('/saved-payment', { method: 'POST', body: JSON.stringify({ user_id: currentUser.id, card_type: cardType, last_four: lastFour, provider }) });
    showToast('Payment method saved!', 'success');
    loadSavedPayments();
  } catch (err) { showToast(err.message, 'error'); }
  finally { showLoading(false); }
}

// ??? FAVORITES ???????????????????????????????????????????????????????????????
async function loadFavorites() {
  showLoading(true);
  try {
    const data = await apiCall(`/favorites?user_id=${currentUser.id}`);
    const el = document.getElementById('favoritesContent');
    el.innerHTML = `
      <div class="page-header">
        <button class="back-btn" onclick="closeOverlay('page-favorites')"><i class="fas fa-arrow-left"></i></button>
        <h2>My Favorites</h2>
      </div>
      <div class="vehicle-grid" style="padding:16px;">
        ${data.length ? data.map(v => `
          <div class="vehicle-card" onclick="openVehicleDetail(${v.id})">
            <div class="vehicle-img-wrap">
              <img src="${v.vehicle_image ? API_BASE+'/'+v.vehicle_image : 'https://via.placeholder.com/400x200?text=No+Image'}" alt="${v.brand} ${v.model}" onerror="this.src='https://via.placeholder.com/400x200?text=No+Image'">
            </div>
            <div class="vehicle-info">
              <h3>${v.brand} ${v.model}</h3>
              <div class="vehicle-meta"><i class="fas fa-map-marker-alt"></i> ${v.location||'—'}</div>
              <div class="vehicle-rate">${formatPHP(v.daily_rate)} <span>/ day</span></div>
            </div>
          </div>`).join('')
          : '<div class="empty-state"><i class="fas fa-heart"></i><p>No favorites yet</p></div>'
        }
      </div>`;
  } catch (err) { showToast(err.message, 'error'); }
  finally { showLoading(false); }
}

// ??? SPLIT PAYMENT ???????????????????????????????????????????????????????????
async function loadSplitPayment() {
  const el = document.getElementById('splitPaymentContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-split-payment')"><i class="fas fa-arrow-left"></i></button>
      <h2>Split Payment</h2>
    </div>
    <div class="scroll-content">
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:14px;">Request Split</h4>
        <div class="form-group"><label>Partner Email</label><input type="email" id="splitEmail" placeholder="partner@gmail.com"><span class="field-error" id="splitEmailErr"></span></div>
        <div class="form-group"><label>Amount for Partner (PHP)</label><input type="number" id="splitAmount" placeholder="0.00"></div>
        <button class="btn-primary" onclick="requestSplit()"><i class="fas fa-users"></i> Request Split</button>
      </div>
      <div class="card" style="margin-top:16px;">
        <h4 style="font-weight:700;margin-bottom:14px;">Incoming Split Requests</h4>
        <div id="splitBillsList"><p style="color:var(--text-muted);font-size:0.875rem;">Loading...</p></div>
      </div>
    </div>`;
  showOverlay('page-split-payment');
  loadSplitBills();
}

async function requestSplit() {
  const email = document.getElementById('splitEmail').value.trim();
  const amount = parseFloat(document.getElementById('splitAmount').value);
  document.getElementById('splitEmailErr').textContent = '';
  if (!email) { document.getElementById('splitEmailErr').textContent = 'Partner email is required.'; return; }
  showLoading(true);
  try {
    await apiCall('/split-bill/request', { method: 'POST', body: JSON.stringify({ booking_id: activeBookingId, partner_email: email, amount }) });
    showToast('Split request sent! Awaiting partner confirmation.', 'success');
  } catch (err) { document.getElementById('splitEmailErr').textContent = err.message; }
  finally { showLoading(false); }
}

async function loadSplitBills() {
  try {
    const data = await apiCall(`/split-bills?email=${currentUser.email || ''}`);
    const el = document.getElementById('splitBillsList');
    if (!data.length) { el.innerHTML = '<p style="color:var(--text-muted);font-size:0.875rem;">No incoming split requests</p>'; return; }
    el.innerHTML = data.map(s => `
      <div class="split-status">
        <strong>${s.initiator_name||'Someone'}</strong> wants to split Booking #${s.booking_id}<br>
        <small>${s.vehicle_brand||''} ${s.vehicle_model||''} | ${s.start_date} ? ${s.end_date}</small><br>
        <strong style="color:var(--primary);">Your share: ${formatPHP(s.amount)}</strong><br>
        <span class="pill ${s.status==='Paid'?'pill-paid':'pill-pending'}">${s.status}</span>
        ${s.status !== 'Paid' ? `<button class="btn-primary btn-sm" style="margin-top:8px;" onclick="paySplit(${s.id})">Pay My Share</button>` : ''}
      </div>`).join('');
  } catch {}
}

async function paySplit(splitId) {
  showLoading(true);
  try {
    await apiCall('/split-bill/pay', { method: 'POST', body: JSON.stringify({ split_id: splitId, user_id: currentUser.id }) });
    showToast('Split payment completed!', 'success');
    loadSplitBills();
  } catch (err) { showToast(err.message, 'error'); }
  finally { showLoading(false); }
}

// ??? SUPPORT ?????????????????????????????????????????????????????????????????
async function loadSupport() {
  const el = document.getElementById('supportContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-support')"><i class="fas fa-arrow-left"></i></button>
      <h2>Support</h2>
    </div>
    <div class="scroll-content">
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:14px;">Submit a Ticket</h4>
        <div class="form-group"><label>Name *</label><input type="text" id="suppName" value="${currentUser.fullName||''}"><span class="field-error" id="suppNameErr"></span></div>
        <div class="form-group"><label>Email</label><input type="email" id="suppEmail" placeholder="yourname@gmail.com"></div>
        <div class="form-group"><label>Subject *</label><input type="text" id="suppSubject" placeholder="Brief description"><span class="field-error" id="suppSubjectErr"></span></div>
        <div class="form-group"><label>Message *</label><textarea id="suppMessage" placeholder="Describe your issue..."></textarea><span class="field-error" id="suppMessageErr"></span></div>
        <span class="field-error" id="suppErr" style="display:block;margin-bottom:12px;"></span>
        <button class="btn-primary" onclick="submitSupport()"><i class="fas fa-paper-plane"></i> Submit Ticket</button>
      </div>
      <div class="card" style="margin-top:16px;">
        <h4 style="font-weight:700;margin-bottom:14px;">Newsletter</h4>
        <p style="font-size:0.875rem;color:var(--text-secondary);margin-bottom:10px;">Subscribe for promos and updates.</p>
        <div class="coupon-row">
          <input type="email" id="newsletterEmail" placeholder="yourname@gmail.com">
          <button onclick="subscribeNewsletter()">Subscribe</button>
        </div>
        <span class="field-error" id="newsletterErr" style="display:block;margin-top:6px;"></span>
      </div>
    </div>`;
  showOverlay('page-support');
}

async function submitSupport() {
  const name = sanitizeInput(document.getElementById('suppName').value.trim());
  const email = sanitizeInput(document.getElementById('suppEmail').value.trim());
  const subject = sanitizeInput(document.getElementById('suppSubject').value.trim());
  const message = sanitizeInput(document.getElementById('suppMessage').value.trim());
  ['suppNameErr','suppSubjectErr','suppMessageErr','suppErr'].forEach(id => document.getElementById(id).textContent = '');
  if (isBlank(name)) { document.getElementById('suppNameErr').textContent = 'Name is required.'; return; }
  if (isBlank(subject)) { document.getElementById('suppSubjectErr').textContent = 'Subject is required.'; return; }
  if (isBlank(message)) { document.getElementById('suppMessageErr').textContent = 'Message is required.'; return; }
  showLoading(true);
  try {
    await apiCall('/support', { method: 'POST', body: JSON.stringify({ name, email, subject, message }) });
    showToast('Support ticket submitted successfully.', 'success');
    closeOverlay('page-support');
  } catch (err) { document.getElementById('suppErr').textContent = err.message; }
  finally { showLoading(false); }
}

async function subscribeNewsletter() {
  const email = document.getElementById('newsletterEmail').value.trim();
  document.getElementById('newsletterErr').textContent = '';
  if (!email || !email.includes('@')) { document.getElementById('newsletterErr').textContent = 'Please enter a valid email.'; return; }
  showLoading(true);
  try {
    await apiCall('/newsletter', { method: 'POST', body: JSON.stringify({ email }) });
    showToast('Subscribed successfully!', 'success');
  } catch (err) { document.getElementById('newsletterErr').textContent = err.message; }
  finally { showLoading(false); }
}

// ??? CHATBOT ?????????????????????????????????????????????????????????????????
function loadChatbot() {
  chatHistory = [];
  const el = document.getElementById('chatbotContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-chatbot')"><i class="fas fa-arrow-left"></i></button>
      <h2>Chat Assistant</h2>
    </div>
    <div class="chat-messages" id="chatMessages">
      <div class="chat-msg bot">Hi! I'm the Autoride assistant. How can I help you today?</div>
    </div>
    <div class="chat-input-row">
      <input type="text" id="chatInput" placeholder="Type a message..." onkeydown="if(event.key==='Enter')sendChat()">
      <button onclick="sendChat()"><i class="fas fa-paper-plane"></i></button>
    </div>`;
  showOverlay('page-chatbot');
}

async function sendChat() {
  const input = document.getElementById('chatInput');
  const msg = sanitizeInput(input.value.trim());
  if (isBlank(msg)) return;
  input.value = '';
  const msgs = document.getElementById('chatMessages');
  msgs.innerHTML += `<div class="chat-msg user">${msg}</div>`;
  msgs.scrollTop = msgs.scrollHeight;
  try {
    const data = await apiCall('/chat', { method: 'POST', body: JSON.stringify({ message: msg, user_id: currentUser.id }) });
    msgs.innerHTML += `<div class="chat-msg bot">${data.response || 'I\'m not sure about that. Please contact support.'}</div>`;
  } catch {
    msgs.innerHTML += `<div class="chat-msg bot">Sorry, I couldn't process that. Please try again.</div>`;
  }
  msgs.scrollTop = msgs.scrollHeight;
}

// ??? NOTIFICATIONS ???????????????????????????????????????????????????????????
async function loadNotifications() {
  const all = await NotifStore.getAll();
  await NotifStore.markAllRead();
  const el = document.getElementById('notificationsContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-notifications')"><i class="fas fa-arrow-left"></i></button>
      <h2>Notifications</h2>
    </div>
    <div class="scroll-content">
      ${all.length ? all.map(n => `
        <div class="notif-item ${n.read ? '' : 'unread'}">
          <p>${n.msg}</p>
          <small>${new Date(n.ts).toLocaleString()}</small>
        </div>`).join('')
        : '<div class="empty-state"><i class="fas fa-bell-slash"></i><p>No notifications yet</p></div>'
      }
    </div>`;
}

// ??? NEWSLETTER OVERLAY ??????????????????????????????????????????????????????
function loadNewsletter() {
  const el = document.getElementById('newsletterContent');
  el.innerHTML = `
    <div class="page-header">
      <button class="back-btn" onclick="closeOverlay('page-newsletter')"><i class="fas fa-arrow-left"></i></button>
      <h2>Newsletter</h2>
    </div>
    <div class="scroll-content">
      <div class="card">
        <h4 style="font-weight:700;margin-bottom:10px;">Stay Updated</h4>
        <p style="font-size:0.875rem;color:var(--text-secondary);margin-bottom:14px;">Subscribe to receive promos, discounts, and news from Autoride.</p>
        <div class="form-group"><label>Email Address</label><input type="email" id="nlEmail" placeholder="yourname@gmail.com"><span class="field-error" id="nlErr"></span></div>
        <button class="btn-primary" onclick="doSubscribeNewsletter()"><i class="fas fa-envelope"></i> Subscribe</button>
      </div>
    </div>`;
  showOverlay('page-newsletter');
}

async function doSubscribeNewsletter() {
  const email = document.getElementById('nlEmail').value.trim();
  document.getElementById('nlErr').textContent = '';
  if (!email || !email.includes('@')) { document.getElementById('nlErr').textContent = 'Please enter a valid email.'; return; }
  showLoading(true);
  try {
    await apiCall('/newsletter', { method: 'POST', body: JSON.stringify({ email }) });
    showToast('Subscribed successfully!', 'success');
    closeOverlay('page-newsletter');
  } catch (err) { document.getElementById('nlErr').textContent = err.message; }
  finally { showLoading(false); }
}
