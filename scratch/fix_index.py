import re

with open('C:/Users/patri/OneDrive/Desktop/AutorideSystem2sides/AutorideSystem/admin_mobile/www/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix Reports.renderBookingsChart
old_report_bookings = """                    datasets: [{
                        label: 'Bookings',
                        data: trend.map(t => t.count || t.bookings || 0),"""
new_report_bookings = """                    datasets: [{
                        label: 'Bookings',
                        data: trend.map(t => t.booking_count || t.count || t.bookings || 0),"""
content = content.replace(old_report_bookings, new_report_bookings)

# 2. Fix initCharts bookingsChart
old_init_bookings = """        // Bookings Bar Chart ? use booking status breakdown
        const bookCtx = document.getElementById('bookingsChart');
        if (bookCtx) {
            const bStatus = data.bookingsByStatus || {};
            const bLabels = Object.keys(bStatus).map(k => k.charAt(0).toUpperCase() + k.slice(1));
            const bData = Object.values(bStatus);
            charts.bookings = new Chart(bookCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: bLabels.length ? bLabels : revTrend.map(t => t.day.split('-').slice(1).join('/')),
                    datasets: [{
                        label: 'Bookings',
                        data: bData.length ? bData : revTrend.map(() => 0),"""
new_init_bookings = """        // Bookings Bar Chart ()
        const bookCtx = document.getElementById('bookingsChart');
        if (bookCtx) {
            charts.bookings = new Chart(bookCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: revTrend.map(t => t.day.split('-').slice(1).join('/')),
                    datasets: [{
                        label: 'Bookings',
                        data: revTrend.map(t => t.booking_count || t.count || t.bookings || 0),"""
content = content.replace(old_init_bookings, new_init_bookings)

# 3. Fix applyPopupFilters for bookings
old_popup_bookings = """            } else if (currentChartType === 'bookings') {
                const trend = data.bookingsByStatus || {};
                const bLabels = Object.keys(trend).map(k => k.charAt(0).toUpperCase() + k.slice(1));
                const bData = Object.values(trend);
                originalChartData.labels = bLabels;
                originalChartData.datasets[0].data = bData;"""
new_popup_bookings = """            } else if (currentChartType === 'bookings') {
                const trend = data.revenueTrend || [];
                originalChartData.labels = trend.map(t => t.day ? t.day.split('-').slice(1).join('/') : t.label || '');
                originalChartData.datasets[0].data = trend.map(t => t.booking_count || t.count || t.bookings || 0);"""
content = content.replace(old_popup_bookings, new_popup_bookings)

with open('C:/Users/patri/OneDrive/Desktop/AutorideSystem2sides/AutorideSystem/admin_mobile/www/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
