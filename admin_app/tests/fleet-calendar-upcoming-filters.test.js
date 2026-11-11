/**
 * Unit Tests for Fleet Calendar Filters & Upcoming Months Booking Count Badges
 * Extracts and tests the production methods directly from admin_app/index.html.
 */

import fs from 'fs';
import path from 'path';
import { describe, test, expect, beforeEach } from 'vitest';

const htmlPath = path.resolve(__dirname, '../index.html');
const htmlContent = fs.readFileSync(htmlPath, 'utf-8');

function buildProductionMethodsSubset() {
    const startMarker = 'bookingPassesStatusFilter(b, opts) {';
    const endMarker = 'onSaBranchSelectChange(val) {';
    const sIdx = htmlContent.indexOf(startMarker);
    const eIdx = htmlContent.indexOf(endMarker);
    if (sIdx === -1 || eIdx === -1) {
        throw new Error('Could not locate FleetCalendar upcoming/filter methods in index.html');
    }
    const methodsChunk = htmlContent.slice(sIdx, eIdx);
    // Wrap inside an object literal and return it
    return new Function(`return { ${methodsChunk} _end: true };`)();
}

describe('FleetCalendar Filters & Upcoming Months Summary', () => {
    let fc;
    const mockNow = new Date(2026, 10, 11); // Nov 11, 2026 (Month 1 = Nov 2026, Month 2 = Dec 2026, Month 3 = Jan 2027)

    const sampleVehicles = [
        { id: 1, brand: 'Toyota', model: 'Hiace', category: 'Van', plate_number: 'NCW 3918', location: 'San Pablo City, Laguna' },
        { id: 2, brand: 'Toyota', model: 'Fortuner', category: 'SUV', plate_number: 'DBH 8812', location: 'Tanauan/Sto. Tomas, Batangas' },
        { id: 3, brand: 'Toyota', model: 'Vios', category: 'Sedan', plate_number: 'DBJ 9483', location: 'Tanauan/Sto. Tomas, Batangas' }
    ];

    const sampleBookings = [
        // Month 1 & 2 (Nov & Dec 2026) -> MUST NOT appear in upcoming badges (starts 3rd month!)
        { id: 101, vehicle_id: 1, start_date: '2026-11-15', end_date: '2026-11-18', status: 'Confirmed', balance_amount: 0, customer_name: 'Alice' },
        { id: 102, vehicle_id: 2, start_date: '2026-12-10', end_date: '2026-12-12', status: 'Confirmed', balance_amount: 500, customer_name: 'Bob' },
        // Month 3 (Jan 2027) -> MUST appear
        { id: 201, vehicle_id: 1, start_date: '2027-01-05', end_date: '2027-01-07', status: 'Confirmed', balance_amount: 2000, customer_name: 'Carlos' },
        // Spanning Jan 30 - Feb 2 -> increments BOTH Jan 2027 and Feb 2027
        { id: 202, vehicle_id: 2, start_date: '2027-01-30', end_date: '2027-02-02', status: 'Approved', balance_amount: 0, customer_name: 'Diana' },
        // Feb 2027 Pending -> hidden under default 'all_active' upcoming, visible under 'pending' / 'all_with_pending'
        { id: 203, vehicle_id: 3, start_date: '2027-02-14', end_date: '2027-02-16', status: 'Pending', balance_amount: 3000, customer_name: 'Evan' },
        // Mar 2027 Cancelled -> NEVER counted
        { id: 204, vehicle_id: 1, start_date: '2027-03-01', end_date: '2027-03-03', status: 'Cancelled', balance_amount: 0, customer_name: 'Frank' },
        // Sep 2027 (11th month out / >8M out) -> visible in 12M out, excluded in 8M out
        { id: 205, vehicle_id: 2, start_date: '2027-09-10', end_date: '2027-09-12', status: 'Confirmed', balance_amount: 1500, customer_name: 'Grace' }
    ];

    beforeEach(() => {
        const subset = buildProductionMethodsSubset();
        fc = Object.assign({
            currentDate: new Date(2026, 10, 1),
            searchQuery: '',
            branchFilter: 'all',
            typeFilter: 'all',
            statusFilter: 'all_active',
            upcomingHorizonMonths: 12,
            vehicles: sampleVehicles,
            upcomingBookings: sampleBookings,
            getVehicleBranch(v) {
                const loc = String((v && v.location) || '').toLowerCase();
                if (loc.includes('san pablo')) return { key: 'spc' };
                if (loc.includes('tanauan')) return { key: 'tanauan' };
                return { key: 'other' };
            },
            getVehicleCategory(v) {
                return v.category || 'Other';
            }
        }, subset);
    });

    test('Toolbar contains required Filter & Upcoming Months DOM elements', () => {
        expect(htmlContent).toContain('id="fleetCalendarTypeSelect"');
        expect(htmlContent).toContain('id="fleetCalendarStatusSelect"');
        expect(htmlContent).toContain('id="fcUpcomingMonthsWrap"');
        expect(htmlContent).toContain('id="fcUpcomingMonthsList"');
        expect(htmlContent).toContain('id="fcUpcomingHorizonSelect"');
        expect(htmlContent).toContain('id="fcResetFiltersBtn"');
    });

    test('Starts at 3rd month (Jan 2027), omits zero months, excludes cancelled & pending by default', () => {
        const buckets = fc.getUpcomingMonthBuckets(mockNow, sampleBookings, sampleVehicles);
        const mapped = buckets.map(b => `${b.shortLabel}:${b.count}`);
        // Jan: Carlos + Diana = 2; Feb: Diana = 1 (Evan is Pending); Mar..Aug = 0 (omitted); Sep: Grace = 1
        expect(mapped).toEqual(['Jan:2', 'Feb:1', 'Sep:1']);
    });

    test('8M horizon stops before Sep 2027 (returns only Jan & Feb)', () => {
        fc.upcomingHorizonMonths = 8;
        const buckets = fc.getUpcomingMonthBuckets(mockNow, sampleBookings, sampleVehicles);
        const mapped = buckets.map(b => `${b.shortLabel}:${b.count}`);
        expect(mapped).toEqual(['Jan:2', 'Feb:1']);
    });

    test('Respects Branch Filter, Vehicle Type Filter, Status/Balance Due, and Search Filter', () => {
        // Branch: tanauan -> Diana (SUV), Evan (Sedan, pending), Grace (SUV)
        fc.branchFilter = 'tanauan';
        expect(fc.getUpcomingMonthBuckets(mockNow, sampleBookings, sampleVehicles).map(b => `${b.shortLabel}:${b.count}`))
            .toEqual(['Jan:1', 'Feb:1', 'Sep:1']);

        // Vehicle Type: Van -> only Carlos (Jan)
        fc.branchFilter = 'all';
        fc.typeFilter = 'Van';
        expect(fc.getUpcomingMonthBuckets(mockNow, sampleBookings, sampleVehicles).map(b => `${b.shortLabel}:${b.count}`))
            .toEqual(['Jan:1']);

        // Status: pending -> only Evan (Feb)
        fc.typeFilter = 'all';
        fc.statusFilter = 'pending';
        expect(fc.getUpcomingMonthBuckets(mockNow, sampleBookings, sampleVehicles).map(b => `${b.shortLabel}:${b.count}`))
            .toEqual(['Feb:1']);

        // Status: balance_due -> Carlos (Jan, 2000), Evan (Feb, 3000), Grace (Sep, 1500)
        fc.statusFilter = 'balance_due';
        expect(fc.getUpcomingMonthBuckets(mockNow, sampleBookings, sampleVehicles).map(b => `${b.shortLabel}:${b.count}`))
            .toEqual(['Jan:1', 'Feb:1', 'Sep:1']);

        // Search: Carlos
        fc.statusFilter = 'all_active';
        fc.searchQuery = 'carlos';
        expect(fc.getUpcomingMonthBuckets(mockNow, sampleBookings, sampleVehicles).map(b => `${b.shortLabel}:${b.count}`))
            .toEqual(['Jan:1']);
    });
});
