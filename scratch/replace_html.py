import re

with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_form = """<!-- ?? LICENSE / ID SECTION ?? -->
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <h4 style="font-weight:700;margin:0;"><i class="fas fa-id-card" style="color:var(--primary);margin-right:8px;"></i>Driver's License Details</h4>
        <button id="licenseEditBtn" onclick="Profile.enterLicenseEdit()" style="background:none;border:none;color:var(--primary);font-size:0.85rem;font-weight:700;cursor:pointer;padding:4px 8px;border-radius:8px;display:flex;align-items:center;gap:5px;">
          <i class="fas fa-pen"></i> Edit
        </button>
      </div>

      <!-- VIEW MODE -->
      <div id="licenseViewMode">
        <div id="profileLicenseThumb" style="margin-bottom:12px; display:flex; gap:10px;">
          <p style="font-size:0.8rem;color:var(--text-muted);">Loading...</p>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
          <div>
            <div style="font-size:0.7rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.4px;margin-bottom:3px;">License No.</div>
            <div id="viewLicenseNumber" style="font-size:0.88rem;font-weight:600;color:var(--text-main);">-</div>
          </div>
          <div>
            <div style="font-size:0.7rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.4px;margin-bottom:3px;">Expiry Date</div>
            <div id="viewLicenseExpiry" style="font-size:0.88rem;font-weight:600;color:var(--text-main);">-</div>
          </div>
          <div>
            <div style="font-size:0.7rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.4px;margin-bottom:3px;">Class / Category</div>
            <div id="viewLicenseClass" style="font-size:0.88rem;font-weight:600;color:var(--text-main);">-</div>
          </div>
          <div>
            <div style="font-size:0.7rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.4px;margin-bottom:3px;">Country / State</div>
            <div id="viewLicenseCountry" style="font-size:0.88rem;font-weight:600;color:var(--text-main);">-</div>
          </div>
        </div>
        <hr style="border:none;border-top:1px solid var(--border);margin:12px 0;">
        <h5 style="margin-top:0;margin-bottom:8px;">Personal Info</h5>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
          <div>
            <div style="font-size:0.7rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.4px;margin-bottom:3px;">Full Name</div>
            <div id="viewLicenseName" style="font-size:0.88rem;font-weight:600;color:var(--text-main);">-</div>
          </div>
          <div>
            <div style="font-size:0.7rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.4px;margin-bottom:3px;">Date of Birth</div>
            <div id="viewLicenseDob" style="font-size:0.88rem;font-weight:600;color:var(--text-main);">-</div>
          </div>
        </div>
        <hr style="border:none;border-top:1px solid var(--border);margin:12px 0;">
        <h5 style="margin-top:0;margin-bottom:8px;">IV. IN CASE OF EMERGENCY NOTIFY:</h5>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
          <div style="grid-column: span 2;">
            <div style="font-size:0.7rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.4px;margin-bottom:3px;">Contact Name</div>
            <div id="viewLicenseEmName" style="font-size:0.88rem;font-weight:600;color:var(--text-main);">-</div>
          </div>
          <div>
            <div style="font-size:0.7rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.4px;margin-bottom:3px;">Phone Number</div>
            <div id="viewLicenseEmPhone" style="font-size:0.88rem;font-weight:600;color:var(--text-main);">-</div>
          </div>
          <div>
            <div style="font-size:0.7rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.4px;margin-bottom:3px;">Relationship</div>
            <div id="viewLicenseEmRel" style="font-size:0.88rem;font-weight:600;color:var(--text-main);">-</div>
          </div>
        </div>
      </div>

      <!-- EDIT MODE (hidden by default) -->
      <div id="licenseEditMode" style="display:none;">
        <div style="display:flex;justify-content:flex-end;margin-bottom:10px;">
          <button onclick="Profile.cancelLicenseEdit()" style="background:none;border:none;color:var(--text-muted);font-size:0.85rem;cursor:pointer;"><i class="fas fa-times"></i> Cancel</button>
        </div>

        <h5 style="margin-top:0;margin-bottom:8px;">Driver's License</h5>
        <div class="form-group">
          <label>License Number</label>
          <input type="text" id="editLicenseNumber" placeholder="e.g. N01-23-456789">
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px;">
          <div class="form-group" style="margin-bottom:0;">
            <label>Expiry Date</label>
            <input type="date" id="editLicenseExpiry" style="width:100%;padding:10px 12px;background:var(--surface-container,#f1f5f9);border:1px solid var(--border);border-radius:10px;color:var(--text-main);font-size:0.88rem;box-sizing:border-box;">
          </div>
          <div class="form-group" style="margin-bottom:0;">
            <label>Country / State</label>
            <input type="text" id="editLicenseCountry" placeholder="e.g. Philippines">
          </div>
        </div>
        <div class="form-group">
          <label>License Class / Category</label>
          <input type="text" id="editLicenseClass" placeholder="e.g. Non-Professional, A, B, etc.">
        </div>

        <hr style="border:none;border-top:1px solid var(--border);margin:12px 0;">
        <h5 style="margin-top:0;margin-bottom:8px;">Personal Info</h5>
        <div class="form-group">
          <label>Full Name</label>
          <input type="text" id="editLicenseName" placeholder="Juan Dela Cruz">
        </div>
        <div class="form-group">
          <label>Date of Birth</label>
          <input type="date" id="editLicenseDob" style="width:100%;padding:10px 12px;background:var(--surface-container,#f1f5f9);border:1px solid var(--border);border-radius:10px;color:var(--text-main);font-size:0.88rem;box-sizing:border-box;">
        </div>

        <hr style="border:none;border-top:1px solid var(--border);margin:12px 0;">
        <h5 style="margin-top:0;margin-bottom:8px;">IV. IN CASE OF EMERGENCY NOTIFY:</h5>
        <div class="form-group">
          <label>Contact Name</label>
          <input type="text" id="editLicenseEmName" placeholder="Maria Dela Cruz">
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px;">
          <div class="form-group" style="margin-bottom:0;">
            <label>Phone Number</label>
            <input type="text" id="editLicenseEmPhone" placeholder="+63 900 000 0000">
          </div>
          <div class="form-group" style="margin-bottom:0;">
            <label>Relationship</label>
            <input type="text" id="editLicenseEmRel" placeholder="Spouse, Parent, etc.">
          </div>
        </div>

        <hr style="border:none;border-top:1px solid var(--border);margin:12px 0;">
        <h5 style="margin-top:0;margin-bottom:8px;">License Image Upload</h5>
        <div class="form-group">
          <label>Front of License</label>
          <button class="btn-secondary" onclick="pickLicenseForProfile('front')"><i class="fas fa-camera"></i> Upload Front</button>
          <img id="licenseEditPreviewFront" style="width:100%;border-radius:var(--radius-sm);margin-top:10px;display:none;">
          <input type="file" id="licenseFileInputFront" accept="image/*" style="display:none;" onchange="handleLicenseFileSelect(event, 'front')">
        </div>
        <div class="form-group">
          <label>Back of License</label>
          <button class="btn-secondary" onclick="pickLicenseForProfile('back')"><i class="fas fa-camera"></i> Upload Back</button>
          <img id="licenseEditPreviewBack" style="width:100%;border-radius:var(--radius-sm);margin-top:10px;display:none;">
          <input type="file" id="licenseFileInputBack" accept="image/*" style="display:none;" onchange="handleLicenseFileSelect(event, 'back')">
        </div>
        
        <span class="field-error" id="licenseEditErr" style="display:block;margin-top:6px;margin-bottom:10px;"></span>
        <button class="btn-primary" onclick="Profile.saveLicenseInfo()"><i class="fas fa-save"></i> Save License Info</button>
      </div>
    </div>
"""

pattern = re.compile(r'<!-- \?\? LICENSE / ID SECTION \?\? -->.*?<!-- Account -->', re.DOTALL)
if pattern.search(content):
    content = pattern.sub(new_form + '\n    <!-- Account -->', content)
    with open('customer_mobile/www/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Pattern not found")
