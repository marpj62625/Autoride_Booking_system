# 📈 Reports & Analytics Module — Autoride Admin

## Overview
The Reports module provides data-driven analytics for the Autoride admin dashboard. It includes KPI summary cards, interactive charts powered by Chart.js, and a detailed top-vehicles ranking table.

## Features
| Feature | Description |
|---------|-------------|
| **Total Bookings** | Count of all bookings in the selected period |
| **Total Revenue** | Sum of `total_price` from bookings |
| **Average Revenue** | Average revenue per booking |
| **Active Vehicles** | Count of vehicles with status `Available` |
| **Revenue Chart** | Bar chart — daily (last 7 days) or monthly (last 12 months) |
| **Booking Status** | Doughnut chart — Pending / Approved / Rejected / Confirmed / Cancelled |
| **Bookings Trend** | Line chart — booking count over time |
| **Most Rented Vehicles** | Horizontal bar chart + detailed ranked table (Top 5) |
| **Daily / Monthly Toggle** | Switch between daily and monthly aggregation |

## Files Created / Modified

### Frontend (admin_app/)
- `reports.html` — Dashboard page with sidebar, KPI cards, chart containers, and top-vehicles table
- `reports.css` — Full styling (dark glassmorphism theme, responsive)
- `reports.js` — Chart.js integration, API calls, animations

### Backend (backend/)
API endpoints provided by `app.py`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reports/summary?period=daily&date=YYYY-MM-DD` | GET | KPIs: total bookings, revenue, avg, active vehicles |
| `/reports/revenue?period=daily&date=YYYY-MM-DD` | GET | Revenue data for bar chart |
| `/reports/booking-status` | GET | Booking status counts for doughnut chart |
| `/reports/bookings-trend?period=daily&date=YYYY-MM-DD` | GET | Booking count data for line chart |
| `/reports/top-vehicles` | GET | Top 5 most-rented vehicles |

### Database (Supabase PostgreSQL)
Reports are generated using PostgreSQL aggregation queries:
- Daily/Monthly revenue aggregation
- Status breakdown counts
- Vehicle rental ranking

## How to Run
1. Ensure your Supabase database is set up (run `backend/setup_db.py`)
2. Start the Flask backend: `python backend/app.py`
3. Serve the admin app: `python -m http.server 8081` in `admin_app/`
4. Open `http://localhost:8081/reports.html` in browser

## Technology
- **Frontend:** HTML5, CSS3, JavaScript (ES6+)
- **Charts:** Chart.js v4.4.7 (CDN)
- **Backend:** Python Flask with Psycopg (PostgreSQL)
- **Database:** Supabase PostgreSQL with aggregation queries (GROUP BY, SUM, COUNT, AVG)
