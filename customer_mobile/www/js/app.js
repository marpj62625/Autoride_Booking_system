/**
 * Autoride Customer Mobile App - Main Application Script
 * utils.js is loaded as a separate script tag before this file
 */

// CONFIG
var API_BASE = 'https://autoride-booking-system.vercel.app/api';

// STATE
var currentUser = { id: null, fullName: '', isVerified: 0, loyaltyPoints: 0 };
var allVehicles = [];
var currentVehicleDetail = null;
var activeBookingId = null;
var activeBookingData = null;
var gpsRefreshInterval = null;
var profilePicBlob = null;
var licenseBlob = null;
var inspectionPhotos = [];
var pendingOtpEmail = '';
var pendingOtpPhone = '';
var appSettings = {
  mileage_limit: '250',
  long_term_discount_days: '7',
  long_term_discount_percent: '10',
  rental_terms: ''
};
var couponData = null;
var selectedAddons = [];
var selectedInsurance = { type: 'Basic', price: 0 };
var bookingFormVehicle = null;
var paymentProofBlob = null;
var selectedRating = 0;
var gpsMap = null;
var gpsMarker = null;

// CAPACITOR PLUGINS (safe access)
function getPreferences() {
  return (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Preferences) || null;
}
function getCamera() {
  return (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Camera) || null;
}

// SESSION
var Session = {
  save: function(user) {
    var prefs = getPreferences();
    if (prefs) {
      prefs.set({ key: 'user', value: JSON.stringify(user) });
    } else {
      try { localStorage.setItem('user', JSON.stringify(user)); } catch(e) {}
    }
  },
  load: function() {
    return new Promise(function(resolve) {
      var prefs = getPreferences();
      if (prefs) {
        prefs.get({ key: 'user' }).then(function(result) {
          try { resolve(result.value ? JSON.parse(result.value) : null); } catch(e) { resolve(null); }
        }).catch(function() { resolve(null); });
      } else {
        try {
          var v = localStorage.getItem('user');
          resolve(v ? JSON.parse(v) : null);
        } catch(e) { resolve(null); }
      }
    });
  },
  clear: function() {
    var prefs = getPreferences();
    if (prefs) {
      prefs.remove({ key: 'user' });
    } else {
      try { localStorage.removeItem('user'); } catch(e) {}
    }
  }
};

// NOTIFICATION STORE
var NotifStore = {
  getAll: function() {
    return new Promise(function(resolve) {
      var prefs = getPreferences();
      if (prefs) {
        prefs.get({ key: 'notifications' }).then(function(r) {
          try { resolve(r.value ? JSON.parse(r.value) : []); } catch(e) { resolve([]); }
        }).catch(function() { resolve([]); });
      } else {
        try {
          var v = localStorage.getItem('notifications');
          resolve(v ? JSON.parse(v) : []);
        } catch(e) { resolve([]); }
      }
    });
  },
  add: function(msg) {
    var self = this;
    self.getAll().then(function(all) {
      all.unshift({ msg: msg, ts: new Date().toISOString(), read: false });
      var data = JSON.stringify(all.slice(0, 50));
      var prefs = getPreferences();
      if (prefs) {
        prefs.set({ key: 'notifications', value: data });
      } else {
        try { localStorage.setItem('notifications', data); } catch(e) {}
      }
      updateNotifBadge();
    });
  },
  markAllRead: function() {
    var self = this;
    self.getAll().then(function(all) {
      all.forEach(function(n) { n.read = true; });
      var data = JSON.stringify(all);
      var prefs = getPreferences();
      if (prefs) {
        prefs.set({ key: 'notifications', value: data });
      } else {
        try { localStorage.setItem('notifications', data); } catch(e) {}
      }
      updateNotifBadge();
    });
  }
};

// API HELPERS
function apiCall(endpoint, options) {
  options = options || {};
  var url = API_BASE + endpoint;
  var headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
  return fetch(url, Object.assign({}, options, { headers: headers }))
    .then(function(res) {
      return res.json().then(function(data) {
        if (!res.ok) {
          if ((res.status === 401 || res.status === 403) && !data.verification_required && !data.reason) {
            Session.clear();
            showPage('page-login');
          }
          var err = new Error(data.error || data.message || 'Request failed');
          err.status = res.status;
          err.data = data;
          throw err;
        }
        return data;
      });
    })
    .catch(function(err) {
      if (err.status) throw err;
      var netErr = new Error('Network error. Please check your connection.');
      netErr.status = 0;
      throw netErr;
    });
}

function uploadFile(endpoint, formData) {
  var url = API_BASE + endpoint;
  return fetch(url, { method: 'POST', body: formData })
    .then(function(res) {
      return res.json().then(function(data) {
        if (!res.ok) {
          var err = new Error(data.error || 'Upload failed');
          err.status = res.status;
          throw err;
        }
        return data;
      });
    })
    .catch(function(err) {
      if (err.status) throw err;
      var netErr = new Error('Network error during upload.');
      netErr.status = 0;
      throw netErr;
    });
}

// UI HELPERS
function showLoading(show) {
  var el = document.getElementById('loadingOverlay');
  if (el) el.style.display = show ? 'flex' : 'none';
}

function showToast(message, type) {
  type = type || 'info';
  var existing = document.querySelector('.toast');
  if (existing) existing.remove();
  var t = document.createElement('div');
  t.className = 'toast toast-' + type;
  t.textContent = message;
  document.body.appendChild(t);
  requestAnimationFrame(function() { t.classList.add('show'); });
  setTimeout(function() {
    t.classList.remove('show');
    setTimeout(function() { if (t.parentNode) t.remove(); }, 300);
  }, 3000);
}

var MAIN_PAGES = ['page-home', 'page-vehicles', 'page-bookings', 'page-profile', 'page-more'];
var NAV_MAP = {
  'page-home': 'nav-home',
  'page-vehicles': 'nav-vehicles',
  'page-bookings': 'nav-bookings',
  'page-profile': 'nav-profile',
  'page-more': 'nav-more'
};

function showPage(id) {
  // Close ALL overlays first
  var overlays = document.querySelectorAll('.overlay-page');
  for (var i = 0; i < overlays.length; i++) {
    overlays[i].classList.remove('active');
    overlays[i].style.display = 'none';
  }
  stopGpsPolling();

  // Hide splash
  var splash = document.getElementById('page-splash');
  if (splash) { splash.style.display = 'none'; }

  // Hide all pages and auth pages
  var pages = document.querySelectorAll('.page, .auth-page');
  for (var i = 0; i < pages.length; i++) {
    pages[i].classList.remove('active');
    pages[i].style.display = 'none';
  }

  // Show target
  var target = document.getElementById(id);
  if (!target) return;

  if (target.classList.contains('auth-page')) {
    target.style.display = 'flex';
  } else {
    target.style.display = 'block';
  }
  target.classList.add('active');

  // Bottom nav
  var nav = document.getElementById('bottomNav');
  if (nav) {
    if (MAIN_PAGES.indexOf(id) >= 0) {
      nav.classList.remove('hidden');
      var navIds = Object.values ? Object.values(NAV_MAP) : ['nav-home','nav-vehicles','nav-bookings','nav-profile','nav-more'];
      navIds.forEach(function(nid) {
        var el = document.getElementById(nid);
        if (el) el.classList.remove('active');
      });
      if (NAV_MAP[id]) {
        var activeNav = document.getElementById(NAV_MAP[id]);
        if (activeNav) activeNav.classList.add('active');
      }
    } else {
      nav.classList.add('hidden');
    }
  }

  // Page load hooks
  if (id === 'page-home') loadHome();
  if (id === 'page-vehicles') loadVehicles();
  if (id === 'page-bookings') loadBookings();
  if (id === 'page-profile') loadProfile();
}

function showOverlay(id) {
  var el = document.getElementById(id);
  if (!el) return;
  el.classList.add('active');
  el.style.display = 'block';
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
  var el = document.getElementById(id);
  if (!el) return;
  el.classList.remove('active');
  el.style.display = 'none';
  if (id === 'page-gps-map') stopGpsPolling();
}

function statusPill(status) {
  var map = {
    'Pending': 'pill-pending', 'Confirmed': 'pill-confirmed', 'Approved': 'pill-approved',
    'Picked Up': 'pill-picked-up', 'Completed': 'pill-completed', 'Cancelled': 'pill-cancelled',
    'Rejected': 'pill-rejected', 'Unpaid': 'pill-unpaid', 'Partially Paid': 'pill-partially-paid',
    'Paid': 'pill-paid', 'Refund Pending': 'pill-refund-pending', 'Refunded': 'pill-refunded'
  };
  return '<span class="pill ' + (map[status] || '') + '">' + (status || '-') + '</span>';
}

function updateNotifBadge() {
  NotifStore.getAll().then(function(all) {
    var unread = all.filter(function(n) { return !n.read; }).length;
    var badge = document.getElementById('notifBadge');
    if (badge) {
      badge.textContent = unread;
      if (unread === 0) badge.classList.add('hidden');
      else badge.classList.remove('hidden');
    }
  });
}

// STARTUP - run immediately when script loads, also on events as fallback
var _appInitialized = false;
function initApp() {
  if (_appInitialized) return;
  _appInitialized = true;
  Session.load().then(function(user) {
    if (user && user.id) {
      currentUser = user;
      // Always refresh verification status from server
      apiCall('/user/verify-status?user_id=' + user.id)
        .then(function(v) {
          currentUser.isVerified = v.is_verified !== undefined ? v.is_verified : user.isVerified;
          Session.save(currentUser);
        }).catch(function() {});
      apiCall('/public/settings').then(function(s) {
        Object.assign(appSettings, s);
      }).catch(function() {});
      showPage('page-home');
    } else {
      showPage('page-login');
    }
    updateNotifBadge();
  }).catch(function() {
    showPage('page-login');
  });
}

// Try immediately (script already loaded after DOM)
initApp();

// Also listen for events as fallback
document.addEventListener('DOMContentLoaded', initApp);
document.addEventListener('deviceready', initApp);

// AUTH: LOGIN
function doLogin() {
  var email = sanitizeInput(document.getElementById('loginEmail').value.trim());
  var password = document.getElementById('loginPassword').value;
  document.getElementById('loginEmailErr').textContent = '';
  document.getElementById('loginPasswordErr').textContent = '';
  document.getElementById('loginErr').textContent = '';
  if (isBlank(email)) { document.getElementById('loginEmailErr').textContent = 'Email is required.'; return; }
  if (!isGmailAddress(email)) { document.getElementById('loginEmailErr').textContent = 'Only @gmail.com emails are allowed.'; return; }
  if (isBlank(password)) { document.getElementById('loginPasswordErr').textContent = 'Password is required.'; return; }
  showLoading(true);
  apiCall('/login', { method: 'POST', body: JSON.stringify({ email: email, password: password }) })
    .then(function(data) {
      currentUser = { id: data.user_id, fullName: data.full_name, isVerified: data.is_verified || 0 };
      Session.save(currentUser);
      // Always fetch fresh verification status after login
      apiCall('/user/verify-status?user_id=' + data.user_id)
        .then(function(v) {
          currentUser.isVerified = v.is_verified !== undefined ? v.is_verified : (data.is_verified || 0);
          Session.save(currentUser);
        }).catch(function() {});
      apiCall('/public/settings').then(function(s) { Object.assign(appSettings, s); }).catch(function() {});
      showPage('page-home');
    })
    .catch(function(err) {
      if (err.status === 403 && err.data && err.data.reason) {
        document.getElementById('loginErr').textContent = err.data.reason;
      } else if (err.status === 403) {
        pendingOtpEmail = email;
        document.getElementById('otpEmailDisplay').textContent = email;
        showPage('page-otp-verify');
      } else {
        document.getElementById('loginErr').textContent = err.message || 'Invalid credentials.';
      }
    })
    .finally(function() { showLoading(false); });
}

function doGoogleLogin() {
  showToast('Google Sign-In requires native setup. Use email login.', 'info');
}

function doLogout() {
  Session.clear();
  currentUser = { id: null, fullName: '', isVerified: 0 };
  showPage('page-login');
}

// AUTH: REGISTER
function doRegister() {
  var name = sanitizeInput(document.getElementById('regName').value.trim());
  var email = sanitizeInput(document.getElementById('regEmail').value.trim());
  var password = document.getElementById('regPassword').value;
  ['regNameErr','regEmailErr','regPasswordErr','regErr'].forEach(function(id) {
    document.getElementById(id).textContent = '';
  });
  if (isBlank(name)) { document.getElementById('regNameErr').textContent = 'Full name is required.'; return; }
  if (!isGmailAddress(email)) { document.getElementById('regEmailErr').textContent = 'Only @gmail.com emails are allowed for registration.'; return; }
  if (isBlank(password) || password.length < 8) { document.getElementById('regPasswordErr').textContent = 'Password must be at least 8 characters.'; return; }
  showLoading(true);
  apiCall('/register', { method: 'POST', body: JSON.stringify({ name: name, email: email, password: password }) })
    .then(function() {
      pendingOtpEmail = email;
      document.getElementById('otpEmailDisplay').textContent = email;
      showToast('Verification code sent to your email!', 'success');
      showPage('page-otp-verify');
    })
    .catch(function(err) {
      if (err.status === 409) {
        document.getElementById('regEmailErr').textContent = 'Email already registered.';
      } else {
        document.getElementById('regErr').textContent = err.message || 'Registration failed.';
      }
    })
    .finally(function() { showLoading(false); });
}

// AUTH: OTP
function otpNext(el, nextIdx) {
  if (el.value.length >= 1 && nextIdx >= 0) {
    var next = document.getElementById('otp' + nextIdx);
    if (next) next.focus();
  }
}

function getOtpValue(prefix) {
  var val = '';
  for (var i = 0; i < 6; i++) {
    var el = document.getElementById(prefix + i);
    val += el ? (el.value || '') : '';
  }
  return val;
}

function doVerifyEmail() {
  var otp = getOtpValue('otp');
  document.getElementById('otpErr').textContent = '';
  if (otp.length < 6) { document.getElementById('otpErr').textContent = 'Please enter the full 6-digit code.'; return; }
  showLoading(true);
  apiCall('/auth/verify-email', { method: 'POST', body: JSON.stringify({ email: pendingOtpEmail, otp: otp }) })
    .then(function() {
      showToast('Email verified! Please log in.', 'success');
      showPage('page-login');
    })
    .catch(function(err) {
      document.getElementById('otpErr').textContent = err.message || 'Invalid or expired verification code.';
    })
    .finally(function() { showLoading(false); });
}

function resendOtp() {
  if (!pendingOtpEmail) return;
  showToast('Resending code...', 'info');
}

function otpNextSms(el, nextIdx) {
  if (el.value.length >= 1 && nextIdx >= 0) {
    var next = document.getElementById('smsOtp' + nextIdx);
    if (next) next.focus();
  }
}

function doRequestOtp() {
  var raw = document.getElementById('phoneNumber').value.trim();
  document.getElementById('phoneErr').textContent = '';
  if (isBlank(raw)) { document.getElementById('phoneErr').textContent = 'Phone number is required.'; return; }
  var phone = normalizePhone(raw);
  pendingOtpPhone = phone;
  showLoading(true);
  apiCall('/auth/request-otp', { method: 'POST', body: JSON.stringify({ phone: phone }) })
    .then(function() {
      document.getElementById('phoneStep1').classList.add('hidden');
      document.getElementById('phoneStep2').classList.remove('hidden');
      showToast('OTP sent to your phone!', 'success');
    })
    .catch(function(err) {
      document.getElementById('phoneErr').textContent = err.message || 'Failed to send OTP.';
    })
    .finally(function() { showLoading(false); });
}

function doVerifyPhone() {
  var otp = getOtpValue('smsOtp');
  document.getElementById('smsOtpErr').textContent = '';
  if (otp.length < 6) { document.getElementById('smsOtpErr').textContent = 'Please enter the full 6-digit code.'; return; }
  showLoading(true);
  apiCall('/auth/verify-otp', { method: 'POST', body: JSON.stringify({ phone: pendingOtpPhone, otp: otp }) })
    .then(function(data) {
      currentUser = { id: data.user_id, fullName: data.full_name, isVerified: 0 };
      Session.save(currentUser);
      showPage('page-home');
    })
    .catch(function(err) {
      document.getElementById('smsOtpErr').textContent = err.message || 'Invalid or expired OTP.';
    })
    .finally(function() { showLoading(false); });
}

// HOME
function loadHome() {
  var nameEl = document.getElementById('homeUserName');
  if (nameEl) nameEl.textContent = currentUser.fullName || 'there';
  apiCall('/user/points?user_id=' + currentUser.id)
    .then(function(pts) {
      var pts_val = parseInt(pts.points) || 0;
      var el = document.getElementById('homePoints');
      if (el) el.textContent = pts_val.toLocaleString();
      var el2 = document.getElementById('homePoints2');
      if (el2) el2.textContent = pts_val.toLocaleString();
      currentUser.loyaltyPoints = pts_val;
      var progress = Math.min(100, (pts_val / 2000) * 100);
      var bar = document.getElementById('loyaltyBar');
      if (bar) bar.style.width = progress + '%';
      var ptsNeeded = document.getElementById('ptsNeeded');
      if (ptsNeeded) ptsNeeded.textContent = Math.max(0, 2000 - pts_val).toLocaleString() + ' pts more to unlock Gold benefits';
    }).catch(function() {});
  apiCall('/user-bookings?user_id=' + currentUser.id)
    .then(function(bookings) {
      var recent = bookings.slice(0, 3);
      var el = document.getElementById('recentBookings');
      if (!el) return;
      if (!recent.length) {
        el.innerHTML = '<div class="empty-state"><i class="fas fa-calendar-times"></i><p>No bookings yet</p></div>';
      } else {
        var statusColors = {
          'Pending': '#fbbf24', 'Confirmed': '#34d399', 'Approved': '#34d399',
          'Picked Up': '#a78bfa', 'Completed': '#a78bfa', 'Cancelled': '#f87171', 'Rejected': '#f87171'
        };
        el.innerHTML = recent.map(function(b) {
          var color = statusColors[b.status] || '#a1a1aa';
          return '<div style="background:#141414;border:1px solid rgba(255,255,255,0.06);border-radius:20px;overflow:hidden;margin-bottom:10px;cursor:pointer;" onclick="openBookingDetail(' + b.id + ')">' +
            '<div style="height:3px;background:' + color + ';opacity:0.5;"></div>' +
            '<div style="padding:14px;display:flex;align-items:center;gap:12px;">' +
            '<div style="width:48px;height:48px;border-radius:14px;background:#1a1a1a;display:flex;align-items:center;justify-content:center;flex-shrink:0;">' +
            '<i class="fas fa-car" style="color:#52525b;font-size:1.1rem;"></i></div>' +
            '<div style="flex:1;min-width:0;">' +
            '<div style="font-weight:800;font-size:0.875rem;color:#fff;">' + (b.brand || '') + ' ' + (b.model || '') + '</div>' +
            '<div style="font-size:0.72rem;color:#52525b;margin-top:2px;">' + b.start_date + ' to ' + b.end_date + '</div>' +
            '<span style="display:inline-block;margin-top:6px;padding:3px 10px;border-radius:20px;font-size:0.65rem;font-weight:700;background:' + color + '22;color:' + color + ';">' + b.status + '</span>' +
            '</div>' +
            '<div style="text-align:right;flex-shrink:0;">' +
            '<div style="font-weight:800;font-size:0.875rem;color:#fff;">' + formatPHP(b.total_price) + '</div>' +
            '</div></div></div>';
        }).join('');
      }
    }).catch(function() {});
  updateNotifBadge();
}

function buildImgUrl(path) {
  if (!path) return 'https://via.placeholder.com/400x200?text=No+Image';
  if (path.startsWith('http')) return path;
  return API_BASE.replace('/api', '') + '/' + path;
}

function searchVehicles(query) {
  var q = (query || '').toLowerCase();
  var filtered = q ? allVehicles.filter(function(v) {
    return (v.brand + ' ' + v.model + ' ' + (v.vehicle_type || '') + ' ' + (v.location || '')).toLowerCase().indexOf(q) >= 0;
  }) : allVehicles;
  var countEl = document.getElementById('vehicleCount');
  if (countEl) countEl.textContent = filtered.length + ' vehicle' + (filtered.length !== 1 ? 's' : '') + ' found';
  renderVehicles(filtered);
}

// VEHICLES - Step 1: Browse models
function loadVehicles() {
  showLoading(true);
  apiCall('/vehicles/categories')
    .then(function(data) {
      allVehicles = data;
      renderVehicles(data);
    })
    .catch(function(err) {
      var grid = document.getElementById('vehicleGrid');
      if (grid) grid.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>' + err.message + '</p></div>';
    })
    .finally(function() { showLoading(false); });
}

function renderVehicles(list) {
  var grid = document.getElementById('vehicleGrid');
  if (!grid) return;
  if (!list.length) {
    grid.innerHTML = '<div class="empty-state"><i class="fas fa-car"></i><p>No vehicles found</p></div>';
    return;
  }
  var countEl = document.getElementById('vehicleCount');
  if (countEl) countEl.textContent = list.length + ' vehicle' + (list.length !== 1 ? 's' : '') + ' found';
  grid.innerHTML = list.map(function(v) {
    var avail = parseInt(v.available_units) || 0;
    var badgeClass = avail > 0 ? 'badge-avail-yes' : 'badge-avail-no';
    var badgeText = avail > 0 ? ('<span style="width:7px;height:7px;border-radius:50%;background:#6ee7b7;display:inline-block;margin-right:5px;"></span>' + avail + ' available') : 'Unavailable';
    var bEnc = encodeURIComponent(v.brand);
    var mEnc = encodeURIComponent(v.model);
    return '<div class="vehicle-card" onclick="openColorSelection(\'' + bEnc + '\',\'' + mEnc + '\')">' +
      '<div class="vehicle-img-wrap">' +
      '<img src="' + buildImgUrl(v.vehicle_image) + '" alt="' + v.brand + ' ' + v.model + '" onerror="this.src=\'https://via.placeholder.com/400x200?text=No+Image\'">' +
      '<span class="badge-available ' + badgeClass + '">' + badgeText + '</span>' +
      '</div>' +
      '<div class="vehicle-info">' +
      '<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px;">' +
      '<div>' +
      '<h3>' + v.brand + ' ' + v.model + '</h3>' +
      '<div style="display:flex;gap:6px;margin-top:4px;">' +
      '<span style="background:#1f1f1f;color:#71717a;padding:2px 8px;border-radius:20px;font-size:0.65rem;font-weight:600;">' + (v.vehicle_type || '-') + '</span>' +
      '<span style="background:#1f1f1f;color:#71717a;padding:2px 8px;border-radius:20px;font-size:0.65rem;font-weight:600;">' + (v.transmission || '-') + '</span>' +
      '</div></div>' +
      '<div style="text-align:right;">' +
      '<div class="vehicle-rate">' + formatPHP(v.daily_rate) + '</div>' +
      '<div style="font-size:0.65rem;color:#52525b;margin-top:1px;">per day</div>' +
      '</div></div>' +
      '<div style="display:flex;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid rgba(255,255,255,0.05);">' +
      '<div style="display:flex;align-items:center;gap:6px;">' +
      '<i class="fas fa-map-marker-alt" style="color:#3f3f46;font-size:0.75rem;"></i>' +
      '<span style="font-size:0.75rem;color:#52525b;">' + (v.location || '-') + '</span>' +
      '</div>' +
      '<div style="display:flex;align-items:center;gap:4px;background:rgba(220,38,38,0.1);color:#f87171;padding:5px 12px;border-radius:12px;font-size:0.75rem;font-weight:700;">' +
      'View <i class="fas fa-chevron-right" style="font-size:0.6rem;"></i></div>' +
      '</div></div></div>';
  }).join('');
}

function filterVehicles(filter, chipEl) {
  var chips = document.querySelectorAll('#vehicleFilters .chip');
  for (var i = 0; i < chips.length; i++) chips[i].classList.remove('active');
  chipEl.classList.add('active');
  if (filter === 'all') { renderVehicles(allVehicles); return; }
  var filtered = allVehicles.filter(function(v) {
    return v.vehicle_type === filter || v.transmission === filter || v.fuel_type === filter;
  });
  renderVehicles(filtered);
}

// VEHICLES - Step 2: Color selection
function openColorSelection(brand, model) {
  showLoading(true);
  apiCall('/vehicles/colors?brand=' + encodeURIComponent(brand) + '&model=' + encodeURIComponent(model))
    .then(function(colors) {
      renderColorSelection(brand, model, colors);
      showOverlay('page-color-selection');
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

function renderColorSelection(brand, model, colors) {
  var el = document.getElementById('colorSelectionContent');
  if (!el) return;
  var colorCards = colors.map(function(c) {
    var colorName = c.color || 'Not Specified';
    var available = parseInt(c.available) || 0;
    var total = parseInt(c.total) || 0;
    var colorStyle = getColorStyle(colorName);
    return '<div class="card" style="cursor:pointer;margin-bottom:10px;" onclick="openVehicleUnits(\'' +
      encodeURIComponent(brand) + '\',\'' + encodeURIComponent(model) + '\',\'' + encodeURIComponent(colorName) + '\')">' +
      '<div style="display:flex;align-items:center;gap:14px;">' +
      '<div style="width:44px;height:44px;border-radius:50%;background:' + colorStyle + ';border:2px solid var(--border);flex-shrink:0;"></div>' +
      '<div style="flex:1;">' +
      '<div style="font-weight:700;font-size:0.95rem;">' + colorName + '</div>' +
      '<div style="font-size:0.78rem;color:var(--text-secondary);">' + available + ' available of ' + total + ' units</div>' +
      '</div>' +
      '<i class="fas fa-chevron-right" style="color:var(--text-muted);"></i>' +
      '</div></div>';
  }).join('');

  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-color-selection\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>' + brand + ' ' + model + '</h2></div>' +
    '<div class="scroll-content">' +
    '<p style="font-size:0.875rem;color:var(--text-secondary);margin-bottom:16px;">Select a color to view available units:</p>' +
    colorCards +
    '<div class="card" style="cursor:pointer;margin-bottom:10px;border:1.5px dashed var(--border);" onclick="openVehicleUnits(\'' +
    encodeURIComponent(brand) + '\',\'' + encodeURIComponent(model) + '\',\'all\')">' +
    '<div style="display:flex;align-items:center;gap:14px;">' +
    '<div style="width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#e63946,#4361ee,#2dc653);border:2px solid var(--border);flex-shrink:0;"></div>' +
    '<div style="flex:1;"><div style="font-weight:700;font-size:0.95rem;">View All Colors</div></div>' +
    '<i class="fas fa-chevron-right" style="color:var(--text-muted);"></i>' +
    '</div></div>' +
    '</div>';
}

function getColorStyle(colorName) {
  var map = {
    'red': '#e63946', 'white': '#f8f9fa', 'black': '#212529', 'silver': '#adb5bd',
    'gray': '#6c757d', 'grey': '#6c757d', 'blue': '#4361ee', 'green': '#2dc653',
    'yellow': '#ffc107', 'orange': '#f4a261', 'brown': '#795548', 'gold': '#ffd700',
    'maroon': '#800000', 'beige': '#f5f5dc', 'pearl': '#f0ece3', 'champagne': '#f7e7ce'
  };
  var key = colorName.toLowerCase().trim();
  return map[key] || '#dee2e6';
}

// VEHICLES - Step 3: Individual units
function openVehicleUnits(brandEnc, modelEnc, colorEnc) {
  var brand = decodeURIComponent(brandEnc);
  var model = decodeURIComponent(modelEnc);
  var color = decodeURIComponent(colorEnc);
  showLoading(true);
  apiCall('/vehicles/units?brand=' + brandEnc + '&model=' + modelEnc + '&color=' + colorEnc + '&user_id=' + (currentUser.id || ''))
    .then(function(units) {
      renderVehicleUnits(brand, model, color, units);
      showOverlay('page-vehicle-units');
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

function renderVehicleUnits(brand, model, color, units) {
  var el = document.getElementById('vehicleUnitsContent');
  if (!el) return;
  var title = brand + ' ' + model + (color !== 'all' ? ' (' + color + ')' : '');
  var unitsHtml = units.map(function(v) {
    var isAvailable = ['Available'].indexOf(v.status) >= 0;
    var statusColor = isAvailable ? 'var(--success)' : (v.status === 'Booked' ? 'var(--info)' : 'var(--warning)');
    var imgSrc = (v.gallery && v.gallery.length) ? buildImgUrl(v.gallery[0]) : buildImgUrl(v.vehicle_image);
    return '<div class="card" style="margin-bottom:14px;">' +
      '<div style="position:relative;height:180px;border-radius:var(--radius-sm);overflow:hidden;margin-bottom:12px;">' +
      '<img src="' + imgSrc + '" style="width:100%;height:100%;object-fit:cover;" onerror="this.src=\'https://via.placeholder.com/400x180?text=No+Image\'">' +
      '<span style="position:absolute;top:8px;right:8px;background:' + statusColor + ';color:#fff;font-size:0.7rem;font-weight:700;padding:4px 10px;border-radius:20px;">' + v.status + '</span>' +
      (v.color_display && v.color_display !== 'Not Specified' ? '<span style="position:absolute;top:8px;left:8px;background:rgba(0,0,0,0.6);color:#fff;font-size:0.7rem;padding:4px 8px;border-radius:20px;">' + v.color_display + '</span>' : '') +
      '</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;">' +
      '<div style="font-size:0.78rem;"><span style="color:var(--text-muted);">Plate</span><br><strong>' + (v.plate_number || 'N/A') + '</strong></div>' +
      '<div style="font-size:0.78rem;"><span style="color:var(--text-muted);">Seats</span><br><strong>' + (v.seats || '-') + '</strong></div>' +
      '<div style="font-size:0.78rem;"><span style="color:var(--text-muted);">Fuel</span><br><strong>' + (v.fuel_type || '-') + '</strong></div>' +
      '<div style="font-size:0.78rem;"><span style="color:var(--text-muted);">Transmission</span><br><strong>' + (v.transmission || '-') + '</strong></div>' +
      '<div style="font-size:0.78rem;"><span style="color:var(--text-muted);">Location</span><br><strong>' + (v.location || '-') + '</strong></div>' +
      '<div style="font-size:0.78rem;"><span style="color:var(--text-muted);">Rate</span><br><strong style="color:var(--primary);">' + formatPHP(v.daily_rate) + '/day</strong></div>' +
      '</div>' +
      (isAvailable
        ? '<button class="btn-primary" onclick="openVehicleDetail(' + v.id + ')"><i class="fas fa-calendar-plus"></i> Book This Vehicle</button>'
        : '<button class="btn-secondary" disabled style="opacity:0.5;cursor:not-allowed;"><i class="fas fa-ban"></i> Not Available (' + v.status + ')</button>'
      ) +
      '</div>';
  }).join('');

  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-vehicle-units\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>' + title + '</h2></div>' +
    '<div class="scroll-content" style="padding-bottom:80px;">' +
    '<p style="font-size:0.875rem;color:var(--text-secondary);margin-bottom:16px;">' + units.length + ' unit(s) found</p>' +
    (units.length ? unitsHtml : '<div class="empty-state"><i class="fas fa-car"></i><p>No units found for this selection</p></div>') +
    '</div>';
}

function toggleFav(vehicleId, btn) {
  if (!currentUser.id) { showToast('Please log in first.', 'error'); return; }
  apiCall('/toggle-favorite', { method: 'POST', body: JSON.stringify({ user_id: currentUser.id, vehicle_id: vehicleId }) })
    .then(function(data) {
      if (btn) btn.classList.toggle('active', data.is_favorite);
      showToast(data.message, 'success');
    })
    .catch(function(err) { showToast(err.message, 'error'); });
}

function renderVehicles(list) {
  var grid = document.getElementById('vehicleGrid');
  if (!grid) return;
  if (!list.length) {
    grid.innerHTML = '<div class="empty-state"><i class="fas fa-car"></i><p>No vehicles found</p></div>';
    return;
  }
  grid.innerHTML = list.map(function(v) {
    var vid = v.id || v.representative_id;
    var available = parseInt(v.available_units) || 0;
    var availBadge = available > 0
      ? '<span class="badge-available">' + available + ' available</span>'
      : '<span class="badge-available" style="background:rgba(230,57,70,0.85);">Unavailable</span>';
    return '<div class="vehicle-card" onclick="openColorSelection(\'' + encodeURIComponent(v.brand) + '\',\'' + encodeURIComponent(v.model) + '\')">' +
      '<div class="vehicle-img-wrap">' +
      '<img src="' + buildImgUrl(v.vehicle_image) + '" alt="' + v.brand + ' ' + v.model + '" onerror="this.src=\'https://via.placeholder.com/400x200?text=No+Image\'">' +
      availBadge +
      '</div>' +
      '<div class="vehicle-info">' +
      '<h3>' + v.brand + ' ' + v.model + '</h3>' +
      '<div class="vehicle-meta">' + (v.vehicle_type || '-') + ' | ' + (v.transmission || '-') + ' | ' + (v.fuel_type || '-') + '</div>' +
      '<div class="vehicle-meta"><i class="fas fa-users"></i> ' + (v.seats || '-') + ' seats</div>' +
      '<div class="vehicle-location"><i class="fas fa-map-marker-alt"></i> ' + (v.location || '-') + '</div>' +
      '<div class="vehicle-rate">' + formatPHP(v.daily_rate) + ' <span>/ day</span></div>' +
      '</div></div>';
  }).join('');
}

function filterVehicles(filter, chipEl) {
  var chips = document.querySelectorAll('#vehicleFilters .chip');
  for (var i = 0; i < chips.length; i++) chips[i].classList.remove('active');
  chipEl.classList.add('active');
  if (filter === 'all') { renderVehicles(allVehicles); return; }
  var filtered = allVehicles.filter(function(v) {
    return v.vehicle_type === filter || v.transmission === filter || v.fuel_type === filter;
  });
  renderVehicles(filtered);
}

// STEP 1: Model tapped - show color selection
function openColorSelection(brandEnc, modelEnc) {
  var brand = decodeURIComponent(brandEnc);
  var model = decodeURIComponent(modelEnc);
  var el = document.getElementById('vehicleDetailContent');
  if (!el) return;
  el.innerHTML = '<div class="page-header"><button class="back-btn" onclick="closeOverlay(\'page-vehicle-detail\')"><i class="fas fa-arrow-left"></i></button><h2>' + brand + ' ' + model + '</h2></div><div class="scroll-content"><div class="empty-state"><i class="fas fa-spinner fa-spin"></i><p>Loading...</p></div></div>';
  showOverlay('page-vehicle-detail');
  showLoading(true);
  apiCall('/vehicles/colors?brand=' + encodeURIComponent(brand) + '&model=' + encodeURIComponent(model))
    .then(function(colors) {
      if (colors.length <= 1) {
        openVehicleUnits(brand, model, colors.length === 1 ? colors[0].color : 'all');
        return;
      }
      var bEnc = encodeURIComponent(brand);
      var mEnc = encodeURIComponent(model);
      var colorCards = colors.map(function(c) {
        var avail = parseInt(c.available) || 0;
        var colorName = c.color || 'Not Specified';
        var cEnc = encodeURIComponent(colorName);
        var knownColors = ['red','blue','black','white','silver','gray','grey','green','yellow','orange','brown','purple','pink','gold','beige'];
        var dot = knownColors.indexOf(colorName.toLowerCase()) >= 0
          ? '<span style="display:inline-block;width:18px;height:18px;border-radius:50%;background:' + colorName.toLowerCase() + ';border:2px solid #dee2e6;margin-right:10px;"></span>'
          : '<i class="fas fa-circle" style="color:#adb5bd;margin-right:10px;"></i>';
        return '<div class="card" style="cursor:pointer;display:flex;align-items:center;justify-content:space-between;padding:14px;" onclick="openVehicleUnits(\'' + bEnc + '\',\'' + mEnc + '\',\'' + cEnc + '\')">' +
          '<div style="display:flex;align-items:center;">' + dot + '<strong>' + colorName + '</strong></div>' +
          '<div style="text-align:right;margin-right:10px;">' +
          '<div style="font-size:0.8rem;color:#6c757d;">' + c.total + ' unit' + (c.total != 1 ? 's' : '') + '</div>' +
          '<div style="font-size:0.75rem;font-weight:700;color:' + (avail > 0 ? '#2dc653' : '#e63946') + ';">' + (avail > 0 ? avail + ' available' : 'Unavailable') + '</div>' +
          '</div><i class="fas fa-chevron-right" style="color:#adb5bd;"></i></div>';
      }).join('');
      el.innerHTML = '<div class="page-header"><button class="back-btn" onclick="closeOverlay(\'page-vehicle-detail\')"><i class="fas fa-arrow-left"></i></button><h2>' + brand + ' ' + model + '</h2></div>' +
        '<div class="scroll-content" style="padding-bottom:80px;">' +
        '<p style="font-size:0.875rem;color:#6c757d;margin-bottom:14px;"><i class="fas fa-palette" style="color:#e63946;margin-right:6px;"></i>Select a color:</p>' +
        colorCards +
        '<div class="card" style="cursor:pointer;display:flex;align-items:center;justify-content:space-between;padding:14px;" onclick="openVehicleUnits(\'' + bEnc + '\',\'' + mEnc + '\',\'all\')"><strong>Show All Colors</strong><i class="fas fa-chevron-right" style="color:#adb5bd;"></i></div>' +
        '</div>';
    })
    .catch(function(err) { showToast(err.message, 'error'); closeOverlay('page-vehicle-detail'); })
    .finally(function() { showLoading(false); });
}

// STEP 2: Color selected - show individual units
function openVehicleUnits(brandEnc, modelEnc, colorEnc) {
  var brand = decodeURIComponent(brandEnc);
  var model = decodeURIComponent(modelEnc);
  var color = decodeURIComponent(colorEnc);
  var bEnc = encodeURIComponent(brand);
  var mEnc = encodeURIComponent(model);
  var el = document.getElementById('vehicleDetailContent');
  if (!el) return;
  el.innerHTML = '<div class="page-header"><button class="back-btn" onclick="openColorSelection(\'' + bEnc + '\',\'' + mEnc + '\')"><i class="fas fa-arrow-left"></i></button><h2>' + brand + ' ' + model + '</h2></div><div class="scroll-content"><div class="empty-state"><i class="fas fa-spinner fa-spin"></i><p>Loading units...</p></div></div>';
  showLoading(true);
  apiCall('/vehicles/units?brand=' + encodeURIComponent(brand) + '&model=' + encodeURIComponent(model) + '&color=' + encodeURIComponent(color) + '&user_id=' + (currentUser.id || ''))
    .then(function(units) {
      if (!units.length) {
        el.innerHTML = '<div class="page-header"><button class="back-btn" onclick="openColorSelection(\'' + bEnc + '\',\'' + mEnc + '\')"><i class="fas fa-arrow-left"></i></button><h2>' + brand + ' ' + model + '</h2></div>' +
          '<div class="scroll-content"><div class="empty-state"><i class="fas fa-car"></i><p>No units found</p></div></div>';
        return;
      }
      var unitsHtml = units.map(function(v) {
        var isAvailable = v.status === 'Available';
        var canBook = isAvailable && parseInt(currentUser.isVerified) === 2;
        var galleryImgs = (v.gallery && v.gallery.length ? v.gallery : [v.vehicle_image]).filter(Boolean);
        var galleryHtml = galleryImgs.map(function(img) {
          return '<img class="gallery-img" src="' + buildImgUrl(img) + '" onerror="this.src=\'https://via.placeholder.com/200x130?text=No+Image\'" alt="Vehicle">';
        }).join('');
        return '<div class="card" style="margin-bottom:16px;">' +
          (galleryHtml ? '<div class="gallery-scroll" style="margin:-16px -16px 14px;">' + galleryHtml + '</div>' : '') +
          '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">' +
          '<h4 style="font-weight:800;">' + v.brand + ' ' + v.model + '</h4>' +
          '<span style="padding:4px 10px;border-radius:20px;font-size:0.72rem;font-weight:700;background:' + (isAvailable ? '#d1e7dd' : '#f8d7da') + ';color:' + (isAvailable ? '#0a3622' : '#842029') + ';">' + v.status + '</span>' +
          '</div>' +
          '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px;">' +
          '<div style="font-size:0.8rem;"><i class="fas fa-palette" style="color:var(--primary);width:16px;"></i> ' + (v.color_display || v.color || 'N/A') + '</div>' +
          '<div style="font-size:0.8rem;"><i class="fas fa-id-card" style="color:var(--primary);width:16px;"></i> ' + (v.plate_number || 'N/A') + '</div>' +
          '<div style="font-size:0.8rem;"><i class="fas fa-users" style="color:var(--primary);width:16px;"></i> ' + (v.seats || '-') + ' seats</div>' +
          '<div style="font-size:0.8rem;"><i class="fas fa-gas-pump" style="color:var(--primary);width:16px;"></i> ' + (v.fuel_type || '-') + '</div>' +
          '<div style="font-size:0.8rem;"><i class="fas fa-cog" style="color:var(--primary);width:16px;"></i> ' + (v.transmission || '-') + '</div>' +
          '<div style="font-size:0.8rem;"><i class="fas fa-map-marker-alt" style="color:var(--primary);width:16px;"></i> ' + (v.location || '-') + '</div>' +
          '</div>' +
          '<div style="display:flex;justify-content:space-between;align-items:center;">' +
          '<div class="vehicle-rate">' + formatPHP(v.daily_rate) + ' <span>/ day</span></div>' +
          (canBook
            ? '<button class="btn-primary" style="width:auto;padding:10px 20px;" onclick="selectVehicleUnit(' + v.id + ')"><i class="fas fa-calendar-plus"></i> Book</button>'
            : '<button style="width:auto;padding:10px 16px;background:var(--bg-input);color:var(--text-muted);border:none;border-radius:var(--radius-sm);font-size:0.8rem;cursor:not-allowed;" disabled>' +
              (isAvailable ? '<i class="fas fa-lock"></i> Verify License' : '<i class="fas fa-ban"></i> Not Available') + '</button>'
          ) +
          '</div></div>';
      }).join('');
      el.innerHTML = '<div class="page-header"><button class="back-btn" onclick="openColorSelection(\'' + bEnc + '\',\'' + mEnc + '\')">' +
        '<i class="fas fa-arrow-left"></i></button><h2>' + brand + ' ' + model + (color !== 'all' ? ' - ' + color : '') + '</h2></div>' +
        '<div class="scroll-content" style="padding-bottom:80px;">' + unitsHtml + '</div>';
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

// STEP 3: Book button tapped on a specific unit
function selectVehicleUnit(vehicleId) {
  showLoading(true);
  apiCall('/vehicle/' + vehicleId + '?user_id=' + (currentUser.id || ''))
    .then(function(v) {
      currentVehicleDetail = v;
      openBookingForm(vehicleId);
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

function toggleFav(vehicleId, btn) {
  if (!currentUser.id) { showToast('Please log in first.', 'error'); return; }
  apiCall('/toggle-favorite', { method: 'POST', body: JSON.stringify({ user_id: currentUser.id, vehicle_id: vehicleId }) })
    .then(function(data) {
      if (btn) btn.classList.toggle('active', data.is_favorite);
      showToast(data.message, 'success');
    })
    .catch(function(err) { showToast(err.message, 'error'); });
}

function openVehicleDetail(vehicleId) {
  showLoading(true);
  apiCall('/vehicle/' + vehicleId + '?user_id=' + (currentUser.id || ''))
    .then(function(v) {
      currentVehicleDetail = v;
      renderVehicleDetail(v);
      showOverlay('page-vehicle-detail');
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

function renderVehicleDetail(v) {
  var ltDays = parseInt(appSettings.long_term_discount_days) || 7;
  var ltPct = parseInt(appSettings.long_term_discount_percent) || 10;
  var mileage = appSettings.mileage_limit || '250';
  var canBook = parseInt(currentUser.isVerified) === 2;
  var el = document.getElementById('vehicleDetailContent');
  if (!el) return;
  var galleryImgs = (v.gallery && v.gallery.length ? v.gallery : [v.vehicle_image]).filter(Boolean);
  var galleryHtml = galleryImgs.map(function(img) {
    return '<img class="gallery-img" src="' + buildImgUrl(img) + '" onerror="this.src=\'https://via.placeholder.com/200x130?text=No+Image\'" alt="Vehicle">';
  }).join('');
  var reviewsHtml = (v.reviews && v.reviews.length) ? v.reviews.map(function(r) {
    return '<div class="review-item"><div class="reviewer">' +
      '<div class="avatar-placeholder">' + ((r.full_name || '?')[0]) + '</div>' +
      '<div><strong style="font-size:0.875rem;">' + (r.full_name || 'Customer') + '</strong></div></div>' +
      (r.comment ? '<p style="font-size:0.875rem;color:var(--text-secondary);">' + r.comment + '</p>' : '') +
      '</div>';
  }).join('') : '<div class="empty-state" style="padding:20px 0;"><p>No reviews yet</p></div>';
  var bookBtn = canBook
    ? '<button class="btn-primary" onclick="openBookingForm(' + v.id + ')"><i class="fas fa-calendar-plus"></i> Book Now</button>'
    : '<div style="background:#f8d7da;border-radius:var(--radius-sm);padding:12px;text-align:center;font-size:0.875rem;color:#842029;margin-bottom:12px;"><i class="fas fa-lock"></i> License verification required before booking.</div>';
  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-vehicle-detail\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>' + v.brand + ' ' + v.model + '</h2>' +
    '</div>' +
    '<div class="gallery-scroll">' + galleryHtml + '</div>' +
    '<div class="scroll-content">' +
    '<div class="card">' +
    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">' +
    '<div class="vehicle-rate">' + formatPHP(v.daily_rate) + ' <span>/ day</span></div>' +
    '<div style="color:#ffc107;">&#9733; ' + ((v.avg_rating || 0).toFixed(1)) + '</div>' +
    '</div>' +
    '<div class="vehicle-meta">' + (v.vehicle_type || '-') + ' | ' + (v.transmission || '-') + ' | ' + (v.fuel_type || '-') + ' | ' + (v.seats || '-') + ' seats</div>' +
    '<div class="vehicle-meta" style="margin-top:6px;"><i class="fas fa-map-marker-alt"></i> ' + (v.location || '-') + '</div>' +
    '<div style="background:#fff3cd;border-radius:var(--radius-sm);padding:10px;margin-top:10px;font-size:0.8rem;color:#856404;">' +
    'Rentals of ' + ltDays + '+ days get a <strong>' + ltPct + '% discount</strong>!</div>' +
    '<div style="background:#e8f4fd;border-radius:var(--radius-sm);padding:10px;margin-top:8px;font-size:0.8rem;color:#084298;">' +
    'Daily mileage limit: <strong>' + mileage + ' km</strong></div>' +
    '</div>' +
    bookBtn +
    '<div style="margin-top:20px;"><h4 style="font-weight:700;margin-bottom:12px;">Customer Reviews</h4>' + reviewsHtml + '</div>' +
    '</div>';
}

// BOOKING FORM
var PICKUP_LOCATIONS = [
  { label: 'San Pablo City, Laguna', value: 'San Pablo City, Laguna', province: 'Laguna', municipality: 'San Pablo City', barangay: '' },
  { label: 'Tanauan/Sto. Tomas, Batangas', value: 'Tanauan/Sto. Tomas, Batangas', province: 'Batangas', municipality: 'Tanauan', barangay: 'Sto. Tomas' }
];

var INSURANCE_OPTIONS = [
  { type: 'Basic Protection', pricePerDay: 0, desc: 'Standard passenger and third-party liability.' },
  { type: 'Standard Protection', pricePerDay: 500, desc: 'Collision Damage Waiver (CDW) with ?10k deductible.' },
  { type: 'Premium Protection', pricePerDay: 1200, desc: 'Full coverage, zero deductible, and roadside assistance.' }
];

var ADDON_OPTIONS = [
  { name: 'GPS Navigation', pricePerDay: 200 },
  { name: 'Child Safety Seat', pricePerDay: 150 },
  { name: 'Roadside Assistance', pricePerDay: 100 }
];

function openBookingForm(vehicleId) {
  bookingFormVehicle = currentVehicleDetail;
  couponData = null;
  selectedAddons = [];
  selectedInsurance = { type: 'Basic Protection', price: 0, pricePerDay: 0 };
  var today = new Date().toISOString().split('T')[0];
  var el = document.getElementById('bookingFormContent');
  if (!el) return;

  var locationOptions = PICKUP_LOCATIONS.map(function(loc, i) {
    return '<option value="' + loc.value + '">' + loc.label + '</option>';
  }).join('');

  var insuranceHtml = INSURANCE_OPTIONS.map(function(ins, i) {
    var priceLabel = ins.pricePerDay === 0 ? 'Included (?0)' : '?' + ins.pricePerDay.toLocaleString() + '/day';
    return '<div class="option-card' + (i === 0 ? ' selected' : '') + '" onclick="selectInsuranceOpt(' + i + ',this)">' +
      '<input type="radio" name="insurance"' + (i === 0 ? ' checked' : '') + '>' +
      '<div><strong>' + ins.type + '</strong> <span style="color:var(--primary);font-weight:700;">' + priceLabel + '</span>' +
      '<br><small style="color:var(--text-secondary);">' + ins.desc + '</small></div>' +
      '</div>';
  }).join('');

  var addonsHtml = ADDON_OPTIONS.map(function(addon, i) {
    return '<div class="option-card" id="addon_' + i + '" onclick="toggleAddon(' + i + ',this)">' +
      '<input type="checkbox" id="addonChk_' + i + '">' +
      '<div><strong>' + addon.name + '</strong> <span style="color:var(--primary);font-weight:700;">?' + addon.pricePerDay + '/day</span></div>' +
      '</div>';
  }).join('');

  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-booking-form\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Book ' + (bookingFormVehicle ? bookingFormVehicle.brand + ' ' + bookingFormVehicle.model : '') + '</h2>' +
    '</div>' +
    '<div class="scroll-content" style="padding-bottom:100px;">' +

    // Rental Period
    '<div class="card"><h4 style="font-weight:700;margin-bottom:14px;">Rental Period</h4>' +
    '<div class="form-group"><label>Start Date</label><input type="date" id="bfStartDate" min="' + today + '" onchange="updateBookingPrice()"><span class="field-error" id="bfStartErr"></span></div>' +
    '<div class="form-group"><label>End Date</label><input type="date" id="bfEndDate" min="' + today + '" onchange="updateBookingPrice()"><span class="field-error" id="bfEndErr"></span></div>' +
    '</div>' +

    // Pickup or Delivery
    '<div class="card"><h4 style="font-weight:700;margin-bottom:14px;">Service Type</h4>' +
    '<div class="toggle-group">' +
    '<button id="btnPickup" class="active" onclick="setServiceType(\'pickup\')"><i class="fas fa-map-marker-alt"></i> Pick-Up</button>' +
    '<button id="btnDelivery" onclick="setServiceType(\'delivery\')"><i class="fas fa-truck"></i> Delivery</button>' +
    '</div><input type="hidden" id="bfServiceType" value="pickup">' +

    // Pick-up location selector
    '<div id="pickupSection" style="margin-top:14px;">' +
    '<div class="form-group"><label>Pick-Up Location</label>' +
    '<select id="bfPickupLocation" onchange="onPickupLocationChange()">' + locationOptions + '</select></div>' +
    '<div class="form-group"><label>Return Location</label>' +
    '<select id="bfReturnLocation">' + locationOptions + '</select></div>' +
    '</div>' +

    // Delivery address with map link
    '<div id="deliverySection" style="display:none;margin-top:14px;">' +
    '<div class="form-group"><label>Delivery Address</label>' +
    '<input type="text" id="bfDeliveryAddress" placeholder="Enter full delivery address"></div>' +
    '<div class="form-group"><label>Barangay</label><input type="text" id="bfDeliveryBarangay" placeholder="Barangay"></div>' +
    '<div class="form-group"><label>Municipality / City</label><input type="text" id="bfDeliveryMunicipality" placeholder="Municipality or City"></div>' +
    '<div class="form-group"><label>Province</label><input type="text" id="bfDeliveryProvince" placeholder="Province"></div>' +
    '<a href="https://maps.google.com" target="_blank" style="display:block;text-align:center;color:var(--primary);font-size:0.875rem;margin-top:8px;"><i class="fas fa-map"></i> Open Google Maps to find your location</a>' +
    '</div></div>' +

    // Rental Type
    '<div class="card"><h4 style="font-weight:700;margin-bottom:14px;">Rental Type</h4>' +
    '<div class="toggle-group">' +
    '<button id="btnSelfDrive" class="active" onclick="setRentalType(\'Self-Drive\')">Self-Drive</button>' +
    '<button id="btnWithDriver" onclick="setRentalType(\'With Driver\')">With Driver</button>' +
    '</div><input type="hidden" id="bfRentalType" value="Self-Drive"></div>' +

    // Insurance
    '<div class="card"><h4 style="font-weight:700;margin-bottom:14px;">Preferred Insurance Coverage</h4>' +
    insuranceHtml + '</div>' +

    // Add-ons
    '<div class="card"><h4 style="font-weight:700;margin-bottom:14px;">Add-ons</h4>' +
    addonsHtml + '</div>' +

    // Payment Type
    '<div class="card"><h4 style="font-weight:700;margin-bottom:14px;">Payment Type</h4>' +
    '<div class="toggle-group">' +
    '<button id="btnFull" class="active" onclick="setPaymentType(\'Full\')">Full Payment</button>' +
    '<button id="btnDown" onclick="setPaymentType(\'Downpayment\')">20% Downpayment</button>' +
    '</div><input type="hidden" id="bfPaymentType" value="Full"></div>' +

    // Coupon
    '<div class="card"><h4 style="font-weight:700;margin-bottom:14px;">Coupon Code</h4>' +
    '<div class="coupon-row"><input type="text" id="bfCoupon" placeholder="Enter coupon code"><button onclick="applyCoupon()">Apply</button></div>' +
    '<div id="couponMsg" style="font-size:0.8rem;margin-top:6px;"></div></div>' +

    // Loyalty Points
    '<div class="card"><h4 style="font-weight:700;margin-bottom:14px;">Loyalty Points</h4>' +
    '<p style="font-size:0.875rem;color:var(--text-secondary);margin-bottom:8px;">Available: <strong>' + (currentUser.loyaltyPoints || 0) + ' pts</strong></p>' +
    '<div class="form-group"><label>Points to Redeem</label><input type="number" id="bfPoints" min="0" max="' + (currentUser.loyaltyPoints || 0) + '" value="0" onchange="updateBookingPrice()"></div>' +
    '</div>' +

    // Price Breakdown
    '<div class="card" id="priceBreakdown"><h4 style="font-weight:700;margin-bottom:14px;">Price Breakdown</h4><p style="color:var(--text-muted);font-size:0.875rem;">Select dates to see pricing</p></div>' +

    // Mileage notice
    '<div style="background:#e8f4fd;border-radius:var(--radius-sm);padding:12px;margin-bottom:12px;font-size:0.8rem;color:#084298;">Daily mileage limit: <strong>' + (appSettings.mileage_limit || 250) + ' km</strong></div>' +

    // Split Bill
    '<div class="card" style="border:2px dashed var(--primary);">' +
    '<h4 style="font-weight:700;margin-bottom:8px;"><i class="fas fa-users" style="color:var(--primary);"></i> Split this Bill with a Friend?</h4>' +
    '<p style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:10px;">Enter your friend\'s email to split the cost after booking.</p>' +
    '<div class="form-group"><label>Friend\'s Email (optional)</label><input type="email" id="bfSplitEmail" placeholder="friend@gmail.com"></div>' +
    '</div>' +

    '<span class="field-error" id="bfErr" style="display:block;margin-bottom:12px;text-align:center;"></span>' +
    '<button class="btn-primary" style="margin-bottom:20px;" onclick="submitBooking()"><i class="fas fa-check"></i> Confirm Booking</button>' +
    '</div>';

  showOverlay('page-booking-form');
  // Auto-set return location to match pickup
  onPickupLocationChange();
}

function setServiceType(type) {
  document.getElementById('bfServiceType').value = type;
  document.getElementById('btnPickup').classList.toggle('active', type === 'pickup');
  document.getElementById('btnDelivery').classList.toggle('active', type === 'delivery');
  document.getElementById('pickupSection').style.display = type === 'pickup' ? 'block' : 'none';
  document.getElementById('deliverySection').style.display = type === 'delivery' ? 'block' : 'none';
}

function onPickupLocationChange() {
  var pickupEl = document.getElementById('bfPickupLocation');
  var returnEl = document.getElementById('bfReturnLocation');
  if (pickupEl && returnEl) {
    returnEl.value = pickupEl.value;
  }
}

function selectInsuranceOpt(idx, el) {
  var ins = INSURANCE_OPTIONS[idx];
  var days = getBookingDays();
  selectedInsurance = { type: ins.type, pricePerDay: ins.pricePerDay, price: ins.pricePerDay * days };
  var cards = document.querySelectorAll('#bookingFormContent .option-card');
  for (var i = 0; i < cards.length; i++) {
    if (cards[i].querySelector('input[name="insurance"]')) cards[i].classList.remove('selected');
  }
  if (el) el.classList.add('selected');
  updateBookingPrice();
}

function toggleAddon(idx, el) {
  var addon = ADDON_OPTIONS[idx];
  var chk = document.getElementById('addonChk_' + idx);
  var days = getBookingDays();
  var existing = selectedAddons.findIndex(function(a) { return a.name === addon.name; });
  if (existing >= 0) {
    selectedAddons.splice(existing, 1);
    if (el) el.classList.remove('selected');
    if (chk) chk.checked = false;
  } else {
    selectedAddons.push({ name: addon.name, price: addon.pricePerDay * days, pricePerDay: addon.pricePerDay });
    if (el) el.classList.add('selected');
    if (chk) chk.checked = true;
  }
  updateBookingPrice();
}

function getBookingDays() {
  var startEl = document.getElementById('bfStartDate');
  var endEl = document.getElementById('bfEndDate');
  if (!startEl || !endEl || !startEl.value || !endEl.value) return 1;
  var start = new Date(startEl.value);
  var end = new Date(endEl.value);
  return Math.max(1, Math.round((end - start) / (1000 * 60 * 60 * 24)));
}

function setRentalType(type) {
  var el = document.getElementById('bfRentalType');
  if (el) el.value = type;
  var sd = document.getElementById('btnSelfDrive');
  var wd = document.getElementById('btnWithDriver');
  if (sd) sd.classList.toggle('active', type === 'Self-Drive');
  if (wd) wd.classList.toggle('active', type === 'With Driver');
}

function setPaymentType(type) {
  var el = document.getElementById('bfPaymentType');
  if (el) el.value = type;
  var bf = document.getElementById('btnFull');
  var bd = document.getElementById('btnDown');
  if (bf) bf.classList.toggle('active', type === 'Full');
  if (bd) bd.classList.toggle('active', type === 'Downpayment');
  updateBookingPrice();
}

function selectInsurance(type, price, el) {
  selectedInsurance = { type: type, price: price };
  var cards = document.querySelectorAll('#bookingFormContent .option-card');
  for (var i = 0; i < cards.length; i++) cards[i].classList.remove('selected');
  if (el) el.classList.add('selected');
  updateBookingPrice();
}

function updateBookingPrice() {
  var startEl = document.getElementById('bfStartDate');
  var endEl = document.getElementById('bfEndDate');
  if (!startEl || !endEl) return;
  var start = startEl.value;
  var end = endEl.value;
  if (!start || !end) return;
  var v = bookingFormVehicle;
  if (!v) return;
  var days = getBookingDays();

  // Recalculate per-day prices
  var insPrice = (selectedInsurance.pricePerDay || 0) * days;
  selectedInsurance.price = insPrice;
  selectedAddons = selectedAddons.map(function(a) {
    return Object.assign({}, a, { price: a.pricePerDay * days });
  });

  var ptsEl = document.getElementById('bfPoints');
  var pts = ptsEl ? (parseInt(ptsEl.value) || 0) : 0;
  var cpPct = couponData ? couponData.discount_percent : 0;
  var result = calculateBookingPrice(
    v.daily_rate, start, end, selectedAddons, insPrice,
    parseInt(appSettings.long_term_discount_days) || 7,
    parseInt(appSettings.long_term_discount_percent) || 10,
    cpPct, pts
  );
  var payTypeEl = document.getElementById('bfPaymentType');
  var payType = payTypeEl ? payTypeEl.value : 'Full';
  var nowDue = payType === 'Downpayment' ? result.downpaymentAmount : result.total;
  var el = document.getElementById('priceBreakdown');
  if (!el) return;
  el.innerHTML = '<h4 style="font-weight:700;margin-bottom:14px;">Price Breakdown</h4>' +
    '<div class="price-row"><span>Base Rate (' + result.days + ' days ï¿½ ' + formatPHP(v.daily_rate) + ')</span><span>' + formatPHP(result.basePrice) + '</span></div>' +
    // Individual add-ons
    (selectedAddons.length > 0 ? selectedAddons.map(function(a) {
      return '<div class="price-row" style="padding-left:12px;color:var(--text-secondary);"><span><i class="fas fa-check" style="color:var(--success);margin-right:6px;"></i>' + a.name + ' (' + result.days + ' days ï¿½ ?' + a.pricePerDay + ')</span><span>' + formatPHP(a.price) + '</span></div>';
    }).join('') : '') +
    // Insurance detail
    (insPrice > 0 ? '<div class="price-row" style="padding-left:12px;color:var(--text-secondary);"><span><i class="fas fa-shield-alt" style="color:var(--info);margin-right:6px;"></i>' + selectedInsurance.type + ' (' + result.days + ' days ï¿½ ?' + selectedInsurance.pricePerDay + ')</span><span>' + formatPHP(insPrice) + '</span></div>' : '') +
    (result.longTermDiscount > 0 ? '<div class="price-row" style="color:var(--success);"><span><i class="fas fa-tag"></i> Long-term Discount (' + (appSettings.long_term_discount_percent || 10) + '%)</span><span>-' + formatPHP(result.longTermDiscount) + '</span></div>' : '') +
    (result.couponDiscount > 0 ? '<div class="price-row" style="color:var(--success);"><span><i class="fas fa-ticket-alt"></i> Coupon Discount</span><span>-' + formatPHP(result.couponDiscount) + '</span></div>' : '') +
    (result.pointsDiscount > 0 ? '<div class="price-row" style="color:var(--success);"><span><i class="fas fa-star"></i> Points Discount</span><span>-' + formatPHP(result.pointsDiscount) + '</span></div>' : '') +
    '<div class="price-row total" style="margin-top:4px;"><span>Total</span><span>' + formatPHP(result.total) + '</span></div>' +
    (payType === 'Downpayment' ? '<div class="price-row" style="color:var(--primary);font-weight:700;"><span>Due Now (20% Downpayment)</span><span>' + formatPHP(nowDue) + '</span></div>' +
    '<div class="price-row" style="color:var(--text-secondary);"><span>Remaining Balance (80%)</span><span>' + formatPHP(result.balanceAmount) + '</span></div>' : '') +
    '<div style="font-size:0.78rem;color:var(--text-muted);margin-top:8px;padding-top:8px;border-top:1px solid var(--border);"><i class="fas fa-star" style="color:#ffc107;"></i> You will earn <strong>' + result.pointsEarned + ' loyalty points</strong> from this booking</div>';
}

function applyCoupon() {
  var codeEl = document.getElementById('bfCoupon');
  var code = codeEl ? codeEl.value.trim().toUpperCase() : '';
  var msg = document.getElementById('couponMsg');
  if (!code) { if (msg) msg.innerHTML = '<span style="color:var(--danger);">Enter a coupon code.</span>'; return; }
  apiCall('/coupons/verify', { method: 'POST', body: JSON.stringify({ code: code }) })
    .then(function(data) {
      couponData = data;
      if (msg) msg.innerHTML = '<span style="color:var(--success);">' + data.discount_percent + '% discount applied!</span>';
      updateBookingPrice();
    })
    .catch(function(err) {
      couponData = null;
      if (msg) msg.innerHTML = '<span style="color:var(--danger);">' + err.message + '</span>';
      updateBookingPrice();
    });
}

function submitBooking() {
  var start = document.getElementById('bfStartDate').value;
  var end = document.getElementById('bfEndDate').value;
  document.getElementById('bfStartErr').textContent = '';
  document.getElementById('bfEndErr').textContent = '';
  document.getElementById('bfErr').textContent = '';
  var dateCheck = validateDateRange(start, end);
  if (!dateCheck.valid) {
    if (dateCheck.error && dateCheck.error.indexOf('Start') >= 0) document.getElementById('bfStartErr').textContent = dateCheck.error;
    else document.getElementById('bfEndErr').textContent = dateCheck.error;
    return;
  }
  var pts = parseInt(document.getElementById('bfPoints').value) || 0;
  var cpPct = couponData ? couponData.discount_percent : 0;
  var result = calculateBookingPrice(
    bookingFormVehicle.daily_rate, start, end, selectedAddons, selectedInsurance.price,
    parseInt(appSettings.long_term_discount_days) || 7,
    parseInt(appSettings.long_term_discount_percent) || 10,
    cpPct, pts
  );
  var payType = document.getElementById('bfPaymentType').value;
  var serviceType = document.getElementById('bfServiceType') ? document.getElementById('bfServiceType').value : 'pickup';
  var pickupLocation, pickupProvince, pickupMunicipality, pickupBarangay;
  var returnLocation, returnProvince, returnMunicipality, returnBarangay;

  if (serviceType === 'pickup') {
    var pickupSel = document.getElementById('bfPickupLocation');
    var returnSel = document.getElementById('bfReturnLocation');
    pickupLocation = pickupSel ? pickupSel.value : '';
    returnLocation = returnSel ? returnSel.value : '';
    var pickupData = PICKUP_LOCATIONS.find(function(l) { return l.value === pickupLocation; }) || {};
    var returnData = PICKUP_LOCATIONS.find(function(l) { return l.value === returnLocation; }) || {};
    pickupProvince = pickupData.province || ''; pickupMunicipality = pickupData.municipality || ''; pickupBarangay = pickupData.barangay || '';
    returnProvince = returnData.province || ''; returnMunicipality = returnData.municipality || ''; returnBarangay = returnData.barangay || '';
  } else {
    pickupLocation = [document.getElementById('bfDeliveryBarangay').value, document.getElementById('bfDeliveryMunicipality').value, document.getElementById('bfDeliveryProvince').value].filter(Boolean).join(', ');
    pickupProvince = sanitizeInput(document.getElementById('bfDeliveryProvince').value);
    pickupMunicipality = sanitizeInput(document.getElementById('bfDeliveryMunicipality').value);
    pickupBarangay = sanitizeInput(document.getElementById('bfDeliveryBarangay').value);
    returnLocation = pickupLocation; returnProvince = pickupProvince; returnMunicipality = pickupMunicipality; returnBarangay = pickupBarangay;
  }

  var splitEmail = document.getElementById('bfSplitEmail') ? document.getElementById('bfSplitEmail').value.trim() : '';

  var payload = {
    user_id: currentUser.id,
    vehicle_id: bookingFormVehicle.id,
    start_date: start, end_date: end,
    pickup_location: pickupLocation,
    pickup_province: pickupProvince, pickup_municipality: pickupMunicipality, pickup_barangay: pickupBarangay,
    return_province: returnProvince, return_municipality: returnMunicipality, return_barangay: returnBarangay,
    rental_type: document.getElementById('bfRentalType').value,
    addons: selectedAddons.map(function(a) { return a.name; }),
    insurance_type: selectedInsurance.type,
    insurance_price: selectedInsurance.price,
    base_price: result.basePrice,
    addon_price: result.addonPrice,
    total_price: result.total,
    payment_type: payType,
    applied_coupon_id: couponData ? couponData.coupon_id : null,
    discount_amount: result.couponDiscount + result.longTermDiscount,
    points_redeemed: pts,
    points_earned: result.pointsEarned,
    service_type: serviceType,
    split_with_email: splitEmail || null
  };
  // Show rental agreement before submitting
  showRentalAgreement(payload, result, payType);
}

// RENTAL AGREEMENT MODAL
var _pendingBookingPayload = null;
var _pendingPriceResult = null;
var _pendingPayType = null;

function showRentalAgreement(payload, result, payType) {
  _pendingBookingPayload = payload;
  _pendingPriceResult = result;
  _pendingPayType = payType;

  // Remove existing modal if any
  var existing = document.getElementById('rentalAgreementModal');
  if (existing) existing.remove();

  var modal = document.createElement('div');
  modal.id = 'rentalAgreementModal';
  modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:9000;display:flex;align-items:flex-end;justify-content:center;';
  modal.innerHTML =
    '<div style="background:var(--bg-card);width:100%;max-width:500px;border-radius:24px 24px 0 0;padding:24px;max-height:85vh;overflow-y:auto;">' +
    '<div style="text-align:center;margin-bottom:16px;">' +
    '<i class="fas fa-file-contract" style="font-size:2rem;color:var(--primary);"></i>' +
    '<h3 style="font-size:1.2rem;font-weight:800;margin-top:8px;">Rental Agreement</h3>' +
    '</div>' +
    '<div style="background:var(--bg-input);border-radius:var(--radius-sm);padding:14px;margin-bottom:16px;font-size:0.8rem;line-height:1.7;">' +
    '<p style="margin-bottom:8px;">By proceeding, you agree to the Autoride Rental Terms and Conditions:</p>' +
    '<p><strong>Fuel Policy:</strong> Return the vehicle with the same fuel level as at pickup.</p>' +
    '<p><strong>Mileage Rule:</strong> ' + (appSettings.mileage_limit || 250) + ' km/day limit. Excess charged at ?10/km.</p>' +
    '<p><strong>Driver Responsibility:</strong> You must be the primary driver with a valid verified license.</p>' +
    '<p><strong>Late Return:</strong> Penalty of ?500 per hour for late returns.</p>' +
    '<p><strong>Damages:</strong> Any damages not covered by your selected insurance are your responsibility.</p>' +
    '<p><strong>Cancellation:</strong> 20% reservation fee is non-refundable if cancelled less than 48 hours before pickup.</p>' +
    '</div>' +
    '<div style="background:var(--bg-input);border-radius:var(--radius-sm);padding:12px;margin-bottom:16px;font-size:0.8rem;">' +
    '<strong>Mandatory Requirements:</strong>' +
    '<ul style="margin-top:6px;padding-left:16px;">' +
    '<li>Must present 2 valid government-issued IDs upon pickup</li>' +
    '<li>Driver\'s license must be valid and verified in the system</li>' +
    '</ul>' +
    '</div>' +
    '<label style="display:flex;align-items:flex-start;gap:10px;margin-bottom:16px;font-size:0.875rem;cursor:pointer;">' +
    '<input type="checkbox" id="agreeCheck" style="margin-top:2px;accent-color:var(--primary);width:18px;height:18px;">' +
    '<span>I have read and agree to the Autoride Rental Agreement and Policies.</span>' +
    '</label>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
    '<button class="btn-secondary" onclick="document.getElementById(\'rentalAgreementModal\').remove()">Cancel</button>' +
    '<button class="btn-primary" onclick="confirmAndBook()" id="confirmPayBtn"><i class="fas fa-lock"></i> Confirm & Pay</button>' +
    '</div>' +
    '</div>';
  document.body.appendChild(modal);
}

function confirmAndBook() {
  var agreeCheck = document.getElementById('agreeCheck');
  if (!agreeCheck || !agreeCheck.checked) {
    showToast('Please read and agree to the rental terms first.', 'error');
    return;
  }
  var modal = document.getElementById('rentalAgreementModal');
  if (modal) modal.remove();

  showLoading(true);
  apiCall('/book', { method: 'POST', body: JSON.stringify(_pendingBookingPayload) })
    .then(function(data) {
      activeBookingId = data.booking_id;
      closeOverlay('page-booking-form');
      closeOverlay('page-vehicle-detail');
      NotifStore.add('Booking #' + data.booking_id + ' received! Our team will review it shortly.');
      openPaymentScreen(data.booking_id, _pendingPriceResult, _pendingPayType);
    })
    .catch(function(err) {
      var errEl = document.getElementById('bfErr');
      if (errEl) errEl.textContent = err.message || 'Booking failed. Please try again.';
    })
    .finally(function() { showLoading(false); });
}

// PAYMENT — PayMongo Integration
function openPaymentScreen(bookingId, priceResult, payType) {
  var nowDue = payType === 'Downpayment' ? priceResult.downpaymentAmount : priceResult.total;
  var el = document.getElementById('paymentContent');
  if (!el) return;

  var breakdownHtml =
    '<div class="price-row"><span>Base Rate (' + priceResult.days + ' days)</span><span>' + formatPHP(priceResult.basePrice) + '</span></div>' +
    (selectedAddons.length > 0 ? selectedAddons.map(function(a) {
      return '<div class="price-row" style="padding-left:10px;font-size:0.8rem;color:var(--text-secondary);"><span><i class="fas fa-check" style="color:var(--success);"></i> ' + a.name + '</span><span>' + formatPHP(a.price) + '</span></div>';
    }).join('') : '') +
    (priceResult.insurancePrice > 0 ? '<div class="price-row" style="padding-left:10px;font-size:0.8rem;color:var(--text-secondary);"><span><i class="fas fa-shield-alt" style="color:var(--info);"></i> ' + selectedInsurance.type + '</span><span>' + formatPHP(priceResult.insurancePrice) + '</span></div>' : '') +
    (priceResult.longTermDiscount > 0 ? '<div class="price-row" style="color:var(--success);"><span>Long-term Discount</span><span>-' + formatPHP(priceResult.longTermDiscount) + '</span></div>' : '') +
    (priceResult.couponDiscount > 0 ? '<div class="price-row" style="color:var(--success);"><span>Coupon Discount</span><span>-' + formatPHP(priceResult.couponDiscount) + '</span></div>' : '') +
    '<div class="price-row total"><span>Total</span><span>' + formatPHP(priceResult.total) + '</span></div>' +
    (payType === 'Downpayment' ?
      '<div class="price-row" style="color:var(--primary);font-weight:700;"><span>Due Now (20%)</span><span>' + formatPHP(nowDue) + '</span></div>' +
      '<div class="price-row" style="color:var(--text-secondary);"><span>Remaining Balance</span><span>' + formatPHP(priceResult.balanceAmount) + '</span></div>' : '');

  el.innerHTML =
    '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-payment\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Payment</h2></div>' +
    '<div class="scroll-content" style="padding-bottom:100px;">' +

    // Summary
    '<div class="card">' +
    '<h4 style="font-weight:700;margin-bottom:12px;"><i class="fas fa-receipt" style="color:var(--primary);margin-right:8px;"></i>Booking #' + bookingId + ' Summary</h4>' +
    breakdownHtml +
    '<div style="margin-top:10px;padding:10px;background:var(--primary);border-radius:var(--radius-sm);text-align:center;">' +
    '<div style="color:rgba(255,255,255,0.8);font-size:0.8rem;">Amount Due Now</div>' +
    '<div style="color:#fff;font-size:1.4rem;font-weight:800;">' + formatPHP(nowDue) + '</div>' +
    '</div></div>' +

    // PayMongo payment methods
    '<div class="card">' +
    '<h4 style="font-weight:700;margin-bottom:6px;">Select Payment Method</h4>' +
    '<p style="font-size:0.75rem;color:var(--text-secondary);margin-bottom:14px;">Secure payments powered by PayMongo</p>' +

    // GCash
    '<div class="option-card" id="pmGcash" onclick="selectPayMethod(\'gcash\',this)" style="margin-bottom:8px;">' +
    '<div style="width:40px;height:40px;background:#0070e0;border-radius:8px;display:flex;align-items:center;justify-content:center;">' +
    '<span style="color:#fff;font-weight:900;font-size:0.85rem;">G</span></div>' +
    '<div><strong>GCash</strong><br><small style="color:var(--text-secondary);">Pay via GCash e-wallet</small></div>' +
    '<i class="fas fa-chevron-right" style="color:var(--text-secondary);margin-left:auto;"></i>' +
    '</div>' +

    // Maya
    '<div class="option-card" id="pmMaya" onclick="selectPayMethod(\'maya\',this)" style="margin-bottom:8px;">' +
    '<div style="width:40px;height:40px;background:#00b4d8;border-radius:8px;display:flex;align-items:center;justify-content:center;">' +
    '<span style="color:#fff;font-weight:900;font-size:0.85rem;">M</span></div>' +
    '<div><strong>Maya</strong><br><small style="color:var(--text-secondary);">Pay via Maya e-wallet</small></div>' +
    '<i class="fas fa-chevron-right" style="color:var(--text-secondary);margin-left:auto;"></i>' +
    '</div>' +

    // Credit/Debit Card
    '<div class="option-card" id="pmCard" onclick="selectPayMethod(\'card\',this)" style="margin-bottom:8px;">' +
    '<div style="width:40px;height:40px;background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:8px;display:flex;align-items:center;justify-content:center;">' +
    '<i class="fas fa-credit-card" style="color:#fff;font-size:1rem;"></i></div>' +
    '<div><strong>Credit / Debit Card</strong><br><small style="color:var(--text-secondary);">Visa, Mastercard, JCB</small></div>' +
    '<i class="fas fa-chevron-right" style="color:var(--text-secondary);margin-left:auto;"></i>' +
    '</div>' +

    // Cash
    '<div class="option-card" id="pmCash" onclick="selectPayMethod(\'cash\',this)">' +
    '<div style="width:40px;height:40px;background:#2dc653;border-radius:8px;display:flex;align-items:center;justify-content:center;">' +
    '<i class="fas fa-money-bill-wave" style="color:#fff;font-size:1rem;"></i></div>' +
    '<div><strong>Cash Over the Counter</strong><br><small style="color:var(--text-secondary);">Pay at our office upon pickup</small></div>' +
    '</div>' +

    '<input type="hidden" id="payMethod" value="gcash">' +
    '</div>' +

    // Cash reference fields (only for cash)
    '<div class="card" id="cashPayFields" style="display:none;">' +
    '<div class="form-group"><label>Reference / Transaction Number (optional)</label>' +
    '<input type="text" id="payRef" placeholder="e.g. 1234567890"></div>' +
    '<div class="form-group"><label>Payment Screenshot / Proof (optional)</label>' +
    '<button class="btn-secondary" onclick="pickPaymentProof()"><i class="fas fa-upload"></i> Upload Screenshot</button>' +
    '<img id="payProofPreview" style="width:100%;border-radius:var(--radius-sm);margin-top:8px;display:none;">' +
    '</div></div>' +

    // Split payment
    '<div class="card" style="border:1.5px dashed var(--primary);">' +
    '<button class="btn-outline" onclick="showOverlay(\'page-split-payment\')" style="width:100%;">' +
    '<i class="fas fa-users"></i> Split Payment with a Friend</button>' +
    '</div>' +

    '<span class="field-error" id="payErr" style="display:block;margin-bottom:12px;text-align:center;"></span>' +
    '<button class="btn-primary" style="margin-bottom:20px;" onclick="submitPayment(' + bookingId + ',' + nowDue + ')">' +
    '<i class="fas fa-lock"></i> Pay ' + formatPHP(nowDue) + '</button>' +
    '</div>';

  // Auto-select GCash
  var gcashEl = document.getElementById('pmGcash');
  if (gcashEl) gcashEl.classList.add('selected');

  showOverlay('page-payment');
}

function selectPayMethod(method, el) {
  document.getElementById('payMethod').value = method;
  var cards = document.querySelectorAll('#paymentContent .option-card');
  for (var i = 0; i < cards.length; i++) cards[i].classList.remove('selected');
  if (el) el.classList.add('selected');
  // Show cash fields only for cash method
  var cashFields = document.getElementById('cashPayFields');
  if (cashFields) {
    cashFields.style.display = (method === 'cash') ? 'block' : 'none';
  }
}

function pickPaymentProof() {
  var input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/jpeg,image/png';
  input.onchange = function(e) {
    var file = e.target.files[0];
    if (!file) return;
    var err = validateUploadFile(file);
    if (err) { document.getElementById('payProofErr').textContent = err; return; }
    paymentProofBlob = file;
    var preview = document.getElementById('payProofPreview');
    if (preview) { preview.src = URL.createObjectURL(file); preview.style.display = 'block'; }
  };
  input.click();
}

function submitPayment(bookingId, amount) {
  var methodEl = document.getElementById('payMethod');
  var method = methodEl ? methodEl.value : 'gcash';
  var errEl = document.getElementById('payErr');
  if (errEl) errEl.textContent = '';

  // Cash payment — use existing manual flow
  if (method === 'cash') {
    var refEl = document.getElementById('payRef');
    var ref = refEl ? sanitizeInput(refEl.value.trim()) : '';
    showLoading(true);
    var promise;
    if (paymentProofBlob) {
      var fd = new FormData();
      fd.append('booking_id', bookingId);
      fd.append('amount', amount);
      fd.append('method', 'Cash (Over the counter)');
      fd.append('reference_number', ref);
      fd.append('payment_proof', paymentProofBlob, 'proof.jpg');
      promise = uploadFile('/legacy-payment', fd);
    } else {
      promise = apiCall('/payment', { method: 'POST', body: JSON.stringify({ booking_id: bookingId, amount: amount, method: 'Cash (Over the counter)', reference_number: ref }) });
    }
    promise
      .then(function(data) {
        closeOverlay('page-payment');
        NotifStore.add('Booking #' + bookingId + ' received! Pay at our office upon pickup.');
        showReceipt(bookingId, data, amount, 'Cash (Over the counter)', ref);
      })
      .catch(function(err) {
        if (errEl) errEl.textContent = err.message || 'Payment failed. Please try again.';
      })
      .finally(function() { showLoading(false); });
    return;
  }

  // Online payment — redirect to PayMongo
  showLoading(true);
  apiCall('/paymongo/create-payment', {
    method: 'POST',
    body: JSON.stringify({
      booking_id: bookingId,
      amount: amount,
      method: method,
      description: 'Autoride Booking #' + bookingId,
      customer_name: currentUser.fullName || '',
      customer_email: currentUser.email || ''
    })
  })
    .then(function(data) {
      showLoading(false);
      if (data.checkout_url) {
        // Open PayMongo checkout in browser
        if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Browser) {
          window.Capacitor.Plugins.Browser.open({ url: data.checkout_url });
        } else {
          window.open(data.checkout_url, '_blank');
        }
        // Show waiting screen and poll for payment confirmation
        showPaymentWaiting(bookingId, amount, method);
      } else {
        if (errEl) errEl.textContent = data.error || 'Failed to create payment. Please try again.';
      }
    })
    .catch(function(err) {
      showLoading(false);
      if (errEl) errEl.textContent = err.message || 'Payment failed. Please try again.';
    });
}

function showPaymentWaiting(bookingId, amount, method) {
  var el = document.getElementById('paymentContent');
  if (!el) return;
  var methodLabel = method === 'gcash' ? 'GCash' : method === 'maya' ? 'Maya' : 'Card';
  el.innerHTML =
    '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-payment\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Waiting for Payment</h2></div>' +
    '<div class="scroll-content" style="padding-bottom:100px;text-align:center;padding-top:40px;">' +
    '<div style="width:80px;height:80px;border-radius:50%;background:rgba(220,38,38,0.1);display:flex;align-items:center;justify-content:center;margin:0 auto 20px;">' +
    '<i class="fas fa-spinner fa-spin" style="font-size:2rem;color:var(--primary);"></i></div>' +
    '<h3 style="font-size:1.2rem;font-weight:800;margin-bottom:8px;">Complete Payment in ' + methodLabel + '</h3>' +
    '<p style="color:var(--text-secondary);font-size:0.875rem;margin-bottom:24px;">A ' + methodLabel + ' payment page has been opened.<br>Complete your payment there, then return here.</p>' +
    '<div style="background:var(--bg-card);border-radius:var(--radius-sm);padding:16px;margin-bottom:24px;">' +
    '<div style="font-size:0.75rem;color:var(--text-secondary);">Amount to Pay</div>' +
    '<div style="font-size:1.5rem;font-weight:900;color:var(--primary);">' + formatPHP(amount) + '</div>' +
    '</div>' +
    '<button class="btn-primary" style="margin-bottom:12px;" onclick="checkPaymentStatus(' + bookingId + ',' + amount + ',\'' + method + '\')">' +
    '<i class="fas fa-check-circle"></i> I\'ve Completed Payment</button>' +
    '<button class="btn-secondary" onclick="closeOverlay(\'page-payment\')" style="width:100%;">Cancel</button>' +
    '</div>';
}

function checkPaymentStatus(bookingId, amount, method) {
  showLoading(true);
  apiCall('/paymongo/status/' + bookingId)
    .then(function(data) {
      showLoading(false);
      if (data.paid) {
        closeOverlay('page-payment');
        NotifStore.add('Payment confirmed for Booking #' + bookingId + '! A receipt has been sent to your email.');
        showToast('Payment confirmed! Booking #' + bookingId + ' is now active.', 'success');
        showPage('page-bookings');
      } else {
        var debugMsg = '';
        if (data.debug) {
          var d = data.debug;
          debugMsg = ' [key:' + d.has_key + ' link:' + (d.link_status || 'none') + ' pays:' + (d.payments_count || 0) + ']';
        }
        showToast('Payment not yet confirmed.' + debugMsg, 'info');
      }
    })
    .catch(function() {
      showLoading(false);
      showToast('Could not verify payment. Please check your bookings.', 'error');
    });
}

function showReceipt(bookingId, data, amountPaid, method, refNum) {
  var receipt = data.receipt || {};
  var vehicle = bookingFormVehicle || {};
  var now = new Date();
  var dateStr = now.toLocaleDateString('en-PH', { year:'numeric', month:'long', day:'numeric' });
  var timeStr = now.toLocaleTimeString('en-PH', { hour:'2-digit', minute:'2-digit' });
  var el = document.getElementById('receiptContent');
  if (!el) return;

  var addonsText = selectedAddons.length > 0 ? selectedAddons.map(function(a) { return a.name; }).join(', ') : 'None';
  var insText = selectedInsurance.type || 'Basic Protection';

  el.innerHTML =
    '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-receipt\');showPage(\'page-bookings\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Receipt</h2></div>' +
    '<div class="scroll-content" style="padding-bottom:100px;">' +
    '<div class="receipt-card">' +
    '<div class="receipt-header">' +
    '<i class="fas fa-check-circle" style="font-size:3.5rem;color:var(--success);"></i>' +
    '<h2>Booking Confirmed!</h2>' +
    '<p style="color:var(--text-secondary);font-size:0.875rem;">Your receipt has been sent to your email</p>' +
    '</div>' +

    // Receipt details
    '<div style="border-top:2px dashed var(--border);padding-top:16px;margin-top:8px;">' +
    '<div class="receipt-row"><span>Booking ID</span><strong>#' + bookingId + '</strong></div>' +
    '<div class="receipt-row"><span>Vehicle</span><strong>' + (receipt.brand || vehicle.brand || '') + ' ' + (receipt.model || vehicle.model || '') + '</strong></div>' +
    (receipt.start_date ? '<div class="receipt-row"><span>Rental Period</span><strong>' + receipt.start_date + ' ? ' + receipt.end_date + '</strong></div>' : '') +
    '<div class="receipt-row"><span>Insurance</span><strong>' + insText + '</strong></div>' +
    '<div class="receipt-row"><span>Add-ons</span><strong>' + addonsText + '</strong></div>' +
    '<div class="receipt-row"><span>Payment Method</span><strong>' + (method || receipt.method || 'GCash') + '</strong></div>' +
    (refNum ? '<div class="receipt-row"><span>Reference No.</span><strong>' + refNum + '</strong></div>' : '') +
    '<div class="receipt-row"><span>Date & Time</span><strong>' + dateStr + ', ' + timeStr + '</strong></div>' +
    '</div>' +

    // Amount
    '<div style="background:var(--primary);border-radius:var(--radius-sm);padding:14px;text-align:center;margin:16px 0;">' +
    '<div style="color:rgba(255,255,255,0.8);font-size:0.8rem;">Amount Paid</div>' +
    '<div style="color:#fff;font-size:1.6rem;font-weight:800;">' + formatPHP(amountPaid || receipt.amount || 0) + '</div>' +
    '</div>' +

    // Email notice
    '<div style="background:#e8f4fd;border-radius:var(--radius-sm);padding:12px;text-align:center;margin-bottom:16px;font-size:0.8rem;color:#084298;">' +
    '<i class="fas fa-envelope"></i> A receipt has been sent to <strong>' + (currentUser.email || 'your email') + '</strong>' +
    '</div>' +

    '<button class="btn-primary" onclick="downloadReceipt(' + bookingId + ')" style="margin-bottom:10px;">' +
    '<i class="fas fa-download"></i> Download PDF Receipt</button>' +
    '<button class="btn-secondary" onclick="closeOverlay(\'page-receipt\');showPage(\'page-bookings\')">' +
    '<i class="fas fa-list"></i> View My Bookings</button>' +
    '</div>' +
    '</div>';

  showOverlay('page-receipt');
}

function downloadReceipt(bookingId) {
  showToast('Downloading receipt...', 'info');
  window.open(API_BASE + '/bookings/' + bookingId + '/receipt', '_blank');
}

// BOOKINGS
var _allBookingsData = [];

function loadBookings() {
  if (!currentUser.id) return;
  showLoading(true);
  apiCall('/user-bookings?user_id=' + currentUser.id)
    .then(function(data) {
      _allBookingsData = data;
      // Update stats
      var total = data.length;
      var completed = data.filter(function(b) { return b.status === 'Completed'; }).length;
      var spent = data.filter(function(b) { return b.payment_status === 'Paid'; }).reduce(function(s, b) { return s + parseFloat(b.total_price || 0); }, 0);
      var statTotal = document.getElementById('bkStatTotal');
      var statDone = document.getElementById('bkStatDone');
      var statSpent = document.getElementById('bkStatSpent');
      if (statTotal) statTotal.querySelector('div').textContent = total;
      if (statDone) statDone.querySelector('div').textContent = completed;
      if (statSpent) statSpent.querySelector('div').textContent = spent > 0 ? ('P' + (spent / 1000).toFixed(1) + 'k') : '-';
      renderBookingsList(data);
    })
    .catch(function(err) {
      var el = document.getElementById('bookingsList');
      if (el) el.innerHTML = '<div class="empty-state"><p>' + err.message + '</p></div>';
    })
    .finally(function() { showLoading(false); });
}

function filterBookingsList(filter, btn) {
  // Update tab styles
  var tabs = document.querySelectorAll('#bookingFilterTabs button');
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].style.background = 'transparent';
    tabs[i].style.color = '#52525b';
  }
  if (btn) {
    btn.style.background = 'linear-gradient(135deg,#dc2626,#9b1a1a)';
    btn.style.color = '#fff';
  }
  var filtered = filter === 'all' ? _allBookingsData : _allBookingsData.filter(function(b) {
    if (filter === 'Confirmed') return b.status === 'Confirmed' || b.status === 'Approved' || b.status === 'Picked Up';
    return b.status === filter;
  });
  renderBookingsList(filtered);
}

function renderBookingsList(data) {
  var el = document.getElementById('bookingsList');
  if (!el) return;
  if (!data.length) {
    el.innerHTML = '<div class="empty-state"><i class="fas fa-calendar-times"></i><p>No bookings found</p></div>';
    return;
  }
  var statusColors = {
    'Pending': '#fbbf24', 'Confirmed': '#34d399', 'Approved': '#34d399',
    'Picked Up': '#a78bfa', 'Completed': '#a78bfa', 'Cancelled': '#f87171', 'Rejected': '#f87171'
  };
  el.innerHTML = data.map(function(b) {
    var color = statusColors[b.status] || '#a1a1aa';
    var payColor = b.payment_status === 'Paid' ? '#60a5fa' : '#f87171';
    return '<div style="background:#141414;border:1px solid rgba(255,255,255,0.06);border-radius:24px;overflow:hidden;margin-bottom:12px;cursor:pointer;" onclick="openBookingDetail(' + b.id + ')">' +
      '<div style="height:3px;background:' + color + ';opacity:0.5;"></div>' +
      '<div style="padding:14px;">' +
      '<div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:10px;">' +
      '<div style="width:56px;height:56px;border-radius:16px;background:#1a1a1a;display:flex;align-items:center;justify-content:center;flex-shrink:0;">' +
      '<i class="fas fa-car" style="color:#3f3f46;font-size:1.3rem;"></i></div>' +
      '<div style="flex:1;min-width:0;">' +
      '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:8px;">' +
      '<h3 style="font-weight:900;font-size:0.875rem;color:#fff;line-height:1.2;">' + (b.brand || '') + ' ' + (b.model || '') + '</h3>' +
      '<span style="padding:3px 10px;border-radius:20px;font-size:0.6rem;font-weight:800;background:' + color + '22;color:' + color + ';flex-shrink:0;">' + b.status + '</span>' +
      '</div>' +
      '<div style="font-size:0.7rem;color:#52525b;margin-top:4px;">' + (b.color || '') + (b.color && b.plate_number ? ' · ' : '') + (b.plate_number || '') + '</div>' +
      '</div></div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;">' +
      '<div style="background:#1a1a1a;border-radius:12px;padding:10px;">' +
      '<div style="font-size:0.6rem;color:#52525b;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px;">Pick-up</div>' +
      '<div style="font-size:0.75rem;font-weight:800;color:#fff;">' + b.start_date + '</div>' +
      '</div>' +
      '<div style="background:#1a1a1a;border-radius:12px;padding:10px;">' +
      '<div style="font-size:0.6rem;color:#52525b;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px;">Return</div>' +
      '<div style="font-size:0.75rem;font-weight:800;color:#fff;">' + b.end_date + '</div>' +
      '</div></div>' +
      '<div style="display:flex;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid rgba(255,255,255,0.05);">' +
      '<div style="display:flex;align-items:center;gap:8px;">' +
      '<span style="padding:3px 10px;border-radius:20px;font-size:0.6rem;font-weight:800;background:' + payColor + '22;color:' + payColor + ';">' + (b.payment_status || 'Unpaid') + '</span>' +
      '</div>' +
      '<div style="font-weight:900;font-size:0.95rem;color:#fff;">' + formatPHP(b.total_price) + '</div>' +
      '</div></div></div>';
  }).join('');
}

function openBookingDetail(bookingId) {
  if (!currentUser.id) return;
  showLoading(true);
  apiCall('/user-bookings?user_id=' + currentUser.id)
    .then(function(bookings) {
      var b = null;
      for (var i = 0; i < bookings.length; i++) {
        if (bookings[i].id === bookingId) { b = bookings[i]; break; }
      }
      if (!b) { showToast('Booking not found.', 'error'); return; }
      activeBookingData = b;
      renderBookingDetail(b);
      showOverlay('page-booking-detail');
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

function renderBookingDetail(b) {
  var canCancel = b.status === 'Pending' || b.status === 'Confirmed';
  var canPreInspect = b.status === 'Confirmed' || b.status === 'Approved';
  var canPostInspect = b.status === 'Picked Up';
  var canTrack = b.status === 'Picked Up';
  var canReview = b.status === 'Completed';
  var canPayBalance = b.payment_status === 'Partially Paid';
  var el = document.getElementById('bookingDetailContent');
  if (!el) return;
  var actions = '';
  if (canPayBalance) actions += '<button class="btn-primary btn-sm" onclick="openPayBalanceScreen(' + b.id + ',' + b.balance_amount + ')"><i class="fas fa-money-bill"></i> Pay Balance</button>';
  if (canCancel) actions += '<button class="btn-danger btn-sm" onclick="promptCancelBooking(' + b.id + ')"><i class="fas fa-times"></i> Cancel</button>';
  if (canPreInspect) actions += '<button class="btn-secondary btn-sm" onclick="openInspection(' + b.id + ',\'pickup\')"><i class="fas fa-clipboard-check"></i> Pre-Rental Check</button>';
  if (canPostInspect) actions += '<button class="btn-secondary btn-sm" onclick="openInspection(' + b.id + ',\'return\')"><i class="fas fa-clipboard-check"></i> Post-Rental Check</button>';
  if (canTrack) actions += '<button class="btn-outline btn-sm" onclick="openGpsMap(' + b.vehicle_id + ')"><i class="fas fa-map-marker-alt"></i> Track Vehicle</button>';
  if (canReview) actions += '<button class="btn-outline btn-sm" onclick="openReviewForm(' + b.vehicle_id + ')"><i class="fas fa-star"></i> Leave Review</button>';
  actions += '<button class="btn-secondary btn-sm" onclick="downloadReceipt(' + b.id + ')"><i class="fas fa-download"></i> Receipt PDF</button>';
  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-booking-detail\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Booking #' + b.id + '</h2></div>' +
    '<div class="scroll-content">' +
    '<div class="card">' +
    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;"><h4 style="font-weight:700;">' + (b.brand || '') + ' ' + (b.model || '') + '</h4>' + statusPill(b.status) + '</div>' +
    '<div class="price-row"><span>Period</span><span>' + b.start_date + ' to ' + b.end_date + '</span></div>' +
    '<div class="price-row"><span>Rental Type</span><span>' + (b.rental_type || '-') + '</span></div>' +
    '<div class="price-row"><span>Insurance</span><span>' + (b.insurance_type || 'Basic') + '</span></div>' +
    '</div>' +
    '<div class="card">' +
    '<div class="price-row"><span>Total</span><span>' + formatPHP(b.total_price) + '</span></div>' +
    '<div class="price-row"><span>Paid</span><span>' + formatPHP(b.amount_paid) + '</span></div>' +
    (b.balance_amount > 0 ? '<div class="price-row"><span>Balance</span><span style="color:var(--danger);">' + formatPHP(b.balance_amount) + '</span></div>' : '') +
    '<div class="price-row"><span>Payment Status</span><span>' + statusPill(b.payment_status) + '</span></div>' +
    '</div>' +
    (b.cancellation_reason ? '<div class="card" style="border-left:4px solid var(--danger);"><p style="font-size:0.875rem;"><strong>Cancellation Reason:</strong> ' + b.cancellation_reason + '</p></div>' : '') +
    '<div class="action-btn-grid">' + actions + '</div>' +
    '</div>';
}

function promptCancelBooking(bookingId) {
  var reason = prompt('Please provide a reason for cancellation:');
  if (!reason) return;
  showLoading(true);
  apiCall('/cancel-booking', { method: 'POST', body: JSON.stringify({ booking_id: bookingId, user_id: currentUser.id, reason: reason }) })
    .then(function() {
      showToast('Booking cancelled successfully.', 'success');
      NotifStore.add('Booking #' + bookingId + ' has been cancelled.');
      closeOverlay('page-booking-detail');
      loadBookings();
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

function openPayBalanceScreen(bookingId, balance) {
  var el = document.getElementById('paymentContent');
  if (!el) return;
  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-payment\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Pay Balance</h2></div>' +
    '<div class="scroll-content">' +
    '<div class="card"><div class="price-row total"><span>Balance Due</span><span>' + formatPHP(balance) + '</span></div></div>' +
    '<div class="card">' +
    '<div class="form-group"><label>Method</label><select id="balMethod"><option>GCash</option><option>Credit Card</option><option>Cash (Over the counter)</option></select></div>' +
    '<div class="form-group"><label>Reference Number</label><input type="text" id="balRef" placeholder="Reference number"></div>' +
    '</div>' +
    '<span class="field-error" id="balErr" style="display:block;margin-bottom:12px;text-align:center;"></span>' +
    '<button class="btn-primary" onclick="submitBalancePayment(' + bookingId + ',' + balance + ')">Pay ' + formatPHP(balance) + '</button>' +
    '</div>';
  showOverlay('page-payment');
}

function submitBalancePayment(bookingId, amount) {
  var methodEl = document.getElementById('balMethod');
  var refEl = document.getElementById('balRef');
  var method = methodEl ? methodEl.value : 'GCash';
  var ref = refEl ? sanitizeInput(refEl.value.trim()) : '';
  showLoading(true);
  apiCall('/bookings/' + bookingId + '/pay-balance', { method: 'POST', body: JSON.stringify({ amount: amount, method: method, reference_number: ref }) })
    .then(function() {
      showToast('Balance paid successfully!', 'success');
      closeOverlay('page-payment');
      closeOverlay('page-booking-detail');
      loadBookings();
    })
    .catch(function(err) {
      var errEl = document.getElementById('balErr');
      if (errEl) errEl.textContent = err.message;
    })
    .finally(function() { showLoading(false); });
}

// INSPECTION
function openInspection(bookingId, type) {
  inspectionPhotos = [];
  var el = document.getElementById('inspectionContent');
  if (!el) return;
  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-inspection\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>' + (type === 'pickup' ? 'Pre-Rental' : 'Post-Rental') + ' Inspection</h2></div>' +
    '<div class="scroll-content">' +
    '<div class="card">' +
    '<div class="form-group"><label>Mileage Reading (km) *</label><input type="number" id="inspMileage" placeholder="e.g. 12500"><span class="field-error" id="inspMileageErr"></span></div>' +
    '<div class="form-group"><label>Fuel Level</label><select id="inspFuel"><option>Full</option><option>3/4</option><option>1/2</option><option>1/4</option><option>Empty</option></select></div>' +
    '<div class="form-group"><label>Condition Notes</label><textarea id="inspNotes" placeholder="Describe vehicle condition..."></textarea></div>' +
    '</div>' +
    '<div class="card"><h4 style="font-weight:700;margin-bottom:10px;">Photos</h4>' +
    '<button class="btn-secondary" onclick="addInspectionPhoto()"><i class="fas fa-camera"></i> Add Photo</button>' +
    '<div class="photo-thumbs" id="inspPhotoThumbs"></div></div>' +
    '<span class="field-error" id="inspErr" style="display:block;margin-bottom:12px;text-align:center;"></span>' +
    '<button class="btn-primary" onclick="submitInspection(' + bookingId + ',\'' + type + '\')"><i class="fas fa-check"></i> Submit Inspection</button>' +
    '<div style="margin-top:20px;" id="pastInspectionsWrap"></div>' +
    '</div>';
  showOverlay('page-inspection');
  loadPastInspections(bookingId);
}

function addInspectionPhoto() {
  var input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.onchange = function(e) {
    var file = e.target.files[0];
    if (!file) return;
    var err = validateUploadFile(file);
    if (err) { showToast(err, 'error'); return; }
    inspectionPhotos.push(file);
    var thumbs = document.getElementById('inspPhotoThumbs');
    if (thumbs) {
      var img = document.createElement('img');
      img.className = 'photo-thumb';
      img.src = URL.createObjectURL(file);
      thumbs.appendChild(img);
    }
  };
  input.click();
}

function submitInspection(bookingId, type) {
  var mileageEl = document.getElementById('inspMileage');
  var mileage = mileageEl ? mileageEl.value : '';
  var mileageErrEl = document.getElementById('inspMileageErr');
  var inspErrEl = document.getElementById('inspErr');
  if (mileageErrEl) mileageErrEl.textContent = '';
  if (inspErrEl) inspErrEl.textContent = '';
  if (isBlank(mileage)) { if (mileageErrEl) mileageErrEl.textContent = 'Mileage reading is required.'; return; }
  var fd = new FormData();
  fd.append('booking_id', bookingId);
  fd.append('inspection_type', type);
  fd.append('mileage', mileage);
  var fuelEl = document.getElementById('inspFuel');
  fd.append('fuel_level', fuelEl ? fuelEl.value : 'Full');
  var notesEl = document.getElementById('inspNotes');
  fd.append('notes', notesEl ? sanitizeInput(notesEl.value) : '');
  fd.append('inspector_id', currentUser.id);
  inspectionPhotos.forEach(function(p, i) { fd.append('photo_' + i, p, 'photo_' + i + '.jpg'); });
  showLoading(true);
  uploadFile('/inspections/submit', fd)
    .then(function() {
      showToast('Inspection submitted successfully!', 'success');
      closeOverlay('page-inspection');
    })
    .catch(function(err) { if (inspErrEl) inspErrEl.textContent = err.message; })
    .finally(function() { showLoading(false); });
}

function loadPastInspections(bookingId) {
  apiCall('/inspections/' + bookingId)
    .then(function(data) {
      if (!data.length) return;
      var el = document.getElementById('pastInspectionsWrap');
      if (!el) return;
      el.innerHTML = '<h4 style="font-weight:700;margin-bottom:10px;">Past Inspections</h4>' +
        data.map(function(i) {
          return '<div class="card" style="margin-bottom:10px;">' +
            '<div style="display:flex;justify-content:space-between;"><strong>' + (i.inspection_type === 'pickup' ? 'Pre-Rental' : 'Post-Rental') + '</strong><small>' + new Date(i.created_at).toLocaleDateString() + '</small></div>' +
            '<div style="font-size:0.8rem;color:var(--text-secondary);margin-top:6px;">Mileage: ' + i.mileage + ' km | Fuel: ' + i.fuel_level + '</div>' +
            (i.notes ? '<div style="font-size:0.8rem;margin-top:4px;">' + i.notes + '</div>' : '') +
            '</div>';
        }).join('');
    }).catch(function() {});
}

// GPS MAP
function openGpsMap(vehicleId) {
  showOverlay('page-gps-map');
  var el = document.getElementById('gpsMapContent');
  if (!el) return;
  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-gps-map\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Track Vehicle</h2></div>' +
    '<div class="scroll-content" style="padding:16px;">' +
    '<div id="map"></div>' +
    '<div id="gpsTimestamp" style="font-size:0.8rem;color:var(--text-muted);margin-top:8px;text-align:center;"></div>' +
    '<button class="btn-secondary" style="margin-top:10px;" onclick="centerGpsMap()"><i class="fas fa-crosshairs"></i> Center on Vehicle</button>' +
    '</div>';
  setTimeout(function() {
    if (typeof L !== 'undefined') {
      if (!gpsMap) {
        gpsMap = L.map('map').setView([14.5995, 120.9842], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OpenStreetMap' }).addTo(gpsMap);
      }
      fetchVehicleLocation(vehicleId);
      startGpsPolling(vehicleId);
    }
  }, 300);
}

function fetchVehicleLocation(vehicleId) {
  apiCall('/vehicles/' + vehicleId + '/location?user_id=' + currentUser.id)
    .then(function(data) {
      if (data.latitude && data.longitude) {
        var latlng = [data.latitude, data.longitude];
        if (gpsMarker) { gpsMarker.setLatLng(latlng); }
        else { gpsMarker = L.marker(latlng).addTo(gpsMap).bindPopup('Vehicle Location').openPopup(); }
        gpsMap.setView(latlng, 15);
        var ts = document.getElementById('gpsTimestamp');
        if (ts) ts.textContent = 'Last updated: ' + (data.last_gps_update ? new Date(data.last_gps_update).toLocaleString() : 'Unknown');
      } else {
        var ts = document.getElementById('gpsTimestamp');
        if (ts) ts.textContent = 'Live tracking is currently unavailable for this vehicle.';
      }
    }).catch(function() {});
}

function centerGpsMap() { if (gpsMarker && gpsMap) gpsMap.setView(gpsMarker.getLatLng(), 15); }
function startGpsPolling(vehicleId) { gpsRefreshInterval = setInterval(function() { fetchVehicleLocation(vehicleId); }, 30000); }
function stopGpsPolling() {
  if (gpsRefreshInterval) { clearInterval(gpsRefreshInterval); gpsRefreshInterval = null; }
  if (gpsMap) { gpsMap.remove(); gpsMap = null; gpsMarker = null; }
}

// REVIEW
function openReviewForm(vehicleId) {
  selectedRating = 0;
  var el = document.getElementById('reviewContent');
  if (!el) return;
  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-review\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Leave a Review</h2></div>' +
    '<div class="scroll-content"><div class="card">' +
    '<h4 style="font-weight:700;margin-bottom:14px;">Rate your experience</h4>' +
    '<div class="star-rating" id="starRating">' +
    [1,2,3,4,5].map(function(n) { return '<i class="fas fa-star" onclick="setRating(' + n + ')" data-val="' + n + '"></i>'; }).join('') +
    '</div>' +
    '<span class="field-error" id="ratingErr" style="margin-top:8px;display:block;"></span>' +
    '<div class="form-group" style="margin-top:16px;"><label>Comment (optional)</label><textarea id="reviewComment" placeholder="Share your experience..."></textarea></div>' +
    '<span class="field-error" id="reviewErr" style="display:block;margin-bottom:12px;"></span>' +
    '<button class="btn-primary" onclick="submitReview(' + vehicleId + ')"><i class="fas fa-paper-plane"></i> Submit Review</button>' +
    '</div></div>';
  showOverlay('page-review');
}

function setRating(val) {
  selectedRating = val;
  var stars = document.querySelectorAll('#starRating i');
  for (var i = 0; i < stars.length; i++) {
    stars[i].classList.toggle('active', parseInt(stars[i].getAttribute('data-val')) <= val);
  }
}

function submitReview(vehicleId) {
  var ratingErrEl = document.getElementById('ratingErr');
  var reviewErrEl = document.getElementById('reviewErr');
  if (ratingErrEl) ratingErrEl.textContent = '';
  if (reviewErrEl) reviewErrEl.textContent = '';
  if (!selectedRating) { if (ratingErrEl) ratingErrEl.textContent = 'Please select a rating before submitting.'; return; }
  var commentEl = document.getElementById('reviewComment');
  var comment = commentEl ? sanitizeInput(commentEl.value.trim()) : '';
  showLoading(true);
  apiCall('/review', { method: 'POST', body: JSON.stringify({ user_id: currentUser.id, vehicle_id: vehicleId, rating: selectedRating, comment: comment }) })
    .then(function() {
      showToast('Review submitted! Thank you.', 'success');
      closeOverlay('page-review');
    })
    .catch(function(err) { if (reviewErrEl) reviewErrEl.textContent = err.message; })
    .finally(function() { showLoading(false); });
}

// PROFILE
function loadProfile() {
  if (!currentUser.id) return;
  showLoading(true);
  apiCall('/user/profile-full?user_id=' + currentUser.id)
    .then(function(profile) {
      var nameEl = document.getElementById('profileName');
      var emailEl = document.getElementById('profileEmail');
      var editNameEl = document.getElementById('editName');
      var editPhoneEl = document.getElementById('editPhone');
      var pointsEl = document.getElementById('profilePoints');
      if (nameEl) nameEl.textContent = profile.full_name || '';
      if (emailEl) emailEl.textContent = profile.email || '';
      if (editNameEl) editNameEl.value = profile.full_name || '';
      if (editPhoneEl) editPhoneEl.value = profile.phone || '';
      if (pointsEl) pointsEl.textContent = profile.loyalty_points || 0;
      currentUser.loyaltyPoints = profile.loyalty_points || 0;
      currentUser.isVerified = profile.is_verified !== undefined ? profile.is_verified : 0;
      currentUser.email = profile.email || '';
      Session.save(currentUser);

      // Verification badge
      var badge = document.getElementById('profileVerifyBadge');
      var labels = { 0: 'Not Verified', 1: 'Pending Review', 2: 'Verified' };
      if (badge) {
        badge.textContent = labels[currentUser.isVerified] || 'Not Verified';
        badge.className = 'verify-badge verify-' + currentUser.isVerified;
      }

      // Profile picture
      var avatarWrap = document.getElementById('profileAvatarWrap');
      if (avatarWrap) {
        if (profile.profile_picture) {
          avatarWrap.innerHTML = '<img class="profile-avatar" src="' + buildImgUrl(profile.profile_picture) + '" alt="Avatar">';
        } else {
          var placeholder = document.getElementById('profileAvatarPlaceholder');
          if (placeholder) placeholder.textContent = (profile.full_name || '?')[0].toUpperCase();
        }
      }

      // Phone and email display
      var phoneDisplay = document.getElementById('profilePhoneDisplay');
      if (phoneDisplay) phoneDisplay.textContent = profile.phone || 'Not set';
      var emailDisplay = document.getElementById('profileEmailDisplay');
      if (emailDisplay) emailDisplay.textContent = profile.email || '';

      // License image thumbnail
      var licenseThumb = document.getElementById('profileLicenseThumb');
      if (licenseThumb) {
        if (profile.license_image_url) {
          licenseThumb.innerHTML = '<img src="' + profile.license_image_url + '" style="width:100%;border-radius:var(--radius-sm);margin-top:8px;cursor:pointer;" onclick="viewLicenseImage(\'' + profile.license_image_url + '\')" alt="License ID">';
        } else {
          licenseThumb.innerHTML = '<p style="font-size:0.8rem;color:var(--text-muted);margin-top:6px;">No license uploaded yet</p>';
        }
      }
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

function viewLicenseImage(url) {
  var modal = document.createElement('div');
  modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.92);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px;';
  modal.innerHTML = '<div style="position:relative;width:100%;max-width:500px;">' +
    '<p style="color:#fff;text-align:center;margin-bottom:10px;font-weight:700;">Uploaded License / ID</p>' +
    '<img src="' + url + '" style="width:100%;border-radius:var(--radius-md);" alt="License">' +
    '<button onclick="this.parentElement.parentElement.remove()" style="display:block;width:100%;margin-top:12px;background:var(--danger);color:#fff;border:none;border-radius:var(--radius-sm);padding:12px;font-weight:700;cursor:pointer;">Close</button>' +
    '</div>';
  document.body.appendChild(modal);
}

function pickProfilePicture() {
  var input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/jpeg,image/png';
  input.onchange = function(e) {
    var file = e.target.files[0];
    if (!file) return;
    var err = validateUploadFile(file);
    if (err) { showToast(err, 'error'); return; }
    profilePicBlob = file;
    var preview = document.getElementById('profilePicPreview');
    if (preview) { preview.src = URL.createObjectURL(file); preview.style.display = 'block'; }
  };
  input.click();
}

function doUpdateProfile() {
  var nameEl = document.getElementById('editName');
  var phoneEl = document.getElementById('editPhone');
  var phoneErrEl = document.getElementById('editPhoneErr');
  var name = nameEl ? sanitizeInput(nameEl.value.trim()) : '';
  var phone = phoneEl ? phoneEl.value.trim() : '';
  if (phoneErrEl) phoneErrEl.textContent = '';
  if (phone && (!/^\d+$/.test(phone) || phone.length < 10 || phone.length > 11)) {
    if (phoneErrEl) phoneErrEl.textContent = 'Phone must be 10-11 digits.'; return;
  }
  var fd = new FormData();
  fd.append('user_id', currentUser.id);
  fd.append('full_name', name);
  fd.append('phone', phone);
  if (profilePicBlob) fd.append('profile_picture', profilePicBlob, 'avatar.jpg');
  showLoading(true);
  uploadFile('/update-profile', fd)
    .then(function() {
      currentUser.fullName = name;
      Session.save(currentUser);
      showToast('Profile updated successfully!', 'success');
      loadProfile();
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

// LICENSE UPLOAD
function openLicenseUpload() {
  var el = document.getElementById('licenseUploadContent');
  if (!el || el.innerHTML.trim() !== '') return; // already loaded
  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-license-upload\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Upload License</h2></div>' +
    '<div class="scroll-content"><div class="card">' +
    '<p style="font-size:0.875rem;color:var(--text-secondary);margin-bottom:14px;">Upload a clear photo of your driver\'s license. JPEG or PNG, max 5 MB.</p>' +
    (currentUser.isVerified == 0 ? '<div style="background:#f8d7da;border-radius:var(--radius-sm);padding:10px;margin-bottom:12px;font-size:0.8rem;color:#842029;">Please re-upload a valid document.</div>' : '') +
    '<button class="btn-secondary" onclick="pickLicense()"><i class="fas fa-id-card"></i> Choose License Photo</button>' +
    '<img id="licensePreview" style="width:100%;border-radius:var(--radius-sm);margin-top:10px;display:none;">' +
    '<span class="field-error" id="licenseErr" style="display:block;margin-top:8px;"></span>' +
    '<button class="btn-primary" style="margin-top:14px;" onclick="submitLicense()"><i class="fas fa-upload"></i> Submit for Verification</button>' +
    '</div></div>';
}

function pickLicense() {
  var input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/jpeg,image/png';
  input.onchange = function(e) {
    var file = e.target.files[0];
    if (!file) return;
    var err = validateUploadFile(file);
    if (err) { var errEl = document.getElementById('licenseErr'); if (errEl) errEl.textContent = err; return; }
    licenseBlob = file;
    var preview = document.getElementById('licensePreview');
    if (preview) { preview.src = URL.createObjectURL(file); preview.style.display = 'block'; }
  };
  input.click();
}

function submitLicense() {
  var errEl = document.getElementById('licenseErr');
  if (errEl) errEl.textContent = '';
  if (!licenseBlob) { if (errEl) errEl.textContent = 'Please select a license image first.'; return; }
  var fd = new FormData();
  fd.append('user_id', currentUser.id);
  fd.append('license', licenseBlob, 'license.jpg');
  showLoading(true);
  uploadFile('/user/upload-license', fd)
    .then(function() {
      currentUser.isVerified = 1;
      Session.save(currentUser);
      showToast('Your license has been submitted for review.', 'success');
      NotifStore.add('Your license has been submitted for review.');
      closeOverlay('page-license-upload');
      loadProfile();
    })
    .catch(function(err) { if (errEl) errEl.textContent = err.message; })
    .finally(function() { showLoading(false); });
}

// SAVED PAYMENTS
function loadSavedPayments() {
  if (!currentUser.id) return;
  showLoading(true);
  apiCall('/saved-payments?user_id=' + currentUser.id)
    .then(function(data) {
      var el = document.getElementById('savedPaymentsContent');
      if (!el) return;
      var listHtml = data.length ? data.map(function(p) {
        return '<div class="payment-card-item"><div class="payment-card-icon"><i class="fas fa-credit-card"></i></div>' +
          '<div><strong>' + p.card_type + '</strong><br><small style="color:var(--text-secondary);">**** ' + p.last_four + ' - ' + p.provider + '</small></div></div>';
      }).join('') : '<div class="empty-state"><i class="fas fa-credit-card"></i><p>No saved payment methods</p></div>';
      el.innerHTML = '<div class="page-header">' +
        '<button class="back-btn" onclick="closeOverlay(\'page-saved-payments\')"><i class="fas fa-arrow-left"></i></button>' +
        '<h2>Saved Payments</h2></div>' +
        '<div class="scroll-content">' + listHtml +
        '<div class="card" style="margin-top:16px;"><h4 style="font-weight:700;margin-bottom:14px;">Add Payment Method</h4>' +
        '<div class="form-group"><label>Card Type</label><select id="newCardType"><option>Visa</option><option>Mastercard</option><option>GCash</option><option>Maya</option></select></div>' +
        '<div class="form-group"><label>Last 4 Digits</label><input type="text" id="newLastFour" maxlength="4" placeholder="1234"><span class="field-error" id="lastFourErr"></span></div>' +
        '<div class="form-group"><label>Provider</label><input type="text" id="newProvider" placeholder="e.g. BDO, BPI, GCash"></div>' +
        '<button class="btn-primary" onclick="addSavedPayment()"><i class="fas fa-plus"></i> Add Method</button>' +
        '</div></div>';
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

function addSavedPayment() {
  var cardTypeEl = document.getElementById('newCardType');
  var lastFourEl = document.getElementById('newLastFour');
  var providerEl = document.getElementById('newProvider');
  var errEl = document.getElementById('lastFourErr');
  var cardType = cardTypeEl ? cardTypeEl.value : 'Visa';
  var lastFour = lastFourEl ? lastFourEl.value.trim() : '';
  var provider = providerEl ? sanitizeInput(providerEl.value.trim()) : '';
  if (errEl) errEl.textContent = '';
  if (!isValidLastFour(lastFour)) { if (errEl) errEl.textContent = 'Must be exactly 4 digits.'; return; }
  showLoading(true);
  apiCall('/saved-payment', { method: 'POST', body: JSON.stringify({ user_id: currentUser.id, card_type: cardType, last_four: lastFour, provider: provider }) })
    .then(function() { showToast('Payment method saved!', 'success'); loadSavedPayments(); })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

// FAVORITES
function loadFavorites() {
  if (!currentUser.id) return;
  showLoading(true);
  apiCall('/favorites?user_id=' + currentUser.id)
    .then(function(data) {
      var el = document.getElementById('favoritesContent');
      if (!el) return;
      el.innerHTML = '<div class="page-header">' +
        '<button class="back-btn" onclick="closeOverlay(\'page-favorites\')"><i class="fas fa-arrow-left"></i></button>' +
        '<h2>My Favorites</h2></div>' +
        '<div class="vehicle-grid" style="padding:16px;">' +
        (data.length ? data.map(function(v) {
          return '<div class="vehicle-card" onclick="openVehicleDetail(' + v.id + ')">' +
            '<div class="vehicle-img-wrap"><img src="' + buildImgUrl(v.vehicle_image) + '" alt="' + v.brand + ' ' + v.model + '" onerror="this.src=\'https://via.placeholder.com/400x200?text=No+Image\'"></div>' +
            '<div class="vehicle-info"><h3>' + v.brand + ' ' + v.model + '</h3>' +
            '<div class="vehicle-meta"><i class="fas fa-map-marker-alt"></i> ' + (v.location || '-') + '</div>' +
            '<div class="vehicle-rate">' + formatPHP(v.daily_rate) + ' <span>/ day</span></div></div></div>';
        }).join('') : '<div class="empty-state"><i class="fas fa-heart"></i><p>No favorites yet</p></div>') +
        '</div>';
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

// SPLIT PAYMENT
function loadSplitPayment() {
  var el = document.getElementById('splitPaymentContent');
  if (!el) return;
  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-split-payment\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Split Payment</h2></div>' +
    '<div class="scroll-content"><div class="card">' +
    '<h4 style="font-weight:700;margin-bottom:14px;">Request Split</h4>' +
    '<div class="form-group"><label>Partner Email</label><input type="email" id="splitEmail" placeholder="partner@gmail.com"><span class="field-error" id="splitEmailErr"></span></div>' +
    '<div class="form-group"><label>Amount for Partner (PHP)</label><input type="number" id="splitAmount" placeholder="0.00"></div>' +
    '<button class="btn-primary" onclick="requestSplit()"><i class="fas fa-users"></i> Request Split</button>' +
    '</div>' +
    '<div class="card" style="margin-top:16px;"><h4 style="font-weight:700;margin-bottom:14px;">Incoming Split Requests</h4>' +
    '<div id="splitBillsList"><p style="color:var(--text-muted);font-size:0.875rem;">Loading...</p></div></div>' +
    '</div>';
  loadSplitBills();
}

function requestSplit() {
  var emailEl = document.getElementById('splitEmail');
  var amountEl = document.getElementById('splitAmount');
  var errEl = document.getElementById('splitEmailErr');
  var email = emailEl ? emailEl.value.trim() : '';
  var amount = amountEl ? parseFloat(amountEl.value) : 0;
  if (errEl) errEl.textContent = '';
  if (!email) { if (errEl) errEl.textContent = 'Partner email is required.'; return; }
  showLoading(true);
  apiCall('/split-bill/request', { method: 'POST', body: JSON.stringify({ booking_id: activeBookingId, partner_email: email, amount: amount }) })
    .then(function() { showToast('Split request sent! Awaiting partner confirmation.', 'success'); })
    .catch(function(err) { if (errEl) errEl.textContent = err.message; })
    .finally(function() { showLoading(false); });
}

function loadSplitBills() {
  if (!currentUser.id) return;
  apiCall('/split-bills?email=' + (currentUser.email || ''))
    .then(function(data) {
      var el = document.getElementById('splitBillsList');
      if (!el) return;
      if (!data.length) { el.innerHTML = '<p style="color:var(--text-muted);font-size:0.875rem;">No incoming split requests</p>'; return; }
      el.innerHTML = data.map(function(s) {
        return '<div class="split-status">' +
          '<strong>' + (s.initiator_name || 'Someone') + '</strong> wants to split Booking #' + s.booking_id + '<br>' +
          '<small>' + (s.vehicle_brand || '') + ' ' + (s.vehicle_model || '') + ' | ' + s.start_date + ' to ' + s.end_date + '</small><br>' +
          '<strong style="color:var(--primary);">Your share: ' + formatPHP(s.amount) + '</strong><br>' +
          statusPill(s.status) +
          (s.status !== 'Paid' ? '<button class="btn-primary btn-sm" style="margin-top:8px;" onclick="paySplit(' + s.id + ')">Pay My Share</button>' : '') +
          '</div>';
      }).join('');
    }).catch(function() {});
}

function paySplit(splitId) {
  showLoading(true);
  apiCall('/split-bill/pay', { method: 'POST', body: JSON.stringify({ split_id: splitId, user_id: currentUser.id }) })
    .then(function() { showToast('Split payment completed!', 'success'); loadSplitBills(); })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

// SUPPORT
function loadSupport() {
  var el = document.getElementById('supportContent');
  if (!el) return;
  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-support\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Support</h2></div>' +
    '<div class="scroll-content"><div class="card">' +
    '<h4 style="font-weight:700;margin-bottom:14px;">Submit a Ticket</h4>' +
    '<div class="form-group"><label>Name *</label><input type="text" id="suppName" value="' + (currentUser.fullName || '') + '"><span class="field-error" id="suppNameErr"></span></div>' +
    '<div class="form-group"><label>Email</label><input type="email" id="suppEmail" placeholder="yourname@gmail.com"></div>' +
    '<div class="form-group"><label>Subject *</label><input type="text" id="suppSubject" placeholder="Brief description"><span class="field-error" id="suppSubjectErr"></span></div>' +
    '<div class="form-group"><label>Message *</label><textarea id="suppMessage" placeholder="Describe your issue..."></textarea><span class="field-error" id="suppMessageErr"></span></div>' +
    '<span class="field-error" id="suppErr" style="display:block;margin-bottom:12px;"></span>' +
    '<button class="btn-primary" onclick="submitSupport()"><i class="fas fa-paper-plane"></i> Submit Ticket</button>' +
    '</div></div>';
}

function submitSupport() {
  var name = sanitizeInput(document.getElementById('suppName').value.trim());
  var email = sanitizeInput(document.getElementById('suppEmail').value.trim());
  var subject = sanitizeInput(document.getElementById('suppSubject').value.trim());
  var message = sanitizeInput(document.getElementById('suppMessage').value.trim());
  ['suppNameErr','suppSubjectErr','suppMessageErr','suppErr'].forEach(function(id) {
    var el = document.getElementById(id); if (el) el.textContent = '';
  });
  if (isBlank(name)) { document.getElementById('suppNameErr').textContent = 'Name is required.'; return; }
  if (isBlank(subject)) { document.getElementById('suppSubjectErr').textContent = 'Subject is required.'; return; }
  if (isBlank(message)) { document.getElementById('suppMessageErr').textContent = 'Message is required.'; return; }
  showLoading(true);
  apiCall('/support', { method: 'POST', body: JSON.stringify({ name: name, email: email, subject: subject, message: message }) })
    .then(function() { showToast('Support ticket submitted successfully.', 'success'); closeOverlay('page-support'); })
    .catch(function(err) { document.getElementById('suppErr').textContent = err.message; })
    .finally(function() { showLoading(false); });
}

// CHATBOT
function loadChatbot() {
  var el = document.getElementById('chatbotContent');
  if (!el) return;
  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-chatbot\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Chat Assistant</h2></div>' +
    '<div class="chat-messages" id="chatMessages">' +
    '<div class="chat-msg bot">Hi! I\'m the Autoride assistant. How can I help you today?</div>' +
    '</div>' +
    '<div class="chat-input-row">' +
    '<input type="text" id="chatInput" placeholder="Type a message..." onkeydown="if(event.key===\'Enter\')sendChat()">' +
    '<button onclick="sendChat()"><i class="fas fa-paper-plane"></i></button>' +
    '</div>';
}

function sendChat() {
  var inputEl = document.getElementById('chatInput');
  if (!inputEl) return;
  var msg = sanitizeInput(inputEl.value.trim());
  if (isBlank(msg)) return;
  inputEl.value = '';
  var msgs = document.getElementById('chatMessages');
  if (!msgs) return;
  msgs.innerHTML += '<div class="chat-msg user">' + msg + '</div>';
  msgs.scrollTop = msgs.scrollHeight;
  apiCall('/chat', { method: 'POST', body: JSON.stringify({ message: msg, user_id: currentUser.id }) })
    .then(function(data) {
      msgs.innerHTML += '<div class="chat-msg bot">' + (data.response || 'I\'m not sure about that. Please contact support.') + '</div>';
    })
    .catch(function() {
      msgs.innerHTML += '<div class="chat-msg bot">Sorry, I couldn\'t process that. Please try again.</div>';
    })
    .finally(function() { msgs.scrollTop = msgs.scrollHeight; });
}

// NOTIFICATIONS
function loadNotifications() {
  NotifStore.getAll().then(function(all) {
    NotifStore.markAllRead();
    var el = document.getElementById('notificationsContent');
    if (!el) return;
    el.innerHTML = '<div class="page-header">' +
      '<button class="back-btn" onclick="closeOverlay(\'page-notifications\')"><i class="fas fa-arrow-left"></i></button>' +
      '<h2>Notifications</h2></div>' +
      '<div class="scroll-content">' +
      (all.length ? all.map(function(n) {
        return '<div class="notif-item ' + (n.read ? '' : 'unread') + '">' +
          '<p>' + n.msg + '</p>' +
          '<small>' + new Date(n.ts).toLocaleString() + '</small>' +
          '</div>';
      }).join('') : '<div class="empty-state"><i class="fas fa-bell-slash"></i><p>No notifications yet</p></div>') +
      '</div>';
  });
}

// NEWSLETTER
function loadNewsletter() {
  var el = document.getElementById('newsletterContent');
  if (!el) return;
  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-newsletter\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Newsletter</h2></div>' +
    '<div class="scroll-content"><div class="card">' +
    '<h4 style="font-weight:700;margin-bottom:10px;">Stay Updated</h4>' +
    '<p style="font-size:0.875rem;color:var(--text-secondary);margin-bottom:14px;">Subscribe to receive promos and news from Autoride.</p>' +
    '<div class="form-group"><label>Email Address</label><input type="email" id="nlEmail" placeholder="yourname@gmail.com"><span class="field-error" id="nlErr"></span></div>' +
    '<button class="btn-primary" onclick="doSubscribeNewsletter()"><i class="fas fa-envelope"></i> Subscribe</button>' +
    '</div></div>';
}

function doSubscribeNewsletter() {
  var emailEl = document.getElementById('nlEmail');
  var errEl = document.getElementById('nlErr');
  var email = emailEl ? emailEl.value.trim() : '';
  if (errEl) errEl.textContent = '';
  if (!email || email.indexOf('@') < 0) { if (errEl) errEl.textContent = 'Please enter a valid email.'; return; }
  showLoading(true);
  apiCall('/newsletter', { method: 'POST', body: JSON.stringify({ email: email }) })
    .then(function() { showToast('Subscribed successfully!', 'success'); closeOverlay('page-newsletter'); })
    .catch(function(err) { if (errEl) errEl.textContent = err.message; })
    .finally(function() { showLoading(false); });
}
