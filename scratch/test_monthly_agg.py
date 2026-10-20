import sys, os, datetime
sys.path.append(os.path.abspath('backend'))
from database import get_connection
from psycopg.rows import dict_row

conn = get_connection()
cur = conn.cursor(row_factory=dict_row)

date_from = '2026-01-01'
date_to = '2026-12-31'
filter_period = 'year'
is_year_view = True
date_format = 'YYYY-MM'

trend_query = f"""
    SELECT 
        TO_CHAR(b.start_date, '{date_format}') as day,
        SUM(CASE WHEN b.status = 'Cancelled' THEN (COALESCE(b.amount_paid, 0) - COALESCE(b.refund_amount, 0)) ELSE b.total_price END) as amount,
        COUNT(b.id) as booking_count
    FROM bookings b
    JOIN vehicles v ON b.vehicle_id = v.id
    WHERE (b.status != 'Cancelled' OR (b.status = 'Cancelled' AND COALESCE(b.amount_paid, 0) > COALESCE(b.refund_amount, 0)))
      AND b.start_date >= %s AND b.start_date <= %s
    GROUP BY day ORDER BY day ASC
"""
cur.execute(trend_query, (date_from, date_to))
raw_trend = cur.fetchall()

target_year = '2026'
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
trend_map = {r['day']: r for r in raw_trend}
revenue_trend = []
for idx, m_num in enumerate(['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']):
    m_key = f'{target_year}-{m_num}'
    if m_key in trend_map:
        row = trend_map[m_key]
        revenue_trend.append({
            'day': m_key,
            'label': month_names[idx],
            'amount': float(row.get('amount') or 0),
            'booking_count': int(row.get('booking_count') or 0)
        })
    else:
        revenue_trend.append({
            'day': m_key,
            'label': month_names[idx],
            'amount': 0.0,
            'booking_count': 0
        })

print('=== 12-Month Clean Monthly Aggregation ===')
for m in revenue_trend:
    print(f"{m['label']} ({m['day']}): {m['booking_count']} bookings | PHP {m['amount']:,.2f}")

total_rev = sum(m['amount'] for m in revenue_trend)
total_bks = sum(m['booking_count'] for m in revenue_trend)
print(f"Total: {total_bks} bookings | PHP {total_rev:,.2f}")
conn.close()
