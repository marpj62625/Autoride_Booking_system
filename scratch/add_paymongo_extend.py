# -*- coding: utf-8 -*-
with open('customer_mobile/www/js/app.js', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find the exact text in submitExtension to insert before
marker = (
    "  var method = (document.getElementById('extMethod') || {}).value || 'cash';\n"
    "  var ref = (document.getElementById('extRef') || {}).value || '';\n"
    "  var methodLabel = method === 'gcash' ? 'GCash' : method === 'maya' ? 'Maya' : 'Cash (Over the counter)';\n"
    "\n"
    "  showLoading(true);\n"
    "\n"
    "  var fd = new FormData();"
)

idx_fn = content.find('function submitExtension(')
idx_marker = content.find(marker, idx_fn)
if idx_marker < 0:
    print('ERROR: marker not found')
    exit(1)

new_block = (
    "  var method = (document.getElementById('extMethod') || {}).value || 'cash';\n"
    "  var ref = (document.getElementById('extRef') || {}).value || '';\n"
    "  var methodLabel = method === 'gcash' ? 'GCash' : method === 'maya' ? 'Maya' : 'Cash (Over the counter)';\n"
    "\n"
    "  // PayMongo for GCash / Maya\n"
    "  if (method === 'gcash' || method === 'maya') {\n"
    "    showLoading(true);\n"
    "    apiCall('/paymongo/create-payment', {\n"
    "      method: 'POST',\n"
    "      body: JSON.stringify({\n"
    "        booking_id: bookingId,\n"
    "        amount: price,\n"
    "        method: method,\n"
    "        description: 'Booking #' + bookingId + ' extension (' + days + ' day' + (days !== 1 ? 's' : '') + ')',\n"
    "        customer_name: currentUser.fullName || '',\n"
    "        customer_email: currentUser.email || ''\n"
    "      })\n"
    "    }).then(function(data) {\n"
    "      showLoading(false);\n"
    "      if (data.checkout_url) {\n"
    "        if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Browser) {\n"
    "          window.Capacitor.Plugins.Browser.open({ url: data.checkout_url });\n"
    "        } else {\n"
    "          window.open(data.checkout_url, '_blank');\n"
    "        }\n"
    "        _showExtPaymentWaiting(bookingId, newEnd, price, methodLabel, days);\n"
    "      } else {\n"
    "        if (errEl) errEl.textContent = data.error || 'Failed to create payment. Please try again.';\n"
    "      }\n"
    "    }).catch(function(err) {\n"
    "      showLoading(false);\n"
    "      if (errEl) errEl.textContent = err.message || 'Payment failed. Please try again.';\n"
    "    });\n"
    "    return;\n"
    "  }\n"
    "\n"
    "  showLoading(true);\n"
    "\n"
    "  var fd = new FormData();"
)

content = content[:idx_marker] + new_block + content[idx_marker + len(marker):]
print('Step 1: PayMongo block inserted into submitExtension')

# Now add the _showExtPaymentWaiting helper function after submitExtension
insert_before = 'function pickExtProof() {'
idx_insert = content.find(insert_before)
if idx_insert < 0:
    print('ERROR: _extProofBlob not found')
    exit(1)

waiting_fn = (
    "function _showExtPaymentWaiting(bookingId, newEnd, price, methodLabel, days) {\n"
    "  var container = document.getElementById('bookingDetailContent');\n"
    "  if (!container) return;\n"
    "  var parts = [];\n"
    "  parts.push('<div class=\"page-header\">');\n"
    "  parts.push('<h2 style=\"text-align:center;flex:1;\">Waiting for Payment</h2>');\n"
    "  parts.push('</div>');\n"
    "  parts.push('<div class=\"scroll-content\" style=\"padding:20px;text-align:center;padding-top:40px;\">');\n"
    "  parts.push('<div style=\"width:80px;height:80px;border-radius:50%;background:rgba(0,177,79,0.1);display:flex;align-items:center;justify-content:center;margin:0 auto 20px;\">');\n"
    "  parts.push('<i class=\"fas fa-spinner fa-spin\" style=\"font-size:2rem;color:var(--primary);\"></i></div>');\n"
    "  parts.push('<h3 style=\"font-size:1.1rem;font-weight:800;margin-bottom:8px;\">Complete Payment in ' + methodLabel + '</h3>');\n"
    "  parts.push('<p style=\"color:var(--text-secondary);font-size:0.875rem;margin-bottom:24px;\">Complete your payment in ' + methodLabel + ', then return here.</p>');\n"
    "  parts.push('<div style=\"background:var(--bg-card);border-radius:12px;padding:16px;margin-bottom:24px;\">');\n"
    "  parts.push('<div style=\"font-size:0.75rem;color:var(--text-secondary);\">' + days + '-day extension fee</div>');\n"
    "  parts.push('<div style=\"font-size:1.4rem;font-weight:900;color:var(--primary);\">' + formatPHP(price) + '</div></div>');\n"
    "  parts.push('<button class=\"btn-primary\" style=\"margin-bottom:12px;\" onclick=\"_checkExtPayment(' + bookingId + ',\\'' + newEnd + '\\',' + price + ',\\'' + methodLabel + '\\',' + days + ')\"><i class=\"fas fa-check-circle\"></i> I\\'ve Completed Payment</button>');\n"
    "  parts.push('<button class=\"btn-secondary\" onclick=\"closeOverlay(\\'page-booking-detail\\')\" style=\"width:100%;\">Cancel</button>');\n"
    "  parts.push('</div>');\n"
    "  container.innerHTML = parts.join('');\n"
    "}\n"
    "\n"
    "function _checkExtPayment(bookingId, newEnd, price, methodLabel, days) {\n"
    "  showLoading(true);\n"
    "  if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Browser) {\n"
    "    window.Capacitor.Plugins.Browser.close().catch(function() {});\n"
    "  }\n"
    "  apiCall('/paymongo/status/' + bookingId)\n"
    "    .then(function(data) {\n"
    "      showLoading(false);\n"
    "      if (data.paid) {\n"
    "        // Payment confirmed - now submit extension request\n"
    "        var fd = new FormData();\n"
    "        fd.append('new_end_date', newEnd);\n"
    "        fd.append('extension_price', price);\n"
    "        fd.append('payment_method', methodLabel);\n"
    "        fd.append('reference_number', '');\n"
    "        fetch(API_BASE + '/bookings/' + bookingId + '/extend', { method: 'POST', body: fd })\n"
    "          .then(function(r) { return r.json(); })\n"
    "          .then(function(extData) {\n"
    "            if (extData.error) { showToast(extData.error, 'error'); return; }\n"
    "            closeOverlay('page-booking-detail');\n"
    "            showToast('Extension request submitted! Awaiting admin approval.', 'success');\n"
    "            NotifStore.add('Extension request for Booking #' + bookingId + ' submitted.');\n"
    "            loadBookings();\n"
    "          }).catch(function() { showToast('Payment confirmed but extension submission failed. Please contact support.', 'error'); });\n"
    "      } else {\n"
    "        showToast('Payment not yet confirmed. Please wait and try again.', 'info');\n"
    "      }\n"
    "    }).catch(function() {\n"
    "      showLoading(false);\n"
    "      showToast('Could not verify payment. Please check your bookings.', 'error');\n"
    "    });\n"
    "}\n"
    "\n"
)

content = content[:idx_insert] + waiting_fn + content[idx_insert:]
print('Step 2: _showExtPaymentWaiting and _checkExtPayment added')

with open('customer_mobile/www/js/app.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print('Saved')
