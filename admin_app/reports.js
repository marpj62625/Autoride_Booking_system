/* ============================================================
   Autoride Admin — Reports & Analytics JS
   Handles fetching report data and rendering Chart.js charts
   ============================================================ */

const API_BASE = "/api";

// ==================== DOM REFERENCES ====================
const reportDate        = document.getElementById('reportDate');
const btnGenerate       = document.getElementById('btnGenerate');
const tabDaily          = document.getElementById('tabDaily');
const tabMonthly        = document.getElementById('tabMonthly');
const chartPeriodLabel  = document.getElementById('chartPeriodLabel');
const loadingState      = document.getElementById('loadingState');
const emptyState        = document.getElementById('emptyState');
const topVehiclesBody   = document.getElementById('topVehiclesBody');
const topVehiclesTable  = document.getElementById('topVehiclesTable');

// Stats
const statTotalBookings = document.getElementById('statTotalBookings');
const statTotalRevenue  = document.getElementById('statTotalRevenue');
const statAvgRevenue    = document.getElementById('statAvgRevenue');
const statActiveVehicles = document.getElementById('statActiveVehicles');

// Trend elements
const trendBookings    = document.getElementById('trendBookings');
const trendBookingsPct = document.getElementById('trendBookingsPct');
const trendRevenue     = document.getElementById('trendRevenue');
const trendRevenuePct  = document.getElementById('trendRevenuePct');

// Sidebar
const sidebar    = document.getElementById('sidebar');
const menuToggle = document.getElementById('menuToggle');

// State
let currentPeriod = 'daily'; // 'daily' | 'monthly'
let revenueChart, statusChart, bookingsTrendChart, topVehiclesChart;

// ==================== INIT ====================
document.addEventListener('DOMContentLoaded', () => {
    // Set today's date
    const today = new Date().toISOString().split('T')[0];
    reportDate.value = today;

    updateClock();
    setInterval(updateClock, 1000);

    // Event listeners
    tabDaily.addEventListener('click', () => setPeriod('daily'));
    tabMonthly.addEventListener('click', () => setPeriod('monthly'));
    btnGenerate.addEventListener('click', loadReport);
    menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));

    // Close sidebar on outside click (mobile)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 &&
            sidebar.classList.contains('open') &&
            !sidebar.contains(e.target) &&
            e.target !== menuToggle) {
            sidebar.classList.remove('open');
        }
    });

    // Initial load
    loadReport();
});

// ==================== CLOCK ====================
function updateClock() {
    const el = document.getElementById('headerTime');
    if (!el) return;
    const now = new Date();
    el.textContent = now.toLocaleString('en-US', {
        weekday: 'short', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
}

// ==================== PERIOD TOGGLE ====================
function setPeriod(period) {
    currentPeriod = period;
    document.querySelectorAll('.period-tab').forEach(t => t.classList.remove('active'));
    if (period === 'daily') {
        tabDaily.classList.add('active');
        chartPeriodLabel.textContent = 'Daily';
    } else {
        tabMonthly.classList.add('active');
        chartPeriodLabel.textContent = 'Monthly';
    }
    loadReport();
}

// ==================== LOAD REPORT ====================
async function loadReport() {
    const date = reportDate.value;
    if (!date) {
        showToast('error', 'Please select a date first.');
        return;
    }

    showLoading(true);

    try {
        // Fetch all report endpoints in parallel
        const [summaryRes, revenueRes, statusRes, trendRes, vehiclesRes] = await Promise.all([
            fetch(`${API_BASE}/reports/summary?period=${currentPeriod}&date=${date}`),
            fetch(`${API_BASE}/reports/revenue?period=${currentPeriod}&date=${date}`),
            fetch(`${API_BASE}/reports/booking-status`),
            fetch(`${API_BASE}/reports/bookings-trend?period=${currentPeriod}&date=${date}`),
            fetch(`${API_BASE}/reports/top-vehicles`)
        ]);

        if (!summaryRes.ok || !revenueRes.ok || !statusRes.ok || !trendRes.ok || !vehiclesRes.ok) {
            throw new Error('One or more report APIs returned an error.');
        }

        const summary  = await summaryRes.json();
        const revenue  = await revenueRes.json();
        const statuses = await statusRes.json();
        const trend    = await trendRes.json();
        const vehicles = await vehiclesRes.json();

        // Update KPI cards
        updateKPIs(summary);

        // Render charts
        renderRevenueChart(revenue);
        renderStatusChart(statuses);
        renderBookingsTrendChart(trend);
        renderTopVehiclesChart(vehicles);

        // Render table
        renderTopVehiclesTable(vehicles);

        showToast('success', 'Report generated successfully!');
    } catch (err) {
        console.error('Report load error:', err);
        showToast('error', 'Failed to load report. Is the backend running?');
    } finally {
        showLoading(false);
    }
}

// ==================== UPDATE KPI CARDS ====================
function updateKPIs(data) {
    animateValue(statTotalBookings, data.total_bookings || 0);
    statTotalRevenue.textContent  = '₱' + formatPrice(data.total_revenue || 0);
    statAvgRevenue.textContent    = '₱' + formatPrice(data.avg_revenue || 0);
    animateValue(statActiveVehicles, data.active_vehicles || 0);

    // Animate stat cards
    document.querySelectorAll('.stat-value').forEach(el => {
        el.style.animation = 'none';
        el.offsetHeight;
        el.style.animation = 'popIn 0.35s ease';
    });

    // Update trends (mock: compare period total to overall avg)
    // The backend could provide these, but for now we show a static indicator
    setTrend(trendBookings, trendBookingsPct, data.total_bookings, 'up');
    setTrend(trendRevenue, trendRevenuePct, data.total_revenue, 'up');
}

function setTrend(trendEl, pctEl, value, direction) {
    if (!value || value === 0) {
        trendEl.className = 'stat-trend neutral';
        trendEl.querySelector('.trend-arrow').textContent = '→';
        pctEl.textContent = '—';
    } else {
        trendEl.className = `stat-trend ${direction}`;
        trendEl.querySelector('.trend-arrow').textContent = direction === 'up' ? '↑' : '↓';
        pctEl.textContent = direction === 'up' ? '+Active' : '-Decline';
    }
}

function animateValue(el, target) {
    const duration = 600;
    const start = parseInt(el.textContent) || 0;
    const diff = target - start;
    if (diff === 0) { el.textContent = target; return; }
    const startTime = performance.now();
    function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3); // easeOutCubic
        el.textContent = Math.round(start + diff * ease);
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

// ==================== CHART RENDERERS ====================

// -- Revenue Chart (Bar/Line) --
function renderRevenueChart(data) {
    const ctx = document.getElementById('revenueChart').getContext('2d');
    if (revenueChart) revenueChart.destroy();

    const gradient = ctx.createLinearGradient(0, 0, 0, 280);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.5)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0.02)');

    revenueChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: 'Revenue (₱)',
                data: data.values || [],
                backgroundColor: gradient,
                borderColor: '#6366f1',
                borderWidth: 2,
                borderRadius: 6,
                hoverBackgroundColor: 'rgba(99, 102, 241, 0.7)',
            }]
        },
        options: chartOptions('₱')
    });
}

// -- Booking Status Doughnut --
function renderStatusChart(data) {
    const ctx = document.getElementById('statusChart').getContext('2d');
    if (statusChart) statusChart.destroy();

    const colors = {
        'Pending':   '#f59e0b',
        'Approved':  '#22c55e',
        'Rejected':  '#ef4444',
        'Confirmed': '#3b82f6',
        'Cancelled': '#64748b'
    };

    statusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels || [],
            datasets: [{
                data: data.values || [],
                backgroundColor: (data.labels || []).map(l => colors[l] || '#6366f1'),
                borderColor: '#111827',
                borderWidth: 3,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '68%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#94a3b8',
                        font: { family: 'Inter', size: 12, weight: 500 },
                        padding: 16,
                        usePointStyle: true,
                        pointStyleWidth: 10
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: { family: 'Inter', weight: 600 },
                    bodyFont: { family: 'Inter' }
                }
            }
        }
    });
}

// -- Bookings Trend (Line) --
function renderBookingsTrendChart(data) {
    const ctx = document.getElementById('bookingsTrendChart').getContext('2d');
    if (bookingsTrendChart) bookingsTrendChart.destroy();

    const gradient = ctx.createLinearGradient(0, 0, 0, 280);
    gradient.addColorStop(0, 'rgba(6, 182, 212, 0.35)');
    gradient.addColorStop(1, 'rgba(6, 182, 212, 0.0)');

    bookingsTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: 'Bookings',
                data: data.values || [],
                borderColor: '#06b6d4',
                backgroundColor: gradient,
                borderWidth: 2.5,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#06b6d4',
                pointBorderColor: '#111827',
                pointBorderWidth: 2,
                pointHoverRadius: 7,
            }]
        },
        options: chartOptions('')
    });
}

// -- Top Vehicles (Horizontal Bar) --
function renderTopVehiclesChart(data) {
    const ctx = document.getElementById('topVehiclesChart').getContext('2d');
    if (topVehiclesChart) topVehiclesChart.destroy();

    const barColors = [
        'rgba(99, 102, 241, 0.8)',
        'rgba(6, 182, 212, 0.8)',
        'rgba(168, 85, 247, 0.8)',
        'rgba(34, 197, 94, 0.8)',
        'rgba(245, 158, 11, 0.8)'
    ];

    topVehiclesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: (data.vehicles || []).map(v => v.vehicle_name),
            datasets: [{
                label: 'Bookings',
                data: (data.vehicles || []).map(v => v.total_bookings),
                backgroundColor: barColors.slice(0, (data.vehicles || []).length),
                borderRadius: 6,
                barThickness: 22,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } }
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        color: '#94a3b8',
                        font: { family: 'Inter', size: 12, weight: 500 },
                        padding: 8
                    }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: { family: 'Inter', weight: 600 },
                    bodyFont: { family: 'Inter' }
                }
            }
        }
    });
}

// -- Shared chart options  --
function chartOptions(prefix) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        scales: {
            x: {
                grid: { color: 'rgba(255,255,255,0.04)' },
                ticks: {
                    color: '#64748b',
                    font: { family: 'Inter', size: 11 },
                    maxRotation: 45
                }
            },
            y: {
                grid: { color: 'rgba(255,255,255,0.04)' },
                ticks: {
                    color: '#64748b',
                    font: { family: 'Inter', size: 11 },
                    callback: v => prefix + v.toLocaleString()
                },
                beginAtZero: true
            }
        },
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: '#1e293b',
                titleColor: '#f1f5f9',
                bodyColor: '#94a3b8',
                padding: 12,
                cornerRadius: 8,
                titleFont: { family: 'Inter', weight: 600 },
                bodyFont: { family: 'Inter' },
                callbacks: {
                    label: ctx => ` ${prefix}${ctx.parsed.y != null ? ctx.parsed.y.toLocaleString() : ctx.parsed.x.toLocaleString()}`
                }
            }
        }
    };
}

// ==================== TOP VEHICLES TABLE ====================
function renderTopVehiclesTable(data) {
    const vehicles = data.vehicles || [];
    topVehiclesBody.innerHTML = '';

    if (vehicles.length === 0) {
        topVehiclesTable.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }

    topVehiclesTable.classList.remove('hidden');
    emptyState.classList.add('hidden');

    const maxBookings = Math.max(...vehicles.map(v => v.total_bookings), 1);

    vehicles.forEach((v, i) => {
        const rank = i + 1;
        const pct = Math.round((v.total_bookings / maxBookings) * 100);
        let rankClass = 'rank-default';
        if (rank === 1) rankClass = 'rank-1';
        else if (rank === 2) rankClass = 'rank-2';
        else if (rank === 3) rankClass = 'rank-3';

        const tr = document.createElement('tr');
        tr.style.animation = `fadeInUp 0.4s ease ${i * 0.06}s both`;
        tr.innerHTML = `
            <td><span class="rank-badge ${rankClass}">${rank}</span></td>
            <td class="vehicle-name">${escapeHtml(v.vehicle_name)}</td>
            <td style="font-weight:600; font-variant-numeric:tabular-nums;">${v.total_bookings}</td>
            <td class="revenue-cell">₱${formatPrice(v.total_revenue)}</td>
            <td>
                <div class="popularity-bar-wrap">
                    <div class="popularity-bar">
                        <div class="popularity-fill" style="width:${pct}%"></div>
                    </div>
                    <span class="popularity-pct">${pct}%</span>
                </div>
            </td>
        `;
        topVehiclesBody.appendChild(tr);
    });
}

// ==================== TOAST ====================
let _toastTimeout = null;
function showToast(type, message) {
    const toast = document.getElementById('toast');
    const toastIcon = document.getElementById('toastIcon');
    const toastMsg  = document.getElementById('toastMsg');

    toast.className = `toast ${type}`;
    toastIcon.textContent = type === 'success' ? '✅' : '❌';
    toastMsg.textContent = message;

    clearTimeout(_toastTimeout);
    _toastTimeout = setTimeout(() => toast.classList.add('hidden'), 4000);
}

// ==================== HELPERS ====================
function showLoading(show) {
    loadingState.classList.toggle('hidden', !show);
    if (show) {
        emptyState.classList.add('hidden');
    }
}

function formatPrice(price) {
    if (price == null) return '0.00';
    return parseFloat(price).toLocaleString('en-PH', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
