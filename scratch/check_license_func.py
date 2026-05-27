with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

if 'function viewLicenseImage' in content:
    print("viewLicenseImage function already exists")
else:
    print("viewLicenseImage function NOT found - needs to be added")
    
# Also check for licensePreviewModal
if 'licensePreviewModal' in content:
    print("licensePreviewModal found")
else:
    print("licensePreviewModal NOT found")
