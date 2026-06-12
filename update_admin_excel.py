import re

with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# Add script to head
if 'xlsx.full.min.js' not in content:
    content = content.replace('</head>', '    <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>\n</head>')

# Rewrite exportExcel function
old_export_start = 'async exportExcel() {'
old_export_end = '        async printReport() {'

# Find the exact string to replace
start_idx = content.find(old_export_start)
end_idx = content.find(old_export_end)

if start_idx != -1 and end_idx != -1:
    new_export_func = '''async exportExcel() {
            const data = this._rawData;
            if (!data) { showNotification('No data to export', 'error'); return; }

            const totalRev = data.totalRevenue || 0;
            const totalBook = data.totalBookings || 0;

            const rows = [];
            rows.push(['Autoride Sales Report']);
            rows.push(['Generated:', new Date().toLocaleString()]);
            rows.push([]);
            rows.push(['Summary']);
            rows.push(['Total Revenue (PHP)', totalRev]);
            rows.push(['Total Bookings', totalBook]);
            rows.push(['Average Revenue per Booking (PHP)', totalBook > 0 ? Math.floor(totalRev / totalBook) : 0]);
            rows.push([]);
            rows.push(['Top Vehicles by Revenue']);
            rows.push(['#', 'Vehicle', 'Bookings', 'Revenue (PHP)']);
            (data.topVehicles || []).forEach((c, i) => {
                rows.push([i + 1, ${c.brand} , c.booking_count, c.revenue || 0]);
            });
            rows.push([]);
            rows.push(['Revenue Trend']);
            rows.push(['Date', 'Revenue (PHP)']);
            (data.revenueTrend || []).forEach(t => {
                rows.push([t.day || t.label || '', t.amount || 0]);
            });

            // Generate real Excel file using SheetJS
            try {
                if (typeof XLSX === 'undefined') {
                    throw new Error('Excel library not loaded');
                }
                
                const wb = XLSX.utils.book_new();
                const ws = XLSX.utils.aoa_to_sheet(rows);
                XLSX.utils.book_append_sheet(wb, ws, "Report");
                
                // Write as base64
                const wboutBase64 = XLSX.write(wb, { bookType: 'xlsx', type: 'base64' });
                const filename = utoride_report_.xlsx;

                const { Filesystem, Directory } = window.Capacitor.Plugins;
                if (Filesystem) {
                    const result = await Filesystem.writeFile({
                        path: filename,
                        data: wboutBase64,
                        directory: Directory ? Directory.Documents : 'DOCUMENTS',
                        recursive: true
                    });
                    
                    const { Share } = window.Capacitor.Plugins;
                    if (Share) {
                        await Share.share({
                            title: 'Autoride Sales Report',
                            url: result.uri,
                            dialogTitle: 'Share Excel Report'
                        });
                    }
                    showNotification('Excel Report saved and ready to share!', 'success');
                    return;
                }
            } catch (err) {
                console.error('Excel generation/sharing failed:', err);
            }

            // Fallback for web or if plugins fail
            try {
                if (typeof XLSX !== 'undefined') {
                    const wb = XLSX.utils.book_new();
                    const ws = XLSX.utils.aoa_to_sheet(rows);
                    XLSX.utils.book_append_sheet(wb, ws, "Report");
                    XLSX.writeFile(wb, utoride_report_.xlsx);
                    showNotification('Excel file downloaded!', 'success');
                } else {
                    showNotification('Export failed. Excel library not available.', 'error');
                }
            } catch (err) {
                showNotification('Export failed. Please try again.', 'error');
            }
        },

'''
    content = content[:start_idx] + new_export_func + content[end_idx:]
    
    with open('admin_mobile/www/index.html', 'w', encoding='latin-1') as f:
        f.write(content)
    print('Updated exportExcel to generate real .xlsx file')
else:
    print('Could not find exportExcel function')
