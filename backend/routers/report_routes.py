from flask import Blueprint, request, jsonify
from database import get_cursor
import json
from decimal import Decimal

report_bp = Blueprint('report', __name__)

@report_bp.route('/reports/summary', methods=['GET'])
def report_summary():
    """Return KPI summary: total bookings, total revenue, avg revenue, active vehicles."""
    period = request.args.get('period', 'daily')
    date = request.args.get('date')

    if not date:
        return jsonify({"error": "date parameter is required (YYYY-MM-DD)"}), 400

    try:
        cur = get_cursor()

        if period == 'monthly':
            date_filter = "TO_CHAR(b.start_date, 'YYYY-MM') = TO_CHAR(%s::date, 'YYYY-MM')"
        else:
            date_filter = "b.start_date = %s::date"

        cur.execute(f"""
            SELECT COUNT(*) AS total_bookings,
                   COALESCE(SUM(b.total_price), 0) AS total_revenue,
                   COALESCE(AVG(b.total_price), 0) AS avg_revenue
            FROM bookings b
            WHERE {date_filter}
        """, (date,))
        row = cur.fetchone()
        summary = dict(row)

        cur.execute("SELECT COUNT(*) AS cnt FROM vehicles WHERE status = 'Available'")
        active = cur.fetchone()['cnt']
        summary['active_vehicles'] = int(active)

        summary['total_revenue'] = float(summary['total_revenue'])
        summary['avg_revenue'] = float(summary['avg_revenue'])

        return jsonify(summary), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@report_bp.route('/reports/revenue', methods=['GET'])
def report_revenue():
    """Revenue breakdown for bar chart."""
    period = request.args.get('period', 'daily')
    date = request.args.get('date')

    if not date:
        return jsonify({"error": "date parameter is required"}), 400

    try:
        cur = get_cursor()

        if period == 'monthly':
            cur.execute("""
                SELECT TO_CHAR(b.start_date, 'YYYY-MM') AS label,
                       COALESCE(SUM(b.total_price), 0) AS revenue
                FROM bookings b
                WHERE b.start_date >= %s::date - INTERVAL '12 months'
                  AND b.start_date <= DATE_TRUNC('month', %s::date) + INTERVAL '1 month - 1 day'
                GROUP BY label
                ORDER BY label ASC
            """, (date, date))
        else:
            cur.execute("""
                SELECT TO_CHAR(b.start_date, 'Mon DD') AS label,
                       COALESCE(SUM(b.total_price), 0) AS revenue
                FROM bookings b
                WHERE b.start_date BETWEEN %s::date - INTERVAL '6 days' AND %s::date
                GROUP BY b.start_date, label
                ORDER BY b.start_date ASC
            """, (date, date))

        rows = cur.fetchall()
        labels = [r['label'] for r in rows]
        values = [float(r['revenue']) for r in rows]

        return jsonify({"labels": labels, "values": values}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@report_bp.route('/reports/booking-status', methods=['GET'])
def report_status():
    """Booking counts grouped by status for doughnut chart."""
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT status, COUNT(*) AS cnt
            FROM bookings
            GROUP BY status
            ORDER BY cnt DESC
        """)
        rows = cur.fetchall()
        labels = [r['status'] or 'Unknown' for r in rows]
        values = [r['cnt'] for r in rows]

        return jsonify({"labels": labels, "values": values}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@report_bp.route('/reports/bookings-trend', methods=['GET'])
def report_trend():
    """Bookings count trend for line chart."""
    period = request.args.get('period', 'daily')
    date = request.args.get('date')

    if not date:
        return jsonify({"error": "date parameter is required"}), 400

    try:
        cur = get_cursor()

        if period == 'monthly':
            cur.execute("""
                SELECT TO_CHAR(b.start_date, 'YYYY-MM') AS label,
                       COUNT(*) AS cnt
                FROM bookings b
                WHERE b.start_date >= %s::date - INTERVAL '12 months'
                  AND b.start_date <= DATE_TRUNC('month', %s::date) + INTERVAL '1 month - 1 day'
                GROUP BY label
                ORDER BY label ASC
            """, (date, date))
        else:
            cur.execute("""
                SELECT TO_CHAR(b.start_date, 'Mon DD') AS label,
                       COUNT(*) AS cnt
                FROM bookings b
                WHERE b.start_date BETWEEN %s::date - INTERVAL '6 days' AND %s::date
                GROUP BY b.start_date, label
                ORDER BY b.start_date ASC
            """, (date, date))

        rows = cur.fetchall()
        labels = [r['label'] for r in rows]
        values = [r['cnt'] for r in rows]

        return jsonify({"labels": labels, "values": values}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@report_bp.route('/reports/top-vehicles', methods=['GET'])
def report_top_vehicles():
    """Get Top 5 vehicles based on booking count and total revenue."""
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT v.name AS vehicle_name, 
                   COUNT(b.id) AS total_bookings,
                   COALESCE(SUM(b.total_price), 0) AS total_revenue
            FROM vehicles v
            JOIN bookings b ON v.id = b.vehicle_id
            GROUP BY v.id, v.name
            ORDER BY total_bookings DESC
            LIMIT 5
        """)
        rows = cur.fetchall()
        for r in rows:
            r['total_revenue'] = float(r['total_revenue'])
            
        return jsonify({"vehicles": rows}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@report_bp.route('/reports/user-stats', methods=['GET'])
def report_user_stats():
    """Get breakdown of verified vs unverified users."""
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT 
                CASE WHEN is_verified THEN 'Verified' ELSE 'Unverified' END AS status,
                COUNT(*) AS cnt
            FROM users
            GROUP BY is_verified
        """)
        rows = cur.fetchall()
        labels = [r['status'] for r in rows]
        values = [r['cnt'] for r in rows]
        return jsonify({"labels": labels, "values": values}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@report_bp.route('/reports/filtered', methods=['GET'])
def report_filtered():
    """Get filtered report data based on date range, status, and vehicle type."""
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    status = request.args.get('status', 'all')
    vehicle_type = request.args.get('vehicle_type', 'all')
    period = request.args.get('period', 'daily')

    if not start_date or not end_date:
        return jsonify({"error": "start and end date parameters are required"}), 400

    try:
        cur = get_cursor()
        
        # Build WHERE clause based on filters
        where_clauses = ["b.start_date BETWEEN %s::date AND %s::date"]
        params = [start_date, end_date]
        
        if status != 'all':
            where_clauses.append("b.status = %s")
            params.append(status)
        
        if vehicle_type != 'all':
            where_clauses.append("v.vehicle_type = %s")
            params.append(vehicle_type)
        
        where_clause = " AND ".join(where_clauses)
        
        # Get revenue data
        if period == 'monthly':
            cur.execute(f"""
                SELECT TO_CHAR(b.start_date, 'YYYY-MM') AS label,
                       COALESCE(SUM(b.total_price), 0) AS revenue,
                       COUNT(*) AS bookings
                FROM bookings b
                LEFT JOIN vehicles v ON b.vehicle_id = v.id
                WHERE {where_clause}
                GROUP BY label
                ORDER BY label ASC
            """, params)
        else:
            cur.execute(f"""
                SELECT TO_CHAR(b.start_date, 'Mon DD') AS label,
                       COALESCE(SUM(b.total_price), 0) AS revenue,
                       COUNT(*) AS bookings
                FROM bookings b
                LEFT JOIN vehicles v ON b.vehicle_id = v.id
                WHERE {where_clause}
                GROUP BY b.start_date, label
                ORDER BY b.start_date ASC
            """, params)
        
        rows = cur.fetchall()
        labels = [r['label'] for r in rows]
        revenue_values = [float(r['revenue']) for r in rows]
        booking_values = [r['bookings'] for r in rows]
        
        # Get status distribution
        cur.execute(f"""
            SELECT b.status, COUNT(*) AS cnt
            FROM bookings b
            LEFT JOIN vehicles v ON b.vehicle_id = v.id
            WHERE {where_clause}
            GROUP BY b.status
            ORDER BY cnt DESC
        """, params)
        status_rows = cur.fetchall()
        status_labels = [r['status'] or 'Unknown' for r in status_rows]
        status_values = [r['cnt'] for r in status_rows]
        
        # Get top vehicles for filtered period
        cur.execute(f"""
            SELECT v.name AS vehicle_name, 
                   COUNT(b.id) AS total_bookings,
                   COALESCE(SUM(b.total_price), 0) AS total_revenue
            FROM vehicles v
            JOIN bookings b ON v.id = b.vehicle_id
            WHERE {where_clause}
            GROUP BY v.id, v.name
            ORDER BY total_bookings DESC
            LIMIT 5
        """, params)
        vehicle_rows = cur.fetchall()
        for r in vehicle_rows:
            r['total_revenue'] = float(r['total_revenue'])
        
        return jsonify({
            "revenue": {
                "labels": labels,
                "values": revenue_values
            },
            "bookings_trend": {
                "labels": labels,
                "values": booking_values
            },
            "status": {
                "labels": status_labels,
                "values": status_values
            },
            "top_vehicles": {
                "vehicles": vehicle_rows
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
