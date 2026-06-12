import re

with open('customer_mobile/www/js/app.js', 'r', encoding='latin-1') as f:
    content = f.read()

# Modify breakdownHtml in openPaymentScreen to make addons toggleable
old_addon_html = '''    (selectedAddons.length > 0 ? selectedAddons.map(function(a) {
      return '<div class="price-row" style="padding-left:10px;font-size:0.8rem;color:var(--text-secondary);"><span><i class="fas fa-check" style="color:var(--success);"></i> ' + a.name + '</span><span>' + formatPHP(a.price) + '</span></div>';
    }).join('') : '') +'''

new_addon_html = '''    // Render all available addons as toggleable on payment page
    (ADDON_OPTIONS.map(function(opt, idx) {
      var isSelected = selectedAddons.some(function(a) { return a.name === opt.name; });
      var aPrice = opt.pricePerDay * priceResult.days;
      return '<div class="price-row" style="padding-left:10px;font-size:0.8rem;color:var(--text-secondary);cursor:pointer;" onclick="togglePaymentAddon(' + idx + ', ' + bookingId + ')">' +
             '<span><i class="fas ' + (isSelected ? 'fa-check-square' : 'fa-square') + '" style="color:var(--' + (isSelected ? 'success' : 'border') + ');margin-right:6px;font-size:1.1em;vertical-align:middle;"></i> ' + opt.name + '</span>' +
             '<span>' + formatPHP(aPrice) + '</span></div>';
    }).join('')) +'''

content = content.replace(old_addon_html, new_addon_html)

# Add togglePaymentAddon function right before selectPayMethod
toggle_func = '''
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
'''

content = content.replace('function selectPayMethod(method, el) {', toggle_func + '\\nfunction selectPayMethod(method, el) {')

with open('customer_mobile/www/js/app.js', 'w', encoding='latin-1') as f:
    f.write(content)
print('Done frontend updates')
