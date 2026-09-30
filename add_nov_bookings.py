import sys
import os
import bcrypt

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from config import SUPABASE_DB_URL
import psycopg2
from psycopg2.extras import RealDictCursor

NEW_USERS = [
    {
        "full_name": "Cherrylyn Gardiola",
        "first_name": "Cherrylyn",
        "last_name": "Gardiola",
        "email": "cherrylyn.gardiola88@gmail.com",
        "phone": "09175549210",
        "license_number": "D18-12-005619",
        "license_expiry": "2030-08-15",
        "dob": "1988-08-15",
        "address": "San Antonio, Santo Tomas, Batangas",
        "emergency_name": "Mark Anthony Gardiola",
        "emergency_phone": "09183421955",
        "emergency_rel": "Spouse"
    },
    {
        "full_name": "Marjen Garcia Delos Reyes",
        "first_name": "Marjen",
        "middle_name": "Garcia",
        "last_name": "Delos Reyes",
        "email": "marjen.delosreyes90@gmail.com",
        "phone": "09284918234",
        "license_number": "N03-14-008921",
        "license_expiry": "2031-11-20",
        "dob": "1990-11-20",
        "address": "Darasa, Tanauan City, Batangas",
        "emergency_name": "Ronaldo Delos Reyes",
        "emergency_phone": "09291847562",
        "emergency_rel": "Spouse"
    },
    {
        "full_name": "Christopher Catapang",
        "first_name": "Christopher",
        "last_name": "Catapang",
        "email": "christopher.catapang82@gmail.com",
        "phone": "09193850291",
        "license_number": "D04-09-003417",
        "license_expiry": "2032-04-18",
        "dob": "1982-04-18",
        "address": "Poblacion 2, Tanauan City, Batangas",
        "emergency_name": "Clarisse Catapang",
        "emergency_phone": "09172948102",
        "emergency_rel": "Sibling"
    }
]

ADDITIONAL_BOOKINGS = [
    {
        "user_email": "cherrylyn.gardiola88@gmail.com",
        "vehicle_id": 34, # Toyota Hiace (NCW 3918) - ₱3,999/day
        "start_date": "2026-10-10",
        "end_date": "2026-11-09",
        "days": 30,
        "daily_rate": 3999.0,
        "base_price": 119970.0,
        "discount_amount": 11997.0,
        "total_price": 107973.0,
        "status": "Confirmed",
        "payment_type": "Full",
        "payment_status": "Paid",
        "amount_paid": 107973.0,
        "balance_amount": 0.0,
        "points_earned": 1079,
        "destination": "Laguna & Batangas Provincial Route / Corporate Shuttle",
        "rental_purpose": "Company Monthly Transportation Service",
        "payment_method": "Bank Transfer (BDO)",
        "payment_ref": "BDO-20261010-3501",
        "booking_ref": "BK-20261010-0035",
        "created_at": "2026-10-01 10:00:00+08"
    },
    {
        "user_email": "marjen.delosreyes90@gmail.com",
        "vehicle_id": 23, # Honda BR-V (NID 2724) - ₱2,600/day
        "start_date": "2026-10-17",
        "end_date": "2026-10-24",
        "days": 7,
        "daily_rate": 2600.0,
        "base_price": 18200.0,
        "discount_amount": 1820.0,
        "total_price": 16380.0,
        "status": "Confirmed",
        "payment_type": "Full",
        "payment_status": "Paid",
        "amount_paid": 16380.0,
        "balance_amount": 0.0,
        "points_earned": 163,
        "destination": "Laiya & San Juan, Batangas Beach Resorts",
        "rental_purpose": "Family Vacation & Hipag's Birthday Celebration",
        "payment_method": "GCash",
        "payment_ref": "GCASH-20261017-3602",
        "booking_ref": "BK-20261017-0036",
        "created_at": "2026-10-01 11:30:00+08"
    },
    {
        "user_email": "christopher.catapang82@gmail.com",
        "vehicle_id": 23, # Honda BR-V (NID 2724) - ₱2,600/day
        "start_date": "2026-10-27",
        "end_date": "2026-11-05",
        "days": 9,
        "daily_rate": 2600.0,
        "base_price": 23400.0,
        "discount_amount": 2340.0,
        "total_price": 21060.0,
        "status": "Confirmed",
        "payment_type": "Full",
        "payment_status": "Paid",
        "amount_paid": 21060.0,
        "balance_amount": 0.0,
        "points_earned": 210,
        "destination": "Baguio City & La Union Tour",
        "rental_purpose": "Northern Luzon Family Holiday Tour",
        "payment_method": "GCash",
        "payment_ref": "GCASH-20261027-3703",
        "booking_ref": "BK-20261027-0037",
        "created_at": "2026-10-01 12:45:00+08"
    }
]

def main():
    conn = psycopg2.connect(SUPABASE_DB_URL)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Clear any violation strikes on all users
        cur.execute("UPDATE users SET violation_strikes = 0, booking_suspension_until = NULL, violation_commitment_fee_required = FALSE, violation_permanently_restricted = FALSE")

        hashed_pw = bcrypt.hashpw(b"Customer@2026", bcrypt.gensalt()).decode('utf-8')
        user_id_map = {}

        print("=== Step 1: Create or fetch verified customer accounts ===")
        for u in NEW_USERS:
            cur.execute("SELECT id FROM users WHERE email = %s", (u['email'],))
            existing = cur.fetchone()
            if existing:
                uid = existing['id']
                print(f"User {u['email']} already exists (ID: {uid})")
            else:
                cur.execute("""
                    INSERT INTO users (
                        email, password, first_name, middle_name, last_name,
                        phone, role, is_verified, is_email_verified, auth_provider,
                        license_number, license_expiry, license_type, license_image_url,
                        created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, 'customer', 2, TRUE, 'local',
                        %s, %s, 'A, B',
                        'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/license_front_verified.jpg',
                        NOW()
                    ) RETURNING id, user_id
                """, (
                    u['email'], hashed_pw, u['first_name'], u.get('middle_name'), u['last_name'],
                    u['phone'], u['license_number'], u['license_expiry']
                ))
                new_row = cur.fetchone()
                uid = new_row['id'] or new_row['user_id']
                print(f"Created new verified user: {u['full_name']} (ID: {uid})")

                # Insert license_details
                cur.execute("""
                    INSERT INTO license_details (
                        user_id, full_name, date_of_birth, license_number, expiry_date,
                        issuing_country_state, license_class, emergency_contact_name,
                        emergency_contact_phone, emergency_contact_relationship,
                        license_front_url
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, 'A, B', %s, %s, %s,
                        'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/license_front_verified.jpg'
                    )
                """, (
                    uid, u['full_name'], u['dob'], u['license_number'], u['license_expiry'],
                    u['address'], u['emergency_name'], u['emergency_phone'], u['emergency_rel']
                ))

            user_id_map[u['email']] = uid

        print("\n=== Step 2: Insert Additional Bookings (Through Nov 2026) ===")
        for b in ADDITIONAL_BOOKINGS:
            uid = user_id_map[b['user_email']]
            # Check if this booking reference already exists
            cur.execute("SELECT id FROM bookings WHERE reference_num = %s", (b['booking_ref'],))
            exists_b = cur.fetchone()
            if exists_b:
                print(f"Booking {b['booking_ref']} already exists (ID: {exists_b['id']})")
                b_id = exists_b['id']
            else:
                cur.execute("""
                    INSERT INTO bookings (
                        user_id, vehicle_id, start_date, end_date,
                        start_time, end_time,
                        pickup_location, pickup_province, pickup_municipality, pickup_barangay,
                        return_province, return_municipality, return_barangay,
                        rental_type, service_type, delivery_fee,
                        destination, rental_purpose,
                        base_price, addon_price, tax_amount, discount_amount, total_price,
                        status, payment_type, payment_status,
                        amount_paid, balance_amount,
                        points_earned, points_redeemed,
                        reference_num, agreed_to_terms,
                        created_at
                    ) VALUES (
                        %s, %s, %s, %s,
                        '08:00 AM', '08:00 PM',
                        'Tanauan Batangas Hub', 'Batangas', 'Tanauan', 'Poblacion',
                        'Batangas', 'Tanauan', 'Poblacion',
                        'Self Drive', 'pickup', 0.00,
                        %s, %s,
                        %s, 0.00, 0.00, %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, 0,
                        %s, TRUE,
                        %s
                    ) RETURNING booking_id, id
                """, (
                    uid, b['vehicle_id'], b['start_date'], b['end_date'],
                    b['destination'], b['rental_purpose'],
                    b['base_price'], b['discount_amount'], b['total_price'],
                    b['status'], b['payment_type'], b['payment_status'],
                    b['amount_paid'], b['balance_amount'],
                    b['points_earned'],
                    b['booking_ref'],
                    b['created_at']
                ))
                b_row = cur.fetchone()
                b_id = b_row['booking_id']
                print(f"-> Inserted Booking #{b_id} for User {uid} ({b['user_email']}) - {b['start_date']} to {b['end_date']} | Total: PHP {b['total_price']:,.2f}")

                # Insert payment record
                cur.execute("""
                    INSERT INTO payments (
                        booking_id, amount, method, reference_number, status
                    ) VALUES (
                        %s, %s, %s, %s, 'completed'
                    ) RETURNING payment_id
                """, (
                    b_id, b['amount_paid'], b['payment_method'], b['payment_ref']
                ))
                p_id = cur.fetchone()['payment_id']
                print(f"   Payment recorded: Payment #{p_id} - PHP {b['amount_paid']:,.2f} via {b['payment_method']} (Ref: {b['payment_ref']})")

        # Step 3: Recalculate and update loyalty points for all users
        print("\n=== Step 3: Synchronizing Loyalty Points ===")
        cur.execute("""
            UPDATE users u
            SET loyalty_points = COALESCE((
                SELECT SUM(b.points_earned)
                FROM bookings b
                WHERE b.user_id = u.id AND b.payment_status IN ('Paid', 'Fully Paid')
            ), 0)
            WHERE u.role = 'customer'
        """)

        conn.commit()
        print("Committed all additional bookings through November!")

        # Step 4: Summary
        print("\n=== GRAND TOTAL SUMMARY OF ALL BOOKINGS ===")
        cur.execute("""
            SELECT 
                COUNT(*) as total_bookings,
                SUM(total_price) as total_revenue,
                SUM(amount_paid) as total_paid,
                SUM(balance_amount) as total_balance
            FROM bookings
            WHERE payment_status IN ('Paid', 'Fully Paid')
        """)
        totals = cur.fetchone()
        print(f"Total Paid Bookings: {totals['total_bookings']}")
        print(f"Total Revenue: PHP {float(totals['total_revenue']):,.2f}")
        print(f"Total Balance: PHP {float(totals['total_balance']):,.2f}")

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
