-- =====================================================================
-- Rollback: 001_rollback_extension_tables.sql
-- Description: Rollback booking extension and conflict resolution tables
-- Created: 2024
-- Wave: 1 - Database Foundation
-- =====================================================================

-- This rollback script removes all database changes made by 001_add_extension_tables.sql
-- CAUTION: This will delete all extension data. Use only if migration needs to be undone.

BEGIN;

-- =====================================================================
-- 1. Drop triggers (must be dropped before functions)
-- =====================================================================
DROP TRIGGER IF EXISTS update_booking_extensions_updated_at ON booking_extensions;
DROP TRIGGER IF EXISTS update_booking_conflicts_updated_at ON booking_conflicts;

-- Note: We don't drop the update_updated_at_column() function as it may be used by other tables

-- =====================================================================
-- 2. Remove foreign key constraint from bookings table
-- =====================================================================
ALTER TABLE bookings DROP CONSTRAINT IF EXISTS bookings_conflict_id_fkey;

-- =====================================================================
-- 3. Remove columns from bookings table
-- =====================================================================
ALTER TABLE bookings DROP COLUMN IF EXISTS conflict_id;
ALTER TABLE bookings DROP COLUMN IF EXISTS is_conflict_affected;
ALTER TABLE bookings DROP COLUMN IF EXISTS extension_count;
ALTER TABLE bookings DROP COLUMN IF EXISTS has_active_extension;

-- =====================================================================
-- 4. Drop extension_payments table (and its indexes automatically)
-- =====================================================================
DROP TABLE IF EXISTS extension_payments CASCADE;

-- =====================================================================
-- 5. Drop booking_conflicts table (and its indexes automatically)
-- =====================================================================
-- Note: Must be dropped before booking_extensions due to foreign key
DROP TABLE IF EXISTS booking_conflicts CASCADE;

-- =====================================================================
-- 6. Drop booking_extensions table (and its indexes automatically)
-- =====================================================================
DROP TABLE IF EXISTS booking_extensions CASCADE;

COMMIT;

-- =====================================================================
-- Rollback Complete
-- =====================================================================
-- All extension feature database changes have been removed:
--   - booking_extensions table dropped
--   - booking_conflicts table dropped
--   - extension_payments table dropped
--   - 4 columns removed from bookings table
--   - All foreign keys and indexes automatically removed
--   - All triggers removed
-- 
-- The database is now in its pre-migration state.
-- =====================================================================
