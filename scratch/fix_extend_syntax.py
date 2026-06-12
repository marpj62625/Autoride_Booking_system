# -*- coding: utf-8 -*-
with open('customer_mobile/www/js/app.js', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

start = content.find('function _renderExtendForm(')
end = content.find('\nfunction pickExtProof()', start)

# Replace the entire broken function with a clean version using DOM methods
new_fn = r"""function _renderExtendForm(container, bookingId, currentEndDate, dailyRate, isModal, prevHtml) {
  var rate = parseFloat(dailyRate) || 0;
  var minDate = currentEndDate;
  try {
    var d = new Date(currentEndDate + 'T00:00:00');
    d.setDate(d.getDate() + 1);
    minDate = d.toISOString().split('T')[0];
  } catch(e) {}

  // Build HTML using array join to avoid quote escaping issues
  var parts = [];
  parts.push('<div class="page-header">');
  if (!isModal) {
    parts.push('<button class="back-btn" onclick="closeOverlay(\'page-booking-detail\')"><i class="fas fa-arrow-left"></i></button>');
  }
  parts.push('<h2 style="text-align:center;flex:1;">Extend Booking #' + bookingId + '</h2>');
  parts.push('</div>');
  parts.push('<div class="scroll-content" style="padding:20px;padding-bottom:60px;">');

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

"""

content = content[:start] + new_fn + content[end:]
with open('customer_mobile/www/js/app.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print('_renderExtendForm replaced')
