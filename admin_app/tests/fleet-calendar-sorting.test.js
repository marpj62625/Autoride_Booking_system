/**
 * Unit Tests for Fleet Calendar Vehicle Sorting & Reordering (Option C - Hybrid)
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';

describe('FleetCalendar Sorting and Manual Reorder', () => {
    let mockStorage = {};
    let FleetCalendar;

    beforeEach(() => {
        mockStorage = {};
        global.localStorage = {
            getItem: vi.fn((key) => mockStorage[key] || null),
            setItem: vi.fn((key, val) => { mockStorage[key] = String(val); }),
            removeItem: vi.fn((key) => { delete mockStorage[key]; }),
            clear: vi.fn(() => { mockStorage = {}; })
        };

        const mockElements = {
            fleetCalendarSortSelect: { value: 'default' },
            fcResetSortBtn: { style: { display: 'none' } }
        };

        global.document = {
            getElementById: vi.fn((id) => mockElements[id] || null)
        };

        global.showNotification = vi.fn();

        FleetCalendar = {
            vehicles: [
                { id: 1, brand: 'Toyota', model: 'Vios', category: 'Sedan', plate_number: 'XYZ 123', daily_rate: 1800 },
                { id: 2, brand: 'Toyota', model: 'Hiace', category: 'Van', plate_number: 'ABC 456', daily_rate: 3500 },
                { id: 3, brand: 'Toyota', model: 'Fortuner', category: 'SUV', plate_number: 'DEF 789', daily_rate: 3000 },
                { id: 4, brand: 'Toyota', model: 'Innova', category: 'MPV', plate_number: 'GHI 101', daily_rate: 2500 }
            ],
            bookings: [
                { id: 101, vehicle_id: 3, status: 'Confirmed' },
                { id: 102, vehicle_id: 3, status: 'Approved' },
                { id: 103, vehicle_id: 2, status: 'Confirmed' },
                { id: 104, vehicle_id: 1, status: 'Cancelled' } // Should not count
            ],
            sortMode: 'default',
            customOrder: [],
            searchQuery: '',
            render: vi.fn(),

            getVehicleCategory(v) {
                if (v.category && String(v.category).trim()) return String(v.category).trim();
                if (v.type && String(v.type).trim()) return String(v.type).trim();
                const str = `${v.brand || ''} ${v.model || ''}`.toLowerCase();
                if (str.includes('hiace') || str.includes('van') || str.includes('commuter') || str.includes('grandia')) return 'Van';
                if (str.includes('fortuner') || str.includes('montero') || str.includes('everest') || str.includes('terra') || str.includes('mu-x') || str.includes('suv')) return 'SUV';
                if (str.includes('innova') || str.includes('avanza') || str.includes('rush') || str.includes('xpander') || str.includes('mpv') || str.includes('ertiga')) return 'MPV';
                if (str.includes('vios') || str.includes('mirage') || str.includes('city') || str.includes('almera') || str.includes('sedan') || str.includes('civic')) return 'Sedan';
                if (str.includes('hilux') || str.includes('d-max') || str.includes('ranger') || str.includes('strada') || str.includes('navara') || str.includes('pickup')) return 'Pickup';
                if (str.includes('wigo') || str.includes('brio') || str.includes('hatchback')) return 'Hatchback';
                return 'Other';
            },

            initSortSettings() {
                try {
                    const savedMode = localStorage.getItem('fleet_calendar_sort_mode');
                    if (savedMode) this.sortMode = savedMode;
                    const savedOrder = localStorage.getItem('fleet_calendar_custom_order');
                    if (savedOrder) {
                        const parsed = JSON.parse(savedOrder);
                        if (Array.isArray(parsed)) this.customOrder = parsed;
                    }
                } catch (e) {
                    console.warn('Failed to load fleet calendar sort settings:', e);
                }
            },

            syncSortUI() {
                const selectEl = document.getElementById('fleetCalendarSortSelect');
                const resetBtn = document.getElementById('fcResetSortBtn');
                if (selectEl) {
                    selectEl.value = this.sortMode || 'default';
                }
                if (resetBtn) {
                    const isCustom = (this.sortMode && this.sortMode !== 'default') || (Array.isArray(this.customOrder) && this.customOrder.length > 0);
                    resetBtn.style.display = isCustom ? 'inline-flex' : 'none';
                }
            },

            onSortChange(mode) {
                this.sortMode = mode || 'default';
                try {
                    localStorage.setItem('fleet_calendar_sort_mode', this.sortMode);
                } catch (e) {}
                this.syncSortUI();
                this.render();
            },

            resetVehicleOrder() {
                this.sortMode = 'default';
                this.customOrder = [];
                try {
                    localStorage.removeItem('fleet_calendar_sort_mode');
                    localStorage.removeItem('fleet_calendar_custom_order');
                } catch (e) {}
                this.syncSortUI();
                this.render();
                if (typeof showNotification === 'function') {
                    showNotification('Vehicle order reset to default', 'info');
                }
            },

            moveVehicle(vehicleId, direction, event) {
                if (event) {
                    event.stopPropagation();
                    if (typeof event.preventDefault === 'function') event.preventDefault();
                }
                const fullOrdered = this.getOrderedVehicles();
                const currentView = this.searchQuery ? fullOrdered.filter(v => {
                    const matchVeh = (v.brand + ' ' + v.model + ' ' + (v.plate_number || '')).toLowerCase().includes(this.searchQuery);
                    if (matchVeh) return true;
                    return (this.bookings || []).some(b => {
                        if (String(b.vehicle_id) !== String(v.id)) return false;
                        return (b.customer_name || '').toLowerCase().includes(this.searchQuery) ||
                               String(b.id).includes(this.searchQuery);
                    });
                }) : fullOrdered;

                const viewIdx = currentView.findIndex(v => Number(v.id) === Number(vehicleId));
                if (viewIdx === -1) return;
                const targetViewIdx = viewIdx + direction;
                if (targetViewIdx < 0 || targetViewIdx >= currentView.length) return;

                const targetVehicle = currentView[targetViewIdx];
                const fullIdxA = fullOrdered.findIndex(v => Number(v.id) === Number(vehicleId));
                const fullIdxB = fullOrdered.findIndex(v => Number(v.id) === Number(targetVehicle.id));
                if (fullIdxA === -1 || fullIdxB === -1) return;

                const temp = fullOrdered[fullIdxA];
                fullOrdered[fullIdxA] = fullOrdered[fullIdxB];
                fullOrdered[fullIdxB] = temp;

                this.customOrder = fullOrdered.map(v => Number(v.id));
                this.sortMode = 'custom';
                try {
                    localStorage.setItem('fleet_calendar_custom_order', JSON.stringify(this.customOrder));
                    localStorage.setItem('fleet_calendar_sort_mode', 'custom');
                } catch (e) {}
                this.syncSortUI();
                this.render();
            },

            getOrderedVehicles() {
                const list = [...(this.vehicles || [])];
                if (this.sortMode === 'custom' && Array.isArray(this.customOrder) && this.customOrder.length > 0) {
                    const orderMap = new Map();
                    this.customOrder.forEach((id, index) => orderMap.set(Number(id), index));
                    list.sort((a, b) => {
                        const idA = Number(a.id);
                        const idB = Number(b.id);
                        const idxA = orderMap.has(idA) ? orderMap.get(idA) : 99999;
                        const idxB = orderMap.has(idB) ? orderMap.get(idB) : 99999;
                        return idxA - idxB;
                    });
                    return list;
                }

                if (this.sortMode === 'brand_asc') {
                    list.sort((a, b) => {
                        const nameA = `${a.brand || ''} ${a.model || ''}`.trim().toLowerCase();
                        const nameB = `${b.brand || ''} ${b.model || ''}`.trim().toLowerCase();
                        return nameA.localeCompare(nameB);
                    });
                } else if (this.sortMode === 'brand_desc') {
                    list.sort((a, b) => {
                        const nameA = `${a.brand || ''} ${a.model || ''}`.trim().toLowerCase();
                        const nameB = `${b.brand || ''} ${b.model || ''}`.trim().toLowerCase();
                        return nameB.localeCompare(nameA);
                    });
                } else if (this.sortMode === 'category') {
                    const catPriority = { 'van': 1, 'suv': 2, 'mpv': 3, 'auv': 3, 'sedan': 4, 'hatchback': 5, 'pickup': 6 };
                    list.sort((a, b) => {
                        const cA = this.getVehicleCategory(a).toLowerCase();
                        const cB = this.getVehicleCategory(b).toLowerCase();
                        const pA = catPriority[cA] || 10;
                        const pB = catPriority[cB] || 10;
                        if (pA !== pB) return pA - pB;
                        return `${a.brand} ${a.model}`.localeCompare(`${b.brand} ${b.model}`);
                    });
                } else if (this.sortMode === 'plate_asc') {
                    list.sort((a, b) => (a.plate_number || '').localeCompare(b.plate_number || ''));
                } else if (this.sortMode === 'most_booked') {
                    const counts = {};
                    (this.bookings || []).forEach(b => {
                        const st = String(b.status || '').toLowerCase().trim();
                        if (st !== 'cancelled' && st !== 'rejected') {
                            const vid = Number(b.vehicle_id);
                            counts[vid] = (counts[vid] || 0) + 1;
                        }
                    });
                    list.sort((a, b) => {
                        const cA = counts[Number(a.id)] || 0;
                        const cB = counts[Number(b.id)] || 0;
                        if (cB !== cA) return cB - cA;
                        return Number(a.id) - Number(b.id);
                    });
                } else if (this.sortMode === 'rate_desc') {
                    list.sort((a, b) => parseFloat(b.daily_rate || 0) - parseFloat(a.daily_rate || 0));
                } else if (this.sortMode === 'rate_asc') {
                    list.sort((a, b) => parseFloat(a.daily_rate || 0) - parseFloat(b.daily_rate || 0));
                }
                return list;
            }
        };
    });

    test('should maintain default server order when sortMode is default', () => {
        const ordered = FleetCalendar.getOrderedVehicles();
        expect(ordered.map(v => v.id)).toEqual([1, 2, 3, 4]);
    });

    test('should sort alphabetically A to Z by brand/model', () => {
        FleetCalendar.onSortChange('brand_asc');
        const ordered = FleetCalendar.getOrderedVehicles();
        // Fortuner, Hiace, Innova, Vios
        expect(ordered.map(v => v.model)).toEqual(['Fortuner', 'Hiace', 'Innova', 'Vios']);
        expect(FleetCalendar.render).toHaveBeenCalled();
    });

    test('should sort alphabetically Z to A by brand/model', () => {
        FleetCalendar.onSortChange('brand_desc');
        const ordered = FleetCalendar.getOrderedVehicles();
        // Vios, Innova, Hiace, Fortuner
        expect(ordered.map(v => v.model)).toEqual(['Vios', 'Innova', 'Hiace', 'Fortuner']);
    });

    test('should sort by vehicle category priority: Van -> SUV -> MPV -> Sedan', () => {
        FleetCalendar.onSortChange('category');
        const ordered = FleetCalendar.getOrderedVehicles();
        expect(ordered.map(v => v.model)).toEqual(['Hiace', 'Fortuner', 'Innova', 'Vios']);
    });

    test('should sort by plate number A to Z', () => {
        FleetCalendar.onSortChange('plate_asc');
        const ordered = FleetCalendar.getOrderedVehicles();
        // ABC 456 (2), DEF 789 (3), GHI 101 (4), XYZ 123 (1)
        expect(ordered.map(v => v.id)).toEqual([2, 3, 4, 1]);
    });

    test('should sort by most booked active bookings descending', () => {
        FleetCalendar.onSortChange('most_booked');
        const ordered = FleetCalendar.getOrderedVehicles();
        // Fortuner (2 bookings: id 3), Hiace (1 booking: id 2), others 0
        expect(ordered[0].id).toBe(3);
        expect(ordered[1].id).toBe(2);
    });

    test('should sort by daily rental rate descending and ascending', () => {
        FleetCalendar.onSortChange('rate_desc');
        let ordered = FleetCalendar.getOrderedVehicles();
        // Hiace (3500), Fortuner (3000), Innova (2500), Vios (1800)
        expect(ordered.map(v => v.model)).toEqual(['Hiace', 'Fortuner', 'Innova', 'Vios']);

        FleetCalendar.onSortChange('rate_asc');
        ordered = FleetCalendar.getOrderedVehicles();
        expect(ordered.map(v => v.model)).toEqual(['Vios', 'Innova', 'Fortuner', 'Hiace']);
    });

    test('should manually move vehicle down (swap with next vehicle) and switch to custom mode', () => {
        const mockEvent = { stopPropagation: vi.fn(), preventDefault: vi.fn() };
        // Move Vios (id 1 at index 0) down (+1)
        FleetCalendar.moveVehicle(1, 1, mockEvent);

        expect(mockEvent.stopPropagation).toHaveBeenCalled();
        expect(FleetCalendar.sortMode).toBe('custom');
        const ordered = FleetCalendar.getOrderedVehicles();
        // Index 0 was 1, Index 1 was 2 -> after swap: [2, 1, 3, 4]
        expect(ordered.map(v => v.id)).toEqual([2, 1, 3, 4]);
        expect(localStorage.setItem).toHaveBeenCalledWith('fleet_calendar_sort_mode', 'custom');
    });

    test('should manually move vehicle up (swap with previous vehicle)', () => {
        const mockEvent = { stopPropagation: vi.fn(), preventDefault: vi.fn() };
        // Move Fortuner (id 3 at index 2) up (-1)
        FleetCalendar.moveVehicle(3, -1, mockEvent);

        expect(FleetCalendar.sortMode).toBe('custom');
        const ordered = FleetCalendar.getOrderedVehicles();
        // Original: [1, 2, 3, 4] -> Fortuner swaps with Hiace: [1, 3, 2, 4]
        expect(ordered.map(v => v.id)).toEqual([1, 3, 2, 4]);
    });

    test('should reset vehicle order to default when resetVehicleOrder is called', () => {
        // First set custom order
        FleetCalendar.sortMode = 'custom';
        FleetCalendar.customOrder = [4, 3, 2, 1];
        mockStorage['fleet_calendar_sort_mode'] = 'custom';
        mockStorage['fleet_calendar_custom_order'] = JSON.stringify([4, 3, 2, 1]);

        FleetCalendar.resetVehicleOrder();

        expect(FleetCalendar.sortMode).toBe('default');
        expect(FleetCalendar.customOrder).toEqual([]);
        expect(localStorage.removeItem).toHaveBeenCalledWith('fleet_calendar_sort_mode');
        expect(localStorage.removeItem).toHaveBeenCalledWith('fleet_calendar_custom_order');
        expect(FleetCalendar.getOrderedVehicles().map(v => v.id)).toEqual([1, 2, 3, 4]);
        expect(showNotification).toHaveBeenCalledWith('Vehicle order reset to default', 'info');
    });
});
