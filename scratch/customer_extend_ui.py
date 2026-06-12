# -*- coding: utf-8 -*-
with open('customer_mobile/www/js/app.js', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# ?? 1. Add Extend button to active rental card on Home page ??
# Find the two grid cells (Start Date / Booking #) and add buttons below them
old_home_grid = (
    "            '<div style=\"display:grid;grid-template-columns:1fr 1fr;gap:8px;\">' +\n"
    "              '<div style=\"background:var(--bg-card2);border-radius:12px;padding:10px;\">' +\n"
    "                '<div style=\"font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:3px;\">Start Date</div>' +\n"
    "                '<div style=\"font-size:0.82rem;font-weight:700;color:var(--text-primary);\">' + _fmtDate(startNorm) + '</div>' +\n"
    "              '</div>' +\n"
    "              '<div style=\"background:var(--bg-card2);border-radius:12px;padding:10px;\">' +\n"
    "                '<div style=\"font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:3px;\">Booking #</div>' +\n"
    "                '<div style=\"font-size:0.82rem;font-weight:700;color:var(--text-primary);\">' + active.id + '</div>' +\n"
    "              '</div>' +\n"
    "            '</div>' +"
)

new_home_grid = (
    "            '<div style=\"display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;\">' +\n"
    "              '<div style=\"background:var(--bg-card2);border-radius:12px;padding:10px;\">' +\n"
    "                '<div style=\"font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:3px;\">Start Date</div>' +\n"
    "                '<div style=\"font-size:0.82rem;font-weight:700;color:var(--text-primary);\">' + _fmtDate(startNorm) + '</div>' +\n"
    "              '</div>' +\n"
    "              '<div style=\"background:var(--bg-card2);border-radius:12px;padding:10px;\">' +\n"
    "                '<div style=\"font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:3px;\">Booking #</div>' +\n"
    "                '<div style=\"font-size:0.82rem;font-weight:700;color:var(--text-primary);\">' + active.id + '</div>' +\n"
    "              '</div>' +\n"
    "            '</div>' +\n"
    "            '<div style=\"display:grid;grid-template-columns:1fr 1fr;gap:8px;\">' +\n"
    "              '<button onclick=\"openExtendBooking(' + active.id + ',\\'' + endNorm + '\\',\\'' + (active.daily_rate||0) + '\\')\" style=\"padding:10px;background:var(--primary);color:#fff;border:none;border-radius:12px;font-size:0.78rem;font-weight:700;cursor:pointer;\"><i class=\"fas fa-calendar-plus\" style=\"margin-right:5px;\"></i>Extend</button>' +\n"
    "              '<button onclick=\"showOverlay(\\'page-livechat\\')\" style=\"padding:10px;background:var(--bg-card2);color:var(--text-primary);border:1px solid var(--border);border-radius:12px;font-size:0.78rem;font-weight:700;cursor:pointer;\"><i class=\"fas fa-comments\" style=\"margin-right:5px;\"></i>Chat</button>' +\n"
    "            '</div>' +"
)

if old_home_grid in content:
    content = content.replace(old_home_grid, new_home_grid, 1)
    print('Step 1 done: Home active card buttons added')
else:
    print('Step 1: pattern not found')

# ?? 2. Add Extend button in renderBookingDetail for Picked Up bookings ??
old_primary = (
    "  if (canPayBalance) {\n"
    "    primaryAction = '<button class=\"btn-primary\" style=\"margin-bottom:12px;\" onclick=\"openPayBalanceScreen(' + b.id + ',' + b.balance_amount + ')\"><i class=\"fas fa-money-bill\"></i> Pay Balance (' + formatPHP(b.balance_amount) + ')</button>';\n"
    "  } else if (canReview) {\n"
    "    primaryAction = '<button class=\"btn-primary\" style=\"margin-bottom:12px;\" onclick=\"openReviewForm(' + b.vehicle_id + ')\"><i class=\"fas fa-star\"></i> Leave a Review</button>';\n"
    "  }"
)
new_primary = (
    "  var canExtend = (b.status === 'Picked Up' || b.status === 'Ongoing');\n"
    "  if (canPayBalance) {\n"
    "    primaryAction = '<button class=\"btn-primary\" style=\"margin-bottom:12px;\" onclick=\"openPayBalanceScreen(' + b.id + ',' + b.balance_amount + ')\"><i class=\"fas fa-money-bill\"></i> Pay Balance (' + formatPHP(b.balance_amount) + ')</button>';\n"
    "  } else if (canReview) {\n"
    "    primaryAction = '<button class=\"btn-primary\" style=\"margin-bottom:12px;\" onclick=\"openReviewForm(' + b.vehicle_id + ')\"><i class=\"fas fa-star\"></i> Leave a Review</button>';\n"
    "  }\n"
    "  if (canExtend) {\n"
    "    primaryAction += '<button class=\"btn-primary\" style=\"margin-bottom:12px;background:linear-gradient(135deg,#00b14f,#059669);\" onclick=\"openExtendBooking(' + b.id + ',\\'' + (b.end_date||'').split('T')[0] + '\\',\\'' + (b.daily_rate||0) + '\\')\">' +\n"
    "      '<i class=\"fas fa-calendar-plus\" style=\"margin-right:6px;\"></i> Extend Booking</button>';\n"
    "  }"
)

if old_primary in content:
    content = content.replace(old_primary, new_primary, 1)
    print('Step 2 done: Extend button in booking detail')
else:
    print('Step 2: pattern not found')

# ?? 3. Add openExtendBooking function and submitExtension ??
# Insert after renderBookingDetail's closing lines, before loadInspectionsForDetail
insert_before_fn = 'function loadInspectionsForDetail(bookingId) {'
extend_fn = '''function openExtendBooking(bookingId, currentEndDate, dailyRate) {
  var el = document.getElementById('bookingDetailContent');
  if (!el) {
    // Fallback - open a simple modal
    var modal = document.createElement('div');
    modal.id = 'extendModal';
    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.75);z-index:9999;display:flex;align-items:flex-end;justify-content:center;';
    document.body.appendChild(modal);
    _renderExtendForm(modal, bookingId, currentEndDate, dailyRate, true);
    return;
  }
  // Replace page-booking-detail content with the extend form
  var prev = el.innerHTML;
  _renderExtendForm(el, bookingId, currentEndDate, dailyRate, false, prev);
}

function _renderExtendForm(container, bookingId, currentEndDate, dailyRate, isModal, prevHtml) {
  var rate = parseFloat(dailyRate) || 0;
  var today = new Date().toISOString().split('T')[0];
  // Min new end date = currentEndDate + 1 day
  var minDate = currentEndDate;
  try {
    var d = new Date(currentEndDate + 'T00:00:00');
    d.setDate(d.getDate() + 1);
    minDate = d.toISOString().split('T')[0];
  } catch(e) {}

  var backBtn = isModal
    ? '<button onclick="document.getElementById(\\'extendModal\\').remove()" style="background:none;border:none;color:white;font-size:1.2rem;padding:4px;"><i class=\\"fas fa-times\\"></i></button>'
    : '<button onclick="closeOverlay(\\'page-booking-detail\\')" style="background:none;border:none;color:var(--text-primary);font-size:1.1rem;padding:4px;"><i class=\\"fas fa-arrow-left\\"></i></button>';

  var html =
    '<div class="page-header">' +
      (isModal ? '' : '<button class="back-btn" onclick="closeOverlay(\'page-booking-detail\')"><i class="fas fa-arrow-left"></i></button>') +
      '<h2 style="text-align:center;flex:1;">Extend Booking #' + bookingId + '</h2>' +
    '</div>' +
    '<div class="scroll-content" style="padding:20px;padding-bottom:60px;">' +

    '<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:16px;">' +
      '<div style="font-size:0.7rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:4px;">Current Return Date</div>' +
      '<div style="font-size:1rem;font-weight:800;color:var(--text-primary);">' + currentEndDate + '</div>' +
    '</div>' +

    '<div class="card">' +
      '<h4 style="font-weight:700;margin-bottom:14px;"><i class="fas fa-calendar-plus" style="color:var(--primary);margin-right:8px;"></i>New Return Date</h4>' +
      '<div class="form-group"><label>Extend Until</label>' +
        '<input type="date" id="extNewEnd" min="' + minDate + '" onchange="calcExtPrice(\'' + currentEndDate + '\',' + rate + ')" style="width:100%;padding:12px;background:var(--bg-input);border:1.5px solid transparent;border-radius:var(--radius-sm);font-size:0.95rem;color:var(--text-primary);">' +
      '</div>' +
      '<div id="extPriceBox" style="display:none;background:rgba(0,177,79,0.08);border:1px solid rgba(0,177,79,0.3);border-radius:12px;padding:14px;margin-top:8px;">' +
        '<div style="display:flex;justify-content:space-between;align-items:center;">' +
          '<span style="font-size:0.82rem;color:var(--text-secondary);" id="extDaysLabel">Extension fee</span>' +
          '<span style="font-size:1.1rem;font-weight:900;color:var(--primary);" id="extPriceLabel">-</span>' +
        '</div>' +
      '</div>' +
    '</div>' +

    '<div class="card">' +
      '<h4 style="font-weight:700;margin-bottom:14px;"><i class="fas fa-money-bill-wave" style="color:var(--primary);margin-right:8px;"></i>Payment</h4>' +
      '<div class="form-group"><label>Payment Method</label>' +
        '<select id="extMethod" style="width:100%;padding:12px;background:var(--bg-input);border:1.5px solid transparent;border-radius:var(--radius-sm);font-size:0.95rem;color:var(--text-primary);" onchange="document.getElementById(\\'extCashFields\\').style.display=(this.value===\\'cash\\'?\\'block\\':\\'none\\')">' +
          '<option value="gcash">GCash</option>' +
          '<option value="maya">Maya</option>' +
          '<option value="cash">Cash Over the Counter</option>' +
        '</select>' +
      '</div>' +
      '<div id="extCashFields" style="display:none;">' +
        '<div class="form-group"><label>Reference / Transaction # (optional)</label>' +
          '<input type="text" id="extRef" placeholder="e.g. 1234567890">' +
        '</div>' +
        '<div class="form-group"><label>Payment Proof Screenshot</label>' +
          '<button class="btn-secondary" onclick="pickExtProof()"><i class="fas fa-upload"></i> Upload Screenshot</button>' +
          '<img id="extProofPreview" style="width:100%;margin-top:8px;border-radius:8px;display:none;">' +
        '</div>' +
      '</div>' +
    '</div>' +

    '<div style="margin-top:4px;padding:12px;background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.3);border-radius:12px;margin-bottom:20px;">' +
      '<p style="font-size:0.8rem;color:var(--text-secondary);margin:0;"><i class="fas fa-info-circle" style="color:#fbbf24;margin-right:6px;"></i><strong>Note:</strong> If admin does not approve, your payment will be refunded upon vehicle return.</p>' +
    '</div>' +

    '<span class="field-error" id="extErr" style="display:block;margin-bottom:12px;text-align:center;"></span>' +
    '<button class="btn-primary" onclick="submitExtension(' + bookingId + ')" style="margin-bottom:12px;"><i class="fas fa-paper-plane" style="margin-right:6px;"></i>Submit Extension Request</button>' +
    '</div>';

  if (isModal) {
    container.innerHTML = '<div style="background:var(--bg-app);width:100%;max-width:500px;border-radius:24px 24px 0 0;max-height:90vh;overflow-y:auto;">' + html + '</div>';
  } else {
    container.innerHTML = html;
  }
}

var _extProofBlob = null;
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
  try {
    var orig = new Date(currentEndDate + 'T00:00:00');
    var next = new Date(newEnd + 'T00:00:00');
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
  var priceBox = document.getElementById('extPriceBox');
  var errEl = document.getElementById('extErr');
  if (errEl) errEl.textContent = '';

  if (!newEnd) { if (errEl) errEl.textContent = 'Please select a new return date.'; return; }
  if (!priceBox || priceBox.style.display === 'none') { if (errEl) errEl.textContent = 'Please select a valid date.'; return; }

  var price = priceBox.dataset.price || 0;
  var method = (document.getElementById('extMethod') || {}).value || 'cash';
  var ref = (document.getElementById('extRef') || {}).value || '';
  var methodLabel = method === 'gcash' ? 'GCash' : method === 'maya' ? 'Maya' : 'Cash (Over the counter)';

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

'''

if insert_before_fn in content:
    content = content.replace(insert_before_fn, extend_fn + insert_before_fn, 1)
    print('Step 3 done: openExtendBooking functions added')
else:
    print('Step 3: insertion point not found')

with open('customer_mobile/www/js/app.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print('Customer app.js saved')
