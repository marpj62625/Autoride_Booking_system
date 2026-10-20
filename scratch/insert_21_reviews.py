import sys
from datetime import datetime, timedelta
sys.path.insert(0, 'backend')
from app import app, get_cursor, commit_db

reviews_data = [
    {
        "booking_id": 642,
        "rating": 5,
        "comment": "Sobrang smooth ng drive at napakalamig ng aircon. Maayos kausap ang staff sa pickup."
    },
    {
        "booking_id": 643,
        "rating": 5,
        "comment": "Fuel efficient at malinis ang loob ng sasakyan. Walang naging aberya sa biyahe."
    },
    {
        "booking_id": 644,
        "rating": 5,
        "comment": "Very comfortable gamitin ang BR-V, perfect for long drives with family. 5 stars!"
    },
    {
        "booking_id": 645,
        "rating": 5,
        "comment": "Spacious at malakas humatak ang Innova. Maganda ang suspension, komportable ang mga sakay."
    },
    {
        "booking_id": 646,
        "rating": 5,
        "comment": "Mabilis ang turnover ng susi at very transparent ang inspection bago i-release. Salamat AutoRide!"
    },
    {
        "booking_id": 647,
        "rating": 4,
        "comment": "Malaki at kasya buong tropa. May kaunting traffic lang sa pickup area pero all in all very good unit."
    },
    {
        "booking_id": 648,
        "rating": 5,
        "comment": "Tipid sa gas at napakakinis ng unit. Worth it ang rate."
    },
    {
        "booking_id": 649,
        "rating": 5,
        "comment": "Ang sarap i-drive, responsive ang handling at malinis pagka-deliver. Will book again."
    },
    {
        "booking_id": 650,
        "rating": 5,
        "comment": "Sobrang komportable para sa out of town trip. Mabait din ang nag-asikaso sa amin."
    },
    {
        "booking_id": 651,
        "rating": 4,
        "comment": "Reliable manual Vios. Well-maintained ang makina at preno, very safe gamitin."
    },
    {
        "booking_id": 652,
        "rating": 5,
        "comment": "Solid ang unit! Malamig aircon hanggang third row. Convenient din ang digital booking."
    },
    {
        "booking_id": 653,
        "rating": 5,
        "comment": "Pangalawang beses ko na nag-rent dito, laging maayos at walang hassle. Highly recommended!"
    },
    {
        "booking_id": 654,
        "rating": 5,
        "comment": "Ganda ng interior, amoy bago at mabango. Smooth overall experience with AutoRide."
    },
    {
        "booking_id": 655,
        "rating": 5,
        "comment": "Hassle-free rental process mula reservation hanggang pagbalik. Thank you!"
    },
    {
        "booking_id": 693,
        "rating": 5,
        "comment": "Maayos at alaga ang sasakyan. Quick return process din sa depot."
    },
    {
        "booking_id": 656,
        "rating": 5,
        "comment": "Very sleek and modern unit. Complete accessories and tools. 10/10 service."
    },
    {
        "booking_id": 657,
        "rating": 5,
        "comment": "Very accommodating staff. Napakalaking tulong ng Hiace para sa event namin."
    },
    {
        "booking_id": 695,
        "rating": 5,
        "comment": "1 week rental for our business trip, zero issues encountered. Napakatipid sa konsumo ng gas."
    },
    {
        "booking_id": 696,
        "rating": 4,
        "comment": "Malakas ang makina, swabe sa akyatan. On-time ang handover."
    },
    {
        "booking_id": 697,
        "rating": 5,
        "comment": "Easy to book online, mabilis ma-verify ang requirements. Ganda ng kotse!"
    },
    {
        "booking_id": 658,
        "rating": 5,
        "comment": "Saktong-sakto ang van para sa pamilya. Maayos ang gulong at kondisyon."
    }
]

with app.app_context():
    cur = get_cursor()

    # Clear existing reviews if any
    cur.execute("DELETE FROM reviews")

    inserted_count = 0
    for rev in reviews_data:
        bid = rev['booking_id']
        cur.execute("SELECT user_id, vehicle_id, end_date FROM bookings WHERE id = %s", (bid,))
        b_info = cur.fetchone()
        if not b_info:
            print(f"Booking #{bid} not found!")
            continue

        end_date = b_info['end_date']
        # Set review created_at 2-4 hours after end_date at 4:30 PM
        created_at_dt = datetime.combine(end_date, datetime.min.time()) + timedelta(hours=16, minutes=30)

        cur.execute("""
            INSERT INTO reviews (user_id, vehicle_id, rating, comment, booking_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (b_info['user_id'], b_info['vehicle_id'], rev['rating'], rev['comment'], bid, created_at_dt))
        inserted_count += 1
        print(f"Inserted review #{inserted_count}: Booking #{bid} | User #{b_info['user_id']} | Vehicle #{b_info['vehicle_id']} | {rev['rating']} stars | Date: {created_at_dt.strftime('%b %d, %Y')}")

    commit_db()
    print(f"\n[SUCCESS] Successfully inserted {inserted_count} verified reviews into database!")
