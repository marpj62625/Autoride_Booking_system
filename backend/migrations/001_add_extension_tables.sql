-- =====================================================================
-- Migration: 001_add_extension_tables.sql
-- Description: Add booking extension and conflict resolution tables
-- Created: 2024
-- Wave: 1 - Database Foundation
-- =====================================================================

-- This migration adds support for booking extensions with conflict resolution:
-- 1. booking_extensions: Stores extension requests and approvals
-- 2. booking_conflicts: Tracks conflicts when extensions overlap with future bookings
-- 3. extension_payments: Records payment transactions for approved extensions
-- 4. Adds extension tracking columns to bookings table (with DEFAULT values for backward compatibility)

BEGIN;

-- =====================================================================
-- 1. Create booking_extensions table
-- =====================================================================
CREATE TABLE IF NOT EXISTS booking_extensions (
    extension_id SERIAL PRIMARY KEY,
    booking_id INT NOT NULL,
    requested_by_user_id INT NOT NULL,
    original_end_date DATE NOT NULL,
    requested_end_date DATE NOT NULL,
    additional_days INT NOT NULL,
    additional_cost DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Rejected', 'Cancelled')),
    admin_notes TEXT,
    approved_by_admin_id INT,
    approved_at TIMESTAMP,
    has_conflicts BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (requested_by_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by_admin_id) REFERENCES admins(id) ON DELETE SET NULL
);

COMMENT ON TABLE booking_extensions IS 'Stores customer extension requests and admin approvals with cost calculations';
COMMENT ON COLUMN booking_extensions.status IS 'Extension request status: Pending, Approved, Rejected, or Cancelled';
COMMENT ON COLUMN booking_extensions.has_conflicts IS 'Flag indicating if this extension overlaps with future bookings';

-- =====================================================================
-- 2. Create booking_conflicts table
-- =====================================================================
CREATE TABLE IF NOT EXISTS booking_conflicts (
    conflict_id SERIAL PRIMARY KEY,
    extension_id INT NOT NULL,
    affected_booking_id INT NOT NULL,
    affected_user_id INT NOT NULL,
    conflict_start_date DATE NOT NULL,
    conflict_end_date DATE NOT NULL,
    resolution_status VARCHAR(30) DEFAULT 'Pending' CHECK (resolution_status IN ('Pending', 'Alternative_Selected', 'Refund_Processed', 'Auto_Cancelled')),
    resolution_deadline TIMESTAMP NOT NULL,
    selected_alternative_vehicle_id INT,
    refund_amount DECIMAL(10,2),
    refund_status VARCHAR(20) CHECK (refund_status IN ('Pending', 'Processing', 'Completed', 'Failed')),
    refund_transaction_id VARCHAR(100),
    customer_notified_at TIMESTAMP,
    customer_responded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (extension_id) REFERENCES booking_extensions(extension_id) ON DELETE CASCADE,
    FOREIGN KEY (affected_booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (affected_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (selected_alternative_vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL
);

COMMENT ON TABLE booking_conflicts IS 'Tracks conflicts when extensions overlap with future bookings and their resolutions';
COMMENT ON COLUMN booking_conflicts.resolution_status IS 'Customer choice: Pending, Alternative_Selected, Refund_Processed, or Auto_Cancelled';
COMMENT ON COLUMN booking_conflicts.resolution_deadline IS 'Customer must respond by this timestamp (72 hours from notification)';

-- =====================================================================
-- 3. Create extension_payments table
-- =====================================================================
CREATE TABLE IF NOT EXISTS extension_payments (
    payment_id SERIAL PRIMARY KEY,
    extension_id INT NOT NULL,
    booking_id INT NOT NULL,
    user_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('GCash', 'Maya', 'PayMongo', 'Cash')),
    payment_status VARCHAR(20) DEFAULT 'Pending' CHECK (payment_status IN ('Pending', 'Completed', 'Failed', 'Refunded')),
    payment_proof_url VARCHAR(500),
    transaction_reference VARCHAR(100),
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (extension_id) REFERENCES booking_extensions(extension_id) ON DELETE CASCADE,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

COMMENT ON TABLE extension_payments IS 'Records payment transactions for approved booking extensions';
COMMENT ON COLUMN extension_payments.payment_method IS 'Payment method used: GCash, Maya, PayMongo, or Cash';

-- =====================================================================
-- 4. Add extension tracking columns to bookings table
-- =====================================================================
-- Using DEFAULT values ensures backward compatibility with existing queries
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS has_active_extension BOOLEAN DEFAULT FALSE;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS extension_count INT DEFAULT 0;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS is_conflict_affected BOOLEAN DEFAULT FALSE;
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS conflict_id INT DEFAULT NULL;

COMMENT ON COLUMN bookings.has_active_extension IS 'Flag indicating if this booking currently has an active extension';
COMMENT ON COLUMN bookings.extension_count IS 'Count of extensions requested on this booking (max 1 per booking)';
COMMENT ON COLUMN bookings.is_conflict_affected IS 'Flag indicating if this booking is affected by a conflict';
COMMENT ON COLUMN bookings.conflict_id IS 'References the conflict record if this booking is affected';

-- =====================================================================
-- 5. Add foreign key constraint for bookings.conflict_id
-- =====================================================================
-- Added separately after booking_conflicts table is created
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'bookings_conflict_id_fkey'
    ) THEN
        ALTER TABLE bookings 
        ADD CONSTRAINT bookings_conflict_id_fkey 
        FOREIGN KEY (conflict_id) REFERENCES booking_conflicts(conflict_id) ON DELETE SET NULL;
    END IF;
END $$;

-- =====================================================================
-- 6. Create indexes on frequently queried columns
-- =====================================================================

-- Indexes for booking_extensions table
CREATE INDEX IF NOT EXISTS idx_booking_extensions_booking_id 
    ON booking_extensions(booking_id);
    
CREATE INDEX IF NOT EXISTS idx_booking_extensions_status 
    ON booking_extensions(status);
    
CREATE INDEX IF NOT EXISTS idx_booking_extensions_created_at 
    ON booking_extensions(created_at);

COMMENT ON INDEX idx_booking_extensions_booking_id IS 'Optimizes queries for extension status by booking';
COMMENT ON INDEX idx_booking_extensions_status IS 'Optimizes admin queries for pending/approved extensions';
COMMENT ON INDEX idx_booking_extensions_created_at IS 'Optimizes queries for recent extension requests';

-- Indexes for booking_conflicts table
CREATE INDEX IF NOT EXISTS idx_booking_conflicts_affected_booking_id 
    ON booking_conflicts(affected_booking_id);
    
CREATE INDEX IF NOT EXISTS idx_booking_conflicts_resolution_status 
    ON booking_conflicts(resolution_status);
    
CREATE INDEX IF NOT EXISTS idx_booking_conflicts_resolution_deadline 
    ON booking_conflicts(resolution_deadline);
    
CREATE INDEX IF NOT EXISTS idx_booking_conflicts_created_at 
    ON booking_conflicts(created_at);

COMMENT ON INDEX idx_booking_conflicts_affected_booking_id IS 'Optimizes queries for customer affected booking lookups';
COMMENT ON INDEX idx_booking_conflicts_resolution_status IS 'Optimizes admin dashboard queries for pending resolutions';
COMMENT ON INDEX idx_booking_conflicts_resolution_deadline IS 'Optimizes background job queries for deadline monitoring';
COMMENT ON INDEX idx_booking_conflicts_created_at IS 'Optimizes queries for recent conflicts';

-- Indexes for extension_payments table
CREATE INDEX IF NOT EXISTS idx_extension_payments_extension_id 
    ON extension_payments(extension_id);
    
CREATE INDEX IF NOT EXISTS idx_extension_payments_payment_status 
    ON extension_payments(payment_status);

COMMENT ON INDEX idx_extension_payments_extension_id IS 'Optimizes payment status lookups by extension';
COMMENT ON INDEX idx_extension_payments_payment_status IS 'Optimizes queries for pending/completed payments';

-- =====================================================================
-- 7. Create trigger to auto-update updated_at timestamps
-- =====================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for booking_extensions
DROP TRIGGER IF EXISTS update_booking_extensions_updated_at ON booking_extensions;
CREATE TRIGGER update_booking_extensions_updated_at
    BEFORE UPDATE ON booking_extensions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for booking_conflicts
DROP TRIGGER IF EXISTS update_booking_conflicts_updated_at ON booking_conflicts;
CREATE TRIGGER update_booking_conflicts_updated_at
    BEFORE UPDATE ON booking_conflicts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;

-- =====================================================================
-- Migration Complete
-- =====================================================================
-- Tables created:
--   1. booking_extensions (with 14 columns, 3 foreign keys, 3 indexes)
--   2. booking_conflicts (with 16 columns, 4 foreign keys, 4 indexes)
--   3. extension_payments (with 11 columns, 3 foreign keys, 2 indexes)
-- 
-- Bookings table modified:
--   4 new columns added (has_active_extension, extension_count, is_conflict_affected, conflict_id)
--   1 foreign key constraint added (conflict_id)
--
-- Performance optimizations:
--   9 indexes created for frequently queried columns
--   2 triggers created for automatic timestamp updates
-- =====================================================================
