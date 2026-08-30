# Booking Management Module

This module provides a simple admin interface and backend APIs to review rental bookings and approve or reject them.

## Tech Stack

- Backend: Python Flask (`backend/app.py`)
- Frontend: HTML, CSS, JavaScript (`admin_app/booking-management.html`)
- Database: Supabase PostgreSQL (`backend/setup_db.py`)

## Admin UI Features

- View all bookings in a table
- Search bookings by customer name or selected car
- Filter by booking status
- Approve pending bookings
- Reject pending bookings
- Show booking details:
  - Customer name
  - Car selected
  - Rental dates
  - Total price
  - Status (`Pending`, `Approved`, `Rejected`)

## API Endpoints

All endpoints are hosted on Port 9999.

### 1) Get all bookings

- Method: `GET`
- Path: `/bookings`
- Response: list of bookings for admin view

Example item:

```json
{
  "id": 101,
  "customer_name": "John Doe",
  "car": "Toyota Vios (ABC-1234)",
  "start_date": "2026-03-20",
  "end_date": "2026-03-22",
  "total_price": "5400.00",
  "status": "Pending"
}
```

### 2) Approve booking

- Method: `PUT`
- Path: `/bookings/{id}/approve`

### 3) Reject booking

- Method: `PUT`
- Path: `/bookings/{id}/reject`

## PostgreSQL Table Structure

Core table used by this module:

```sql
CREATE TABLE IF NOT EXISTS bookings(
    id SERIAL PRIMARY KEY,
    user_id INT,
    vehicle_id INT,
    start_date DATE,
    end_date DATE,
    total_price DECIMAL(10,2),
    status VARCHAR(20)
);
```

## Files Involved

- `backend/app.py` (API routes for list/approve/reject)
- `admin_app/booking-management.html` (admin page markup)
- `admin_app/booking-management.js` (data fetch, table render, actions)
- `backend/setup_db.py` (database initialization)
