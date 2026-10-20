new_func = """async exportExcel() {
            if (typeof anime !== 'undefined') {
                const _btn = (window.event && (window.event.currentTarget || window.event.target));
                if (_btn) {
                    anime({
                        targets: (_btn.querySelector && _btn.querySelector('i')) || _btn,
                        translateY: [0, -6, 2, 0],
                        duration: 450,
                        easing: 'easeOutBack'
                    });
                }
            }

            try {
                showNotification('Generating Executive Excel report with interactive charts...', 'success');
                const user = (typeof adminAuth !== 'undefined' && adminAuth.getUser()) || {};
                const from = document.getElementById('rptDateFrom') ? document.getElementById('rptDateFrom').value : '';
                const to = document.getElementById('rptDateTo') ? document.getElementById('rptDateTo').value : '';
                const filter = this._filter || 'year';
                const adminId = user.id || '';

                const url = `${API_BASE}/api/admin/reports/export-excel?filter=${filter}&date_from=${from}&date_to=${to}&admin_id=${adminId}`;
                const filename = `Autoride_Executive_Report_${from || 'all'}_to_${to || 'all'}.xlsx`;

                const res = await fetch(url);
                if (!res.ok) {
                    throw new Error(`Server returned status ${res.status}`);
                }
                const blob = await res.blob();

                // Check for Capacitor Mobile download
                const { Filesystem } = window.Capacitor?.Plugins || {};
                if (Filesystem) {
                    try {
                        const reader = new FileReader();
                        reader.readAsDataURL(blob);
                        reader.onloadend = async () => {
                            const base64data = reader.result.split(',')[1];
                            const result = await Filesystem.writeFile({
                                path: filename,
                                data: base64data,
                                directory: 'DOWNLOADS',
                                recursive: true
                            });
                            showNotification('Excel saved to Downloads: ' + filename, 'success');
                        };
                        return;
                    } catch (mErr) {
                        console.warn('Mobile download failed, falling back to browser download:', mErr);
                    }
                }

                // Standard Web Browser download
                const downloadUrl = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                setTimeout(() => URL.revokeObjectURL(downloadUrl), 5000);
                showNotification('Executive Excel report with charts downloaded!', 'success');

            } catch (err) {
                console.error('Excel export failed:', err);
                showNotification('Export failed: ' + err.message, 'error');
            }
        },"""

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Normalize
normalized = text.replace('\r\n', '\n')

# Find Reports.exportExcel
idx_start = normalized.find('async exportExcel()', 900000)
assert idx_start != -1, "Reports.exportExcel not found"

idx_end_marker = normalized.find('\n    };\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n    // --- SETTINGS MODULE ---', idx_start)
if idx_end_marker == -1:
    idx_end_marker = normalized.find('\n    };\n', idx_start)

assert idx_end_marker != -1, "End of Reports object not found"

old_block = normalized[idx_start:idx_end_marker]
print(f"Replacing {len(old_block)} chars with {len(new_func)} chars...")

new_content = normalized[:idx_start] + new_func + normalized[idx_end_marker:]

with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SUCCESS: Reports.exportExcel() replaced successfully in admin_app/index.html!")
