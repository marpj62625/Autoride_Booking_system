# -*- coding: utf-8 -*-
with open('customer_mobile/www/js/app.js', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# ?? 1. Add BookingSession object after Session object ??
session_end = content.find('\n};', content.find('var Session = {')) + 3

booking_session_code = """

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
"""

content = content[:session_end] + booking_session_code + content[session_end:]
print('Step 1: BookingSession object added')

# ?? 2. Hook into showPage() to save session before navigating away ??
old_show_page_start = 'function showPage(id) {\n  // Close ALL overlays first'
new_show_page_start = ('function showPage(id) {\n'
    '  // Save booking session if user navigates away mid-booking\n'
    '  BookingSession.save();\n'
    '\n'
    '  // Close ALL overlays first')

if old_show_page_start in content:
    content = content.replace(old_show_page_start, new_show_page_start, 1)
    print('Step 2: showPage() now saves session before navigating')
else:
    print('Step 2: showPage pattern not found')

# ?? 3. Restore session when user navigates to page-vehicles or page-bookings ??
old_load_vehicles = '  if (id === \'page-home\') loadHome();\n  if (id === \'page-vehicles\') loadVehicles();\n  if (id === \'page-bookings\') loadBookings();'
new_load_vehicles = ('  if (id === \'page-home\') loadHome();\n'
    '  if (id === \'page-vehicles\') {\n'
    '    // Check for saved booking session (1-min TTL)\n'
    '    var restored = BookingSession.restore();\n'
    '    if (!restored) loadVehicles();\n'
    '  }\n'
    '  if (id === \'page-bookings\') {\n'
    '    // Check for saved payment session (1-min TTL)\n'
    '    var paySession = BookingSession.load();\n'
    '    if (paySession && paySession.overlays && paySession.overlays.payment) {\n'
    '      BookingSession.restore();\n'
    '    } else {\n'
    '      loadBookings();\n'
    '    }\n'
    '  }')

if old_load_vehicles in content:
    content = content.replace(old_load_vehicles, new_load_vehicles, 1)
    print('Step 3: Session restore hooked into page navigation')
else:
    print('Step 3: load hooks pattern not found')

# ?? 4. Clear session after successful booking and payment ??
old_confirm = ('  apiCall(\'/book\', { method: \'POST\', body: JSON.stringify(_pendingBookingPayload) })\n'
    '    .then(function(data) {\n'
    '      activeBookingId = data.booking_id;\n'
    '      closeOverlay(\'page-booking-form\');\n'
    '      closeOverlay(\'page-vehicle-detail\');\n'
    '      NotifStore.add(\'Booking #\' + data.booking_id + \' received! Our team will review it shortly.\');\n'
    '      openPaymentScreen(data.booking_id, _pendingPriceResult, _pendingPayType);\n'
    '    })')

new_confirm = ('  apiCall(\'/book\', { method: \'POST\', body: JSON.stringify(_pendingBookingPayload) })\n'
    '    .then(function(data) {\n'
    '      activeBookingId = data.booking_id;\n'
    '      BookingSession.clear(); // booking submitted - clear any stale session\n'
    '      closeOverlay(\'page-booking-form\');\n'
    '      closeOverlay(\'page-vehicle-detail\');\n'
    '      NotifStore.add(\'Booking #\' + data.booking_id + \' received! Our team will review it shortly.\');\n'
    '      openPaymentScreen(data.booking_id, _pendingPriceResult, _pendingPayType);\n'
    '    })')

if old_confirm in content:
    content = content.replace(old_confirm, new_confirm, 1)
    print('Step 4: Session cleared after booking submitted')
else:
    print('Step 4: confirmAndBook pattern not found')

# ?? 5. Clear session after payment completes ??
old_cash_success = ('        closeOverlay(\'page-payment\');\n'
    '        NotifStore.add(\'Booking #\' + bookingId + \' received! Pay at our office upon pickup.\');\n'
    '        showReceipt(bookingId, data, amount, \'Cash (Over the counter)\', ref);')
new_cash_success = ('        BookingSession.clear();\n'
    '        closeOverlay(\'page-payment\');\n'
    '        NotifStore.add(\'Booking #\' + bookingId + \' received! Pay at our office upon pickup.\');\n'
    '        showReceipt(bookingId, data, amount, \'Cash (Over the counter)\', ref);')
if old_cash_success in content:
    content = content.replace(old_cash_success, new_cash_success, 1)
    print('Step 5: Session cleared after cash payment')
else:
    print('Step 5: cash payment success pattern not found')

old_online_success = ('        closeOverlay(\'page-payment\');\n'
    '        showToast(\'Payment confirmed! Booking #\' + bookingId + \' is now active.\', \'success\');')
new_online_success = ('        BookingSession.clear();\n'
    '        closeOverlay(\'page-payment\');\n'
    '        showToast(\'Payment confirmed! Booking #\' + bookingId + \' is now active.\', \'success\');')
if old_online_success in content:
    content = content.replace(old_online_success, new_online_success, 1)
    print('Step 5b: Session cleared after online payment confirmed')
else:
    print('Step 5b: online payment success pattern not found')

with open('customer_mobile/www/js/app.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print('\nAll changes saved to app.js')
