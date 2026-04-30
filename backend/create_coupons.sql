-- Create Coupons Table
CREATE TABLE IF NOT EXISTS coupons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    discount_percent INTEGER NOT NULL CHECK (discount_percent > 0 AND discount_percent <= 100),
    expiry_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    usage_limit INTEGER DEFAULT NULL,
    times_used INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed with a test coupon
INSERT INTO coupons (code, discount_percent, expiry_date, is_active)
VALUES ('WELCOME10', 10, '2027-12-31', TRUE)
ON CONFLICT (code) DO NOTHING;

INSERT INTO coupons (code, discount_percent, expiry_date, is_active)
VALUES ('AUTORIDE10', 10, '2027-12-31', TRUE)
ON CONFLICT (code) DO NOTHING;
