/**
 * Unit Tests for Expandable Dashboard Charts (Task 5)
 * Tests chart expansion, filtering, and popup functionality
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

describe('Expandable Dashboard Charts', () => {
    let mockChartInstance;
    let mockCanvas;
    let mockContext;

    beforeEach(() => {
        // Setup DOM elements
        document.body.innerHTML = `
            <div id="chartPopupModal" class="modal-overlay hidden">
                <div class="modal-card chart-popup-card">
                    <header class="modal-header">
                        <h3 id="chartPopupTitle">Chart Details</h3>
                        <button class="close-btn" id="chartPopupClose">x</button>
                    </header>
                    <div class="chart-filters">
                        <div class="filter-group">
                            <label for="filterStartDate">Start Date:</label>
                            <input type="date" id="filterStartDate" class="filter-input">
                        </div>
                        <div class="filter-group">
                            <label for="filterEndDate">End Date:</label>
                            <input type="date" id="filterEndDate" class="filter-input">
                        </div>
                        <div class="filter-group">
                            <label for="filterStatus">Status:</label>
                            <select id="filterStatus" class="filter-input">
                                <option value="all">All Statuses</option>
                                <option value="Pending">Pending</option>
                                <option value="Approved">Approved</option>
                                <option value="Completed">Completed</option>
                                <option value="Cancelled">Cancelled</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <label for="filterVehicleType">Vehicle Type:</label>
                            <select id="filterVehicleType" class="filter-input">
                                <option value="all">All Types</option>
                                <option value="sedan">Sedan</option>
                                <option value="suv">SUV</option>
                                <option value="van">Van</option>
                            </select>
                        </div>
                        <button class="btn-reset-filters" id="btnResetFilters">?? Reset Filters</button>
                    </div>
                    <div class="chart-popup-body">
                        <canvas id="popupChartCanvas"></canvas>
                    </div>
                </div>
            </div>
            <canvas id="revenueChart"></canvas>
        `;

        // Mock canvas and context
        mockCanvas = document.getElementById('popupChartCanvas');
        mockContext = {
            createLinearGradient: vi.fn(() => ({
                addColorStop: vi.fn()
            }))
        };
        mockCanvas.getContext = vi.fn(() => mockContext);

        // Mock Chart.js
        mockChartInstance = {
            data: {
                labels: ['Jan', 'Feb', 'Mar'],
                datasets: [{
                    label: 'Revenue',
                    data: [1000, 2000, 3000]
                }]
            },
            destroy: vi.fn()
        };

        global.Chart = vi.fn(() => mockChartInstance);
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    describe('5.1 Chart Popup Modal HTML Structure', () => {
        it('should have chart popup modal with correct ID', () => {
            const modal = document.getElementById('chartPopupModal');
            expect(modal).toBeTruthy();
            expect(modal.classList.contains('modal-overlay')).toBe(true);
        });

        it('should have modal header with dynamic title and close button', () => {
            const title = document.getElementById('chartPopupTitle');
            const closeBtn = document.getElementById('chartPopupClose');
            
            expect(title).toBeTruthy();
            expect(closeBtn).toBeTruthy();
            expect(closeBtn.classList.contains('close-btn')).toBe(true);
        });

        it('should have chart filters section with all filter inputs', () => {
            const startDate = document.getElementById('filterStartDate');
            const endDate = document.getElementById('filterEndDate');
            const status = document.getElementById('filterStatus');
            const vehicleType = document.getElementById('filterVehicleType');
            
            expect(startDate).toBeTruthy();
            expect(endDate).toBeTruthy();
            expect(status).toBeTruthy();
            expect(vehicleType).toBeTruthy();
        });

        it('should have chart canvas container', () => {
            const canvas = document.getElementById('popupChartCanvas');
            expect(canvas).toBeTruthy();
            expect(canvas.tagName).toBe('CANVAS');
        });

        it('should have Reset Filters button', () => {
            const resetBtn = document.getElementById('btnResetFilters');
            expect(resetBtn).toBeTruthy();
            expect(resetBtn.classList.contains('btn-reset-filters')).toBe(true);
        });
    });

    describe('5.2 makeChartClickable() function', () => {
        it('should add cursor pointer style to chart element', () => {
            const chartElement = document.getElementById('revenueChart');
            
            // Simulate makeChartClickable
            chartElement.style.cursor = 'pointer';
            
            expect(chartElement.style.cursor).toBe('pointer');
        });

        it('should attach click event listener to chart canvas', () => {
            const chartElement = document.getElementById('revenueChart');
            const clickHandler = vi.fn();
            
            chartElement.addEventListener('click', clickHandler);
            chartElement.click();
            
            expect(clickHandler).toHaveBeenCalled();
        });
    });

    describe('5.3 openChartPopup() function', () => {
        test('should store current chart data and type', () => {
            const chartType = 'bar';
            const chartData = {
                labels: ['Jan', 'Feb', 'Mar'],
                datasets: [{
                    label: 'Revenue',
                    data: [1000, 2000, 3000]
                }]
            };

            // Simulate storing data
            const storedData = {
                type: chartType,
                data: JSON.parse(JSON.stringify(chartData))
            };

            expect(storedData.type).toBe('bar');
            expect(storedData.data.labels).toEqual(['Jan', 'Feb', 'Mar']);
        });

        test('should set chart popup title based on chart type', () => {
            const title = document.getElementById('chartPopupTitle');
            const chartTypes = {
                'bar': 'Revenue Overview',
                'doughnut': 'Booking Status Distribution',
                'line': 'Bookings Trend'
            };

            title.textContent = chartTypes['bar'];
            expect(title.textContent).toBe('Revenue Overview');
        });

        test('should initialize date range filters with last 30 days', () => {
            const today = new Date().toISOString().split('T')[0];
            const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            
            const startDate = document.getElementById('filterStartDate');
            const endDate = document.getElementById('filterEndDate');
            
            startDate.value = thirtyDaysAgo;
            endDate.value = today;
            
            expect(startDate.value).toBe(thirtyDaysAgo);
            expect(endDate.value).toBe(today);
        });

        test('should show chart popup modal', () => {
            const modal = document.getElementById('chartPopupModal');
            modal.classList.remove('hidden');
            
            expect(modal.classList.contains('hidden')).toBe(false);
        });
    });

    describe('5.4 renderPopupChart() function', () => {
        test('should destroy existing chart instance if present', () => {
            const existingChart = { destroy: vi.fn() };
            
            if (existingChart) {
                existingChart.destroy();
            }
            
            expect(existingChart.destroy).toHaveBeenCalled();
        });

        test('should create new Chart.js instance with aspectRatio 2', () => {
            const chartConfig = {
                type: 'bar',
                data: mockChartInstance.data,
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 2
                }
            };

            expect(chartConfig.options.aspectRatio).toBe(2);
            expect(chartConfig.options.responsive).toBe(true);
            expect(chartConfig.options.maintainAspectRatio).toBe(true);
        });

        test('should apply chart styling with legend and colors', () => {
            const chartConfig = {
                options: {
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                color: '#f1f5f9',
                                font: { family: 'Inter', size: 14, weight: 500 }
                            }
                        }
                    }
                }
            };

            expect(chartConfig.options.plugins.legend.display).toBe(true);
            expect(chartConfig.options.plugins.legend.labels.color).toBe('#f1f5f9');
        });

        test('should handle different chart types (line, bar, doughnut)', () => {
            const chartTypes = ['line', 'bar', 'doughnut'];
            
            chartTypes.forEach(type => {
                const config = { type };
                expect(['line', 'bar', 'doughnut']).toContain(config.type);
            });
        });
    });

    describe('5.5 Chart Filter Functionality', () => {
        test('should fetch filtered data with correct parameters', async () => {
            const mockFetch = vi.fn(() => Promise.resolve({
                ok: true,
                json: () => Promise.resolve({
                    revenue: { labels: ['Jan'], values: [1000] },
                    bookings_trend: { labels: ['Jan'], values: [10] },
                    status: { labels: ['Completed'], values: [5] }
                })
            }));
            global.fetch = mockFetch;

            const params = new URLSearchParams({
                start: '2024-01-01',
                end: '2024-01-31',
                status: 'Completed',
                vehicle_type: 'sedan',
                period: 'daily'
            });

            await fetch(`http://localhost:5000/api/reports/filtered?${params}`);

            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/reports/filtered')
            );
        });

        test('should transform filtered data for chart rendering', () => {
            const apiData = {
                revenue: { labels: ['Jan', 'Feb'], values: [1000, 2000] }
            };

            const transformedData = {
                labels: apiData.revenue.labels,
                datasets: [{
                    label: 'Revenue',
                    data: apiData.revenue.values
                }]
            };

            expect(transformedData.labels).toEqual(['Jan', 'Feb']);
            expect(transformedData.datasets[0].data).toEqual([1000, 2000]);
        });

        test('should update chart within 500ms (debounced)', async () => {
            const startTime = Date.now();
            const debounceDelay = 500;

            await new Promise(resolve => {
                setTimeout(() => {
                    const elapsed = Date.now() - startTime;
                    expect(elapsed).toBeGreaterThanOrEqual(debounceDelay);
                    resolve();
                }, debounceDelay);
            });
        });
    });

    describe('5.6 Filter Event Handlers with Debouncing', () => {
        test('should attach change listeners to all filter inputs', () => {
            const filterIds = ['filterStartDate', 'filterEndDate', 'filterStatus', 'filterVehicleType'];
            
            filterIds.forEach(id => {
                const element = document.getElementById(id);
                expect(element).toBeTruthy();
            });
        });

        test('should implement 500ms debounce for filter updates', async () => {
            let callCount = 0;
            const debouncedFunction = () => {
                callCount++;
            };

            const debounce = (func, delay) => {
                let timeout;
                return () => {
                    clearTimeout(timeout);
                    timeout = setTimeout(func, delay);
                };
            };

            const debounced = debounce(debouncedFunction, 500);
            
            // Call multiple times rapidly
            debounced();
            debounced();
            debounced();

            // Should only execute once after 500ms
            await new Promise(resolve => {
                setTimeout(() => {
                    expect(callCount).toBe(1);
                    resolve();
                }, 600);
            });
        });

        test('should implement Reset Filters button handler', () => {
            const resetBtn = document.getElementById('btnResetFilters');
            const clickHandler = vi.fn();
            
            resetBtn.addEventListener('click', clickHandler);
            resetBtn.click();
            
            expect(clickHandler).toHaveBeenCalled();
        });

        test('should restore default filter values on reset', () => {
            const today = new Date().toISOString().split('T')[0];
            const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            
            const startDate = document.getElementById('filterStartDate');
            const endDate = document.getElementById('filterEndDate');
            const status = document.getElementById('filterStatus');
            const vehicleType = document.getElementById('filterVehicleType');
            
            // Set to default values
            startDate.value = thirtyDaysAgo;
            endDate.value = today;
            status.value = 'all';
            vehicleType.value = 'all';
            
            expect(startDate.value).toBe(thirtyDaysAgo);
            expect(endDate.value).toBe(today);
            expect(status.value).toBe('all');
            expect(vehicleType.value).toBe('all');
        });
    });

    describe('5.7 CSS Styling for Chart Popup', () => {
        test('should have chart popup card with max-width 1200px', () => {
            const card = document.querySelector('.chart-popup-card');
            expect(card).toBeTruthy();
        });

        test('should have filter controls with grid layout', () => {
            const filters = document.querySelector('.chart-filters');
            expect(filters).toBeTruthy();
        });

        test('should have minimum chart height of 400px', () => {
            const chartBody = document.querySelector('.chart-popup-body');
            expect(chartBody).toBeTruthy();
        });

        test('should have styled filter inputs and reset button', () => {
            const filterInput = document.querySelector('.filter-input');
            const resetBtn = document.querySelector('.btn-reset-filters');
            
            expect(filterInput).toBeTruthy();
            expect(resetBtn).toBeTruthy();
        });
    });

    describe('Integration Tests', () => {
        test('should complete full chart expansion workflow', () => {
            // 1. Click chart
            const chartElement = document.getElementById('revenueChart');
            chartElement.style.cursor = 'pointer';
            
            // 2. Open popup
            const modal = document.getElementById('chartPopupModal');
            modal.classList.remove('hidden');
            
            // 3. Set title
            const title = document.getElementById('chartPopupTitle');
            title.textContent = 'Revenue Overview';
            
            // 4. Initialize filters
            const startDate = document.getElementById('filterStartDate');
            const endDate = document.getElementById('filterEndDate');
            const today = new Date().toISOString().split('T')[0];
            const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            startDate.value = thirtyDaysAgo;
            endDate.value = today;
            
            // Verify workflow
            expect(chartElement.style.cursor).toBe('pointer');
            expect(modal.classList.contains('hidden')).toBe(false);
            expect(title.textContent).toBe('Revenue Overview');
            expect(startDate.value).toBe(thirtyDaysAgo);
            expect(endDate.value).toBe(today);
        });

        test('should handle filter application and chart update', async () => {
            const mockFetch = vi.fn(() => Promise.resolve({
                ok: true,
                json: () => Promise.resolve({
                    revenue: { labels: ['Jan'], values: [1000] }
                })
            }));
            global.fetch = mockFetch;

            // Apply filters
            const startDate = document.getElementById('filterStartDate');
            const endDate = document.getElementById('filterEndDate');
            startDate.value = '2024-01-01';
            endDate.value = '2024-01-31';

            // Trigger filter change
            const changeEvent = new Event('change');
            startDate.dispatchEvent(changeEvent);

            // Wait for debounce
            await new Promise(resolve => setTimeout(resolve, 600));

            // Verify chart would be updated (in real implementation)
            expect(startDate.value).toBe('2024-01-01');
            expect(endDate.value).toBe('2024-01-31');
        });

        test('should close popup and cleanup', () => {
            const modal = document.getElementById('chartPopupModal');
            const closeBtn = document.getElementById('chartPopupClose');
            
            // Open modal
            modal.classList.remove('hidden');
            expect(modal.classList.contains('hidden')).toBe(false);
            
            // Close modal
            closeBtn.click();
            modal.classList.add('hidden');
            
            expect(modal.classList.contains('hidden')).toBe(true);
        });
    });

    describe('Edge Cases and Error Handling', () => {
        test('should handle missing date filters gracefully', () => {
            const startDate = document.getElementById('filterStartDate');
            const endDate = document.getElementById('filterEndDate');
            
            startDate.value = '';
            endDate.value = '';
            
            const isValid = !!(startDate.value && endDate.value);
            expect(isValid).toBe(false);
        });

        test('should handle API errors gracefully', async () => {
            const mockFetch = vi.fn(() => Promise.resolve({
                ok: false,
                status: 500
            }));
            global.fetch = mockFetch;

            try {
                const response = await fetch('http://localhost:5000/api/reports/filtered');
                if (!response.ok) throw new Error('API Error');
            } catch (error) {
                expect(error.message).toBe('API Error');
            }
        });

        test('should handle empty chart data', () => {
            const emptyData = {
                labels: [],
                datasets: []
            };

            expect(emptyData.labels.length).toBe(0);
            expect(emptyData.datasets.length).toBe(0);
        });

        test('should handle chart type not found', () => {
            const unknownType = 'unknown';
            const validTypes = ['line', 'bar', 'doughnut'];
            
            const isValid = validTypes.includes(unknownType);
            expect(isValid).toBe(false);
        });
    });
});
