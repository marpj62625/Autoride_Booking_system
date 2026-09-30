import sys
import os
from datetime import datetime, date

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from config import SUPABASE_DB_URL
import psycopg2
from psycopg2.extras import RealDictCursor

# 16 Official Bookings Definition based on ARC-MONITORING-2026.xlsx and 16 Verified Accounts
# Sept 14, 2026 onwards
BOOKINGS_DATA = [
    {
        "user_id": 25, # Guamil Gabriel Delos Reyes Sanchez
        "vehicle_id": 17, # Toyota Vios XE AT (DAT 1396) - ₱2,000/day
        "start_date": "2026-09-14",
        "end_date": "2026-09-16",
        "days": 2,
        "daily_rate": 2000.0,
        "total_price": 4000.0,
        "status": "Completed",
        "payment_type": "Full",
        "payment_status": "Fully Paid",
        "amount_paid": 4000.0,
        "balance_amount": 0.0,
        "points_earned": 40,
        "destination": "Tagaytay City, Cavite",
        "rental_purpose": "Family Weekend Trip",
        "payment_method": "GCash",
        "payment_ref": "GCASH-20260914-2501",
        "booking_ref": "BK-20260914-0025",
        "created_at": "2026-09-13 14:20:00+08",
        "completed_at": "2026-09-16 20:00:00+08",
        "is_vip": False
    },
    {
        "user_id": 26, # Michael Ortega Jarina
        "vehicle_id": 14, # Toyota Vios J MT (NCX 4117) - ₱1,699/day
        "start_date": "2026-09-15",
        "end_date": "2026-09-17",
        "days": 2,
        "daily_rate": 1699.0,
        "total_price": 3398.0,
        "status": "Completed",
        "payment_type": "Full",
        "payment_status": "Fully Paid",
        "amount_paid": 3398.0,
        "balance_amount": 0.0,
        "points_earned": 33,
        "destination": "Calamba & Los Baños, Laguna",
        "rental_purpose": "Business & Client Meeting",
        "payment_method": "Bank Transfer (BDO)",
        "payment_ref": "BDO-20260915-2602",
        "booking_ref": "BK-20260915-0026",
        "created_at": "2026-09-14 10:15:00+08",
        "completed_at": "2026-09-17 19:30:00+08",
        "is_vip": False
    },
    {
        "user_id": 27, # Allan Jr. Tan Anas
        "vehicle_id": 23, # Honda BR-V (NID 2724) - ₱2,600/day
        "start_date": "2026-09-16",
        "end_date": "2026-09-18",
        "days": 2,
        "daily_rate": 2600.0,
        "total_price": 5200.0,
        "status": "Completed",
        "payment_type": "Full",
        "payment_status": "Fully Paid",
        "amount_paid": 5200.0,
        "balance_amount": 0.0,
        "points_earned": 52,
        "destination": "Nasugbu, Batangas",
        "rental_purpose": "Beach Vacation with Friends",
        "payment_method": "GCash",
        "payment_ref": "GCASH-20260916-2703",
        "booking_ref": "BK-20260916-0027",
        "created_at": "2026-09-15 16:45:00+08",
        "completed_at": "2026-09-18 20:15:00+08",
        "is_vip": False
    },
    {
        "user_id": 28, # Villy Sepuesca Arroz
        "vehicle_id": 27, # Toyota Innova XE AT (CCK 1126) - ₱3,000/day
        "start_date": "2026-09-17",
        "end_date": "2026-09-19",
        "days": 2,
        "daily_rate": 3000.0,
        "total_price": 6000.0,
        "status": "Completed",
        "payment_type": "Full",
        "payment_status": "Fully Paid",
        "amount_paid": 6000.0,
        "balance_amount": 0.0,
        "points_earned": 60,
        "destination": "Lucena City, Quezon",
        "rental_purpose": "Family Reunion",
        "payment_method": "Cash",
        "payment_ref": "CSH-20260917-2804",
        "booking_ref": "BK-20260917-0028",
        "created_at": "2026-09-16 11:30:00+08",
        "completed_at": "2026-09-19 20:00:00+08",
        "is_vip": False
    },
    {
        "user_id": 29, # Julius Sensida Labrador
        "vehicle_id": 34, # Toyota Hiace (NCW 3918) - ₱3,999/day
        "start_date": "2026-09-18",
        "end_date": "2026-09-20",
        "days": 2,
        "daily_rate": 3999.0,
        "total_price": 7998.0,
        "status": "Completed",
        "payment_type": "Full",
        "payment_status": "Fully Paid",
        "amount_paid": 7998.0,
        "balance_amount": 0.0,
        "points_earned": 79,
        "destination": "Baguio City",
        "rental_purpose": "Company Team Building",
        "payment_method": "GCash",
        "payment_ref": "GCASH-20260918-2905",
        "booking_ref": "BK-20260918-0029",
        "created_at": "2026-09-17 09:00:00+08",
        "completed_at": "2026-09-20 21:00:00+08",
        "is_vip": False
    },
    {
        "user_id": 38, # Arl Junell Ramos Tobias
        "vehicle_id": 17, # Toyota Vios XE AT (DAT 1396) - ₱2,000/day
        "start_date": "2026-09-18",
        "end_date": "2026-09-20",
        "days": 2,
        "daily_rate": 2000.0,
        "total_price": 4000.0,
        "status": "Completed",
        "payment_type": "Full",
        "payment_status": "Fully Paid",
        "amount_paid": 4000.0,
        "balance_amount": 0.0,
        "points_earned": 40,
        "destination": "Alabang, Muntinlupa",
        "rental_purpose": "Weekend Shopping & Personal",
        "payment_method": "Maya",
        "payment_ref": "MAYA-20260918-3806",
        "booking_ref": "BK-20260918-0038",
        "created_at": "2026-09-17 18:00:00+08",
        "completed_at": "2026-09-20 19:45:00+08",
        "is_vip": False
    },
    {
        "user_id": 39, # Rolly Corton Pelicano
        "vehicle_id": 23, # Honda BR-V (NID 2724) - ₱2,600/day
        "start_date": "2026-09-19",
        "end_date": "2026-09-21",
        "days": 2,
        "daily_rate": 2600.0,
        "total_price": 5200.0,
        "status": "Completed",
        "payment_type": "Full",
        "payment_status": "Fully Paid",
        "amount_paid": 5200.0,
        "balance_amount": 0.0,
        "points_earned": 52,
        "destination": "Laiya, San Juan, Batangas",
        "rental_purpose": "Family Outing",
        "payment_method": "GCash",
        "payment_ref": "GCASH-20260919-3907",
        "booking_ref": "BK-20260919-0039",
        "created_at": "2026-09-18 13:10:00+08",
        "completed_at": "2026-09-21 20:30:00+08",
        "is_vip": False
    },
    {
        "user_id": 40, # Vicmar Goloran Alquino
        "vehicle_id": 27, # Toyota Innova XE AT (CCK 1126) - ₱3,000/day
        "start_date": "2026-09-19",
        "end_date": "2026-09-21",
        "days": 2,
        "daily_rate": 3000.0,
        "total_price": 6000.0,
        "status": "Completed",
        "payment_type": "Full",
        "payment_status": "Fully Paid",
        "amount_paid": 6000.0,
        "balance_amount": 0.0,
        "points_earned": 60,
        "destination": "Lipa City & Batangas City",
        "rental_purpose": "Official Business",
        "payment_method": "GCash",
        "payment_ref": "GCASH-20260919-4008",
        "booking_ref": "BK-20260919-0040",
        "created_at": "2026-09-18 15:30:00+08",
        "completed_at": "2026-09-21 20:00:00+08",
        "is_vip": False
    },
    {
        "user_id": 41, # Danny Lastra Calix
        "vehicle_id": 17, # Toyota Vios XE AT (DAT 1396) - ₱2,000/day
        "start_date": "2026-09-19",
        "end_date": "2026-09-21",
        "days": 2,
        "daily_rate": 2000.0,
        "total_price": 4000.0,
        "status": "Completed",
        "payment_type": "Full",
        "payment_status": "Fully Paid",
        "amount_paid": 4000.0,
        "balance_amount": 0.0,
        "points_earned": 40,
        "destination": "Santa Rosa, Laguna",
        "rental_purpose": "Family Gathering",
        "payment_method": "Cash",
        "payment_ref": "CSH-20260919-4109",
        "booking_ref": "BK-20260919-0041",
        "created_at": "2026-09-18 17:00:00+08",
        "completed_at": "2026-09-21 19:30:00+08",
        "is_vip": False
    },
    {
        "user_id": 42, # John Robin Castillo Uri
        "vehicle_id": 27, # Toyota Innova XE AT (CCK 1126) - ₱3,000/day
        "start_date": "2026-09-20",
        "end_date": "2026-09-22",
        "days": 2,
        "daily_rate": 3000.0,
        "total_price": 6000.0,
        "status": "Completed",
        "payment_type": "Full",
        "payment_status": "Fully Paid",
        "amount_paid": 6000.0,
        "balance_amount": 0.0,
        "points_earned": 60,
        "destination": "Subic Bay, Zambales",
        "rental_purpose": "Vacation Trip",
        "payment_method": "GCash",
        "payment_ref": "GCASH-20260920-4210",
        "booking_ref": "BK-20260920-0042",
        "created_at": "2026-09-19 11:20:00+08",
        "completed_at": "2026-09-22 21:00:00+08",
        "is_vip": False
    },
    {
        "user_id": 43, # Mike Handomon
        "vehicle_id": 14, # Toyota Vios J MT (NCX 4117) - ₱1,699/day
        "start_date": "2026-09-20",
        "end_date": "2026-09-22",
        "days": 2,
        "daily_rate": 1699.0,
        "total_price": 3398.0,
        "status": "Completed",
        "payment_type": "Full",
        "payment_status": "Fully Paid",
        "amount_paid": 3398.0,
        "balance_amount": 0.0,
        "points_earned": 33,
        "destination": "San Pablo City, Laguna",
        "rental_purpose": "Personal Errand",
        "payment_method": "GCash",
        "payment_ref": "GCASH-20260920-4311",
        "booking_ref": "BK-20260920-0043",
        "created_at": "2026-09-19 14:00:00+08",
        "completed_at": "2026-09-22 20:00:00+08",
        "is_vip": False
    },
    {
        "user_id": 44, # Eliezer Cadarit Amador
        "vehicle_id": 14, # Toyota Vios J MT (NCX 4117) - ₱1,699/day
        "start_date": "2026-09-23",
        "end_date": "2026-09-25",
        "days": 2,
        "daily_rate": 1699.0,
        "total_price": 3398.0,
        "status": "Completed",
        "payment_type": "Full",
        "payment_status": "Fully Paid",
        "amount_paid": 3398.0,
        "balance_amount": 0.0,
        "points_earned": 33,
        "destination": "Batangas Port / Pier",
        "rental_purpose": "Airport / Pier Drop-off & Pickup",
        "payment_method": "GCash",
        "payment_ref": "GCASH-20260923-4412",
        "booking_ref": "BK-20260923-0044",
        "created_at": "2026-09-22 10:00:00+08",
        "completed_at": "2026-09-25 19:30:00+08",
        "is_vip": False
    },
    {
        "user_id": 45, # Aldwin A Maghirang
        "vehicle_id": 23, # Honda BR-V (NID 2724) - ₱2,600/day
        "start_date": "2026-09-24",
        "end_date": "2026-09-26",
        "days": 2,
        "daily_rate": 2600.0,
        "total_price": 5200.0,
        "status": "Completed",
        "payment_type": "Full",
        "payment_status": "Fully Paid",
        "amount_paid": 5200.0,
        "balance_amount": 0.0,
        "points_earned": 52,
        "destination": "Taal & Lemery, Batangas",
        "rental_purpose": "Heritage Tour & Family Outing",
        "payment_method": "Bank Transfer (BPI)",
        "payment_ref": "BPI-20260924-4513",
        "booking_ref": "BK-20260924-0045",
        "created_at": "2026-09-23 15:40:00+08",
        "completed_at": "2026-09-26 20:10:00+08",
        "is_vip": False
    },
    {
        "user_id": 46, # Virgilio Gonzales Oña - Regular Customer / VIP (No DP policy)
        "vehicle_id": 17, # Toyota Vios XE AT (DAT 1396) - ₱2,000/day
        "start_date": "2026-09-27",
        "end_date": "2026-09-29",
        "days": 2,
        "daily_rate": 2000.0,
        "total_price": 4000.0,
        "status": "Completed",
        "payment_type": "Pay on Pickup",
        "payment_status": "Fully Paid",
        "amount_paid": 4000.0,
        "balance_amount": 0.0,
        "points_earned": 40,
        "destination": "Metro Manila",
        "rental_purpose": "Medical Appointment & Personal",
        "payment_method": "Cash",
        "payment_ref": "CSH-20260929-4614",
        "booking_ref": "BK-20260927-0046",
        "created_at": "2026-09-26 12:00:00+08",
        "completed_at": "2026-09-29 20:00:00+08",
        "is_vip": True
    },
    {
        "user_id": 47, # Nelso Tipo Delos Reyes
        "vehicle_id": 18, # Toyota Vios XLE AT (DBJ 9483) - ₱2,000/day
        "start_date": "2026-10-01",
        "end_date": "2026-10-07",
        "days": 6,
        "daily_rate": 2000.0,
        "total_price": 12000.0,
        "status": "Confirmed",
        "payment_type": "Downpayment",
        "payment_status": "Deposit Paid",
        "amount_paid": 2400.0, # 20% downpayment
        "balance_amount": 9600.0,
        "points_earned": 120,
        "destination": "Ilocos Norte & Sur Tour",
        "rental_purpose": "Long Distance Vacation",
        "payment_method": "GCash",
        "payment_ref": "GCASH-20260928-4715",
        "booking_ref": "BK-20260928-0047",
        "created_at": "2026-09-28 14:00:00+08",
        "completed_at": None,
        "is_vip": False
    },
    {
        "user_id": 48, # Reymark Dizon Lejano - VIP / Regular Customer (Walang DP / 0 DP)
        "vehicle_id": 34, # Toyota Hiace (NCW 3918) - ₱3,999/day
        "start_date": "2026-10-01",
        "end_date": "2026-10-03",
        "days": 2,
        "daily_rate": 3999.0,
        "total_price": 7998.0,
        "status": "Confirmed",
        "payment_type": "Pay on Pickup",
        "payment_status": "Pending Payment",
        "amount_paid": 0.0, # Walang DP dahil VIP customer!
        "balance_amount": 7998.0,
        "points_earned": 79,
        "destination": "Tanay, Rizal",
        "rental_purpose": "Church & Community Retreat",
        "payment_method": "Cash",
        "payment_ref": None,
        "booking_ref": "BK-20260929-0048",
        "created_at": "2026-09-29 11:00:00+08",
        "completed_at": None,
        "is_vip": True
    }
]

def main():
    conn = psycopg2.connect(SUPABASE_DB_URL)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        print("=== Step 1: Clean existing bookings and payments if any ===")
        cur.execute("DELETE FROM payments")
        cur.execute("DELETE FROM bookings")
        # Reset users loyalty points and violation strikes before seeding
        cur.execute("UPDATE users SET loyalty_points = 0, is_regular_customer = FALSE, regular_customer_manual = FALSE, violation_strikes = 0, booking_suspension_until = NULL, violation_permanently_restricted = FALSE")
        print("Cleared previous test bookings, payments, and violation strikes.")

        print("\n=== Step 2: Inserting 16 Official Bookings ===")
        inserted_bookings = []

        for b in BOOKINGS_DATA:
            # Insert into bookings
            cur.execute("""
                INSERT INTO bookings (
                    user_id, vehicle_id, start_date, end_date,
                    start_time, end_time,
                    pickup_location, pickup_province, pickup_municipality, pickup_barangay,
                    return_province, return_municipality, return_barangay,
                    rental_type, service_type, delivery_fee,
                    destination, rental_purpose,
                    base_price, addon_price, tax_amount, total_price,
                    status, payment_type, payment_status,
                    amount_paid, balance_amount,
                    points_earned, points_redeemed,
                    reference_num, agreed_to_terms,
                    created_at, completed_at
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s
                ) RETURNING id, booking_id
            """, (
                b['user_id'], b['vehicle_id'], b['start_date'], b['end_date'],
                '08:00 AM', '08:00 PM',
                'Tanauan Batangas Hub', 'Batangas', 'Tanauan', 'Poblacion',
                'Batangas', 'Tanauan', 'Poblacion',
                'Self Drive', 'pickup', 0.00,
                b['destination'], b['rental_purpose'],
                b['total_price'], 0.00, 0.00, b['total_price'],
                b['status'], b['payment_type'], b['payment_status'],
                b['amount_paid'], b['balance_amount'],
                b['points_earned'], 0,
                b['booking_ref'], True,
                b['created_at'], b['completed_at']
            ))
            row = cur.fetchone()
            b_id = row['booking_id']

            print(f"-> Inserted Booking #{b_id} for User ID {b['user_id']} ({b['status']}) - {b['start_date']} to {b['end_date']} | Total: PHP {b['total_price']:,.2f}")

            # Step 3: Insert Payment if amount_paid > 0
            if b['amount_paid'] > 0 and b['payment_ref']:
                cur.execute("""
                    INSERT INTO payments (
                        booking_id, amount, method, reference_number, status
                    ) VALUES (
                        %s, %s, %s, %s, %s
                    ) RETURNING payment_id
                """, (
                    b_id, b['amount_paid'], b['payment_method'], b['payment_ref'], 'completed'
                ))
                pay_id = cur.fetchone()['payment_id']
                print(f"   Payment recorded: Payment #{pay_id} - PHP {b['amount_paid']:,.2f} via {b['payment_method']} (Ref: {b['payment_ref']})")
            elif b['amount_paid'] == 0:
                print(f"   No advance downpayment recorded (VIP 0 Downpayment / Pay on Pickup)")

            # Step 4: Loyalty Points Update
            # Completed bookings credit points immediately to user's loyalty_points
            if b['status'] == 'Completed' and b['points_earned'] > 0:
                cur.execute("""
                    UPDATE users
                    SET loyalty_points = loyalty_points + %s
                    WHERE id = %s
                """, (b['points_earned'], b['user_id']))
                print(f"   Credited {b['points_earned']} loyalty points to User #{b['user_id']}")

            # Step 5: VIP / Regular Customer Flag
            if b['is_vip']:
                cur.execute("""
                    UPDATE users
                    SET is_regular_customer = TRUE, regular_customer_manual = TRUE
                    WHERE id = %s
                """, (b['user_id'],))
                print(f"   Marked User #{b['user_id']} as VIP / Regular Customer (Downpayment Exempt)")

            inserted_bookings.append(b_id)

        conn.commit()
        print("\nAll 16 bookings, payments, and VIP flags committed successfully!")

        # Step 6: Verify Database Records
        print("\n=== VERIFICATION: SUMMARY OF ALL 16 BOOKINGS ===")
        cur.execute("""
            SELECT b.id, b.user_id, u.full_name, u.is_regular_customer, u.loyalty_points,
                   v.brand || ' ' || v.model AS vehicle_name, v.plate_number,
                   b.start_date, b.end_date, b.status, b.payment_status,
                   b.amount_paid, b.balance_amount, b.total_price, b.points_earned,
                   p.method AS payment_method, p.reference_number AS payment_ref
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN vehicles v ON b.vehicle_id = v.id
            LEFT JOIN payments p ON b.id = p.booking_id
            ORDER BY b.id
        """)
        results = cur.fetchall()
        for r in results:
            vip_tag = " [VIP/REGULAR - NO DP]" if r['is_regular_customer'] else ""
            print(f"#{r['id']:02d} | User: {r['full_name']} (ID {r['user_id']}){vip_tag} | {r['vehicle_name']} ({r['plate_number']}) | {r['start_date']} to {r['end_date']} | Status: {r['status']} | Pay: {r['payment_status']} (Paid: PHP {r['amount_paid']:,.2f}, Bal: PHP {r['balance_amount']:,.2f}) | Pts: {r['points_earned']} (Acc: {r['loyalty_points']}) | Ref: {r['payment_ref'] or 'N/A'}")

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
