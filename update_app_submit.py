import re

with open('customer_mobile/www/js/app.js', 'r', encoding='latin-1') as f:
    content = f.read()

submit_old = '''function submitPayment(bookingId, amount) {
  var methodEl = document.getElementById('payMethod');
  var method = methodEl ? methodEl.value : 'gcash';
  var errEl = document.getElementById('payErr');
  if (errEl) errEl.textContent = '';

  // Cash payment  use existing manual flow
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

  // Online payment  redirect to PayMongo
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
}'''

submit_new = '''function submitPayment(bookingId, amount) {
  var methodEl = document.getElementById('payMethod');
  var method = methodEl ? methodEl.value : 'gcash';
  var errEl = document.getElementById('payErr');
  if (errEl) errEl.textContent = '';

  showLoading(true);
  
  // 1. Update booking price with any add-on changes
  apiCall('/bookings/' + bookingId + '/update-price', {
    method: 'POST',
    body: JSON.stringify({
      addons: _pendingBookingPayload.addons,
      addon_price: _pendingBookingPayload.addon_price,
      total_price: _pendingBookingPayload.total_price,
      amount_paid: _pendingPayType === 'Downpayment' ? _pendingPriceResult.downpaymentAmount : _pendingPriceResult.total,
      balance_amount: _pendingPayType === 'Downpayment' ? _pendingPriceResult.balanceAmount : 0
    })
  }).then(function() {
    proceedWithPaymentSubmission(bookingId, amount, method, errEl);
  }).catch(function(err) {
    showLoading(false);
    if (errEl) errEl.textContent = err.message || 'Failed to update booking. Please try again.';
  });
}

function proceedWithPaymentSubmission(bookingId, amount, method, errEl) {
  // Cash payment - use existing manual flow
  if (method === 'cash') {
    var refEl = document.getElementById('payRef');
    var ref = refEl ? sanitizeInput(refEl.value.trim()) : '';
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

  // Online payment - redirect to PayMongo
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
}'''

content = content.replace(submit_old, submit_new)

with open('customer_mobile/www/js/app.js', 'w', encoding='latin-1') as f:
    f.write(content)
print('Done frontend submit updates')
