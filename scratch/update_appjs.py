import re

with open('customer_mobile/www/js/app.js', 'r', encoding='latin-1') as f:
    content = f.read()

# The old block starts at "// PROFILE" and ends just before "function pickProfilePicture()"
old_start = '// PROFILE\nvar _licenseBlob = null;'
old_end = 'function pickProfilePicture()'

start_idx = content.find(old_start)
end_idx = content.find(old_end)

if start_idx == -1 or end_idx == -1:
    # try with \r\n
    old_start2 = '// PROFILE\r\nvar _licenseBlob = null;'
    start_idx = content.find(old_start2)
    if start_idx == -1:
        print("ERROR: Could not find start marker")
        exit(1)

print(f"Found start at char {start_idx}, end at char {end_idx}")

new_block = r"""// PROFILE
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
    uploadFile('/api/user/license-details', fd)
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
  apiCall('/api/user/license-details?user_id=' + currentUser.id)
    .then(function(data) {
      if (!data || !data.license_number) return;
      var el;
      el = document.getElementById('editLicenseNumber'); if (el) el.value = data.license_number || '';
      el = document.getElementById('editLicenseExpiry'); if (el) el.value = data.expiry_date || '';
      el = document.getElementById('editLicenseCountry'); if (el) el.value = data.issuing_country_state || '';
      el = document.getElementById('editLicenseClass'); if (el) el.value = data.license_class || '';
      el = document.getElementById('editLicenseName'); if (el) el.value = data.full_name || '';
      el = document.getElementById('editLicenseDob'); if (el) el.value = data.date_of_birth || '';
      el = document.getElementById('editLicenseEmName'); if (el) el.value = data.emergency_contact_name || '';
      el = document.getElementById('editLicenseEmPhone'); if (el) el.value = data.emergency_contact_phone || '';
      el = document.getElementById('editLicenseEmRel'); if (el) el.value = data.emergency_contact_relationship || '';
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
  showLoading(true);

  // Load main profile
  var profilePromise = apiCall('/user/profile-full?user_id=' + currentUser.id);
  // Load license details from new table
  var licensePromise = apiCall('/api/user/license-details?user_id=' + currentUser.id).catch(function() { return {}; });

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
          if (placeholder) placeholder.textContent = (profile.full_name || '?')[0].toUpperCase();
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

"""

content = content[:start_idx] + new_block + content[end_idx:]

with open('customer_mobile/www/js/app.js', 'w', encoding='latin-1') as f:
    f.write(content)

print("SUCCESS: app.js updated")
