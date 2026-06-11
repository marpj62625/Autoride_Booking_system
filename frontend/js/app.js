/**
 * Autoride Customer Mobile App - Main Application Script
 * utils.js is loaded as a separate script tag before this file
 */

// CONFIG Â auto-detect API URL for web vs APK
var API_BASE = (function() {
  if (typeof window !== 'undefined' && window._API_BASE) return window._API_BASE;
  // Always use production URL on native Capacitor APK
  if (typeof window !== 'undefined' && window.Capacitor && window.Capacitor.isNative) {
    return 'https://autoride-booking-system.vercel.app/api';
  }
  if (typeof window !== 'undefined') {
    var h = window.location.hostname;
    if (h === 'localhost' || h === '127.0.0.1') return 'http://localhost:5000/api';
    if (window.location.protocol === 'https:') {
      return window.location.origin + '/api';
    }
  }
  return 'https://autoride-booking-system.vercel.app/api';
}());

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

// SUPABASE REALTIME (in-app notifications)
var SUPABASE_URL = 'https://fydfsgjrlowrrtlmefwq.supabase.co';
var SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5ZGZzZ2pybG93cnJ0bG1lZndxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUwMjkwNTcsImV4cCI6MjA5MDYwNTA1N30.m94HHMC7852zw9xfkkOYTPY1IzoH_kNPLYpTe0myGB4';
var supabaseClient = null;
var notifChannel = null;
var notifList = [];

// CAPACITOR PLUGINS (safe access)
function getPreferences() {
  return (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Preferences) || null;
}
function getCamera() {
  return (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Camera) || null;
}

// SESSION - expires after 8 hours of inactivity
var SESSION_TTL_MS = 8 * 60 * 60 * 1000; // 8 hours

var Session = {
  save: function(user) {
    var data = JSON.stringify({ user: user, savedAt: Date.now() });
    var prefs = getPreferences();
    if (prefs) {
      prefs.set({ key: 'user', value: data });
    } else {
      try { localStorage.setItem('user', data); } catch(e) {}
    }
  },
  load: function() {
    return new Promise(function(resolve) {
      var prefs = getPreferences();
      var parse = function(raw) {
        if (!raw) return null;
        try {
          var parsed = JSON.parse(raw);
          // Support old format (plain user object without savedAt)
          if (parsed && parsed.id) return parsed; // old format - no expiry check
          if (parsed && parsed.user && parsed.savedAt) {
            var age = Date.now() - parsed.savedAt;
            if (age > SESSION_TTL_MS) return null; // expired
            return parsed.user;
          }
          return null;
        } catch(e) { return null; }
      };
      if (prefs) {
        var _prefsDone = false;
        var _prefsTimer = setTimeout(function() {
          if (!_prefsDone) { _prefsDone = true;
            try { resolve(parse(localStorage.getItem('user'))); } catch(e) { resolve(null); }
          }
        }, 3000);
        prefs.get({ key: 'user' }).then(function(result) {
          if (!_prefsDone) { _prefsDone = true; clearTimeout(_prefsTimer); resolve(parse(result.value)); }
        }).catch(function() {
          if (!_prefsDone) { _prefsDone = true; clearTimeout(_prefsTimer); resolve(null); }
        });
      } else {
        try {
          resolve(parse(localStorage.getItem('user')));
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

// ?? BOOKING SESSION: save/restore in-progress booking state (1 minute TTL) ??
var BOOKING_SESSION_KEY = 'autoride_booking_session';
var BOOKING_SESSION_TTL = 60 * 1000; // 1 minute

var BookingSession = {
  save: function() {
    // Only save if there's an active booking flow
    var bookingFormOpen = document.getElementById('page-booking-form') &&
      document.getElementById('page-booking-form').classList.contains('active');
    var paymentOpen = document.getElementById('page-payment') &&
      document.getElementById('page-payment').classList.contains('active');
    var vehicleDetailOpen = document.getElementById('page-vehicle-detail') &&
      document.getElementById('page-vehicle-detail').classList.contains('active');

    if (!bookingFormOpen && !paymentOpen && !vehicleDetailOpen) return;

    var data = {
      savedAt: Date.now(),
      // Which overlays were open
      overlays: {
        vehicleDetail: vehicleDetailOpen,
        bookingForm: bookingFormOpen,
        payment: paymentOpen
      },
      // Vehicle
      vehicleId: bookingFormVehicle ? bookingFormVehicle.id : null,
      vehicle: bookingFormVehicle,
      currentVehicle: currentVehicleDetail,
      // Booking form fields
      startDate: (document.getElementById('bfStartDate') || {}).value || null,
      endDate: (document.getElementById('bfEndDate') || {}).value || null,
      pickupTime: (document.getElementById('bfPickupTime') || {}).value || '06:00',
      returnTime: (document.getElementById('bfReturnTime') || {}).value || '06:00',
      serviceType: (document.getElementById('bfServiceType') || {}).value || 'pickup',
      pickupLocation: (document.getElementById('bfPickupLocation') || {}).value || null,
      rentalType: (document.getElementById('bfRentalType') || {}).value || 'Self-Drive',
      paymentType: (document.getElementById('bfPaymentType') || {}).value || 'Full',
      points: (document.getElementById('bfPoints') || {}).value || '0',
      // Selections
      selectedAddons: JSON.parse(JSON.stringify(selectedAddons)),
      selectedInsurance: JSON.parse(JSON.stringify(selectedInsurance)),
      couponData: couponData ? JSON.parse(JSON.stringify(couponData)) : null,
      // Payment state
      bookingId: activeBookingId,
      pendingPriceResult: _pendingPriceResult ? JSON.parse(JSON.stringify(_pendingPriceResult)) : null,
      pendingPayType: _pendingPayType,
      pendingPayload: _pendingBookingPayload ? JSON.parse(JSON.stringify(_pendingBookingPayload)) : null
    };
    try { localStorage.setItem(BOOKING_SESSION_KEY, JSON.stringify(data)); } catch(e) {}
  },

  load: function() {
    try {
      var raw = localStorage.getItem(BOOKING_SESSION_KEY);
      if (!raw) return null;
      var data = JSON.parse(raw);
      if (!data || !data.savedAt) return null;
      var age = Date.now() - data.savedAt;
      if (age > BOOKING_SESSION_TTL) {
        localStorage.removeItem(BOOKING_SESSION_KEY);
        return null;
      }
      return data;
    } catch(e) { return null; }
  },

  clear: function() {
    try { localStorage.removeItem(BOOKING_SESSION_KEY); } catch(e) {}
  },

  restore: function() {
    var data = this.load();
    if (!data) return false;

    // Restore global state
    if (data.vehicle) bookingFormVehicle = data.vehicle;
    if (data.currentVehicle) currentVehicleDetail = data.currentVehicle;
    if (data.selectedAddons) selectedAddons = data.selectedAddons;
    if (data.selectedInsurance) selectedInsurance = data.selectedInsurance;
    if (data.couponData !== undefined) couponData = data.couponData;
    if (data.pendingPriceResult) _pendingPriceResult = data.pendingPriceResult;
    if (data.pendingPayType) _pendingPayType = data.pendingPayType;
    if (data.pendingPayload) _pendingBookingPayload = data.pendingPayload;
    if (data.bookingId) activeBookingId = data.bookingId;

    this.clear(); // consume the session

    // Reopen to the deepest overlay that was open
    if (data.overlays.payment && data.bookingId && data.pendingPriceResult) {
      // Restore to payment screen
      showToast('Restored your payment session.', 'info');
      openPaymentScreen(data.bookingId, data.pendingPriceResult, data.pendingPayType || 'Full');
      return true;
    }

    if (data.overlays.bookingForm && data.vehicle) {
      // Reopen booking form - need to show vehicle detail first then form
      showToast('Restored your booking session.', 'info');
      openBookingFormWithData(data);
      return true;
    }

    if (data.overlays.vehicleDetail && data.currentVehicle) {
      showToast('Restored your last viewed vehicle.', 'info');
      openVehicleDetail(data.currentVehicle);
      return true;
    }

    return false;
  }
};

function openBookingFormWithData(sessionData) {
  // Open the booking form and restore field values after render
  openBookingForm(sessionData.vehicleId || (sessionData.vehicle && sessionData.vehicle.id));
  // Restore fields after a short delay (form renders async)
  setTimeout(function() {
    if (sessionData.startDate) {
      var el = document.getElementById('bfStartDate');
      if (el) { el.value = sessionData.startDate; }
    }
    if (sessionData.endDate) {
      var el = document.getElementById('bfEndDate');
      if (el) { el.value = sessionData.endDate; }
    }
    if (sessionData.pickupTime) {
      var el = document.getElementById('bfPickupTime');
      if (el) { el.value = sessionData.pickupTime; }
    }
    if (sessionData.returnTime) {
      var el = document.getElementById('bfReturnTime');
      if (el) { el.value = sessionData.returnTime; }
    }
    if (sessionData.serviceType) {
      var el = document.getElementById('bfServiceType');
      if (el) { el.value = sessionData.serviceType; }
      setServiceType(sessionData.serviceType);
    }
    if (sessionData.pickupLocation) {
      var el = document.getElementById('bfPickupLocation');
      if (el) { el.value = sessionData.pickupLocation; }
    }
    if (sessionData.rentalType) {
      var el = document.getElementById('bfRentalType');
      if (el) { el.value = sessionData.rentalType; }
    }
    if (sessionData.paymentType) {
      var el = document.getElementById('bfPaymentType');
      if (el) { el.value = sessionData.paymentType; }
    }
    if (sessionData.points) {
      var el = document.getElementById('bfPoints');
      if (el) { el.value = sessionData.points; }
    }
    // Restore addon checkboxes
    if (sessionData.selectedAddons && sessionData.selectedAddons.length > 0) {
      sessionData.selectedAddons.forEach(function(addon) {
        var ADDON_NAMES = (typeof ADDON_OPTIONS !== 'undefined') ? ADDON_OPTIONS.map(function(a) { return a.name; }) : [];
        var idx = ADDON_NAMES.indexOf(addon.name);
        if (idx >= 0) {
          var chk = document.getElementById('addonChk_' + idx);
          var card = document.getElementById('addon_' + idx);
          if (chk) chk.checked = true;
          if (card) card.classList.add('selected');
        }
      });
    }
    // Trigger price update
    if (typeof updateBookingPrice === 'function') updateBookingPrice();
  }, 300);
}


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

// FCM TOKEN REGISTRATION
function saveFcmToken(token) {
  if (!token || !currentUser.id) return;
  apiCall('/user/fcm-token', {
    method: 'POST',
    body: JSON.stringify({ user_id: currentUser.id, fcm_token: token })
  }).catch(function() {});
}

// SERVER-BACKED NOTIFICATIONS
function loadNotifications(userId) {    return apiCall('/notifications?user_id=' + userId)
        .then(function(data) {
            notifList = Array.isArray(data) ? data : [];
            updateNotifBadge();
            return notifList;
        })
        .catch(function() {
            notifList = [];
            return [];
        });
}

function subscribeToNotifications(userId) {
    if (!supabaseClient) return;
    if (notifChannel) supabaseClient.removeChannel(notifChannel);
    notifChannel = supabaseClient
        .channel('user-notifications-' + userId)
        .on('postgres_changes', {
            event: 'INSERT',
            schema: 'public',
            table: 'notifications',
            filter: 'user_id=eq.' + userId
        }, function(payload) {
            if (payload && payload.new) {
                notifList.unshift(payload.new);
                updateNotifBadge();

                var type  = payload.new.type  || '';
                var title = payload.new.title || 'Autoride';
                var msg   = payload.new.message || '';

                // Show in-app popup toast for all actionable notification types
                if (type === 'extension_approved') {
                    _showNotifPopup(title, msg, '#00b14f', 'fa-calendar-check');
                    // Refresh bookings so the new end date shows immediately
                    if (typeof loadBookings === 'function') loadBookings();
                } else if (type === 'extension_rejected') {
                    _showNotifPopup(title, msg, '#f59e0b', 'fa-calendar-times');
                    if (typeof loadBookings === 'function') loadBookings();
                } else if (type === 'refund_processed') {
                    _showNotifPopup(title, msg, '#00b14f', 'fa-undo-alt');
                    if (typeof loadBookings === 'function') loadBookings();
                } else if (type === 'booking_approved' || type === 'booking_confirmed') {
                    _showNotifPopup(title, msg, '#00b14f', 'fa-check-circle');
                } else if (type === 'booking_cancelled' || type === 'booking_cancelled_by_admin') {
                    _showNotifPopup(title, msg, '#f87171', 'fa-times-circle');
                } else if (type === 'payment_confirmed') {
                    _showNotifPopup(title, msg, '#00b14f', 'fa-money-bill-wave');
                }

                // License status refresh
                if (type === 'license_approved' || type === 'license_rejected') {
                    if (type === 'license_approved') {
                        _showNotifPopup(title, msg, '#00b14f', 'fa-id-card');
                    } else {
                        _showNotifPopup(title, msg, '#f87171', 'fa-id-card');
                    }
                    apiCall('/user/verify-status?user_id=' + userId)
                        .then(function(v) {
                            currentUser.isVerified = v.is_verified !== undefined ? v.is_verified : currentUser.isVerified;
                            Session.save(currentUser);
                            var badge = document.getElementById('profileVerifyBadge');
                            if (badge) {
                                var labels = { 0: 'Not Verified', 1: 'Pending Review', 2: 'Verified' };
                                badge.textContent = labels[currentUser.isVerified] || 'Not Verified';
                                badge.className = 'verify-badge verify-' + currentUser.isVerified;
                            }
                            var statusEl = document.getElementById('viewLicenseStatus');
                            if (statusEl) {
                                var statusMap = { 0: 'Not Verified', 1: 'Pending Review', 2: 'Verified' };
                                var statusColor = { 0: 'var(--danger)', 1: '#f59e0b', 2: '#10b981' };
                                var v2 = currentUser.isVerified;
                                statusEl.textContent = statusMap[v2] || '-';
                                statusEl.style.color = statusColor[v2] || 'var(--text-main)';
                            }
                        }).catch(function() {});
                }
            }
        })
        .subscribe();
}

// In-app notification popup (shown when app is open and notification arrives)
var _notifPopupTimer = null;
function _showNotifPopup(title, message, color, iconClass) {
    color = color || '#00b14f';
    iconClass = iconClass || 'fa-bell';

    // Remove existing popup
    var existing = document.getElementById('_notifPopup');
    if (existing) existing.remove();
    if (_notifPopupTimer) clearTimeout(_notifPopupTimer);

    var popup = document.createElement('div');
    popup.id = '_notifPopup';
    popup.style.cssText = [
        'position:fixed',
        'top:16px',
        'left:50%',
        'transform:translateX(-50%) translateY(-80px)',
        'z-index:99999',
        'background:var(--bg-card, #1e293b)',
        'color:var(--text-primary, #f1f5f9)',
        'border:1.5px solid ' + color,
        'border-radius:16px',
        'padding:12px 18px',
        'min-width:280px',
        'max-width:340px',
        'box-shadow:0 8px 32px rgba(0,0,0,0.35)',
        'display:flex',
        'align-items:flex-start',
        'gap:12px',
        'transition:transform 0.3s cubic-bezier(0.34,1.56,0.64,1),opacity 0.3s',
        'opacity:0',
        'cursor:pointer'
    ].join(';');

    popup.innerHTML =
        '<div style="width:34px;height:34px;border-radius:50%;background:' + color + '22;border:1.5px solid ' + color + ';display:flex;align-items:center;justify-content:center;flex-shrink:0;">' +
            '<i class="fas ' + iconClass + '" style="font-size:0.85rem;color:' + color + ';"></i>' +
        '</div>' +
        '<div style="flex:1;min-width:0;">' +
            '<div style="font-size:0.82rem;font-weight:800;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + (title || 'Autoride') + '</div>' +
            '<div style="font-size:0.75rem;color:var(--text-muted,#94a3b8);line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">' + (message || '') + '</div>' +
        '</div>' +
        '<button onclick="document.getElementById(\'_notifPopup\').remove()" style="background:none;border:none;color:var(--text-muted,#94a3b8);font-size:1rem;cursor:pointer;padding:0;line-height:1;flex-shrink:0;">&times;</button>';

    // Tap to open notifications
    popup.addEventListener('click', function(e) {
        if (e.target.tagName !== 'BUTTON') {
            showOverlay('page-notifications');
        }
    });

    document.body.appendChild(popup);

    // Animate in
    requestAnimationFrame(function() {
        popup.style.opacity = '1';
        popup.style.transform = 'translateX(-50%) translateY(0)';
    });

    // Auto dismiss after 5s
    _notifPopupTimer = setTimeout(function() {
        if (popup.parentNode) {
            popup.style.opacity = '0';
            popup.style.transform = 'translateX(-50%) translateY(-80px)';
            setTimeout(function() { if (popup.parentNode) popup.remove(); }, 300);
        }
    }, 5000);
}

function unsubscribeFromNotifications() {
    if (supabaseClient && notifChannel) {
        supabaseClient.removeChannel(notifChannel);
        notifChannel = null;
    }
}

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
      return res.text().then(function(text) {
        var data;
        try { data = JSON.parse(text); } catch(e) {
          var parseErr = new Error('Server error (status ' + res.status + ')');
          parseErr.status = res.status;
          throw parseErr;
        }
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
      var netErr = new Error('Network error during upload. Check connection.');
      netErr.status = 0;
      throw netErr;
    });
}

// UI HELPERS
// Progress bar loading - also shows full-screen blocking overlay
var _loadingCount = 0;
var _loadingTimeout = null;
function showLoading(show) {
  var overlay = document.getElementById('loadingOverlay');
  if (show) {
    _loadingCount++;
    if (overlay) overlay.style.display = 'flex';
    // Safety: auto-hide after 10s to prevent spinner getting stuck
    clearTimeout(_loadingTimeout);
    _loadingTimeout = setTimeout(function() {
      _loadingCount = 0;
      if (overlay) overlay.style.display = 'none';
    }, 10000);
  } else {
    _loadingCount = Math.max(0, _loadingCount - 1);
    if (_loadingCount === 0) {
      clearTimeout(_loadingTimeout);
      if (overlay) overlay.style.display = 'none';
    }
  }
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
  // Save booking session if user navigates away mid-booking
  try { BookingSession.save(); } catch(e) {}

  // Close ALL overlays first
  var overlays = document.querySelectorAll('.overlay-page');
  for (var i = 0; i < overlays.length; i++) {
    overlays[i].classList.remove('active');
    overlays[i].style.display = 'none';
  }
  stopGpsPolling();
  // Stop active booking countdown when leaving home
  if (id !== 'page-home' && _activeBookingTimer) {
    clearInterval(_activeBookingTimer);
    _activeBookingTimer = null;
  }

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
  if (id === 'page-vehicles') {
    // Check for saved booking session (1-min TTL)
    try {
      var restored = BookingSession.restore();
      if (!restored) loadVehicles();
    } catch(e) { loadVehicles(); }

    // Show banner if user has an active booking
    setTimeout(function() {
      var banner = document.getElementById('browseActiveBanner');
      var ACTIVE_STATUSES = ['Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing'];
      var hasActive = _allBookingsData.some(function(b) {
        return ACTIVE_STATUSES.indexOf(b.status) !== -1;
      });
      if (banner) banner.style.display = hasActive ? 'flex' : 'none';
    }, 100);
  }
  if (id === 'page-bookings') {
    try {
      var paySession = BookingSession.load();
      if (paySession && paySession.overlays && paySession.overlays.payment) {
        BookingSession.restore();
      } else {
        loadBookings();
      }
    } catch(e) { loadBookings(); }
  }
  if (id === 'page-profile') loadProfile();
  if (id === 'page-more') loadMorePage();
}

function showOverlay(id) {
  var el = document.getElementById(id);
  if (!el) return;
  el.classList.add('active');
  el.style.display = 'block';
  if (id === 'page-notifications') openNotificationsPage();
  if (id === 'page-favorites') loadFavorites();
  if (id === 'page-saved-payments') loadSavedPayments();
  if (id === 'page-license-upload') openLicenseUpload();
  if (id === 'page-chatbot') loadChatbot();
  if (id === 'page-livechat') loadLiveChat();
  if (id === 'page-newsletter') loadNewsletter();
}

function closeOverlay(id) {
  var el = document.getElementById(id);
  if (!el) return;
  el.classList.remove('active');
  el.style.display = 'none';
  if (id === 'page-gps-map') stopGpsPolling();
  if (id === 'page-livechat') LiveChat.stopPolling();
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
    var unread = notifList.filter(function(n) { return !n.is_read; }).length;
    var badge = document.getElementById('notifBadge');
    if (!badge) return;
    if (unread > 0) {
        badge.textContent = unread > 99 ? '99+' : String(unread);
        badge.classList.remove('hidden');
    } else {
        badge.classList.add('hidden');
    }
}

function updateChatUnreadBadge() {
    if (!currentUser.id) return;
    apiCall('/chat/inbox?viewer_type=user&viewer_id=' + currentUser.id)
        .then(function(data) {
            var badge = document.getElementById('chatUnreadBadge');
            if (!badge) return;
            var total = 0;
            if (Array.isArray(data)) {
                data.forEach(function(c) { total += parseInt(c.unread_count) || 0; });
            }
            if (total > 0) {
                badge.textContent = total > 9 ? '9+' : String(total);
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        })
        .catch(function() {});
}

// STARTUP - run immediately when script loads, also on events as fallback
var _appInitialized = false;
function initApp() {
  if (_appInitialized) return;
  _appInitialized = true;
  // Load theme - default to LIGHT
  var savedTheme = null;
  try { savedTheme = localStorage.getItem('theme'); } catch(e) {}
  if (savedTheme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    var icon = document.getElementById('darkModeIcon');
    var label = document.getElementById('darkModeLabel');
    if (icon) icon.className = 'fas fa-sun';
    if (label) label.textContent = 'Light Mode';
  } else {
    document.documentElement.removeAttribute('data-theme');
  }
  // Clear stale booking session at every app start
  try { BookingSession.clear(); } catch(e) {}

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
      // Initialise Supabase client and load notifications
      if (typeof supabase !== 'undefined') {
          supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
      }
      loadNotifications(user.id);
      subscribeToNotifications(user.id);
      startBgChatPolling();
      // Register FCM token if already available from native layer
      if (window._fcmToken) saveFcmToken(window._fcmToken);
      showPage('page-home');
    } else {
      showPage('page-login');
    }
    updateNotifBadge();
  }).catch(function() {
    clearTimeout(_initTimeout);
    showPage('page-login');
  });
}

// Try immediately (script already loaded after DOM)
initApp();

// Also listen for events as fallback
document.addEventListener('DOMContentLoaded', initApp);
document.addEventListener('deviceready', function() {
  initApp();
  
  // Initialize Google Auth with explicit configuration
  if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.GoogleAuth) {
            console.log('Google Auth plugin available - initializing with config');
            window.Capacitor.Plugins.GoogleAuth.initialize({
      clientId: '857792394948-9m57q54s4638muf0ab5ihgakj4g44lje.apps.googleusercontent.com',
      scopes: ['profile', 'email'],
      grantOfflineAccess: true
    }).then(function() {
      console.log('[GoogleAuth] Initialized successfully');
    }).catch(function(err) {
      console.error('[GoogleAuth] Initialization error:', err);
            });
        } else {
    console.warn('[GoogleAuth] Plugin not available');
  }
});

// ---------------------------------------------------------------------------
// DARK MODE TOGGLE
// ---------------------------------------------------------------------------
function toggleDarkMode() {
  var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  var icon = document.getElementById('darkModeIcon');
  var label = document.getElementById('darkModeLabel');
  if (isDark) {
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('theme', 'light');
    if (icon) icon.className = 'fas fa-moon';
    if (label) label.textContent = 'Dark Mode';
  } else {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
    if (icon) icon.className = 'fas fa-sun';
    if (label) label.textContent = 'Light Mode';
  }
}

// ---------------------------------------------------------------------------
// PHYSICAL BACK BUTTON HANDLER
// ---------------------------------------------------------------------------
var _backPressedOnce = false;
var _backPressTimer = null;

function handleBackButton() {
  // 1. Close any open rental agreement modal
  var rentalModal = document.getElementById('rentalAgreementModal');
  if (rentalModal && rentalModal.parentNode) {
    rentalModal.remove();
    return;
  }

  // 2. Close any active overlay page (in reverse open order)
  var overlays = document.querySelectorAll('.overlay-page.active');
  if (overlays.length > 0) {
    // Close the last opened overlay
    var last = overlays[overlays.length - 1];
    closeOverlay(last.id);
    return;
  }

  // 3. On auth pages - do nothing (can't go back from login/register)
  var authPages = document.querySelectorAll('.auth-page.active');
  if (authPages.length > 0) {
    // On register/otp pages, go back to login
    var activeAuth = authPages[0];
    if (activeAuth.id === 'page-register' || activeAuth.id === 'page-otp-verify') {
      showPage('page-login');
    }
    // On login page itself - double-back to exit
    else {
      if (_backPressedOnce) {
        clearTimeout(_backPressTimer);
        if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App) {
          window.Capacitor.Plugins.App.exitApp();
        }
      } else {
        _backPressedOnce = true;
        showToast('Press back again to exit', 'info');
        _backPressTimer = setTimeout(function() { _backPressedOnce = false; }, 2000);
      }
    }
    return;
  }

  // 4. On main pages - double-back to exit (with logout)
  if (_backPressedOnce) {
    clearTimeout(_backPressTimer);
    // Logout then exit
    unsubscribeFromNotifications();
    notifList = [];
    Session.clear();
    currentUser = { id: null, fullName: '', isVerified: 0, loyaltyPoints: 0 };
    if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App) {
      window.Capacitor.Plugins.App.exitApp();
    }
  } else {
    _backPressedOnce = true;
    showToast('Press back again to exit and logout', 'info');
    _backPressTimer = setTimeout(function() { _backPressedOnce = false; }, 2000);
  }
}

// Register back button - always register immediately, also re-register on deviceready
(function() {
  function _backListener(e) {
    if (e && e.preventDefault) e.preventDefault();
    handleBackButton();
  }
  // Register now (for when script loads after deviceready)
  document.addEventListener('backbutton', _backListener, false);
  // Also register on deviceready (for Capacitor App plugin)
  document.addEventListener('deviceready', function() {
    // Re-add in case it wasn't registered yet
    document.removeEventListener('backbutton', _backListener, false);
    document.addEventListener('backbutton', _backListener, false);
    // Capacitor 3+ App plugin
    if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App) {
      window.Capacitor.Plugins.App.addListener('backButton', function() {
        handleBackButton();
      });
      // Deep link handler - fires when PayMongo success page redirects back
      window.Capacitor.Plugins.App.addListener('appUrlOpen', function(event) {
        var url = event.url || '';
        // com.autoride.customer://payment-success?booking_id=123
        if (url.indexOf('payment-success') !== -1) {
          // Close the in-app browser if open
          if (window.Capacitor.Plugins.Browser) {
            window.Capacitor.Plugins.Browser.close().catch(function() {});
          }
          // Extract booking_id
          var match = url.match(/booking_id=(\d+)/);
          if (match) {
            var bookingId = parseInt(match[1]);
            // Auto-check payment status
            checkPaymentStatus(bookingId, 0, 'online');
          }
        }
      });
    }
  }, false);
})();

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
      // Initialise Supabase client and load notifications
      if (typeof supabase !== 'undefined') {
          supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
      }
      loadNotifications(data.user_id);
      subscribeToNotifications(data.user_id);
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
  var GOOGLE_CLIENT_ID = '857792394948-9m57q54s4638muf0ab5ihgakj4g44lje.apps.googleusercontent.com';

  var isCapacitorNative = window.Capacitor && window.Capacitor.isNative;
  var plugins = window.Capacitor && window.Capacitor.Plugins;
  var GoogleAuthPlugin = plugins && plugins.GoogleAuth;

  // Native APK Â use Capacitor GoogleAuth plugin
  if (isCapacitorNative && GoogleAuthPlugin) {
    showLoading(true);
    GoogleAuthPlugin.signIn()
      .then(function(result) {
        showLoading(false);
        var idToken = (result.authentication && result.authentication.idToken)
          || result.idToken || result.credential || null;
        var accessToken = (result.authentication && result.authentication.accessToken)
          || result.accessToken || null;
        var email = result.email || (result.profile && result.profile.email);
        var name = result.name || result.displayName
          || (result.profile && result.profile.name) || 'User';

        if (!email) throw new Error('No email received from Google');
        return _finishGoogleLogin(idToken || accessToken || ('ga_' + Date.now()), email, name);
      })
      .catch(function(err) {
        showLoading(false);
        var rawMsg = '';
        try { rawMsg = JSON.stringify(err); } catch(e) { rawMsg = String(err); }
        var msg = (err && (err.message || err.errorMessage || rawMsg)) || 'Unknown';
        var code = (err && (err.errorCode || err.code || '')) || '';

        if (msg.includes('12501') || msg.toLowerCase().includes('cancel')) {
          showToast('Sign-in cancelled', 'info');
        } else if (msg.includes('12500')) {
          showToast('No Google account on device. Add a Google account in Settings first.', 'error');
        } else if (msg.includes('10') || code === '10') {
          showToast('Google Sign-In configuration error. Please contact support.', 'error');
        } else {
          showToast('Google Sign-In failed. Please try again.', 'error');
        }
      });
    return;
  }

  // Web browser Â use OAuth2 popup
  _doGoogleOAuth2Popup(GOOGLE_CLIENT_ID);
}

function _doGoogleOAuth2Popup(clientId) {
  if (typeof google === 'undefined' || !google.accounts || !google.accounts.oauth2) {
    showToast('Google Sign-In not available. Please try again.', 'error');
    return;
  }
  var tokenClient = google.accounts.oauth2.initTokenClient({
    client_id: clientId,
    scope: 'email profile openid',
    callback: function(tokenResponse) {
      if (tokenResponse.error) {
        showToast('Google Sign-In failed: ' + tokenResponse.error, 'error');
        return;
      }
      showLoading(true);
      fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
        headers: { 'Authorization': 'Bearer ' + tokenResponse.access_token }
      })
        .then(function(r) { return r.json(); })
        .then(function(userInfo) {
          showLoading(false); // hand off to _finishGoogleLogin which manages its own loading
          return _finishGoogleLogin(
            tokenResponse.access_token,
            userInfo.email,
            userInfo.name || ((userInfo.given_name || '') + ' ' + (userInfo.family_name || '')).trim()
          );
        })
        .catch(function(err) {
          showLoading(false);
          showToast('Google Sign-In failed. Please try again.', 'error');
        });
    }
  });
  tokenClient.requestAccessToken({ prompt: 'select_account' });
}

function _finishGoogleLogin(idToken, email, name) {
  showLoading(true);
  return apiCall('/auth/google', {
    method: 'POST',
    body: JSON.stringify({ id_token: idToken, email: email, name: name })
  })
    .then(function(data) {
      if (data && data.user) {
        currentUser = data.user;
        Session.save(currentUser);
        showToast('Welcome, ' + currentUser.fullName + '!', 'success');
        apiCall('/public/settings').then(function(s) { Object.assign(appSettings, s); }).catch(function() {});
        if (typeof supabase !== 'undefined') {
          supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        }
        loadNotifications(currentUser.id);
        subscribeToNotifications(currentUser.id);
        startBgChatPolling();
        showPage('page-home');
      } else {
        showToast('Login failed. Please try again.', 'error');
      }
    })
    .catch(function(err) {
      showToast('Google Sign-In failed. Please try again.', 'error');
    })
    .finally(function() { showLoading(false); });
}

function doLogout() {
  unsubscribeFromNotifications();
  notifList = [];
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
      // Start countdown timer
      startResendCountdown();
      // Focus first OTP input
      setTimeout(function() {
        document.getElementById('otp0').focus();
      }, 300);
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
    .then(function(data) {
      showToast('Email verified successfully!', 'success');
      
      // Auto-login after verification
      if (data && data.user) {
        currentUser = data.user;
        Session.save(currentUser);
        
        // Initialize Supabase client and load notifications
        if (typeof supabase !== 'undefined') {
          supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        }
        loadNotifications(data.user.id);
        subscribeToNotifications(data.user.id);
        
        // Redirect to home page
        setTimeout(function() {
          loadHome();
          showPage('page-home');
        }, 500);
      } else {
        // Fallback to login page if no user data
        setTimeout(function() {
          showPage('page-login');
        }, 1000);
      }
    })
    .catch(function(err) {
      document.getElementById('otpErr').textContent = err.message || 'Invalid or expired verification code.';
    })
    .finally(function() { showLoading(false); });
}

var resendCountdown = 0;
var resendInterval = null;

function startResendCountdown() {
  resendCountdown = 30;
  document.getElementById('resendLink').style.display = 'none';
  document.getElementById('resendTimer').style.display = 'inline';
  document.getElementById('countdown').textContent = resendCountdown;
  
  if (resendInterval) clearInterval(resendInterval);
  
  resendInterval = setInterval(function() {
    resendCountdown--;
    document.getElementById('countdown').textContent = resendCountdown;
    
    if (resendCountdown <= 0) {
      clearInterval(resendInterval);
      document.getElementById('resendLink').style.display = 'inline';
      document.getElementById('resendTimer').style.display = 'none';
    }
  }, 1000);
}

function resendOtp() {
  if (!pendingOtpEmail || resendCountdown > 0) return;
  
  showLoading(true);
  apiCall('/auth/resend-otp', { method: 'POST', body: JSON.stringify({ email: pendingOtpEmail }) })
    .then(function() {
      showToast('Verification code sent!', 'success');
      startResendCountdown();
      // Clear OTP inputs
      for (var i = 0; i < 6; i++) {
        document.getElementById('otp' + i).value = '';
      }
      document.getElementById('otp0').focus();
    })
    .catch(function(err) {
      showToast(err.message || 'Failed to resend code', 'error');
    })
    .finally(function() { showLoading(false); });
}

function openGmail() {
  // Try to open Gmail app first, fallback to web
  var gmailApp = 'googlegmail://';
  var gmailWeb = 'https://mail.google.com';
  
  // For mobile apps, try to open Gmail app
  if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App) {
    window.Capacitor.Plugins.App.openUrl({ url: gmailApp }).catch(function() {
      // If Gmail app not installed, open web version
      window.open(gmailWeb, '_system');
    });
  } else {
    // For web, just open Gmail in new tab
    window.open(gmailWeb, '_blank');
  }
}

function otpBackspace(event, currentInput, prevIdx) {
  if (event.key === 'Backspace' && currentInput.value === '' && prevIdx >= 0) {
    var prev = document.getElementById('otp' + prevIdx);
    if (prev) {
      prev.focus();
      prev.select();
    }
  }
}

// HOME
// Active booking countdown timer handle
var _activeBookingTimer = null;
var _activeBookingNotified = false; // fire warning toast once per session

function _formatCountdown(msLeft) {
  if (msLeft <= 0) return { text: 'Ended', urgent: true };
  var totalSec = Math.floor(msLeft / 1000);
  var days  = Math.floor(totalSec / 86400);
  var hours = Math.floor((totalSec % 86400) / 3600);
  var mins  = Math.floor((totalSec % 3600) / 60);
  var secs  = totalSec % 60;
  var text = days > 0
    ? days + 'd ' + hours + 'h ' + String(mins).padStart(2,'0') + 'm ' + String(secs).padStart(2,'0') + 's'
    : hours + 'h ' + String(mins).padStart(2,'0') + 'm ' + String(secs).padStart(2,'0') + 's';
  return { text: text, urgent: msLeft < 24 * 3600 * 1000 };
}

function _startActiveBookingCountdown(endDateStr) {
  if (_activeBookingTimer) clearInterval(_activeBookingTimer);
  // Normalize to YYYY-MM-DD regardless of what the API returns
  var normalized = _normDateStr(endDateStr);
  function tick() {
    var el = document.getElementById('activeBookingCountdown');
    if (!el) { clearInterval(_activeBookingTimer); return; }
    // End of the return day at 23:59:59 local time
    var endParts = normalized.split('-');
    var endDt = new Date(parseInt(endParts[0]), parseInt(endParts[1])-1, parseInt(endParts[2]), 23, 59, 59);
    var msLeft = endDt - new Date();
    var result = _formatCountdown(msLeft);
    el.textContent = result.text;
    el.style.color = result.urgent ? '#ef4444' : '#10b981';
    if (result.urgent && !_activeBookingNotified) {
      _activeBookingNotified = true;
      showToast('?? Your rental ends in less than 24 hours!', 'error');
      NotifStore.add('Your rental is ending soon - less than 24 hours remaining.');
    }
  }
  tick();
  _activeBookingTimer = setInterval(tick, 1000);
}

// Normalize any date value to YYYY-MM-DD string
function _normDateStr(d) {
  if (!d) return '';
  var s = String(d).trim();
  // Already YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
  // Has a T Â strip time component (ISO datetime)
  if (s.indexOf('T') !== -1) {
    var iso = s.split('T')[0];
    if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) return iso;
  }
  // Parse as date string
  var dt = new Date(s);
  if (!isNaN(dt.getTime())) {
    // HTTP-date format ends in 'GMT' and represents UTC midnight Â use UTC date parts
    // to avoid timezone shift (e.g. UTC+8 would shift "01 Jun 00:00 GMT" to May 31 local)
    var useUTC = /GMT$/i.test(s) || /Z$/i.test(s);
    var y  = useUTC ? dt.getUTCFullYear()            : dt.getFullYear();
    var m  = useUTC ? dt.getUTCMonth() + 1           : dt.getMonth() + 1;
    var dy = useUTC ? dt.getUTCDate()                : dt.getDate();
    return y + '-' + String(m).padStart(2, '0') + '-' + String(dy).padStart(2, '0');
  }
  return '';
}

// Format a normalized date for display: "May 22, 2026"
function _fmtDate(d) {
  var s = _normDateStr(d);
  if (!s) return '';
  var parts = s.split('-');
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return months[parseInt(parts[1])-1] + ' ' + parseInt(parts[2]) + ', ' + parts[0];
}

function loadHome() {
  var nameEl = document.getElementById('homeUserName');
  if (nameEl) {
    var displayName = currentUser.fullName || 'there';
    // Show first name only if full name is too long
    if (displayName.length > 20) {
      displayName = displayName.split(' ')[0];
    }
    nameEl.textContent = displayName;
  }
  // Update chat unread badge
  updateChatUnreadBadge();
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
      // --- Active booking monitor ---
      var active = null;
      for (var i = 0; i < bookings.length; i++) {
        if (bookings[i].status === 'Picked Up' || bookings[i].status === 'Ongoing') {
          active = bookings[i]; break;
        }
      }
      // Store for use by other functions (e.g. extend booking)
      _allBookingsData = bookings;
      if (active) { activeBookingData = active; }
      var monitor = document.getElementById('activeBookingMonitor');
      var card    = document.getElementById('activeBookingCard');
      if (active && monitor && card) {
        window._activeBookingId = active.id;
        var endNorm   = _normDateStr(active.end_date);
        var startNorm = _normDateStr(active.start_date);
        var imgSrc = active.vehicle_image ? buildImgUrl(active.vehicle_image) : null;
        var imgHtml = imgSrc
          ? '<img src="' + imgSrc + '" id="activeRentalImg" style="width:100%;height:200px;object-fit:cover;display:block;">'
          : '<div style="width:100%;height:160px;background:var(--bg-card2);display:flex;align-items:center;justify-content:center;"><i class="fas fa-car" style="font-size:3rem;color:var(--text-muted);opacity:0.3;"></i></div>';
        card.innerHTML =
          imgHtml +
          '<div style="padding:14px;">' +
            '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">' +
              '<div>' +
                '<div style="font-size:1rem;font-weight:900;color:var(--text-primary);">' + (active.brand||'') + ' ' + (active.model||'') + '</div>' +
                '<div style="font-size:0.72rem;color:var(--text-muted);margin-top:2px;">' + (active.plate_number||'') + '</div>' +
              '</div>' +
              '<span style="background:rgba(16,185,129,0.1);color:var(--primary);border:1px solid rgba(16,185,129,0.25);padding:4px 10px;border-radius:20px;font-size:0.65rem;font-weight:800;">Active</span>' +
            '</div>' +
            '<div style="background:var(--bg-card2);border-radius:14px;padding:12px;margin-bottom:10px;">' +
              '<div style="font-size:0.6rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:6px;">Time Remaining</div>' +
              '<div id="activeBookingCountdown" style="font-size:1.6rem;font-weight:900;letter-spacing:-0.5px;color:var(--primary);">-</div>' +
              '<div style="font-size:0.72rem;color:var(--text-muted);margin-top:4px;">Return by <strong style="color:var(--text-primary);">' + _fmtDate(endNorm) + '</strong></div>' +
            '</div>' +
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;">' +
              '<div style="background:var(--bg-card2);border-radius:12px;padding:10px;">' +
                '<div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:3px;">Start Date</div>' +
                '<div style="font-size:0.82rem;font-weight:700;color:var(--text-primary);">' + _fmtDate(startNorm) + '</div>' +
              '</div>' +
              '<div style="background:var(--bg-card2);border-radius:12px;padding:10px;">' +
                '<div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:3px;">Booking #</div>' +
                '<div style="font-size:0.82rem;font-weight:700;color:var(--text-primary);">' + active.id + '</div>' +
              '</div>' +
            '</div>' +
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">' +
              '<button onclick="openExtendBooking(' + active.id + ',\'' + endNorm + '\',\'' + (active.daily_rate||0) + '\')" style="padding:10px;background:var(--primary);color:#fff;border:none;border-radius:12px;font-size:0.78rem;font-weight:700;cursor:pointer;"><i class="fas fa-calendar-plus" style="margin-right:5px;"></i>Extend</button>' +
              '<button onclick="showOverlay(\'page-livechat\')" style="padding:10px;background:var(--bg-card2);color:var(--text-primary);border:1px solid var(--border);border-radius:12px;font-size:0.78rem;font-weight:700;cursor:pointer;"><i class="fas fa-comments" style="margin-right:5px;"></i>Chat</button>' +
            '</div>' +
          '</div>';
        monitor.style.display = '';
        // Attach onerror after DOM insertion to avoid escaping issues
        var imgEl = document.getElementById('activeRentalImg');
        if (imgEl) {
          imgEl.onerror = function() {
            this.parentNode.innerHTML = '<div style="width:100%;height:140px;background:var(--bg-card2);display:flex;align-items:center;justify-content:center;"><i class="fas fa-car" style="font-size:3rem;color:var(--text-muted);opacity:0.3;"></i></div>';
          };
        }
        _startActiveBookingCountdown(endNorm);
      } else {
        if (monitor) monitor.style.display = 'none';
        if (_activeBookingTimer) { clearInterval(_activeBookingTimer); _activeBookingTimer = null; }
      }
      }).catch(function() {});
  updateNotifBadge();
}

function buildImgUrl(path) {
  var _noImg = 'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22400%22%20height%3D%22200%22%3E%3Crect%20width%3D%22400%22%20height%3D%22200%22%20fill%3D%22%23f3f4f6%22%2F%3E%3Ctext%20x%3D%22200%22%20y%3D%2285%22%20font-family%3D%22Arial%22%20font-size%3D%2240%22%20text-anchor%3D%22middle%22%20fill%3D%22%23d1d5db%22%3E%F0%9F%9A%97%3C%2Ftext%3E%3Ctext%20x%3D%22200%22%20y%3D%22130%22%20font-family%3D%22Arial%22%20font-size%3D%2214%22%20text-anchor%3D%22middle%22%20fill%3D%22%239ca3af%22%3ENo%20Image%3C%2Ftext%3E%3C%2Fsvg%3E';
  if (!path) return _noImg;
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
// Vehicle cache key and TTL (5 minutes)
var VEHICLE_CACHE_KEY = 'autoride_vehicles_cache';
var VEHICLE_CACHE_TTL = 5 * 60 * 1000;

function loadVehicles() {
  var grid = document.getElementById('vehicleGrid');
  var countEl = document.getElementById('vehicleCount');

  // 1. Try to show cached data immediately (no spinner)
  try {
    var cached = localStorage.getItem(VEHICLE_CACHE_KEY);
    if (cached) {
      var parsed = JSON.parse(cached);
      var age = Date.now() - (parsed.savedAt || 0);
      if (parsed.data && parsed.data.length && age < VEHICLE_CACHE_TTL) {
        allVehicles = parsed.data;
        renderVehicles(parsed.data);
        // Show subtle refresh indicator
        if (countEl) countEl.innerHTML = '<span style="color:var(--text-muted);font-size:0.7rem;"><i class="fas fa-sync-alt fa-spin" style="font-size:0.6rem;margin-right:4px;"></i>Refreshing...</span>';
      }
    }
  } catch(e) {}

  // 2. Always fetch fresh data in the background (no showLoading overlay)
  if (!allVehicles.length && grid) {
    // Only show skeleton if nothing cached
    grid.innerHTML =
      '<div style="padding:16px;display:grid;grid-template-columns:1fr 1fr;gap:12px;">' +
      [1,2,3,4].map(function() {
        return '<div style="background:var(--bg-card);border-radius:16px;overflow:hidden;border:1px solid var(--border);">' +
          '<div style="height:120px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;"></div>' +
          '<div style="padding:10px;">' +
          '<div style="height:12px;background:var(--border);border-radius:6px;margin-bottom:8px;animation:shimmer 1.2s infinite;"></div>' +
          '<div style="height:10px;background:var(--border);border-radius:6px;width:60%;animation:shimmer 1.2s infinite;"></div>' +
          '</div></div>';
      }).join('') + '</div>';
  }

  apiCall('/vehicles/categories')
    .then(function(data) {
      allVehicles = data;
      renderVehicles(data);
      // Cache the fresh data
      try {
        localStorage.setItem(VEHICLE_CACHE_KEY, JSON.stringify({ data: data, savedAt: Date.now() }));
      } catch(e) {}
      if (countEl) {
        var available = data.filter(function(v) { return (parseInt(v.available_units) || 0) > 0; });
        countEl.textContent = available.length + ' vehicle' + (available.length !== 1 ? 's' : '') + ' found';
      }
    })
    .catch(function(err) {
      // Only show error if nothing was cached
      if (!allVehicles.length && grid) {
        grid.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>' + err.message + '</p></div>';
      }
      if (countEl && allVehicles.length) countEl.textContent = '';
    });
}

function renderVehicles(list) {
  var grid = document.getElementById('vehicleGrid');
  if (!grid) return;
  // Filter out vehicles with no available units
  var available = list.filter(function(v) { return (parseInt(v.available_units) || 0) > 0; });
  if (!available.length) {
    grid.innerHTML = '<div class="empty-state"><i class="fas fa-car"></i><p>No vehicles available</p></div>';
    return;
  }
  var countEl = document.getElementById('vehicleCount');
  if (countEl) countEl.textContent = available.length + ' vehicle' + (available.length !== 1 ? 's' : '') + ' found';

  grid.innerHTML = available.map(function(v) {
    var avail = parseInt(v.available_units) || 0;
    var bEnc = encodeURIComponent(v.brand);
    var mEnc = encodeURIComponent(v.model);
    return '<div class="vehicle-card" onclick="openVehicleUnits(\'' + bEnc + '\',\'' + mEnc + '\',\'all\')">' +
      '<div class="vehicle-img-wrap">' +
      '<img src="' + buildImgUrl(v.vehicle_image) + '" alt="' + v.brand + ' ' + v.model + '" onerror="this.onerror=null; this.src=\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22400%22%20height%3D%22200%22%3E%3Crect%20width%3D%22400%22%20height%3D%22200%22%20fill%3D%22%23f3f4f6%22%2F%3E%3Ctext%20x%3D%22200%22%20y%3D%2285%22%20font-family%3D%22Arial%22%20font-size%3D%2240%22%20text-anchor%3D%22middle%22%20fill%3D%22%23d1d5db%22%3E%F0%9F%9A%97%3C%2Ftext%3E%3Ctext%20x%3D%22200%22%20y%3D%22130%22%20font-family%3D%22Arial%22%20font-size%3D%2214%22%20text-anchor%3D%22middle%22%20fill%3D%22%239ca3af%22%3ENo%20Image%3C%2Ftext%3E%3C%2Fsvg%3E\'">' +
      '<span class="badge-available"><span style="width:7px;height:7px;border-radius:50%;background:#6ee7b7;display:inline-block;margin-right:5px;"></span>' + avail + ' available</span>' +
      '</div>' +
      '<div class="vehicle-info">' +
      '<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px;">' +
      '<div>' +
      '<h3>' + v.brand + ' ' + v.model + '</h3>' +
      '<div style="display:flex;gap:6px;margin-top:4px;">' +
      '<span style="background:#1f1f1f;color:#71717a;padding:2px 8px;border-radius:20px;font-size:0.65rem;font-weight:600;">' + (v.vehicle_type || '-') + '</span>' +
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

// ?? INLINE BROWSE: Transmission selected ? populate Color dropdown ??????????
function onVehicleTransmissionChange(brandEnc, modelEnc, cardId) {
  var transEl = document.getElementById('vtrans-' + cardId);
  var colorWrap = document.getElementById('vcolor-wrap-' + cardId);
  var unitWrap = document.getElementById('vunit-' + cardId);
  if (!transEl || !colorWrap) return;
  var trans = transEl.value;
  colorWrap.style.display = 'none';
  if (unitWrap) unitWrap.style.display = 'none';
  if (!trans) return;

  apiCall('/vehicles/units?brand=' + brandEnc + '&model=' + modelEnc + '&color=all&user_id=' + (currentUser.id || ''))
    .then(function(units) {
      var filtered = units.filter(function(u) {
        return u.transmission === trans && u.status === 'Available';
      });
      var seen = {};
      var colors = [];
      filtered.forEach(function(u) {
        var c = u.color_display || u.color || 'Not Specified';
        if (!seen[c]) { seen[c] = true; colors.push(c); }
      });
      if (!colors.length) {
        showToast('No available units for ' + trans + ' transmission.', 'error');
        return;
      }
      var colorSel = document.getElementById('vcolor-' + cardId);
      if (!colorSel) return;
      colorSel.innerHTML = '<option value="">Select color</option>' +
        colors.map(function(c) { return '<option value="' + c + '">' + c + '</option>'; }).join('');
      colorWrap.style.display = 'block';
    })
    .catch(function(err) { showToast(err.message, 'error'); });
}

// ?? INLINE BROWSE: Color selected ? show plate + image + Book button ?????????
function onVehicleColorChange(brandEnc, modelEnc, cardId) {
  var transEl = document.getElementById('vtrans-' + cardId);
  var colorEl = document.getElementById('vcolor-' + cardId);
  var unitWrap = document.getElementById('vunit-' + cardId);
  var plateEl = document.getElementById('vplate-' + cardId);
  var bookBtn = document.getElementById('vbook-' + cardId);
  var imgWrap = document.getElementById('vimg-' + cardId);
  if (!colorEl || !unitWrap) return;
  var color = colorEl.value;
  var trans = transEl ? transEl.value : '';
  unitWrap.style.display = 'none';
  if (!color) return;

  apiCall('/vehicles/units?brand=' + brandEnc + '&model=' + modelEnc + '&color=' + encodeURIComponent(color) + '&user_id=' + (currentUser.id || ''))
    .then(function(units) {
      var unit = null;
      for (var i = 0; i < units.length; i++) {
        var u = units[i];
        var uColor = u.color_display || u.color || 'Not Specified';
        if (u.status === 'Available' && uColor === color && (!trans || u.transmission === trans)) {
          unit = u; break;
        }
      }
      if (!unit) {
        showToast('No available unit for this combination.', 'error');
        return;
      }
      if (plateEl) plateEl.textContent = unit.plate_number || 'N/A';
      if (imgWrap) {
        var imgSrc = (unit.gallery && unit.gallery.length) ? buildImgUrl(unit.gallery[0]) : buildImgUrl(unit.vehicle_image);
        imgWrap.innerHTML = '<img src="' + imgSrc + '" alt="vehicle" onerror="this.onerror=null; this.src=\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22400%22%20height%3D%22200%22%3E%3Crect%20width%3D%22400%22%20height%3D%22200%22%20fill%3D%22%23f3f4f6%22%2F%3E%3Ctext%20x%3D%22200%22%20y%3D%2285%22%20font-family%3D%22Arial%22%20font-size%3D%2240%22%20text-anchor%3D%22middle%22%20fill%3D%22%23d1d5db%22%3E%F0%9F%9A%97%3C%2Ftext%3E%3Ctext%20x%3D%22200%22%20y%3D%22130%22%20font-family%3D%22Arial%22%20font-size%3D%2214%22%20text-anchor%3D%22middle%22%20fill%3D%22%239ca3af%22%3ENo%20Image%3C%2Ftext%3E%3C%2Fsvg%3E\'" style="width:100%;height:100%;object-fit:cover;">';
      }
      if (bookBtn) {
        var ACTIVE_STATUSES = ['Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing'];
        var hasActiveBooking = _allBookingsData.some(function(b) {
          return ACTIVE_STATUSES.indexOf(b.status) !== -1;
        });
        var canBook = parseInt(currentUser.isVerified) === 2 && !hasActiveBooking;
        if (canBook) {
          bookBtn.removeAttribute('disabled');
          bookBtn.style.opacity = '1';
          bookBtn.innerHTML = '<i class="fas fa-calendar-plus"></i> Book';
          (function(vid) { bookBtn.onclick = function() { selectVehicleUnit(vid); }; })(unit.id);
        } else if (parseInt(currentUser.isVerified) !== 2) {
          bookBtn.setAttribute('disabled', 'true');
          bookBtn.style.opacity = '0.5';
          bookBtn.innerHTML = '<i class="fas fa-lock"></i> Verify License';
        } else {
          bookBtn.setAttribute('disabled', 'true');
          bookBtn.style.opacity = '0.5';
          bookBtn.innerHTML = '<i class="fas fa-calendar-check"></i> Active Booking';
        }
      }
      unitWrap.style.display = 'block';
    })
    .catch(function(err) { showToast(err.message, 'error'); });
}

// VEHICLES - Step 2: Color selection
function openColorSelection(brand, model) {
  showOverlay('page-color-selection');
  var csel = document.getElementById('colorSelectionContent');
  if (csel) csel.innerHTML = '<div style=\"padding:20px;\"><div style=\"display:flex;flex-wrap:wrap;gap:10px;margin-bottom:16px;\"><div style=\"width:60px;height:32px;border-radius:20px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;\"></div><div style=\"width:60px;height:32px;border-radius:20px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;\"></div><div style=\"width:60px;height:32px;border-radius:20px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;\"></div><div style=\"width:60px;height:32px;border-radius:20px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;\"></div><div style=\"width:60px;height:32px;border-radius:20px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;\"></div><div style=\"width:60px;height:32px;border-radius:20px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;\"></div></div><div style=\"height:14px;width:80%;border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;margin-bottom:8px;\"></div><div style=\"height:12px;width:60%;border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;margin-bottom:0px;\"></div></div>';
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
  showOverlay('page-vehicle-units');
  var vuel = document.getElementById('vehicleUnitsContent');
  if (vuel) vuel.innerHTML = '<div style=\"padding:16px;\"><div style=\"background:var(--bg-card);border:1px solid var(--border);border-radius:12px;margin-bottom:12px;overflow:hidden;\"><div style=\"height:140px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;\"></div><div style=\"padding:12px;\"><div style=\"height:12px;width:70%;border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;margin-bottom:6px;\"></div><div style=\"height:10px;width:50%;border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;margin-bottom:0px;\"></div></div></div><div style=\"background:var(--bg-card);border:1px solid var(--border);border-radius:12px;margin-bottom:12px;overflow:hidden;\"><div style=\"height:140px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;\"></div><div style=\"padding:12px;\"><div style=\"height:12px;width:70%;border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;margin-bottom:6px;\"></div><div style=\"height:10px;width:50%;border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;margin-bottom:0px;\"></div></div></div><div style=\"background:var(--bg-card);border:1px solid var(--border);border-radius:12px;margin-bottom:12px;overflow:hidden;\"><div style=\"height:140px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;\"></div><div style=\"padding:12px;\"><div style=\"height:12px;width:70%;border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;margin-bottom:6px;\"></div><div style=\"height:10px;width:50%;border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;margin-bottom:0px;\"></div></div></div></div>';
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
      '<img src="' + imgSrc + '" style="width:100%;height:100%;object-fit:cover;" onerror="this.onerror=null; this.src=\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22400%22%20height%3D%22200%22%3E%3Crect%20width%3D%22400%22%20height%3D%22200%22%20fill%3D%22%23f3f4f6%22%2F%3E%3Ctext%20x%3D%22200%22%20y%3D%2285%22%20font-family%3D%22Arial%22%20font-size%3D%2240%22%20text-anchor%3D%22middle%22%20fill%3D%22%23d1d5db%22%3E%F0%9F%9A%97%3C%2Ftext%3E%3Ctext%20x%3D%22200%22%20y%3D%22130%22%20font-family%3D%22Arial%22%20font-size%3D%2214%22%20text-anchor%3D%22middle%22%20fill%3D%22%239ca3af%22%3ENo%20Image%3C%2Ftext%3E%3C%2Fsvg%3E\'">' +
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

// STEP 2: Color selected - show individual units with inline dropdowns
function openVehicleUnits(brandEnc, modelEnc, colorEnc) {
  var brand = decodeURIComponent(brandEnc);
  var model = decodeURIComponent(modelEnc);
  var bEnc = encodeURIComponent(brand);
  var mEnc = encodeURIComponent(model);
  var el = document.getElementById('vehicleDetailContent');
  if (!el) return;
  el.innerHTML = '<div class="page-header"><button class="back-btn" onclick="closeOverlay(\'page-vehicle-detail\')"><i class="fas fa-arrow-left"></i></button><h2>' + brand + ' ' + model + '</h2></div><div class="scroll-content"><div class="empty-state"><i class="fas fa-spinner fa-spin"></i><p>Loading...</p></div></div>';
  showOverlay('page-vehicle-detail');
  showLoading(true);

  // Load ALL units for this brand/model so we can build the dropdowns
  apiCall('/vehicles/units?brand=' + bEnc + '&model=' + mEnc + '&color=all&user_id=' + (currentUser.id || ''))
    .then(function(allUnits) {
      if (!allUnits.length) {
        el.innerHTML = '<div class="page-header"><button class="back-btn" onclick="closeOverlay(\'page-vehicle-detail\')"><i class="fas fa-arrow-left"></i></button><h2>' + brand + ' ' + model + '</h2></div>' +
          '<div class="scroll-content"><div class="empty-state"><i class="fas fa-car"></i><p>No units available</p></div></div>';
        return;
      }

      // Store units on window for cascade access
      window._vdUnits = allUnits;
      window._vdBrand = brand;
      window._vdModel = model;

      // Get unique transmissions from available units only
      var availUnits = allUnits.filter(function(u) { return u.status === 'Available'; });
      var seenTrans = {};
      var transmissions = [];
      availUnits.forEach(function(u) {
        var t = u.transmission || 'N/A';
        if (!seenTrans[t]) { seenTrans[t] = true; transmissions.push(t); }
      });

      // Pick a default unit to show initially
      var defaultUnit = availUnits[0] || allUnits[0];
      var isAvailable = defaultUnit.status === 'Available';
      var canBook = isAvailable && parseInt(currentUser.isVerified) === 2;
      var imgSrc = (defaultUnit.gallery && defaultUnit.gallery.length) ? buildImgUrl(defaultUnit.gallery[0]) : buildImgUrl(defaultUnit.vehicle_image);

      // Build transmission options
      var transOptions = transmissions.map(function(t) {
        return '<option value="' + t + '"' + (t === defaultUnit.transmission ? ' selected' : '') + '>' + t + '</option>';
      }).join('');

      // Build color options for default transmission
      var defaultTrans = defaultUnit.transmission || transmissions[0];
      var seenColors = {};
      var colors = [];
      availUnits.filter(function(u) { return u.transmission === defaultTrans; }).forEach(function(u) {
        var c = u.color_display || u.color || 'Not Specified';
        if (!seenColors[c]) { seenColors[c] = true; colors.push(c); }
      });
      var colorOptions = colors.map(function(c) {
        return '<option value="' + c + '"' + (c === (defaultUnit.color_display || defaultUnit.color) ? ' selected' : '') + '>' + c + '</option>';
      }).join('');

      var cardHtml =
        '<div class="card" style="margin-bottom:16px;">' +
        // Gallery image
        '<div id="vd-img-wrap" style="margin:-16px -16px 14px;border-radius:var(--radius-sm) var(--radius-sm) 0 0;overflow:hidden;height:200px;">' +
        '<img id="vd-img" src="' + imgSrc + '" style="width:100%;height:100%;object-fit:cover;" onerror="this.onerror=null; this.src=\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22400%22%20height%3D%22200%22%3E%3Crect%20width%3D%22400%22%20height%3D%22200%22%20fill%3D%22%23f3f4f6%22%2F%3E%3Ctext%20x%3D%22200%22%20y%3D%2285%22%20font-family%3D%22Arial%22%20font-size%3D%2240%22%20text-anchor%3D%22middle%22%20fill%3D%22%23d1d5db%22%3E%F0%9F%9A%97%3C%2Ftext%3E%3Ctext%20x%3D%22200%22%20y%3D%22130%22%20font-family%3D%22Arial%22%20font-size%3D%2214%22%20text-anchor%3D%22middle%22%20fill%3D%22%239ca3af%22%3ENo%20Image%3C%2Ftext%3E%3C%2Fsvg%3E\'">' +
        '</div>' +
        // Title + status
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">' +
        '<h4 style="font-weight:800;font-size:1rem;">' + brand + ' ' + model + '</h4>' +
        '<span id="vd-status" style="padding:4px 12px;border-radius:20px;font-size:0.72rem;font-weight:700;background:' + (isAvailable ? '#d1e7dd' : '#f8d7da') + ';color:' + (isAvailable ? '#0a3622' : '#842029') + ';">' + defaultUnit.status + '</span>' +
        '</div>' +
        // Specs grid - Transmission and Color are dropdowns
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;">' +

        // Transmission dropdown
        '<div style="font-size:0.82rem;display:flex;align-items:center;gap:6px;">' +
        '<i class="fas fa-cog" style="color:var(--primary);width:16px;flex-shrink:0;"></i>' +
        '<select id="vd-trans" onchange="onVdTransChange()" style="background:transparent;border:none;border-bottom:1px solid var(--border);color:var(--text-main);font-size:0.82rem;font-weight:600;padding:2px 4px;cursor:pointer;outline:none;width:100%;">' +
        transOptions + '</select>' +
        '</div>' +

        // Plate
        '<div style="font-size:0.82rem;display:flex;align-items:center;gap:6px;">' +
        '<i class="fas fa-id-card" style="color:var(--primary);width:16px;flex-shrink:0;"></i>' +
        '<span id="vd-plate" style="font-weight:600;">' + (defaultUnit.plate_number || 'N/A') + '</span>' +
        '</div>' +

        // Seats
        '<div style="font-size:0.82rem;display:flex;align-items:center;gap:6px;">' +
        '<i class="fas fa-users" style="color:var(--primary);width:16px;flex-shrink:0;"></i>' +
        '<span id="vd-seats">' + (defaultUnit.seats || '-') + ' seats</span>' +
        '</div>' +

        // Fuel
        '<div style="font-size:0.82rem;display:flex;align-items:center;gap:6px;">' +
        '<i class="fas fa-gas-pump" style="color:var(--primary);width:16px;flex-shrink:0;"></i>' +
        '<span id="vd-fuel">' + (defaultUnit.fuel_type || '-') + '</span>' +
        '</div>' +

        // Color dropdown
        '<div style="font-size:0.82rem;display:flex;align-items:center;gap:6px;">' +
        '<i class="fas fa-globe" style="color:var(--primary);width:16px;flex-shrink:0;"></i>' +
        '<select id="vd-color" onchange="onVdColorChange()" style="background:transparent;border:none;border-bottom:1px solid var(--border);color:var(--text-main);font-size:0.82rem;font-weight:600;padding:2px 4px;cursor:pointer;outline:none;width:100%;">' +
        colorOptions + '</select>' +
        '</div>' +

        // Location
        '<div style="font-size:0.82rem;display:flex;align-items:center;gap:6px;">' +
        '<i class="fas fa-map-marker-alt" style="color:var(--primary);width:16px;flex-shrink:0;"></i>' +
        '<span id="vd-location">' + (defaultUnit.location || '-') + '</span>' +
        '</div>' +

        '</div>' +
        // Price + Book
        '<div style="display:flex;justify-content:space-between;align-items:center;padding-top:12px;border-top:1px solid var(--border);">' +
        '<div>' +
        '<div class="vehicle-rate" id="vd-rate">' + formatPHP(defaultUnit.daily_rate) + '</div>' +
        '<div style="font-size:0.72rem;color:var(--text-muted);">/ day</div>' +
        '</div>' +
        '<button id="vd-book-btn" class="btn-primary" style="width:auto;padding:12px 24px;border-radius:30px;font-size:0.9rem;font-weight:800;"' +
        (canBook ? ' onclick="selectVehicleUnit(' + defaultUnit.id + ')"' : ' disabled style="width:auto;padding:12px 20px;background:var(--bg-input);color:var(--text-muted);border:none;border-radius:30px;font-size:0.85rem;cursor:not-allowed;"') + '>' +
        '<i class="fas fa-calendar-plus"></i> ' + (canBook ? 'Book' : (isAvailable ? 'Verify License' : 'Unavailable')) +
        '</button>' +
        '</div></div>';

      el.innerHTML = '<div class="page-header"><button class="back-btn" onclick="closeOverlay(\'page-vehicle-detail\')"><i class="fas fa-arrow-left"></i></button><h2>' + brand + ' ' + model + '</h2></div>' +
        '<div class="scroll-content" style="padding-bottom:80px;">' + cardHtml + '</div>';
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

// Called when transmission dropdown changes - repopulate colors and update card
function onVdTransChange() {
  var trans = document.getElementById('vd-trans').value;
  var availUnits = (window._vdUnits || []).filter(function(u) {
    return u.status === 'Available' && u.transmission === trans;
  });
  var seenColors = {};
  var colors = [];
  availUnits.forEach(function(u) {
    var c = u.color_display || u.color || 'Not Specified';
    if (!seenColors[c]) { seenColors[c] = true; colors.push(c); }
  });
  var colorSel = document.getElementById('vd-color');
  if (colorSel) {
    colorSel.innerHTML = colors.map(function(c) {
      return '<option value="' + c + '">' + c + '</option>';
    }).join('');
  }
  onVdColorChange();
}

// Called when color dropdown changes - update plate, image, book button
function onVdColorChange() {
  var trans = document.getElementById('vd-trans') ? document.getElementById('vd-trans').value : '';
  var color = document.getElementById('vd-color') ? document.getElementById('vd-color').value : '';
  var unit = null;
  var units = window._vdUnits || [];
  for (var i = 0; i < units.length; i++) {
    var u = units[i];
    var uColor = u.color_display || u.color || 'Not Specified';
    if (u.status === 'Available' && uColor === color && (!trans || u.transmission === trans)) {
      unit = u; break;
    }
  }
  if (!unit) return;

  // Update image
  var imgEl = document.getElementById('vd-img');
  if (imgEl) {
    var imgSrc = (unit.gallery && unit.gallery.length) ? buildImgUrl(unit.gallery[0]) : buildImgUrl(unit.vehicle_image);
    imgEl.src = imgSrc;
  }
  // Update specs
  var plateEl = document.getElementById('vd-plate');
  if (plateEl) plateEl.textContent = unit.plate_number || 'N/A';
  var seatsEl = document.getElementById('vd-seats');
  if (seatsEl) seatsEl.textContent = (unit.seats || '-') + ' seats';
  var fuelEl = document.getElementById('vd-fuel');
  if (fuelEl) fuelEl.textContent = unit.fuel_type || '-';
  var locEl = document.getElementById('vd-location');
  if (locEl) locEl.textContent = unit.location || '-';
  var rateEl = document.getElementById('vd-rate');
  if (rateEl) rateEl.textContent = formatPHP(unit.daily_rate);
  // Update status badge
  var statusEl = document.getElementById('vd-status');
  if (statusEl) {
    statusEl.textContent = unit.status;
    statusEl.style.background = unit.status === 'Available' ? '#d1e7dd' : '#f8d7da';
    statusEl.style.color = unit.status === 'Available' ? '#0a3622' : '#842029';
  }
  // Update book button
  var bookBtn = document.getElementById('vd-book-btn');
  if (bookBtn) {
    var canBook = unit.status === 'Available' && parseInt(currentUser.isVerified) === 2;
    bookBtn.disabled = !canBook;
    bookBtn.style.cssText = canBook
      ? 'width:auto;padding:12px 24px;border-radius:30px;font-size:0.9rem;font-weight:800;'
      : 'width:auto;padding:12px 20px;background:var(--bg-input);color:var(--text-muted);border:none;border-radius:30px;font-size:0.85rem;cursor:not-allowed;';
    bookBtn.innerHTML = '<i class="fas fa-calendar-plus"></i> ' + (canBook ? 'Book' : (unit.status === 'Available' ? 'Verify License' : 'Unavailable'));
    if (canBook) {
      (function(vid) { bookBtn.onclick = function() { selectVehicleUnit(vid); }; })(unit.id);
    }
  }
}

// STEP 3: Book button tapped on a specific unit
function selectVehicleUnit(vehicleId) {
  showOverlay('page-vehicle-detail');
  var svdEl = document.getElementById('vehicleDetailContent');
  if (svdEl) svdEl.innerHTML = '<div style=\"height:180px;width:100%;border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;margin-bottom:0px;\"></div>';
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
  showOverlay('page-vehicle-detail');
  var vdEl = document.getElementById('vehicleDetailContent');
  if (vdEl) vdEl.innerHTML = '<div style=\"padding:20px;\"><div style=\"width:100%;aspect-ratio:16/9;border-radius:16px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;margin-bottom:16px;\"></div><div style=\"background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:20px;\"><div style=\"height:22px;width:60%;border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;margin-bottom:12px;\"></div><div style=\"height:12px;width:80%;border-radius:6px;background:linear-gradient(90deg,var(--border) 25%,var(--bg-input,#f4f6fb) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;\"></div></div></div>';
  apiCall('/vehicle/' + vehicleId + '?user_id=' + (currentUser.id || ''))
    .then(function(v) {
      currentVehicleDetail = v;
      renderVehicleDetail(v);
    })
    .catch(function(err) { showToast(err.message, 'error'); closeOverlay('page-vehicle-detail'); });
}

function renderVehicleDetail(v) {
  var ltDays = parseInt(appSettings.long_term_discount_days) || 7;
  var ltPct = parseInt(appSettings.long_term_discount_percent) || 10;
  var mileage = appSettings.mileage_limit || '250';

  // 1 booking per account Â block if any active booking exists
  var ACTIVE_STATUSES = ['Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing'];
  var hasActiveBooking = _allBookingsData.some(function(b) {
    return ACTIVE_STATUSES.indexOf(b.status) !== -1;
  });

  var canBook = parseInt(currentUser.isVerified) === 2 && !hasActiveBooking;
  var el = document.getElementById('vehicleDetailContent');
  if (!el) return;
  var galleryImgs = (v.gallery && v.gallery.length ? v.gallery : [v.vehicle_image]).filter(Boolean);
  var galleryHtml = galleryImgs.map(function(img) {
    return '<img class="gallery-img" src="' + buildImgUrl(img) + '" onerror="this.onerror=null; this.src=\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22400%22%20height%3D%22200%22%3E%3Crect%20width%3D%22400%22%20height%3D%22200%22%20fill%3D%22%23f3f4f6%22%2F%3E%3Ctext%20x%3D%22200%22%20y%3D%2285%22%20font-family%3D%22Arial%22%20font-size%3D%2240%22%20text-anchor%3D%22middle%22%20fill%3D%22%23d1d5db%22%3E%F0%9F%9A%97%3C%2Ftext%3E%3Ctext%20x%3D%22200%22%20y%3D%22130%22%20font-family%3D%22Arial%22%20font-size%3D%2214%22%20text-anchor%3D%22middle%22%20fill%3D%22%239ca3af%22%3ENo%20Image%3C%2Ftext%3E%3C%2Fsvg%3E\'" alt="Vehicle">';
  }).join('');
  var reviewsHtml = (v.reviews && v.reviews.length) ? v.reviews.map(function(r) {
    return '<div class="review-item"><div class="reviewer">' +
      '<div class="avatar-placeholder">' + ((r.full_name || '₱')[0]) + '</div>' +
      '<div><strong style="font-size:0.875rem;">' + (r.full_name || 'Customer') + '</strong></div></div>' +
      (r.comment ? '<p style="font-size:0.875rem;color:var(--text-secondary);">' + r.comment + '</p>' : '') +
      '</div>';
  }).join('') : '<div class="empty-state" style="padding:20px 0;"><p>No reviews yet</p></div>';

  var bookBtn;
  if (parseInt(currentUser.isVerified) !== 2) {
    bookBtn = '<div style="background:#f8d7da;border-radius:var(--radius-sm);padding:12px;text-align:center;font-size:0.875rem;color:#842029;margin-bottom:12px;"><i class="fas fa-lock"></i> License verification required before booking.</div>';
  } else if (hasActiveBooking) {
    bookBtn = '<div style="background:rgba(251,191,36,0.12);border:1px solid rgba(251,191,36,0.35);border-radius:var(--radius-sm);padding:14px;text-align:center;font-size:0.875rem;color:#92400e;margin-bottom:12px;"><i class="fas fa-calendar-check" style="margin-right:6px;color:#f59e0b;"></i><strong>1 booking per account.</strong><br><span style="font-size:0.8rem;">Complete or cancel your current booking before making a new one.</span></div>';
  } else {
    bookBtn = '<button class="btn-primary" onclick="openBookingForm(' + v.id + ')"><i class="fas fa-calendar-plus"></i> Book Now</button>';
  }
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
  { type: 'Standard Protection', pricePerDay: 500, desc: 'Collision Damage Waiver (CDW) with ₱10k deductible.' },
  { type: 'Premium Protection', pricePerDay: 1200, desc: 'Full coverage, zero deductible, and roadside assistance.' }
];

var ADDON_OPTIONS = [
  { name: 'GPS Navigation', pricePerDay: 200 },
  { name: 'Child Safety Seat', pricePerDay: 150 },
  { name: 'Roadside Assistance', pricePerDay: 100 }
];

function generateTimeOptions(selectedTime) {
  var times = [];
  for (var h = 0; h < 24; h++) {
    for (var m = 0; m < 60; m += 30) {
      var hh = String(h).padStart(2, '0');
      var mm = String(m).padStart(2, '0');
      var val = hh + ':' + mm;
      var ampm = h < 12 ? 'AM' : 'PM';
      var h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
      var label = String(h12).padStart(2, '0') + ':' + mm + ' ' + ampm;
      var sel = val === selectedTime ? ' selected' : '';
      times.push('<option value="' + val + '"' + sel + '>' + label + '</option>');
    }
  }
  return times.join('');
}

function autoSetReturnTime() {
  var pickupTimeEl = document.getElementById('bfPickupTime');
  var returnTimeEl = document.getElementById('bfReturnTime');
  var startDateEl  = document.getElementById('bfStartDate');
  var endDateEl    = document.getElementById('bfEndDate');
  if (!pickupTimeEl || !returnTimeEl) return;

  var pickupTime = pickupTimeEl.value || '06:00';
  var parts = pickupTime.split(':');
  var pickupHour = parseInt(parts[0]);
  var pickupMin  = parseInt(parts[1]);

  // Return time = pickup time + 24h (same time next day)
  var returnHour = pickupHour;
  var returnMin  = pickupMin;
  var returnHH = String(returnHour).padStart(2, '0');
  var returnMM = String(returnMin).padStart(2, '0');
  var returnVal = returnHH + ':' + returnMM;

  // Set return time select
  if (returnTimeEl) returnTimeEl.value = returnVal;

  // Auto-advance end date by 1 day from start date if not already set
  if (startDateEl && startDateEl.value && endDateEl) {
    var start = new Date(startDateEl.value + 'T00:00:00');
    var minEnd = new Date(start);
    minEnd.setDate(minEnd.getDate() + 1);
    var minEndStr = minEnd.toISOString().split('T')[0];
    if (!endDateEl.value || endDateEl.value < minEndStr) {
      endDateEl.value = minEndStr;
      updateBookingPrice();
    }
  }
}

function openBookingForm(vehicleId) {
  // 1 booking per account Â hard block if active booking exists
  var ACTIVE_STATUSES = ['Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing'];
  var hasActiveBooking = _allBookingsData.some(function(b) {
    return ACTIVE_STATUSES.indexOf(b.status) !== -1;
  });
  if (hasActiveBooking) {
    showToast('You already have an active booking. Please complete or cancel it first.', 'error');
    return;
  }

  bookingFormVehicle = currentVehicleDetail;
  selectedAddons = [];
  selectedInsurance = { type: 'Basic Protection', price: 0, pricePerDay: 0 };
  var today = new Date().toISOString().split('T')[0];
  var el = document.getElementById('bookingFormContent');
  if (!el) return;

  var locationOptions = PICKUP_LOCATIONS.map(function(loc, i) {
    return '<option value="' + loc.value + '">' + loc.label + '</option>';
  }).join('');

  var insuranceHtml = INSURANCE_OPTIONS.map(function(ins, i) {
    var priceLabel = ins.pricePerDay === 0 ? 'Included (₱0)' : '₱' + ins.pricePerDay.toLocaleString() + '/day';
    return '<div class="option-card' + (i === 0 ? ' selected' : '') + '" onclick="selectInsuranceOpt(' + i + ',this)">' +
      '<input type="radio" name="insurance"' + (i === 0 ? ' checked' : '') + '>' +
      '<div><strong>' + ins.type + '</strong> <span style="color:var(--primary);font-weight:700;">' + priceLabel + '</span>' +
      '<br><small style="color:var(--text-secondary);">' + ins.desc + '</small></div>' +
      '</div>';
  }).join('');

  var addonsHtml = ADDON_OPTIONS.map(function(addon, i) {
    return '<div class="option-card" id="addon_' + i + '" onclick="toggleAddon(' + i + ',this)">' +
      '<input type="checkbox" id="addonChk_' + i + '">' +
      '<div><strong>' + addon.name + '</strong> <span style="color:var(--primary);font-weight:700;">₱' + addon.pricePerDay + '/day</span></div>' +
      '</div>';
  }).join('');

  el.innerHTML = '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-booking-form\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Book ' + (bookingFormVehicle ? bookingFormVehicle.brand + ' ' + bookingFormVehicle.model : '') + '</h2>' +
    '</div>' +
    '<div class="scroll-content" style="padding-bottom:100px;">' +

    // Rental Period
    '<div class="card"><h4 style="font-weight:700;margin-bottom:14px;">Rental Period</h4>' +
    '<div class="form-group"><label>Start Date</label><input type="date" id="bfStartDate" min="' + today + '" onchange="updateBookingPrice();autoSetReturnTime()"><span class="field-error" id="bfStartErr"></span></div>' +
    '<div class="form-group"><label>Pickup Time</label>' +
    '<select id="bfPickupTime" onchange="autoSetReturnTime()" style="width:100%;padding:12px 14px;background:var(--bg-input);border:1.5px solid transparent;border-radius:var(--radius-sm);font-size:0.95rem;color:var(--text-primary);outline:none;">' +
    generateTimeOptions('06:00') +
    '</select></div>' +
    '<div class="form-group"><label>End Date</label><input type="date" id="bfEndDate" min="' + today + '" onchange="updateBookingPrice()"><span class="field-error" id="bfEndErr"></span></div>' +
    '<div class="form-group"><label>Return Time</label>' +
    '<select id="bfReturnTime" style="width:100%;padding:12px 14px;background:var(--bg-input);border:1.5px solid transparent;border-radius:var(--radius-sm);font-size:0.95rem;color:var(--text-primary);outline:none;">' +
    generateTimeOptions('06:00') +
    '</select>' +
    '<small style="color:var(--text-muted);font-size:0.72rem;margin-top:4px;display:block;"><i class="fas fa-info-circle"></i> Return time is auto-set to 24 hrs after pickup</small>' +
    '</div>' +
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

    // Loyalty Points
    '<div class="card"><h4 style="font-weight:700;margin-bottom:14px;">Loyalty Points</h4>' +
    '<p style="font-size:0.875rem;color:var(--text-secondary);margin-bottom:8px;">Available: <strong>' + (currentUser.loyaltyPoints || 0) + ' pts</strong></p>' +
    '<div class="form-group"><label>Points to Redeem</label><input type="number" id="bfPoints" min="0" max="' + (currentUser.loyaltyPoints || 0) + '" value="0" onchange="updateBookingPrice()"></div>' +
    '</div>' +

    // Price Breakdown
    '<div class="card" id="priceBreakdown"><h4 style="font-weight:700;margin-bottom:14px;">Price Breakdown</h4><p style="color:var(--text-muted);font-size:0.875rem;">Select dates to see pricing</p></div>' +

    // Mileage notice
    '<div style="background:#e8f4fd;border-radius:var(--radius-sm);padding:12px;margin-bottom:12px;font-size:0.8rem;color:#084298;">Daily mileage limit: <strong>' + (appSettings.mileage_limit || 250) + ' km</strong></div>' +

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
  var result = calculateBookingPrice(
    v.daily_rate, start, end, selectedAddons, insPrice,
    parseInt(appSettings.long_term_discount_days) || 7,
    parseInt(appSettings.long_term_discount_percent) || 10,
    0, pts
  );
  var payTypeEl = document.getElementById('bfPaymentType');
  var payType = payTypeEl ? payTypeEl.value : 'Full';
  var nowDue = payType === 'Downpayment' ? result.downpaymentAmount : result.total;
  var el = document.getElementById('priceBreakdown');
  if (!el) return;
  el.innerHTML = '<h4 style="font-weight:700;margin-bottom:14px;">Price Breakdown</h4>' +
    '<div class="price-row"><span>Base Rate (' + result.days + ' days - ' + formatPHP(v.daily_rate) + ')</span><span>' + formatPHP(result.basePrice) + '</span></div>' +
    // Individual add-ons
    (selectedAddons.length > 0 ? selectedAddons.map(function(a) {
      return '<div class="price-row" style="padding-left:12px;color:var(--text-secondary);"><span><i class="fas fa-check" style="color:var(--success);margin-right:6px;"></i>' + a.name + ' (' + result.days + ' days - ₱' + a.pricePerDay + ')</span><span>' + formatPHP(a.price) + '</span></div>';
    }).join('') : '') +
    // Insurance detail
    (insPrice > 0 ? '<div class="price-row" style="padding-left:12px;color:var(--text-secondary);"><span><i class="fas fa-shield-alt" style="color:var(--info);margin-right:6px;"></i>' + selectedInsurance.type + ' (' + result.days + ' days - ₱' + selectedInsurance.pricePerDay + ')</span><span>' + formatPHP(insPrice) + '</span></div>' : '') +
    (result.longTermDiscount > 0 ? '<div class="price-row" style="color:var(--success);"><span><i class="fas fa-tag"></i> Long-term Discount (' + (appSettings.long_term_discount_percent || 10) + '%)</span><span>-' + formatPHP(result.longTermDiscount) + '</span></div>' : '') +
    (result.couponDiscount > 0 ? '<div class="price-row" style="color:var(--success);"><span><i class="fas fa-ticket-alt"></i> Coupon Discount</span><span>-' + formatPHP(result.couponDiscount) + '</span></div>' : '') +
    (result.pointsDiscount > 0 ? '<div class="price-row" style="color:var(--success);"><span><i class="fas fa-star"></i> Points Discount</span><span>-' + formatPHP(result.pointsDiscount) + '</span></div>' : '') +
    '<div class="price-row total" style="margin-top:4px;"><span>Total</span><span>' + formatPHP(result.total) + '</span></div>' +
    (payType === 'Downpayment' ? '<div class="price-row" style="color:var(--primary);font-weight:700;"><span>Due Now (20% Downpayment)</span><span>' + formatPHP(nowDue) + '</span></div>' +
    '<div class="price-row" style="color:var(--text-secondary);"><span>Remaining Balance (80%)</span><span>' + formatPHP(result.balanceAmount) + '</span></div>' : '') +
    '<div style="font-size:0.78rem;color:var(--text-muted);margin-top:8px;padding-top:8px;border-top:1px solid var(--border);"><i class="fas fa-star" style="color:#ffc107;"></i> You will earn <strong>' + result.pointsEarned + ' loyalty points</strong> from this booking</div>';
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
  var result = calculateBookingPrice(
    bookingFormVehicle.daily_rate, start, end, selectedAddons, selectedInsurance.price,
    parseInt(appSettings.long_term_discount_days) || 7,
    parseInt(appSettings.long_term_discount_percent) || 10,
    0, pts
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
    pickup_time: document.getElementById('bfPickupTime') ? document.getElementById('bfPickupTime').value : '06:00',
    return_time: document.getElementById('bfReturnTime') ? document.getElementById('bfReturnTime').value : '06:00',
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
    applied_coupon_id: null,
    discount_amount: result.longTermDiscount,
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
    '<p><strong>Mileage Rule:</strong> ' + (appSettings.mileage_limit || 250) + ' km/day limit. Excess charged at ₱10/km.</p>' +
    '<p><strong>Driver Responsibility:</strong> You must be the primary driver with a valid verified license.</p>' +
    '<p><strong>Late Return:</strong> Penalty of ₱500 per hour for late returns.</p>' +
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
      BookingSession.clear(); // booking submitted - clear any stale session
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

// PAYMENT - PayMongo Integration
function openPaymentScreen(bookingId, priceResult, payType) {
  var nowDue = payType === 'Downpayment' ? priceResult.downpaymentAmount : priceResult.total;
  var el = document.getElementById('paymentContent');
  if (!el) return;

  var breakdownHtml =
    '<div class="price-row"><span>Base Rate (' + priceResult.days + ' days)</span><span>' + formatPHP(priceResult.basePrice) + '</span></div>' +
    // Render all available addons as toggleable on payment page
    (ADDON_OPTIONS.map(function(opt, idx) {
      var isSelected = selectedAddons.some(function(a) { return a.name === opt.name; });
      var aPrice = opt.pricePerDay * priceResult.days;
      return '<div class="price-row" style="padding-left:10px;font-size:0.8rem;color:var(--text-secondary);cursor:pointer;" onclick="togglePaymentAddon(' + idx + ', ' + bookingId + ')">' +
             '<span><i class="fas ' + (isSelected ? 'fa-check-square' : 'fa-square') + '" style="color:var(--' + (isSelected ? 'success' : 'border') + ');margin-right:6px;font-size:1.1em;vertical-align:middle;"></i> ' + opt.name + '</span>' +
             '<span>' + formatPHP(aPrice) + '</span></div>';
    }).join('')) +
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


function togglePaymentAddon(idx, bookingId) {
  var opt = ADDON_OPTIONS[idx];
  var days = _pendingPriceResult.days;
  var existingIdx = selectedAddons.findIndex(function(a) { return a.name === opt.name; });
  if (existingIdx >= 0) {
    selectedAddons.splice(existingIdx, 1);
  } else {
    selectedAddons.push({ name: opt.name, price: opt.pricePerDay * days, pricePerDay: opt.pricePerDay });
  }
  
  // Recalculate price
  var v = bookingFormVehicle;
  var cpPct = couponData ? couponData.discount_percent : 0;
  var pts = parseInt(document.getElementById('bfPoints') ? document.getElementById('bfPoints').value : 0) || 0;
  
  _pendingPriceResult = calculateBookingPrice(
    v.daily_rate, _pendingBookingPayload.start_date, _pendingBookingPayload.end_date, selectedAddons, selectedInsurance.price,
    parseInt(appSettings.long_term_discount_days) || 7,
    parseInt(appSettings.long_term_discount_percent) || 10,
    cpPct, pts
  );
  
  _pendingBookingPayload.addons = selectedAddons.map(function(a) { return a.name; });
  _pendingBookingPayload.addon_price = _pendingPriceResult.addonPrice;
  _pendingBookingPayload.total_price = _pendingPriceResult.total;
  
  // Re-render payment screen
  openPaymentScreen(bookingId, _pendingPriceResult, _pendingPayType);
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

  // Cash payment - use existing manual flow
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
        BookingSession.clear();
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

  // Online payment - redirect to PayMongo
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
  // Close in-app browser if still open
  if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Browser) {
    window.Capacitor.Plugins.Browser.close().catch(function() {});
  }
  apiCall('/paymongo/status/' + bookingId)
    .then(function(data) {
      showLoading(false);
      if (data.paid) {
        BookingSession.clear();
        closeOverlay('page-payment');
        showToast('Payment confirmed! Booking #' + bookingId + ' is now active.', 'success');
        loadNotifications(currentUser.id);
        loadBookings();
        showPage('page-bookings');
      } else {
        showPaymentFailed(bookingId, amount, method, 'Payment not yet confirmed. Tap Try Again to create a new payment link.');
      }
    })
    .catch(function() {
      showLoading(false);
      showPaymentFailed(bookingId, amount, method, 'Could not verify payment. Please try again.');
    });
}

function showPaymentFailed(bookingId, amount, method, message) {
  var el = document.getElementById('paymentContent');
  if (!el) return;
  var methodLabel = method === 'gcash' ? 'GCash' : method === 'maya' ? 'Maya' : method === 'card' ? 'Card' : 'Online';
  el.innerHTML =
    '<div class="page-header">' +
    '<button class="back-btn" onclick="closeOverlay(\'page-payment\')"><i class="fas fa-arrow-left"></i></button>' +
    '<h2>Payment</h2></div>' +
    '<div class="scroll-content" style="padding-bottom:100px;text-align:center;padding-top:40px;">' +
    '<div style="width:80px;height:80px;border-radius:50%;background:rgba(220,38,38,0.1);display:flex;align-items:center;justify-content:center;margin:0 auto 20px;">' +
    '<i class="fas fa-exclamation-circle" style="font-size:2.5rem;color:var(--danger);"></i></div>' +
    '<h3 style="font-size:1.2rem;font-weight:800;margin-bottom:8px;color:var(--danger);">Payment Incomplete</h3>' +
    '<p style="color:var(--text-secondary);font-size:0.875rem;margin-bottom:8px;">' + (message || 'Your payment was not completed.') + '</p>' +
    '<p style="color:var(--text-secondary);font-size:0.8rem;margin-bottom:24px;">Tap <strong>Try Again</strong> to open a new ' + methodLabel + ' payment link.</p>' +
    '<div style="background:var(--bg-card);border-radius:var(--radius-sm);padding:16px;margin-bottom:24px;">' +
    '<div style="font-size:0.75rem;color:var(--text-secondary);">Amount to Pay</div>' +
    '<div style="font-size:1.5rem;font-weight:900;color:var(--primary);">' + formatPHP(amount) + '</div>' +
    '</div>' +
    '<button class="btn-primary" style="margin-bottom:12px;" onclick="retryPayment(' + bookingId + ',' + amount + ',\'' + method + '\')">' +
    '<i class="fas fa-redo"></i> Try Again</button>' +
    '<button class="btn-secondary" onclick="closeOverlay(\'page-payment\')" style="width:100%;">Cancel</button>' +
    '</div>';
}

function retryPayment(bookingId, amount, method) {
  showLoading(true);
  apiCall('/paymongo/create-payment', {
    method: 'POST',
    body: JSON.stringify({
      booking_id: bookingId,
      amount: amount,
      method: method,
      description: 'Autoride Booking #' + bookingId,
      customer_name: currentUser.fullName || currentUser.full_name || '',
      customer_email: currentUser.email || ''
    })
  })
    .then(function(data) {
      showLoading(false);
      if (data.checkout_url) {
        if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Browser) {
          window.Capacitor.Plugins.Browser.open({ url: data.checkout_url });
        } else {
          window.open(data.checkout_url, '_blank');
        }
        showPaymentWaiting(bookingId, amount, method);
      } else {
        showPaymentFailed(bookingId, amount, method, data.error || 'Failed to create payment. Please try again.');
      }
    })
    .catch(function(err) {
      showLoading(false);
      showPaymentFailed(bookingId, amount, method, (err && err.message) || 'Network error. Please check your connection and try again.');
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
    '<img src="Autoride-logo-nobg.png" alt="Autoride" style="width:80px;height:80px;object-fit:contain;margin-bottom:8px;">' +
    '<i class="fas fa-check-circle" style="font-size:2.5rem;color:var(--success);"></i>' +
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
  var el = document.getElementById('bookingsList');

  // Show cached data instantly
  try {
    var cached = localStorage.getItem('autoride_bookings_' + currentUser.id);
    if (cached) {
      var parsed = JSON.parse(cached);
      if (parsed.data && Date.now() - parsed.savedAt < 2 * 60 * 1000) {
        _allBookingsData = parsed.data;
        renderBookingsList(parsed.data);
        updateBookingStats(parsed.data);
      }
    }
  } catch(e) {}

  // Fetch fresh in background
  showLoading(true);
  apiCall('/user-bookings?user_id=' + currentUser.id)
    .then(function(data) {
      _allBookingsData = data;
      updateBookingStats(data);
      renderBookingsList(data);
      try { localStorage.setItem('autoride_bookings_' + currentUser.id, JSON.stringify({ data: data, savedAt: Date.now() })); } catch(e) {}
    })
    .catch(function(err) {
      if (!_allBookingsData.length && el) el.innerHTML = '<div class="empty-state"><p>' + err.message + '</p></div>';
    })
    .finally(function() { showLoading(false); });
}

function updateBookingStats(data) {
  var total = data.length;
  var completed = data.filter(function(b) { return b.status === 'Completed'; }).length;
  var spent = data.filter(function(b) { return b.payment_status === 'Paid'; }).reduce(function(s, b) { return s + parseFloat(b.total_price || 0); }, 0);
  var statTotal = document.getElementById('bkStatTotal');
  var statDone = document.getElementById('bkStatDone');
  var statSpent = document.getElementById('bkStatSpent');
  if (statTotal) statTotal.querySelector('div').textContent = total;
  if (statDone) statDone.querySelector('div').textContent = completed;
  if (statSpent) statSpent.querySelector('div').textContent = spent > 0 ? ('P' + (spent / 1000).toFixed(1) + 'k') : '-';
}

function filterBookingsList(filter, btn) {
  // Update tab styles
  var tabs = document.querySelectorAll('#bookingFilterTabs button');
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].style.background = 'transparent';
    tabs[i].style.color = 'var(--text-secondary)';
  }
  if (btn) {
    btn.style.background = 'var(--primary)';
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
    'Pending': '#fbbf24', 'Confirmed': '#00b14f', 'Approved': '#00b14f',
    'Picked Up': '#00b14f', 'Completed': '#00b14f', 'Cancelled': '#f87171', 'Rejected': '#f87171'
  };
  el.innerHTML = data.map(function(b) {
    var color = statusColors[b.status] || '#a1a1aa';
    var payColor = b.payment_status === 'Paid' ? '#00b14f' : '#f87171';
    var vehicleName = ((b.brand || '') + ' ' + (b.model || '')).trim();
    var vehicleSub = [b.color, b.plate_number].filter(Boolean).join(' - ');
    var startFmt = formatBookingDate(b.start_date);
    var endFmt = formatBookingDate(b.end_date);
    return '<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;margin:0 16px 14px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,0.05);" onclick="openBookingDetail(' + b.id + ')">' +
      '<div style="padding:16px;">' +
      
      /* Header row: icon + name + status badge */
      '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;gap:12px;">' +
        '<div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0;">' +
          '<div style="width:40px;height:40px;border-radius:50%;background:rgba(0,177,79,0.1);display:flex;align-items:center;justify-content:center;flex-shrink:0;">' +
            '<i class="fas fa-car" style="color:var(--primary);font-size:1.2rem;"></i>' +
          '</div>' +
          '<div style="flex:1;min-width:0;">' +
            '<div style="font-weight:700;font-size:1rem;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + vehicleName + '</div>' +
            (vehicleSub ? '<div style="font-size:0.75rem;color:var(--text-muted);margin-top:2px;">' + vehicleSub + '</div>' : '') +
          '</div>' +
        '</div>' +
        '<span style="padding:6px 12px;border-radius:6px;font-size:0.75rem;font-weight:600;background:' + color + ';color:#fff;flex-shrink:0;">' + b.status + '</span>' +
      '</div>' +

      '<div style="border-top:1px solid var(--border);margin-bottom:16px;"></div>' +

      /* Date row */
      '<div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;margin-bottom:16px;">' +
        '<div style="min-width:0;">' +
          '<div style="font-size:0.6rem;color:var(--text-muted);font-weight:600;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;white-space:nowrap;">Pick-up</div>' +
          '<div style="font-size:0.85rem;font-weight:700;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + startFmt + '</div>' +
        '</div>' +
        '<div style="color:var(--text-muted);font-size:0.9rem;font-weight:400;margin-top:14px;text-align:center;">&rarr;</div>' +
        '<div style="min-width:0;">' +
          '<div style="font-size:0.6rem;color:var(--text-muted);font-weight:600;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;white-space:nowrap;">Return</div>' +
          '<div style="display:flex;align-items:center;gap:4px;font-size:0.85rem;font-weight:700;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"><span>' + endFmt + '</span><i class="fas fa-chevron-right" style="font-size:0.7rem;color:var(--text-muted);flex-shrink:0;"></i></div>' +
        '</div>' +
      '</div>' +

      '<div style="border-top:1px solid var(--border);margin-bottom:16px;"></div>' +

      /* Footer row: payment badge + price */
      '<div style="display:flex;align-items:center;justify-content:space-between;">' +
        '<span style="padding:6px 12px;border-radius:6px;font-size:0.75rem;font-weight:600;background:' + payColor + ';color:#fff;">' + (b.payment_status || 'Unpaid') + '</span>' +
        '<div style="font-weight:800;font-size:1.1rem;color:var(--primary);">' + formatPHP(b.total_price) + '</div>' +
      '</div>' +

      '</div></div>';
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
  var canCancel = b.status === 'Pending' || b.status === 'Confirmed' || b.status === 'Approved';
  var canReview = b.status === 'Completed';
  var canPayBalance = b.payment_status === 'Partially Paid';
  var el = document.getElementById('bookingDetailContent');
  if (!el) return;

  // Status colors
  var statusColors = {
    'Pending': '#fbbf24', 'Confirmed': '#00b14f', 'Approved': '#00b14f',
    'Picked Up': '#00b14f', 'Completed': '#00b14f', 'Cancelled': '#f87171', 'Rejected': '#f87171'
  };
  var payColors = { 'Paid': '#00b14f', 'Partially Paid': '#fbbf24', 'Unpaid': '#f87171', 'Refund Pending': '#f59e0b', 'Refunded': '#00b14f', 'Cancelled': '#a1a1aa' };
  var sColor = statusColors[b.status] || '#a1a1aa';
  var pColor = payColors[b.payment_status] || '#f87171';

  // License section
  var licenseHtml = '';
  if (b.license_number || b.license_full_name || b.date_of_birth || b.license_expiry) {
    var frontBtn = b.license_front_url
      ? '<a href="' + b.license_front_url + '" target="_blank" style="flex:1;padding:12px;background:var(--bg-input);border:1px solid var(--border);border-radius:10px;text-align:center;font-size:0.8rem;font-weight:600;color:var(--text-secondary);text-decoration:none;display:block;">Front Image</a>'
      : '<div style="flex:1;padding:12px;background:var(--bg-input);border:1px solid var(--border);border-radius:10px;text-align:center;font-size:0.8rem;font-weight:600;color:var(--text-muted);">Front Image</div>';
    var backBtn = b.license_back_url
      ? '<a href="' + b.license_back_url + '" target="_blank" style="flex:1;padding:12px;background:var(--bg-input);border:1px solid var(--border);border-radius:10px;text-align:center;font-size:0.8rem;font-weight:600;color:var(--text-secondary);text-decoration:none;display:block;">Back Image</a>'
      : '<div style="flex:1;padding:12px;background:var(--bg-input);border:1px solid var(--border);border-radius:10px;text-align:center;font-size:0.8rem;font-weight:600;color:var(--text-muted);">Back Image</div>';
    licenseHtml =
      '<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:16px;">' +
        '<h4 style="font-weight:700;font-size:1rem;color:var(--primary);margin-bottom:12px;">Driver\'s License Details</h4>' +
        (b.license_full_name ? '<p style="font-size:0.875rem;color:#1a1a1a;margin-bottom:6px;">Full Name: <strong>' + b.license_full_name + '</strong></p>' : '') +
        (b.date_of_birth ? '<p style="font-size:0.875rem;color:#1a1a1a;margin-bottom:6px;">DOB: ' + b.date_of_birth + '</p>' : '') +
        (b.license_number ? '<p style="font-size:0.875rem;color:#1a1a1a;margin-bottom:6px;">License #: ' + b.license_number + '</p>' : '') +
        (b.license_expiry ? '<p style="font-size:0.875rem;color:#1a1a1a;margin-bottom:12px;">Expiry: ' + b.license_expiry + '</p>' : '') +
        '<div style="display:flex;gap:10px;">' + frontBtn + backBtn + '</div>' +
      '</div>';
  }

  // Emergency contact section
  var emergencyHtml = '';
  if (b.emergency_contact_name || b.emergency_contact_phone) {
    emergencyHtml =
      '<div style="margin-bottom:16px;">' +
        '<h4 style="font-weight:700;font-size:1rem;color:#1a1a1a;margin-bottom:10px;">Emergency Contact</h4>' +
        (b.emergency_contact_name ? '<p style="font-size:0.875rem;color:#1a1a1a;margin-bottom:4px;">Name: ' + b.emergency_contact_name + '</p>' : '') +
        (b.emergency_contact_phone ? '<p style="font-size:0.875rem;color:#1a1a1a;margin-bottom:4px;">Phone: ' + b.emergency_contact_phone + '</p>' : '') +
        (b.emergency_contact_relationship ? '<p style="font-size:0.875rem;color:#1a1a1a;">Rel: ' + b.emergency_contact_relationship + '</p>' : '') +
      '</div>';
  }

  // Inspections section - no button for customers, admin-only action
  var inspectBtn = '';

  // Primary action button - customer-relevant only
  var primaryAction = '';
  var canExtend = (b.status === 'Picked Up' || b.status === 'Ongoing');
  if (canPayBalance) {
    primaryAction = '<button class="btn-primary" style="margin-bottom:12px;" onclick="openPayBalanceScreen(' + b.id + ',' + b.balance_amount + ')"><i class="fas fa-money-bill"></i> Pay Balance (' + formatPHP(b.balance_amount) + ')</button>';
  } else if (canReview) {
    primaryAction = '<button class="btn-primary" style="margin-bottom:12px;" onclick="openReviewForm(' + b.vehicle_id + ')"><i class="fas fa-star"></i> Leave a Review</button>';
  }
  if (canExtend) {
    primaryAction += '<button class="btn-primary" style="margin-bottom:12px;background:linear-gradient(135deg,#00b14f,#059669);" onclick="openExtendBooking(' + b.id + ',\'' + (b.end_date||'').split('T')[0] + '\',\'' + (b.daily_rate||0) + '\')">' +
      '<i class="fas fa-calendar-plus" style="margin-right:6px;"></i> Extend Booking</button>';
  }

  // Secondary action buttons
  var secondaryActions = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;">';
  secondaryActions += '<button class="btn-outline" onclick="downloadReceipt(' + b.id + ')">Download Receipt</button>';
  if (canCancel) secondaryActions += '<button class="btn-outline" style="color:var(--danger);border-color:var(--danger);" onclick="promptCancelBooking(' + b.id + ')">Cancel Booking</button>';
  if (b.status === 'Pending' || b.status === 'Confirmed' || b.status === 'Approved') secondaryActions += '</div><button class="btn-secondary" style="width:100%;margin-bottom:12px;" onclick="openModifyBooking(' + b.id + ',\'' + b.start_date + '\',\'' + b.end_date + '\')"><i class="fas fa-edit"></i> Modify Dates</button>';
  else secondaryActions += '</div>';

  var vehicleName = ((b.brand || '') + ' ' + (b.model || '')).trim();
  var plateInfo = b.plate_number ? ' (' + b.plate_number + ')' : '';

  el.innerHTML =
    '<div class="page-header">' +
      '<button class="back-btn" onclick="closeOverlay(\'page-booking-detail\')"><i class="fas fa-times"></i></button>' +
      '<h2 style="text-align:center;flex:1;">Booking Details</h2>' +
    '</div>' +
    '<div class="scroll-content" style="padding:20px;padding-bottom:40px;">' +

      // Title
      '<h2 style="font-size:1.4rem;font-weight:800;color:var(--text-primary);margin-bottom:20px;">Booking Details #' + b.id + '</h2>' +

      // Info grid: customer / vehicle / rental period
      '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px;">' +
        '<div>' +
          '<div style="font-size:0.65rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Customer</div>' +
          '<div style="font-size:0.9rem;font-weight:600;color:var(--text-primary);">' + (b.license_full_name || currentUser.fullName || '-') + '</div>' +
        '</div>' +
        '<div>' +
          '<div style="font-size:0.65rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Vehicle</div>' +
          '<div style="font-size:0.9rem;font-weight:600;color:var(--text-primary);">' + vehicleName + plateInfo + '</div>' +
        '</div>' +
        '<div>' +
          '<div style="font-size:0.65rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Rental Period</div>' +
          '<div style="font-size:0.9rem;font-weight:600;color:var(--text-primary);">' + formatBookingDate(b.start_date) + ' to ' + formatBookingDate(b.end_date) + '</div>' +
        '</div>' +
      '</div>' +

      // Status grid: payment status / total price / booking status
      '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:24px;">' +
        '<div>' +
          '<div style="font-size:0.65rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Payment Status</div>' +
          '<span style="display:inline-block;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;background:' + pColor + ';color:#fff;">' + (b.payment_status || 'Unpaid') + '</span>' +
        '</div>' +
        '<div>' +
          '<div style="font-size:0.65rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Total Price</div>' +
          '<div style="font-size:1rem;font-weight:700;color:var(--text-primary);">?' + (parseFloat(b.total_price) || 0).toFixed(2) + '</div>' +
        '</div>' +
        '<div>' +
          '<div style="font-size:0.65rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Booking Status</div>' +
          '<span style="display:inline-block;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;background:' + sColor + ';color:#fff;">' + b.status.toUpperCase() + '</span>' +
        '</div>' +
      '</div>' +

      // Divider
      '<div style="border-top:1px solid var(--border);margin-bottom:20px;"></div>' +

      // Driver's License Details
      licenseHtml +

      // Emergency Contact
      emergencyHtml +

      // Divider
      (emergencyHtml ? '<div style="border-top:1px solid var(--border);margin-bottom:20px;"></div>' : '') +

      // Divider before actions
      '<div style="border-top:1px solid var(--border);margin-bottom:20px;"></div>' +

      // Cancellation reason
      (b.cancellation_reason ? '<div style="background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.3);border-radius:12px;padding:14px;margin-bottom:16px;"><p style="font-size:0.875rem;color:var(--danger);"><strong>Cancellation Reason:</strong> ' + b.cancellation_reason + '</p></div>' : '') +

      // Refund status card (shown for cancelled bookings with payment)
      (function() {
        var ps = b.payment_status;
        if (ps !== 'Refund Pending' && ps !== 'Refunded') return '';
        var isRefunded = ps === 'Refunded';
        var accentColor = isRefunded ? '#00b14f' : '#f59e0b';
        var bgColor = isRefunded ? 'rgba(0,177,79,0.07)' : 'rgba(245,158,11,0.07)';
        var borderColor = isRefunded ? 'rgba(0,177,79,0.3)' : 'rgba(245,158,11,0.3)';
        var icon = isRefunded ? 'fa-check-circle' : 'fa-clock';
        var statusLabel = isRefunded ? 'Refund Processed' : 'Refund Pending';
        var refundAmt = parseFloat(b.refund_amount || 0);
        var totalPaid = parseFloat(b.amount_paid || b.total_price || 0);
        var nonRefundable = totalPaid - refundAmt;

        var html = '<div style="background:' + bgColor + ';border:1.5px solid ' + borderColor + ';border-radius:14px;padding:16px;margin-bottom:16px;">' +
          '<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">' +
            '<i class="fas ' + icon + '" style="font-size:1.2rem;color:' + accentColor + ';"></i>' +
            '<span style="font-size:0.95rem;font-weight:800;color:' + accentColor + ';">' + statusLabel + '</span>' +
          '</div>' +
          '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:' + (b.refund_note ? '10px' : '0') + ';">' +
            '<div style="background:var(--bg-card);border-radius:10px;padding:10px;">' +
              '<div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:3px;">Refund Amount</div>' +
              '<div style="font-size:1rem;font-weight:800;color:' + accentColor + ';">' + formatPHP(refundAmt > 0 ? refundAmt : totalPaid) + '</div>' +
            '</div>' +
            (isRefunded && b.refund_method ? (
              '<div style="background:var(--bg-card);border-radius:10px;padding:10px;">' +
                '<div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:3px;">Sent via</div>' +
                '<div style="font-size:0.85rem;font-weight:700;color:var(--text-primary);">' + (b.refund_channel || b.refund_method) + '</div>' +
              '</div>'
            ) : (b.refund_channel ? (
              '<div style="background:var(--bg-card);border-radius:10px;padding:10px;">' +
                '<div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:3px;">Sent via</div>' +
                '<div style="font-size:0.85rem;font-weight:700;color:var(--text-primary);">' + b.refund_channel + '</div>' +
              '</div>'
            ) : (
              '<div style="background:var(--bg-card);border-radius:10px;padding:10px;">' +
                '<div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:3px;">Amount Paid</div>' +
                '<div style="font-size:0.85rem;font-weight:700;color:var(--text-primary);">' + formatPHP(totalPaid) + '</div>' +
              '</div>'
            ))) +
          '</div>' +
          (isRefunded && b.refund_ref ? (
            '<div style="font-size:0.78rem;color:var(--text-muted);margin-top:4px;">Reference #: <strong style="color:var(--text-primary);">' + b.refund_ref + '</strong></div>'
          ) : '') +
          (isRefunded && b.refund_account_name ? (
            '<div style="font-size:0.78rem;color:var(--text-muted);margin-top:4px;">Sent to: <strong style="color:var(--text-primary);">' + b.refund_account_name + '</strong> (' + (b.refund_account_number || '') + ')</div>'
          ) : '') +
          (isRefunded && b.refunded_at ? (
            '<div style="font-size:0.75rem;color:var(--text-muted);margin-top:4px;">Processed: ' + _fmtDate(_normDateStr(b.refunded_at)) + '</div>'
          ) : '') +
          (isRefunded && b.refund_proof_url ? (
            '<div style="margin-top:10px;">' +
              '<button onclick="_viewRefundProof(\'' + b.refund_proof_url.replace(/'/g, '') + '\')" ' +
                'style="width:100%;padding:9px;background:rgba(0,177,79,0.1);border:1.5px solid rgba(0,177,79,0.3);border-radius:10px;color:#00B14F;font-size:0.8rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;">' +
                '<i class="fas fa-image"></i> View Transfer Proof' +
              '</button>' +
            '</div>'
          ) : '') +
          (b.refund_note && nonRefundable > 0.01 ? (
            '<div style="margin-top:10px;padding:8px 10px;background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.2);border-radius:8px;font-size:0.75rem;color:#f87171;">' +
              '<i class="fas fa-info-circle" style="margin-right:4px;"></i>' +
              formatPHP(nonRefundable) + ' non-refundable (20% reservation fee � cancelled <48h before pickup)' +
            '</div>'
          ) : '') +
          (!isRefunded ? (
            '<div style="margin-top:12px;font-size:0.78rem;color:var(--text-muted);margin-bottom:10px;">Our team will process your refund shortly. Please provide your preferred refund channel so we can send the money:</div>' +
            (b.refund_channel ? (
              '<div style="background:rgba(0,177,79,0.08);border:1.5px solid rgba(0,177,79,0.3);border-radius:10px;padding:12px;">' +
                '<div style="font-size:0.72rem;color:#00B14F;font-weight:800;margin-bottom:6px;display:flex;align-items:center;gap:6px;"><i class="fas fa-check-circle"></i> Refund Details Submitted</div>' +
                '<div style="font-size:0.85rem;font-weight:700;color:var(--text-primary);">' + b.refund_channel + ' \u2014 ' + (b.refund_account_name || '') + '</div>' +
                '<div style="font-size:0.78rem;color:var(--text-muted);">Acct: ' + (b.refund_account_number || '') + '</div>' +
                '<div style="font-size:0.72rem;color:var(--text-muted);margin-top:6px;">Waiting for admin to process your refund.</div>' +
              '</div>'
            ) : (
              '<button onclick="openRefundDetailsForm(' + b.id + ',' + (refundAmt > 0 ? refundAmt : totalPaid) + ')" ' +
                'style="width:100%;padding:11px;background:#f59e0b;border:none;border-radius:12px;color:white;font-size:0.875rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;">' +
                '<i class="fas fa-paper-plane"></i> Submit Refund Details' +
              '</button>'
            ))
          ) : '') +
        '</div>';
        return html;
      }()) +

      // Action buttons
      primaryAction +
      secondaryActions +

    '</div>';
}

function openExtendBooking(bookingId, currentEndDate, dailyRate) {
  // Set activeBookingData from bookings cache if not already set
  if ((!activeBookingData || activeBookingData.id !== bookingId) && typeof _allBookingsData !== 'undefined') {
    for (var i = 0; i < _allBookingsData.length; i++) {
      if (_allBookingsData[i].id === bookingId) { activeBookingData = _allBookingsData[i]; break; }
    }
  }
  // Prefer activeBookingData.end_date as authoritative source (avoids attribute-escaping issues)
  var endDate = '';
  if (activeBookingData && activeBookingData.end_date) {
    endDate = activeBookingData.end_date.toString().split('T')[0];
  }
  if (!endDate || endDate === 'undefined') {
    endDate = (currentEndDate || '').toString().split('T')[0];
  }
  var rate = parseFloat(dailyRate) || (activeBookingData ? parseFloat(activeBookingData.daily_rate || 0) : 0);
  var el = document.getElementById('bookingDetailContent');
  if (!el) {
    var modal = document.createElement('div');
    modal.id = 'extendModal';
    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.75);z-index:9999;display:flex;align-items:flex-end;justify-content:center;';
    document.body.appendChild(modal);
    _renderExtendForm(modal, bookingId, endDate, rate, true);
    return;
  }
  var prev = el.innerHTML;
  _renderExtendForm(el, bookingId, endDate, rate, false, prev);
}

function _renderExtendForm(container, bookingId, currentEndDate, dailyRate, isModal, prevHtml) {
  var rate = parseFloat(dailyRate) || 0;

  // Helper: extract YYYY-MM-DD from any date value without UTC conversion
  function _toLocalDateStr(val) {
    if (!val) return '';
    var s = val.toString().trim();
    // Already YYYY-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
    // Strip ISO time component
    if (s.indexOf('T') !== -1) {
      var iso = s.split('T')[0];
      if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) return iso;
    }
    // Parse any format (including HTTP-date "Mon, 01 Jun 2026 00:00:00 GMT")
    var dt = new Date(s);
    if (!isNaN(dt.getTime())) {
      // HTTP-date is UTC midnight Â use UTC parts to avoid timezone shift
      var useUTC = /GMT$/i.test(s) || /Z$/i.test(s);
      var y  = useUTC ? dt.getUTCFullYear()  : dt.getFullYear();
      var mo = useUTC ? dt.getUTCMonth() + 1 : dt.getMonth() + 1;
      var dy = useUTC ? dt.getUTCDate()      : dt.getDate();
      return y + '-' + String(mo).padStart(2, '0') + '-' + String(dy).padStart(2, '0');
    }
    return '';
  }

  // Normalize date Â prefer activeBookingData as most reliable source
  var endDateNorm = _toLocalDateStr(currentEndDate);
  if (!endDateNorm && typeof activeBookingData !== 'undefined' && activeBookingData) {
    endDateNorm = _toLocalDateStr(activeBookingData.end_date);
  }
  if (!endDateNorm) endDateNorm = '';
  currentEndDate = endDateNorm;

  // Also try to get daily_rate from activeBookingData if not provided
  if (!rate && typeof activeBookingData !== 'undefined' && activeBookingData) {
    rate = parseFloat(activeBookingData.daily_rate || 0);
  }

  // Calculate minDate (day after current end) using LOCAL date arithmetic Â no UTC conversion
  var minDate = currentEndDate;
  if (currentEndDate) {
    try {
      var parts0 = currentEndDate.split('-');
      var d = new Date(parseInt(parts0[0]), parseInt(parts0[1]) - 1, parseInt(parts0[2]));
      d.setDate(d.getDate() + 1);
      var y = d.getFullYear();
      var mo = String(d.getMonth() + 1).padStart(2, '0');
      var dy = String(d.getDate()).padStart(2, '0');
      minDate = y + '-' + mo + '-' + dy;
    } catch(e) {}
  }

  // Build HTML using array join to avoid quote escaping issues
  var parts = [];
  parts.push('<div class="page-header">');
  if (!isModal) {
    parts.push('<button class="back-btn" onclick="closeOverlay(\'page-booking-detail\')"><i class="fas fa-arrow-left"></i></button>');
  }
  parts.push('<h2 style="text-align:center;flex:1;">Extend Booking #' + bookingId + '</h2>');
  parts.push('</div>');
  parts.push('<div class="scroll-content" style="padding:20px;padding-bottom:60px;">');

  // Hidden inputs for submit to access
  parts.push('<input type="hidden" id="extOrigEnd" value="' + currentEndDate + '">');
  parts.push('<input type="hidden" id="extDailyRate" value="' + rate + '">');

  // Current return date card
  parts.push('<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:16px;">');
  parts.push('<div style="font-size:0.7rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:4px;">Current Return Date</div>');
  parts.push('<div style="font-size:1rem;font-weight:800;color:var(--text-primary);">' + currentEndDate + '</div>');
  parts.push('</div>');

  // New date picker
  parts.push('<div class="card">');
  parts.push('<h4 style="font-weight:700;margin-bottom:14px;"><i class="fas fa-calendar-plus" style="color:var(--primary);margin-right:8px;"></i>New Return Date</h4>');
  parts.push('<div class="form-group"><label>Extend Until</label>');
  parts.push('<input type="date" id="extNewEnd" min="' + minDate + '" onchange="calcExtPrice(\'' + currentEndDate + '\',' + rate + ')" style="width:100%;padding:12px;background:var(--bg-input);border:1.5px solid transparent;border-radius:var(--radius-sm);font-size:0.95rem;color:var(--text-primary);">');
  parts.push('</div>');
  parts.push('<div id="extPriceBox" style="display:none;background:rgba(0,177,79,0.08);border:1px solid rgba(0,177,79,0.3);border-radius:12px;padding:14px;margin-top:8px;">');
  parts.push('<div style="display:flex;justify-content:space-between;align-items:center;">');
  parts.push('<span style="font-size:0.82rem;color:var(--text-secondary);" id="extDaysLabel">Extension fee</span>');
  parts.push('<span style="font-size:1.1rem;font-weight:900;color:var(--primary);" id="extPriceLabel">-</span>');
  parts.push('</div></div></div>');

  // Payment section
  parts.push('<div class="card">');
  parts.push('<h4 style="font-weight:700;margin-bottom:14px;"><i class="fas fa-money-bill-wave" style="color:var(--primary);margin-right:8px;"></i>Payment</h4>');
  parts.push('<div class="form-group"><label>Payment Method</label>');
  parts.push('<select id="extMethod" style="width:100%;padding:12px;background:var(--bg-input);border:1.5px solid transparent;border-radius:var(--radius-sm);font-size:0.95rem;color:var(--text-primary);" onchange="document.getElementById(\'extCashFields\').style.display=(this.value===\'cash\'?\'block\':\'none\')">');
  parts.push('<option value="gcash">GCash</option>');
  parts.push('<option value="maya">Maya</option>');
  parts.push('<option value="cash">Cash Over the Counter</option>');
  parts.push('</select></div>');
  parts.push('<div id="extCashFields" style="display:none;">');
  parts.push('<div class="form-group"><label>Reference / Transaction # (optional)</label>');
  parts.push('<input type="text" id="extRef" placeholder="e.g. 1234567890">');
  parts.push('</div>');
  parts.push('<div class="form-group"><label>Payment Proof Screenshot</label>');
  parts.push('<button class="btn-secondary" onclick="pickExtProof()"><i class="fas fa-upload"></i> Upload Screenshot</button>');
  parts.push('<img id="extProofPreview" style="width:100%;margin-top:8px;border-radius:8px;display:none;">');
  parts.push('</div></div></div>');

  // Notice
  parts.push('<div style="margin-top:4px;padding:12px;background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.3);border-radius:12px;margin-bottom:20px;">');
  parts.push('<p style="font-size:0.8rem;color:var(--text-secondary);margin:0;"><i class="fas fa-info-circle" style="color:#fbbf24;margin-right:6px;"></i><strong>Note:</strong> If admin does not approve, your payment will be refunded upon vehicle return.</p>');
  parts.push('</div>');

  parts.push('<span class="field-error" id="extErr" style="display:block;margin-bottom:12px;text-align:center;"></span>');
  parts.push('<button class="btn-primary" onclick="submitExtension(' + bookingId + ')" style="margin-bottom:12px;"><i class="fas fa-paper-plane" style="margin-right:6px;"></i>Submit Extension Request</button>');
  parts.push('</div>');

  var html = parts.join('');

  if (isModal) {
    container.innerHTML = '<div style="background:var(--bg-app);width:100%;max-width:500px;border-radius:24px 24px 0 0;max-height:90vh;overflow-y:auto;">' + html + '</div>';
  } else {
    container.innerHTML = html;
  }
}


function _showExtPaymentWaiting(bookingId, newEnd, price, methodLabel, days) {
  var container = document.getElementById('bookingDetailContent');
  if (!container) return;
  var parts = [];
  parts.push('<div class="page-header">');
  parts.push('<h2 style="text-align:center;flex:1;">Waiting for Payment</h2>');
  parts.push('</div>');
  parts.push('<div class="scroll-content" style="padding:20px;text-align:center;padding-top:40px;">');
  parts.push('<div style="width:80px;height:80px;border-radius:50%;background:rgba(0,177,79,0.1);display:flex;align-items:center;justify-content:center;margin:0 auto 20px;">');
  parts.push('<i class="fas fa-spinner fa-spin" style="font-size:2rem;color:var(--primary);"></i></div>');
  parts.push('<h3 style="font-size:1.1rem;font-weight:800;margin-bottom:8px;">Complete Payment in ' + methodLabel + '</h3>');
  parts.push('<p style="color:var(--text-secondary);font-size:0.875rem;margin-bottom:24px;">Complete your payment in ' + methodLabel + ', then return here.</p>');
  parts.push('<div style="background:var(--bg-card);border-radius:12px;padding:16px;margin-bottom:24px;">');
  parts.push('<div style="font-size:0.75rem;color:var(--text-secondary);">' + days + '-day extension fee</div>');
  parts.push('<div style="font-size:1.4rem;font-weight:900;color:var(--primary);">' + formatPHP(price) + '</div></div>');
  parts.push('<button class="btn-primary" style="margin-bottom:12px;" onclick="_checkExtPayment(' + bookingId + ',\'' + newEnd + '\',' + price + ',\'' + methodLabel + '\',' + days + ')"><i class="fas fa-check-circle"></i> I\'ve Completed Payment</button>');
  parts.push('<button class="btn-secondary" onclick="closeOverlay(\'page-booking-detail\')" style="width:100%;">Cancel</button>');
  parts.push('</div>');
  container.innerHTML = parts.join('');
}

function _checkExtPayment(bookingId, newEnd, price, methodLabel, days) {
  showLoading(true);
  if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Browser) {
    window.Capacitor.Plugins.Browser.close().catch(function() {});
  }
  apiCall('/paymongo/status/' + bookingId)
    .then(function(data) {
      showLoading(false);
      if (data.paid) {
        // Payment confirmed - now submit extension request
        var fd = new FormData();
        fd.append('new_end_date', newEnd);
        fd.append('extension_price', price);
        fd.append('payment_method', methodLabel);
        fd.append('reference_number', '');
        fetch(API_BASE + '/bookings/' + bookingId + '/extend', { method: 'POST', body: fd })
          .then(function(r) { return r.json(); })
          .then(function(extData) {
            if (extData.error) { showToast(extData.error, 'error'); return; }
            closeOverlay('page-booking-detail');
            showToast('Extension request submitted! Awaiting admin approval.', 'success');
            NotifStore.add('Extension request for Booking #' + bookingId + ' submitted.');
            loadBookings();
          }).catch(function() { showToast('Payment confirmed but extension submission failed. Please contact support.', 'error'); });
      } else {
        showToast('Payment not yet confirmed. Please wait and try again.', 'info');
      }
    }).catch(function() {
      showLoading(false);
      showToast('Could not verify payment. Please check your bookings.', 'error');
    });
}

function pickExtProof() {
  var input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/jpeg,image/png';
  input.onchange = function(e) {
    var file = e.target.files[0];
    if (!file) return;
    _extProofBlob = file;
    var preview = document.getElementById('extProofPreview');
    if (preview) { preview.src = URL.createObjectURL(file); preview.style.display = 'block'; }
  };
  input.click();
}

function calcExtPrice(currentEndDate, dailyRate) {
  var newEnd = (document.getElementById('extNewEnd') || {}).value;
  if (!newEnd) return;
  // Always read from hidden input for reliability
  var origStr = (document.getElementById('extOrigEnd') || {}).value || currentEndDate || '';
  origStr = origStr.toString().split('T')[0];
  var rate = parseFloat((document.getElementById('extDailyRate') || {}).value || dailyRate || 0);
  try {
    var orig = new Date(origStr + 'T00:00:00');
    var next = new Date(newEnd + 'T00:00:00');
    if (isNaN(orig.getTime()) || isNaN(next.getTime())) return;
    var days = Math.round((next - orig) / (1000 * 60 * 60 * 24));
    if (days <= 0) { document.getElementById('extPriceBox').style.display = 'none'; return; }
    var price = days * (parseFloat(dailyRate) || 0);
    document.getElementById('extDaysLabel').textContent = days + ' day' + (days !== 1 ? 's' : '') + ' extension';
    document.getElementById('extPriceLabel').textContent = formatPHP(price);
    document.getElementById('extPriceBox').style.display = 'block';
    document.getElementById('extPriceBox').dataset.price = price;
    document.getElementById('extPriceBox').dataset.days = days;
  } catch(e) {}
}

function submitExtension(bookingId) {
  var newEnd = (document.getElementById('extNewEnd') || {}).value;
  var errEl = document.getElementById('extErr');
  if (errEl) errEl.textContent = '';

  if (!newEnd) { if (errEl) errEl.textContent = 'Please select a new return date.'; return; }

  // Get stored currentEndDate from hidden input
  var origEnd = (document.getElementById('extOrigEnd') || {}).value || '';
  var rate = parseFloat((document.getElementById('extDailyRate') || {}).value || 0);

  // Calculate price directly (don't rely on priceBox visibility)
  var days = 0;
  var price = 0;
  if (origEnd) {
    try {
      var orig = new Date(origEnd + 'T00:00:00');
      var next = new Date(newEnd + 'T00:00:00');
      days = Math.round((next - orig) / (1000 * 60 * 60 * 24));
      price = days * rate;
    } catch(e) {}
  }

  // Try to get price from priceBox if available (user may have seen it)
  var priceBox = document.getElementById('extPriceBox');
  if (priceBox && priceBox.dataset.price && parseFloat(priceBox.dataset.price) > 0) {
    price = parseFloat(priceBox.dataset.price);
    days = parseInt(priceBox.dataset.days || days);
  }

  if (days <= 0) { if (errEl) errEl.textContent = 'New date must be after current return date.'; return; }
  var method = (document.getElementById('extMethod') || {}).value || 'cash';
  var ref = (document.getElementById('extRef') || {}).value || '';
  var methodLabel = method === 'gcash' ? 'GCash' : method === 'maya' ? 'Maya' : 'Cash (Over the counter)';

  // PayMongo for GCash / Maya
  if (method === 'gcash' || method === 'maya') {
    showLoading(true);
    apiCall('/paymongo/create-payment', {
      method: 'POST',
      body: JSON.stringify({
        booking_id: bookingId,
        amount: price,
        method: method,
        description: 'Booking #' + bookingId + ' extension (' + days + ' day' + (days !== 1 ? 's' : '') + ')',
        customer_name: currentUser.fullName || '',
        customer_email: currentUser.email || ''
      })
    }).then(function(data) {
      showLoading(false);
      if (data.checkout_url) {
        if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Browser) {
          window.Capacitor.Plugins.Browser.open({ url: data.checkout_url });
        } else {
          window.open(data.checkout_url, '_blank');
        }
        _showExtPaymentWaiting(bookingId, newEnd, price, methodLabel, days);
      } else {
        if (errEl) errEl.textContent = data.error || 'Failed to create payment. Please try again.';
      }
    }).catch(function(err) {
      showLoading(false);
      if (errEl) errEl.textContent = err.message || 'Payment failed. Please try again.';
    });
    return;
  }

  showLoading(true);

  var fd = new FormData();
  fd.append('new_end_date', newEnd);
  fd.append('extension_price', price);
  fd.append('payment_method', methodLabel);
  fd.append('reference_number', ref);
  if (_extProofBlob) fd.append('payment_proof', _extProofBlob, 'ext_proof.jpg');

  fetch(API_BASE + '/bookings/' + bookingId + '/extend', { method: 'POST', body: fd })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      showLoading(false);
      if (data.error) { if (errEl) errEl.textContent = data.error; return; }
      _extProofBlob = null;
      closeOverlay('page-booking-detail');
      var modal = document.getElementById('extendModal');
      if (modal) modal.remove();
      showToast('Extension request submitted! Awaiting admin approval.', 'success');
      NotifStore.add('Extension request for Booking #' + bookingId + ' submitted. You will be notified once approved.');
      loadBookings();
    })
    .catch(function(err) {
      showLoading(false);
      if (errEl) errEl.textContent = err.message || 'Failed to submit extension request.';
    });
}

function loadInspectionsForDetail(bookingId) {
  apiCall('/inspections/' + bookingId)
    .then(function(data) {
      var el = document.getElementById('inspectionsList');
      if (!el) return;
      if (!data || !data.length) return;
      el.innerHTML = data.map(function(i) {
        return '<div style="background:var(--bg-input);border:1px solid var(--border);border-radius:10px;padding:12px;margin-bottom:8px;">' +
          '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">' +
            '<strong style="font-size:0.875rem;">' + (i.inspection_type === 'pickup' ? 'Pre-Rental' : 'Post-Rental') + '</strong>' +
            '<small style="color:var(--text-muted);">' + new Date(i.created_at).toLocaleDateString() + '</small>' +
          '</div>' +
          '<div style="font-size:0.8rem;color:var(--text-secondary);">Mileage: ' + i.mileage + ' km | Fuel: ' + i.fuel_level + '</div>' +
          (i.notes ? '<div style="font-size:0.8rem;margin-top:4px;color:var(--text-secondary);">' + i.notes + '</div>' : '') +
        '</div>';
      }).join('');
    }).catch(function() {});
}

function _showCancelPolicyModal(fee, refund, bookingId, reason) {
  // Remove any existing cancel modal
  var old = document.getElementById('_cancelPolicyModal');
  if (old) old.remove();

  var modal = document.createElement('div');
  modal.id = '_cancelPolicyModal';
  modal.style.cssText = 'position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;background:rgba(0,0,0,0.6);backdrop-filter:blur(4px);';
  modal.innerHTML =
    '<div style="background:#fff;border-radius:20px;padding:24px;width:100%;max-width:360px;box-shadow:0 20px 60px rgba(0,0,0,0.3);">' +
      // Header
      '<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">' +
        '<div style="width:40px;height:40px;background:#fef2f2;border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">' +
          '<i class="fas fa-exclamation-triangle" style="color:#ef4444;font-size:1.1rem;"></i>' +
        '</div>' +
        '<div>' +
          '<div style="font-size:1rem;font-weight:800;color:#0f172a;">Cancellation Policy</div>' +
          '<div style="font-size:0.75rem;color:#94a3b8;margin-top:1px;">Less than 48 hours before pickup</div>' +
        '</div>' +
      '</div>' +
      // Warning text
      '<p style="font-size:0.85rem;color:#374151;margin-bottom:16px;line-height:1.5;">You are cancelling <strong>less than 48 hours</strong> before your scheduled pickup. The following fees apply:</p>' +
      // Fee breakdown
      '<div style="background:#fef2f2;border-radius:12px;padding:14px;margin-bottom:16px;border:1px solid #fecaca;">' +
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">' +
          '<span style="font-size:0.82rem;color:#dc2626;display:flex;align-items:center;gap:6px;"><i class="fas fa-times-circle"></i> Non-refundable fee (20%)</span>' +
          '<span style="font-size:0.9rem;font-weight:800;color:#dc2626;">' + formatPHP(fee) + '</span>' +
        '</div>' +
        '<div style="border-top:1px solid #fecaca;padding-top:8px;display:flex;justify-content:space-between;align-items:center;">' +
          '<span style="font-size:0.82rem;color:#16a34a;display:flex;align-items:center;gap:6px;"><i class="fas fa-check-circle"></i> Refundable amount</span>' +
          '<span style="font-size:0.9rem;font-weight:800;color:#16a34a;">' + formatPHP(refund) + '</span>' +
        '</div>' +
      '</div>' +
      '<p style="font-size:0.8rem;color:#64748b;margin-bottom:20px;">Do you still want to cancel this booking?</p>' +
      // Buttons
      '<div style="display:flex;gap:10px;">' +
        '<button onclick="document.getElementById(\'_cancelPolicyModal\').remove();" ' +
          'style="flex:1;padding:12px;background:#f1f5f9;border:none;border-radius:12px;font-size:0.875rem;font-weight:700;color:#475569;cursor:pointer;">Keep Booking</button>' +
        '<button onclick="document.getElementById(\'_cancelPolicyModal\').remove(); _proceedCancel(' + bookingId + ', \'' + reason.replace(/'/g, "\\'") + '\');" ' +
          'style="flex:1;padding:12px;background:#ef4444;border:none;border-radius:12px;font-size:0.875rem;font-weight:700;color:white;cursor:pointer;">Yes, Cancel</button>' +
      '</div>' +
    '</div>';

  document.body.appendChild(modal);
}

function _proceedCancel(bookingId, reason) {
  showLoading(true);
  apiCall('/cancel-booking', { method: 'POST', body: JSON.stringify({ booking_id: bookingId, user_id: currentUser.id, reason: reason }) })
    .then(function(data) {
      var msg = 'Booking cancelled.';
      if (data.refund_amount > 0) {
        msg = 'Booking cancelled. Refund of ' + formatPHP(data.refund_amount) + ' will be processed.';
      }
      showToast(msg, 'success');
      NotifStore.add('Booking #' + bookingId + ' has been cancelled.');
      closeOverlay('page-booking-detail');
      loadBookings();
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

function _viewRefundProof(url) {
  var old = document.getElementById('_refundProofModal');
  if (old) old.remove();
  var modal = document.createElement('div');
  modal.id = '_refundProofModal';
  modal.style.cssText = 'position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;background:rgba(0,0,0,0.85);';
  modal.innerHTML =
    '<div style="position:relative;max-width:480px;width:100%;background:#fff;border-radius:16px;overflow:hidden;">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid #e5e7eb;">' +
        '<span style="font-weight:700;font-size:0.9rem;color:#0f172a;">Transfer Proof</span>' +
        '<button onclick="document.getElementById(\'_refundProofModal\').remove();" style="background:none;border:none;font-size:1.2rem;cursor:pointer;color:#64748b;">&#10005;</button>' +
      '</div>' +
      '<img src="' + url + '" style="width:100%;display:block;max-height:70vh;object-fit:contain;" ' +
        'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'block\';">' +
      '<p style="display:none;padding:20px;text-align:center;color:#ef4444;">Could not load proof image.</p>' +
    '</div>';
  modal.addEventListener('click', function(e) { if (e.target === modal) modal.remove(); });
  document.body.appendChild(modal);
}

function openRefundDetailsForm(bookingId, refundAmount) {
  var old = document.getElementById('_refundDetailsModal');
  if (old) old.remove();

  var modal = document.createElement('div');
  modal.id = '_refundDetailsModal';
  modal.style.cssText = 'position:fixed;inset:0;z-index:99999;display:flex;align-items:flex-end;justify-content:center;background:rgba(0,0,0,0.6);backdrop-filter:blur(4px);';
  modal.innerHTML =
    '<div style="background:var(--bg-card,#fff);border-radius:24px 24px 0 0;padding:24px;width:100%;max-width:480px;box-shadow:0 -8px 40px rgba(0,0,0,0.2);max-height:90vh;overflow-y:auto;">' +
      '<div style="width:36px;height:4px;background:var(--border,#e5e7eb);border-radius:2px;margin:0 auto 20px;"></div>' +
      '<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">' +
        '<div style="width:38px;height:38px;background:rgba(245,158,11,0.1);border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">' +
          '<i class="fas fa-money-bill-wave" style="color:#f59e0b;font-size:1rem;"></i>' +
        '</div>' +
        '<div>' +
          '<div style="font-size:1rem;font-weight:800;color:var(--text-primary,#0f172a);">Submit Refund Details</div>' +
          '<div style="font-size:0.78rem;color:var(--text-muted,#94a3b8);">Refund amount: <strong style="color:#f59e0b;">' + formatPHP(refundAmount) + '</strong></div>' +
        '</div>' +
      '</div>' +
      '<p style="font-size:0.82rem;color:var(--text-secondary,#64748b);margin-bottom:18px;margin-top:10px;">Choose how you want to receive your refund and provide the necessary details.</p>' +

      // Channel selector
      '<div style="margin-bottom:16px;">' +
        '<label style="font-size:0.75rem;font-weight:700;color:var(--text-muted,#94a3b8);text-transform:uppercase;letter-spacing:0.5px;display:block;margin-bottom:8px;">Refund Channel</label>' +
        '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">' +
          '<label style="cursor:pointer;">' +
            '<input type="radio" name="refundChannel" value="GCash" style="display:none;" onchange="document.getElementById(\'refundAcctLabel\').textContent=\'GCash Number\';document.getElementById(\'refundAcctNum\').maxLength=11;document.getElementById(\'refundAcctNum\').placeholder=\'09XX-XXX-XXXX\';document.getElementById(\'refundChannelCard_GCash\').style.background=\'rgba(0,177,79,0.12)\';document.getElementById(\'refundChannelCard_GCash\').style.borderColor=\'#00B14F\';[\'Maya\',\'Bank\'].forEach(function(c){document.getElementById(\'refundChannelCard_\'+c).style.background=\'var(--surface-container,#f4f6fb)\';document.getElementById(\'refundChannelCard_\'+c).style.borderColor=\'var(--border,#e5e7eb)\';});">' +
            '<div id="refundChannelCard_GCash" style="padding:10px 6px;border:2px solid var(--border,#e5e7eb);border-radius:10px;text-align:center;background:var(--surface-container,#f4f6fb);transition:all 0.2s;">' +
              '<i class="fas fa-mobile-alt" style="color:#00B14F;font-size:1.1rem;display:block;margin-bottom:4px;"></i>' +
              '<span style="font-size:0.72rem;font-weight:700;color:var(--text-primary,#0f172a);">GCash</span>' +
            '</div>' +
          '</label>' +
          '<label style="cursor:pointer;">' +
            '<input type="radio" name="refundChannel" value="Maya" style="display:none;" onchange="document.getElementById(\'refundAcctLabel\').textContent=\'Maya Number\';document.getElementById(\'refundAcctNum\').maxLength=11;document.getElementById(\'refundAcctNum\').placeholder=\'09XX-XXX-XXXX\';document.getElementById(\'refundChannelCard_Maya\').style.background=\'rgba(0,177,79,0.12)\';document.getElementById(\'refundChannelCard_Maya\').style.borderColor=\'#00B14F\';[\'GCash\',\'Bank\'].forEach(function(c){document.getElementById(\'refundChannelCard_\'+c).style.background=\'var(--surface-container,#f4f6fb)\';document.getElementById(\'refundChannelCard_\'+c).style.borderColor=\'var(--border,#e5e7eb)\';});">' +
            '<div id="refundChannelCard_Maya" style="padding:10px 6px;border:2px solid var(--border,#e5e7eb);border-radius:10px;text-align:center;background:var(--surface-container,#f4f6fb);transition:all 0.2s;">' +
              '<i class="fas fa-wallet" style="color:#7c3aed;font-size:1.1rem;display:block;margin-bottom:4px;"></i>' +
              '<span style="font-size:0.72rem;font-weight:700;color:var(--text-primary,#0f172a);">Maya</span>' +
            '</div>' +
          '</label>' +
          '<label style="cursor:pointer;">' +
            '<input type="radio" name="refundChannel" value="Bank" style="display:none;" onchange="document.getElementById(\'refundAcctLabel\').textContent=\'Account Number\';document.getElementById(\'refundAcctNum\').maxLength=20;document.getElementById(\'refundAcctNum\').placeholder=\'Bank account number\';document.getElementById(\'refundChannelCard_Bank\').style.background=\'rgba(0,177,79,0.12)\';document.getElementById(\'refundChannelCard_Bank\').style.borderColor=\'#00B14F\';[\'GCash\',\'Maya\'].forEach(function(c){document.getElementById(\'refundChannelCard_\'+c).style.background=\'var(--surface-container,#f4f6fb)\';document.getElementById(\'refundChannelCard_\'+c).style.borderColor=\'var(--border,#e5e7eb)\';});">' +
            '<div id="refundChannelCard_Bank" style="padding:10px 6px;border:2px solid var(--border,#e5e7eb);border-radius:10px;text-align:center;background:var(--surface-container,#f4f6fb);transition:all 0.2s;">' +
              '<i class="fas fa-university" style="color:#2563eb;font-size:1.1rem;display:block;margin-bottom:4px;"></i>' +
              '<span style="font-size:0.72rem;font-weight:700;color:var(--text-primary,#0f172a);">Bank</span>' +
            '</div>' +
          '</label>' +
        '</div>' +
      '</div>' +

      // Account name
      '<div style="margin-bottom:14px;">' +
        '<label style="font-size:0.75rem;font-weight:700;color:var(--text-muted,#94a3b8);text-transform:uppercase;letter-spacing:0.5px;display:block;margin-bottom:6px;">Account Name</label>' +
        '<input id="refundAcctName" type="text" placeholder="Full name on account" ' +
          'style="width:100%;padding:12px 14px;border:1.5px solid var(--border,#e5e7eb);border-radius:12px;font-size:0.9rem;background:var(--surface-container,#f4f6fb);color:var(--text-primary,#0f172a);outline:none;box-sizing:border-box;">' +
      '</div>' +

      // Account number
      '<div style="margin-bottom:14px;">' +
        '<label id="refundAcctLabel" style="font-size:0.75rem;font-weight:700;color:var(--text-muted,#94a3b8);text-transform:uppercase;letter-spacing:0.5px;display:block;margin-bottom:6px;">GCash / Maya / Account Number</label>' +
        '<input id="refundAcctNum" type="tel" placeholder="e.g. 09XX-XXX-XXXX" maxlength="11" ' +
      'oninput="this.value=this.value.replace(/[^0-9]/g,\'\').slice(0,11);" ' +
          'style="width:100%;padding:12px 14px;border:1.5px solid var(--border,#e5e7eb);border-radius:12px;font-size:0.9rem;background:var(--surface-container,#f4f6fb);color:var(--text-primary,#0f172a);outline:none;box-sizing:border-box;">' +
      '</div>' +

      // Notes
      '<div style="margin-bottom:20px;">' +
        '<label style="font-size:0.75rem;font-weight:700;color:var(--text-muted,#94a3b8);text-transform:uppercase;letter-spacing:0.5px;display:block;margin-bottom:6px;">Additional Notes <span style="font-weight:400;text-transform:none;">(optional)</span></label>' +
        '<textarea id="refundNotes" placeholder="e.g. Bank name, branch, etc." rows="2" ' +
          'style="width:100%;padding:12px 14px;border:1.5px solid var(--border,#e5e7eb);border-radius:12px;font-size:0.9rem;background:var(--surface-container,#f4f6fb);color:var(--text-primary,#0f172a);outline:none;resize:none;box-sizing:border-box;font-family:inherit;"></textarea>' +
      '</div>' +

      // Buttons
      '<div style="display:flex;gap:10px;">' +
        '<button onclick="document.getElementById(\'_refundDetailsModal\').remove();" ' +
          'style="flex:1;padding:13px;background:var(--surface-container,#f1f5f9);border:none;border-radius:12px;font-size:0.875rem;font-weight:700;color:var(--text-secondary,#475569);cursor:pointer;">Cancel</button>' +
        '<button onclick="_submitRefundDetails(' + bookingId + ');" ' +
          'style="flex:2;padding:13px;background:#f59e0b;border:none;border-radius:12px;font-size:0.875rem;font-weight:700;color:white;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;">' +
          '<i class="fas fa-paper-plane"></i> Submit Details</button>' +
      '</div>' +
    '</div>';

  document.body.appendChild(modal);
  // Close on backdrop tap
  modal.addEventListener('click', function(e) { if (e.target === modal) modal.remove(); });
}

function _submitRefundDetails(bookingId) {
  var channel = (document.querySelector('input[name="refundChannel"]:checked') || {}).value || '';
  var acctName = (document.getElementById('refundAcctName') || {}).value || '';
  var acctNum = (document.getElementById('refundAcctNum') || {}).value || '';
  var notes = (document.getElementById('refundNotes') || {}).value || '';

  if (!channel) { showToast('Please select a refund channel (GCash, Maya, or Bank).', 'error'); return; }
  if (!acctName.trim()) { showToast('Please enter your account name.', 'error'); return; }
  if (!acctNum.trim()) { showToast('Please enter your account number.', 'error'); return; }

  showLoading(true);
  apiCall('/bookings/' + bookingId + '/refund-details', {
    method: 'POST',
    body: JSON.stringify({
      user_id: currentUser.id,
      refund_channel: channel,
      refund_account_name: acctName.trim(),
      refund_account_number: acctNum.trim(),
      refund_notes: notes.trim()
    })
  })
    .then(function() {
      document.getElementById('_refundDetailsModal').remove();
      showToast('Refund details submitted! Our team will process it shortly.', 'success');
      loadBookings();
    })
    .catch(function(err) { showToast(err.message || 'Failed to submit. Please try again.', 'error'); })
    .finally(function() { showLoading(false); });
}

function promptCancelBooking(bookingId) {
  var reason = prompt('Please provide a reason for cancellation:');
  if (!reason) return;

  // Find booking data to compute 48h warning
  var b = null;
  for (var i = 0; i < _allBookingsData.length; i++) {
    if (_allBookingsData[i].id === bookingId) { b = _allBookingsData[i]; break; }
  }

  // Warn about 20% fee if < 48h before pickup
  if (b && b.start_date && (b.status === 'Confirmed' || b.status === 'Approved')) {
    var startRaw = _normDateStr(b.start_date);
    if (startRaw) {
      var parts = startRaw.split('-');
      var pickupDt = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]), 6, 0, 0);
      var hoursLeft = (pickupDt - new Date()) / (1000 * 60 * 60);
      var amountPaid = parseFloat(b.amount_paid || b.total_price || 0);
      if (hoursLeft < 48 && amountPaid > 0) {
        var fee = Math.round(amountPaid * 0.20 * 100) / 100;
        var refund = Math.round((amountPaid - fee) * 100) / 100;
        // Show custom cancellation policy modal instead of native confirm()
        _showCancelPolicyModal(fee, refund, bookingId, reason);
        return;
      }
    }
  }

  showLoading(true);
  apiCall('/cancel-booking', { method: 'POST', body: JSON.stringify({ booking_id: bookingId, user_id: currentUser.id, reason: reason }) })
    .then(function(data) {
      var msg = 'Booking cancelled.';
      if (data.refund_amount > 0) {
        msg = 'Booking cancelled. Refund of ' + formatPHP(data.refund_amount) + ' will be processed.';
        if (data.non_refundable_fee > 0) {
          msg += ' (' + formatPHP(data.non_refundable_fee) + ' non-refundable fee applied)';
        }
      }
      showToast(msg, 'success');
      NotifStore.add('Booking #' + bookingId + ' has been cancelled.');
      closeOverlay('page-booking-detail');
      loadBookings();
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
}

function openModifyBooking(bookingId, currentStart, currentEnd) {
  var el = document.getElementById('bookingDetailContent');
  if (!el) return;
  // Inject a modify form at the top of the detail content
  var formHtml =
    '<div class="page-header">' +
      '<button class="back-btn" onclick="openBookingDetail(' + bookingId + ')"><i class="fas fa-arrow-left"></i></button>' +
      '<h2>Modify Dates</h2>' +
    '</div>' +
    '<div class="scroll-content">' +
      '<div class="card">' +
        '<p style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:16px;">Select new rental dates. The price will be recalculated.</p>' +
        '<div class="form-group"><label>New Start Date</label><input type="date" id="modStart" value="' + currentStart + '"></div>' +
        '<div class="form-group"><label>New End Date</label><input type="date" id="modEnd" value="' + currentEnd + '"></div>' +
        '<span class="field-error" id="modErr" style="display:block;margin-bottom:12px;"></span>' +
        '<div id="modNewTotal" style="margin-bottom:14px;"></div>' +
        '<button class="btn-primary" onclick="submitModifyBooking(' + bookingId + ')"><i class="fas fa-check"></i> Confirm Changes</button>' +
      '</div>' +
    '</div>';
  el.innerHTML = formHtml;
  // Show new total preview when dates change
  ['modStart','modEnd'].forEach(function(id) {
    var inp = document.getElementById(id);
    if (inp) inp.addEventListener('change', function() { previewModifyTotal(bookingId); });
  });
}

function previewModifyTotal(bookingId) {
  var start = document.getElementById('modStart') ? document.getElementById('modStart').value : '';
  var end = document.getElementById('modEnd') ? document.getElementById('modEnd').value : '';
  var el = document.getElementById('modNewTotal');
  if (!el || !start || !end) return;
  var v = validateDateRange(start, end);
  if (!v.valid) { el.innerHTML = '<p style="color:var(--danger);font-size:0.82rem;">' + v.error + '</p>'; return; }
  el.innerHTML = '<p style="font-size:0.82rem;color:var(--text-muted);">Calculating new total...</p>';
  apiCall('/modify-booking', {
    method: 'POST',
    body: JSON.stringify({ booking_id: bookingId, user_id: currentUser.id, start_date: start, end_date: end, preview: true })
  }).then(function(data) {
    if (data.new_total !== undefined) {
      el.innerHTML = '<div class="price-row total"><span>New Total</span><span>' + formatPHP(data.new_total) + '</span></div>';
    }
  }).catch(function() { el.innerHTML = ''; });
}

function submitModifyBooking(bookingId) {
  var start = document.getElementById('modStart') ? document.getElementById('modStart').value : '';
  var end = document.getElementById('modEnd') ? document.getElementById('modEnd').value : '';
  var errEl = document.getElementById('modErr');
  if (errEl) errEl.textContent = '';
  var v = validateDateRange(start, end);
  if (!v.valid) { if (errEl) errEl.textContent = v.error; return; }
  showLoading(true);
  apiCall('/modify-booking', {
    method: 'POST',
    body: JSON.stringify({ booking_id: bookingId, user_id: currentUser.id, start_date: start, end_date: end })
  })
    .then(function(data) {
      showToast('Booking dates updated! New total: ' + formatPHP(data.new_total), 'success');
      closeOverlay('page-booking-detail');
      loadBookings();
    })
    .catch(function(err) { if (errEl) errEl.textContent = err.message; })
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
var _licenseFrontBlob = null;
var _licenseBackBlob = null;

var Profile = {
  enterEdit: function() {
    var card = document.getElementById('profileEditCard');
    if (card) card.style.display = '';
    var btn = document.getElementById('profileEditBtn');
    if (btn) btn.style.display = 'none';
  },
  cancelEdit: function() {
    var card = document.getElementById('profileEditCard');
    if (card) card.style.display = 'none';
    var btn = document.getElementById('profileEditBtn');
    if (btn) btn.style.display = '';
  },
  enterLicenseEdit: function() {
    document.getElementById('licenseViewMode').style.display = 'none';
    document.getElementById('licenseEditMode').style.display = '';
    document.getElementById('licenseEditBtn').style.display = 'none';
    _licenseFrontBlob = null;
    _licenseBackBlob = null;
    var prevF = document.getElementById('licenseEditPreviewFront');
    if (prevF) { prevF.src = ''; prevF.style.display = 'none'; }
    var prevB = document.getElementById('licenseEditPreviewBack');
    if (prevB) { prevB.src = ''; prevB.style.display = 'none'; }
    // Load existing data into edit fields
    loadLicenseDetailsForEdit();
  },
  cancelLicenseEdit: function() {
    document.getElementById('licenseViewMode').style.display = '';
    document.getElementById('licenseEditMode').style.display = 'none';
    document.getElementById('licenseEditBtn').style.display = '';
    _licenseFrontBlob = null;
    _licenseBackBlob = null;
  },
  saveLicenseInfo: function() {
    var errEl = document.getElementById('licenseEditErr');
    if (errEl) errEl.textContent = '';

    // Validate required fields
    var fields = {
      'editLicenseNumber': 'License Number',
      'editLicenseExpiry': 'Expiry Date',
      'editLicenseCountry': 'Country / State',
      'editLicenseClass': 'License Class',
      'editLicenseName': 'Full Name',
      'editLicenseDob': 'Date of Birth',
      'editLicenseEmName': 'Emergency Contact Name',
      'editLicenseEmPhone': 'Emergency Phone',
      'editLicenseEmRel': 'Relationship'
    };
    for (var fid in fields) {
      var val = (document.getElementById(fid).value || '').trim();
      if (!val) {
        if (errEl) errEl.textContent = fields[fid] + ' is required.';
        return;
      }
    }

    var fd = new FormData();
    fd.append('user_id', currentUser.id);
    fd.append('license_number', document.getElementById('editLicenseNumber').value.trim());
    fd.append('expiry_date', document.getElementById('editLicenseExpiry').value.trim());
    fd.append('issuing_country_state', document.getElementById('editLicenseCountry').value.trim());
    fd.append('license_class', document.getElementById('editLicenseClass').value.trim());
    fd.append('full_name', document.getElementById('editLicenseName').value.trim());
    fd.append('date_of_birth', document.getElementById('editLicenseDob').value.trim());
    fd.append('emergency_contact_name', document.getElementById('editLicenseEmName').value.trim());
    fd.append('emergency_contact_phone', document.getElementById('editLicenseEmPhone').value.trim());
    fd.append('emergency_contact_relationship', document.getElementById('editLicenseEmRel').value.trim());

    // Keep existing URLs if no new files uploaded
    if (_licenseFrontBlob) {
      fd.append('license_front_file', _licenseFrontBlob, 'front.jpg');
    } else {
      fd.append('license_front_url', currentUser._licenseDetails?.license_front_url || '');
    }
    if (_licenseBackBlob) {
      fd.append('license_back_file', _licenseBackBlob, 'back.jpg');
    } else {
      fd.append('license_back_url', currentUser._licenseDetails?.license_back_url || '');
    }

    showLoading(true);
    uploadFile('/user/license-details', fd)
      .then(function() {
        showToast('License details saved!', 'success');
        Profile.cancelLicenseEdit();
        loadProfile();
      })
      .catch(function(err) { if (errEl) errEl.textContent = err.message || 'Failed to save.'; })
      .finally(function() { showLoading(false); });
  }
};

function pickLicenseForProfile(side) {
  var inputId = side === 'back' ? 'licenseFileInputBack' : 'licenseFileInputFront';
  var el = document.getElementById(inputId);
  if (el) el.click();
}

function handleLicenseFileSelect(e, side) {
  var file = e.target.files[0];
  if (!file) return;
  var err = validateUploadFile(file);
  if (err) { var errEl = document.getElementById('licenseEditErr'); if (errEl) errEl.textContent = err; return; }
  if (side === 'front') {
    _licenseFrontBlob = file;
    var preview = document.getElementById('licenseEditPreviewFront');
    if (preview) { preview.src = URL.createObjectURL(file); preview.style.display = 'block'; }
  } else {
    _licenseBackBlob = file;
    var preview = document.getElementById('licenseEditPreviewBack');
    if (preview) { preview.src = URL.createObjectURL(file); preview.style.display = 'block'; }
  }
}

function loadLicenseDetailsForEdit() {
  if (!currentUser.id) return;
  apiCall('/user/license-details?user_id=' + currentUser.id)
    .then(function(data) {
      if (!data || !data.license_number) return;
      var el;
      el = document.getElementById('editLicenseNumber'); if (el) el.value = data.license_number || '';
      el = document.getElementById('editLicenseExpiry'); if (el) el.value = data.expiry_date || '';
      // For select dropdowns, try exact match first, then partial match
      el = document.getElementById('editLicenseCountry');
      if (el) {
        var countryVal = data.issuing_country_state || '';
        el.value = countryVal;
        if (!el.value && countryVal) {
          // Try partial match (e.g. "Ph" -> "Philippines")
          for (var i = 0; i < el.options.length; i++) {
            if (el.options[i].value.toLowerCase().startsWith(countryVal.toLowerCase())) {
              el.value = el.options[i].value; break;
            }
          }
        }
      }
      el = document.getElementById('editLicenseClass');
      if (el) {
        var classVal = data.license_class || '';
        el.value = classVal;
        if (!el.value && classVal) {
          // Try matching just the letter (e.g. "B" -> "B")
          for (var j = 0; j < el.options.length; j++) {
            if (el.options[j].value === classVal || el.options[j].value.startsWith(classVal + ' ')) {
              el.value = el.options[j].value; break;
            }
          }
        }
      }
      el = document.getElementById('editLicenseName'); if (el) el.value = data.full_name || '';
      el = document.getElementById('editLicenseDob'); if (el) el.value = data.date_of_birth || '';
      el = document.getElementById('editLicenseEmName'); if (el) el.value = data.emergency_contact_name || '';
      el = document.getElementById('editLicenseEmPhone'); if (el) el.value = data.emergency_contact_phone || '';
      el = document.getElementById('editLicenseEmRel');
      if (el) {
        var relVal = data.emergency_contact_relationship || '';
        el.value = relVal;
        if (!el.value && relVal) {
          for (var k = 0; k < el.options.length; k++) {
            if (el.options[k].value.toLowerCase() === relVal.toLowerCase()) {
              el.value = el.options[k].value; break;
            }
          }
        }
      }
      // Show existing images in preview
      if (data.license_front_url) {
        var prevF = document.getElementById('licenseEditPreviewFront');
        if (prevF) { prevF.src = data.license_front_url; prevF.style.display = 'block'; }
      }
      if (data.license_back_url) {
        var prevB = document.getElementById('licenseEditPreviewBack');
        if (prevB) { prevB.src = data.license_back_url; prevB.style.display = 'block'; }
      }
    })
    .catch(function() { /* ignore */ });
}

function loadProfile() {
  if (!currentUser.id) return;
    // Load main profile
  var profilePromise = apiCall('/user/profile-full?user_id=' + currentUser.id);
  // Load license details from new table
  var licensePromise = apiCall('/user/license-details?user_id=' + currentUser.id).catch(function() { return {}; });

  Promise.all([profilePromise, licensePromise])
    .then(function(results) {
      var profile = results[0];
      var licenseData = results[1] || {};

      // Store license details on currentUser for reference
      currentUser._licenseDetails = licenseData;

      var nameEl = document.getElementById('profileName');
      var emailEl = document.getElementById('profileEmail');
      var editNameEl = document.getElementById('editName');
      var editPhoneEl = document.getElementById('editPhone');
      var pointsEl = document.getElementById('profilePoints');
      if (nameEl) nameEl.textContent = profile.full_name || '';
      if (emailEl) emailEl.textContent = profile.email || '';
      if (editNameEl) editNameEl.value = profile.full_name || '';
      if (editPhoneEl) editPhoneEl.value = profile.phone || '';
      var editEmailEl = document.getElementById('editEmail');
      if (editEmailEl) editEmailEl.value = profile.email || '';
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
          if (placeholder) placeholder.textContent = (profile.full_name || '₱')[0].toUpperCase();
        }
      }

      // Phone and email display
      var phoneDisplay = document.getElementById('profilePhoneDisplay');
      if (phoneDisplay) phoneDisplay.textContent = profile.phone || 'Not set';
      var emailDisplay = document.getElementById('profileEmailDisplay');
      if (emailDisplay) emailDisplay.textContent = profile.email || '';

      // License images thumbnail (from new license_details table)
      var licenseThumb = document.getElementById('profileLicenseThumb');
      if (licenseThumb) {
        var html = '';
        if (licenseData.license_front_url) {
          html += '<div style="flex:1;"><p style="font-size:0.7rem;font-weight:700;color:var(--text-muted);margin-bottom:4px;">FRONT</p><img src="' + licenseData.license_front_url + '" style="width:100%;border-radius:var(--radius-sm);cursor:pointer;" onclick="viewLicenseImage(\'' + licenseData.license_front_url + '\')"></div>';
        }
        if (licenseData.license_back_url) {
          html += '<div style="flex:1;"><p style="font-size:0.7rem;font-weight:700;color:var(--text-muted);margin-bottom:4px;">BACK</p><img src="' + licenseData.license_back_url + '" style="width:100%;border-radius:var(--radius-sm);cursor:pointer;" onclick="viewLicenseImage(\'' + licenseData.license_back_url + '\')"></div>';
        }
        if (!html) {
          html = '<p style="font-size:0.8rem;color:var(--text-muted);margin-top:6px;">No license photos uploaded yet.</p>';
        }
        licenseThumb.innerHTML = html;
      }

      // License detail fields - view mode (from new license_details table)
      var el;
      el = document.getElementById('viewLicenseNumber');
      if (el) el.textContent = licenseData.license_number || '-';
      el = document.getElementById('viewLicenseExpiry');
      if (el) el.textContent = licenseData.expiry_date || '-';
      el = document.getElementById('viewLicenseClass');
      if (el) el.textContent = licenseData.license_class || '-';
      el = document.getElementById('viewLicenseCountry');
      if (el) el.textContent = licenseData.issuing_country_state || '-';
      el = document.getElementById('viewLicenseName');
      if (el) el.textContent = licenseData.full_name || '-';
      el = document.getElementById('viewLicenseDob');
      if (el) el.textContent = licenseData.date_of_birth || '-';
      el = document.getElementById('viewLicenseEmName');
      if (el) el.textContent = licenseData.emergency_contact_name || '-';
      el = document.getElementById('viewLicenseEmPhone');
      if (el) el.textContent = licenseData.emergency_contact_phone || '-';
      el = document.getElementById('viewLicenseEmRel');
      if (el) el.textContent = licenseData.emergency_contact_relationship || '-';
    })
    .catch(function(err) { showToast(err.message, 'error'); })
    .finally(function() { showLoading(false); });
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
  var emailEl = document.getElementById('editEmail');
  var phoneErrEl = document.getElementById('editPhoneErr');
  var emailErrEl = document.getElementById('editEmailErr');
  var name = nameEl ? sanitizeInput(nameEl.value.trim()) : '';
  var phone = phoneEl ? phoneEl.value.trim() : '';
  var email = emailEl ? emailEl.value.trim().toLowerCase() : '';
  if (phoneErrEl) phoneErrEl.textContent = '';
  if (emailErrEl) emailErrEl.textContent = '';
  if (phone && (!/^\d+$/.test(phone) || phone.length < 10 || phone.length > 11)) {
    if (phoneErrEl) phoneErrEl.textContent = 'Phone must be 10-11 digits.'; return;
  }
  if (email && !isGmailAddress(email)) {
    if (emailErrEl) emailErrEl.textContent = 'Only @gmail.com emails are allowed.'; return;
  }
  var fd = new FormData();
  fd.append('user_id', currentUser.id);
  fd.append('full_name', name);
  fd.append('phone', phone);
  if (email) fd.append('email', email);
  if (profilePicBlob) fd.append('profile_picture', profilePicBlob, 'avatar.jpg');
  showLoading(true);
  uploadFile('/update-profile', fd)
    .then(function() {
      currentUser.fullName = name;
      if (email) currentUser.email = email;
      Session.save(currentUser);
      showToast('Profile updated successfully!', 'success');
      Profile.cancelEdit();
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
      showLoading(false);
      // Force logout after upload Ã¯Â¿Â½ user must wait for admin verification before re-logging in
      showToast('License submitted! You have been logged out. Please wait for admin verification before logging in again.', 'info');
      setTimeout(function() {
        Session.clear();
        showPage('page-login');
      }, 2500);
    })
    .catch(function(err) {
      if (errEl) errEl.textContent = err.message;
      showLoading(false);
    });
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
            '<div class="vehicle-img-wrap"><img src="' + buildImgUrl(v.vehicle_image) + '" alt="' + v.brand + ' ' + v.model + '" onerror="this.onerror=null; this.src=\'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22400%22%20height%3D%22200%22%3E%3Crect%20width%3D%22400%22%20height%3D%22200%22%20fill%3D%22%23f3f4f6%22%2F%3E%3Ctext%20x%3D%22200%22%20y%3D%2285%22%20font-family%3D%22Arial%22%20font-size%3D%2240%22%20text-anchor%3D%22middle%22%20fill%3D%22%23d1d5db%22%3E%F0%9F%9A%97%3C%2Ftext%3E%3Ctext%20x%3D%22200%22%20y%3D%22130%22%20font-family%3D%22Arial%22%20font-size%3D%2214%22%20text-anchor%3D%22middle%22%20fill%3D%22%239ca3af%22%3ENo%20Image%3C%2Ftext%3E%3C%2Fsvg%3E\'"></div>' +
            '<div class="vehicle-info"><h3>' + v.brand + ' ' + v.model + '</h3>' +
            '<div class="vehicle-meta"><i class="fas fa-map-marker-alt"></i> ' + (v.location || '-') + '</div>' +
            '<div class="vehicle-rate">' + formatPHP(v.daily_rate) + ' <span>/ day</span></div></div></div>';
        }).join('') : '<div class="empty-state"><i class="fas fa-heart"></i><p>No favorites yet</p></div>') +
        '</div>';
    })
    .catch(function(err) { showToast(err.message, 'error'); })
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
function openNotificationsPage() {
    var overlay = document.getElementById('page-notifications');
    if (overlay) {
        overlay.classList.add('active');
        overlay.style.display = 'block';
    }
    var container = document.getElementById('notificationsContent');
    if (!container) return;

    // Render header immediately
    container.innerHTML =
        '<div class="page-header">' +
            '<button class="back-btn" onclick="closeOverlay(\'page-notifications\')"><i class="fas fa-arrow-left"></i></button>' +
            '<h2>Notifications</h2>' +
        '</div>' +
        '<div id="notifListBody" class="scroll-content" style="padding:16px;">' +
            '<div style="text-align:center;padding:40px;"><div class="spinner"></div></div>' +
        '</div>';

    var userId = currentUser.id;
    if (!userId) {
        document.getElementById('notifListBody').innerHTML =
            '<div class="empty-state"><i class="fas fa-bell-slash"></i><p>Please log in to view notifications</p></div>';
        return;
    }

    // Mark all as read
    apiCall('/notifications/read-all', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId })
    }).then(function() {
        notifList.forEach(function(n) { n.is_read = true; });
        updateNotifBadge();
    }).catch(function() {});

    // Load and render
    apiCall('/notifications?user_id=' + userId)
        .then(function(data) {
            notifList = Array.isArray(data) ? data : [];
            updateNotifBadge();
            var body = document.getElementById('notifListBody');
            if (!body) return;
            if (!notifList.length) {
                body.innerHTML = '<div class="empty-state"><i class="fas fa-bell-slash"></i><p>No notifications yet</p></div>';
                return;
            }
            body.innerHTML = notifList.map(function(n) {
                var unreadClass = n.is_read ? '' : ' unread';
                var ts = n.created_at ? new Date(n.created_at).toLocaleString() : '';
                var iconMap = {
                    booking_created: 'fa-calendar-check', booking_approved: 'fa-check-circle',
                    booking_rejected: 'fa-times-circle', booking_cancelled: 'fa-ban',
                    booking_cancelled_by_admin: 'fa-ban', booking_picked_up: 'fa-car',
                    booking_completed: 'fa-flag-checkered', booking_modified: 'fa-edit',
                    payment_confirmed: 'fa-credit-card', payment_downpayment: 'fa-credit-card',
                    payment_balance: 'fa-credit-card', payment_cash: 'fa-money-bill',
                    license_approved: 'fa-id-card', license_rejected: 'fa-id-card',
                    split_request: 'fa-users', split_paid: 'fa-users',
                    driver_approved: 'fa-car', driver_rejected: 'fa-car'
                };
                var icon = iconMap[n.type] || 'fa-bell';
                return '<div class="notif-item' + unreadClass + '" style="display:flex;gap:12px;align-items:flex-start;">' +
                    '<div style="width:36px;height:36px;border-radius:50%;background:rgba(230,57,70,0.12);display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px;">' +
                        '<i class="fas ' + icon + '" style="color:var(--primary);font-size:0.85rem;"></i>' +
                    '</div>' +
                    '<div style="flex:1;min-width:0;">' +
                        '<p style="font-weight:700;font-size:0.875rem;margin:0;">' + (n.title || '') + '</p>' +
                        '<p style="font-size:0.82rem;color:var(--text-secondary);margin:3px 0 0;">' + (n.message || '') + '</p>' +
                        '<small style="font-size:0.72rem;color:var(--text-muted);margin-top:4px;display:block;">' + ts + '</small>' +
                    '</div>' +
                '</div>';
            }).join('');
        })
        .catch(function() {
            var body = document.getElementById('notifListBody');
            if (body) body.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>Failed to load notifications</p></div>';
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

// ============================================================
// LIVE CHAT  (customer ? admin)
// ============================================================
// MORE PAGE
// ============================================================
function loadMorePage() {
  if (!currentUser.id) return;
}

// ============================================================
// LIVE CHAT  (customer ? admin)
// ============================================================
var LiveChat = (function () {
  var _pollTimer = null;
  var _currentAdminId = null;
  var _lastMsgId = 0;

  // ?? Inbox ??????????????????????????????????????????????????
  function loadInbox() {
    var el = document.getElementById('liveChatContent');
    if (!el) return;
    el.innerHTML =
      '<div class="page-header">' +
        '<button class="back-btn" onclick="closeOverlay(\'page-livechat\')"><i class="fas fa-arrow-left"></i></button>' +
        '<h2>Live Chat</h2>' +
      '</div>' +
      '<div id="liveChatInboxBody" class="scroll-content" style="padding:16px;">' +
        '<div style="text-align:center;padding:40px;"><div class="spinner"></div></div>' +
      '</div>';

    apiCall('/chat/admins?user_id=' + (currentUser.id || ''))
      .then(function (admins) {
        var body = document.getElementById('liveChatInboxBody');
        if (!body) return;

        if (!admins || !admins.length) {
          // Default to admin_id=20 if no admins returned
          console.log('[LiveChat] No admins returned, using default admin_id=20');
          admins = [{ id: 20, username: 'Support Team' }];
        }

        // Single admin: skip inbox, go straight to chat
        if (admins.length === 1) {
          openConversation(admins[0].id, admins[0].username);
          return;
        }

        body.innerHTML =
          '<p style="font-size:0.82rem;color:var(--text-secondary);margin-bottom:14px;">Choose a support agent:</p>' +
          admins.map(function (a) {
            return '<div class="chat-inbox-item" onclick="LiveChat.openConversation(' + a.id + ',\'' + escapeHtml(a.username) + '\')">' +
              '<div class="chat-inbox-avatar"><i class="fas fa-headset"></i></div>' +
              '<div class="chat-inbox-info">' +
                '<div class="chat-inbox-name">' + escapeHtml(a.username) + '</div>' +
                '<div class="chat-inbox-preview">Tap to start chatting</div>' +
              '</div>' +
              '<i class="fas fa-chevron-right" style="color:var(--text-muted);"></i>' +
            '</div>';
          }).join('');
      })
      .catch(function (err) {
        console.error('[LiveChat] Error loading admins:', err);
        // Fallback to admin_id=20 on error
        openConversation(20, 'Support Team');
      });
  }

  // ?? Conversation ???????????????????????????????????????????
  function openConversation(adminId, adminName) {
    _currentAdminId = adminId;
    _lastMsgId = 0;
    stopPolling();

    var el = document.getElementById('liveChatContent');
    if (!el) return;
    el.innerHTML =
      '<div class="page-header">' +
        '<button class="back-btn" onclick="LiveChat.backToInbox()"><i class="fas fa-arrow-left"></i></button>' +
        '<h2>' + escapeHtml(adminName) + '</h2>' +
      '</div>' +
      '<div id="lcMessages" style="flex:1;overflow-y:auto;padding:14px 16px;display:flex;flex-direction:column;gap:10px;height:calc(100vh - 180px);"></div>' +
      '<div class="chat-input-row">' +
        '<input type="text" id="lcInput" placeholder="Type a message..." onkeydown="if(event.key===\'Enter\')LiveChat.send()">' +
        '<button onclick="LiveChat.send()"><i class="fas fa-paper-plane"></i></button>' +
      '</div>';

    apiCall('/chat/mark-read', {
      method: 'POST',
      body: JSON.stringify({ receiver_type: 'user', receiver_id: currentUser.id, sender_type: 'admin', sender_id: adminId })
    }).catch(function () {});

    fetchMessages(true);
    _pollTimer = setInterval(function () { fetchMessages(false); }, 2000);
  }

  function fetchMessages(initial) {
    if (!_currentAdminId || !currentUser.id) return;
    console.log('[LiveChat] Fetching messages: user_id=' + currentUser.id + ', admin_id=' + _currentAdminId);
    apiCall('/chat/messages?user_id=' + currentUser.id + '&admin_id=' + _currentAdminId + '&limit=100')
      .then(function (msgs) {
        console.log('[LiveChat] Received ' + (msgs ? msgs.length : 0) + ' messages');
        if (msgs && msgs.length > 0) {
          console.log('[LiveChat] First message:', JSON.stringify(msgs[0]));
          console.log('[LiveChat] Last message:', JSON.stringify(msgs[msgs.length - 1]));
        }
        
        var container = document.getElementById('lcMessages');
        if (!container) return;
        if (!msgs || !msgs.length) {
          if (initial) container.innerHTML =
            '<div style="text-align:center;color:var(--text-muted);font-size:0.85rem;padding:30px;">No messages yet. Say hello!</div>';
          return;
        }
        var latestId = msgs[msgs.length - 1].id;
        console.log('[LiveChat] Latest ID: ' + latestId + ', Last ID: ' + _lastMsgId);
        if (String(latestId) === String(_lastMsgId) && !initial) {
          console.log('[LiveChat] Skipping update - same message ID');
          return;
        }

        // Detect new message from admin (not from us)
        var lastMsg = msgs[msgs.length - 1];
        var isNewFromAdmin = !initial && String(latestId) !== String(_lastMsgId) && lastMsg.sender_type === 'admin';
        _lastMsgId = latestId;

        // Show pop-up banner if chat overlay is not focused
        if (isNewFromAdmin) {
          showChatPopup('Support Team', lastMsg.message);
        }

        var atBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 80;
        console.log('[LiveChat] Rendering ' + msgs.length + ' messages');
        container.innerHTML = msgs.map(function (m) {
          var isMe = m.sender_type === 'user';
          var ts = m.created_at ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
          if (isMe) {
            return '<div style="display:flex;justify-content:flex-end;">' +
              '<div style="max-width:78%;background:var(--primary);color:var(--text-primary);padding:10px 14px;border-radius:18px 18px 4px 18px;font-size:0.875rem;line-height:1.4;">' +
                escapeHtml(m.message) +
                '<div style="font-size:0.62rem;color:rgba(255,255,255,0.6);margin-top:3px;text-align:right;">' + ts + '</div>' +
              '</div>' +
            '</div>';
          } else {
            return '<div style="display:flex;justify-content:flex-start;">' +
              '<div style="max-width:78%;background:var(--bg-card);color:var(--text-primary);padding:10px 14px;border-radius:18px 18px 18px 4px;font-size:0.875rem;line-height:1.4;box-shadow:var(--shadow-card);">' +
                escapeHtml(m.message) +
                '<div style="font-size:0.62rem;color:var(--text-muted);margin-top:3px;">' + ts + '</div>' +
              '</div>' +
            '</div>';
          }
        }).join('');

        if (initial || atBottom) container.scrollTop = container.scrollHeight;

        apiCall('/chat/mark-read', {
          method: 'POST',
          body: JSON.stringify({ receiver_type: 'user', receiver_id: currentUser.id, sender_type: 'admin', sender_id: _currentAdminId })
        }).catch(function () {});
      })
      .catch(function (err) {
        console.error('[LiveChat] Error fetching messages:', err);
      });
  }

  function send() {
    var inputEl = document.getElementById('lcInput');
    if (!inputEl) return;
    var msg = (inputEl.value || '').trim();
    if (!msg || !_currentAdminId || !currentUser.id) return;
    inputEl.value = '';
    inputEl.disabled = true;

    apiCall('/chat/send', {
      method: 'POST',
      body: JSON.stringify({
        sender_type: 'user',
        sender_id: currentUser.id,
        receiver_type: 'admin',
        receiver_id: _currentAdminId,
        message: msg
      })
    })
      .then(function () { 
        // Force refresh by resetting _lastMsgId
        _lastMsgId = null;
        fetchMessages(false); 
      })
      .catch(function (err) { showToast(err.message || 'Failed to send', 'error'); })
      .finally(function () { if (inputEl) inputEl.disabled = false; });
  }

  function backToInbox() {
    stopPolling();
    _currentAdminId = null;
    loadInbox();
  }

  function stopPolling() {
    if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
  }

  return {
    loadInbox: loadInbox,
    openConversation: openConversation,
    send: send,
    backToInbox: backToInbox,
    stopPolling: stopPolling
  };
})();

function loadLiveChat() {
  LiveChat.loadInbox();
}

// Chat pop-up banner (shows even when chat overlay is closed)
function showChatPopup(senderName, message) {
  var existing = document.getElementById('chatPopupBanner');
  if (existing) existing.remove();
  var banner = document.createElement('div');
  banner.id = 'chatPopupBanner';
  banner.style.cssText = 'position:fixed;top:16px;left:16px;right:16px;z-index:9998;background:var(--primary);color:#fff;border-radius:16px;padding:14px 16px;box-shadow:0 8px 24px rgba(0,0,0,0.3);display:flex;align-items:center;gap:12px;cursor:pointer;animation:slideDown 0.3s ease;';
  banner.innerHTML =
    '<div style="width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,0.2);display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="fas fa-comments" style="font-size:1rem;"></i></div>' +
    '<div style="flex:1;min-width:0;">' +
      '<div style="font-size:0.78rem;font-weight:700;opacity:0.85;">' + escapeHtml(senderName) + '</div>' +
      '<div style="font-size:0.85rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + escapeHtml(message) + '</div>' +
    '</div>' +
    '<button onclick="document.getElementById(\'chatPopupBanner\').remove()" style="background:rgba(255,255,255,0.2);border:none;color:#fff;width:28px;height:28px;border-radius:50%;cursor:pointer;font-size:0.8rem;flex-shrink:0;">x</button>';
  banner.onclick = function(e) {
    if (e.target.tagName === 'BUTTON') return;
    banner.remove();
    showOverlay('page-livechat');
  };
  document.body.appendChild(banner);
  // Auto-dismiss after 5s
  setTimeout(function() { if (banner.parentNode) banner.remove(); }, 5000);
}

// Background chat polling - checks for new messages even when chat is closed
var _bgChatPollTimer = null;
var _bgChatLastId = 0;

function startBgChatPolling() {
  if (_bgChatPollTimer) return;
  _bgChatPollTimer = setInterval(function() {
    if (!currentUser.id) return;
    // Only poll if chat overlay is NOT open
    var chatOverlay = document.getElementById('page-livechat');
    if (chatOverlay && chatOverlay.classList.contains('active')) return;
    apiCall('/chat/inbox?viewer_type=user&viewer_id=' + currentUser.id)
      .then(function(data) {
        if (!Array.isArray(data) || !data.length) return;
        var totalUnread = 0;
        data.forEach(function(c) { totalUnread += parseInt(c.unread_count) || 0; });
        if (totalUnread > 0) {
          // Find the conversation with unread messages and get latest
          var conv = data.find(function(c) { return parseInt(c.unread_count) > 0; });
          if (conv && conv.last_message) {
            var msgId = conv.last_at || '';
            if (msgId !== _bgChatLastId) {
              _bgChatLastId = msgId;
              showChatPopup(conv.other_name || 'Support Team', conv.last_message);
            }
          }
        }
        updateChatUnreadBadge();
      })
      .catch(function() {});
  }, 10000); // Check every 10s in background
}

function stopBgChatPolling() {
  if (_bgChatPollTimer) { clearInterval(_bgChatPollTimer); _bgChatPollTimer = null; }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}



