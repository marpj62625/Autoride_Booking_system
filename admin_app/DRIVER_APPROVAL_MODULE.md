# Driver Approval Module

This admin module manages driver applications and status updates.

## Features

- View all driver applications in an admin table
- Approve or reject pending applications
- Display:
  - Name
  - License number
  - Contact info
  - Status (`Pending`, `Approved`, `Rejected`)

## Database (Supabase PostgreSQL)

```sql
CREATE TABLE IF NOT EXISTS drivers(
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    license_number VARCHAR(50) NOT NULL UNIQUE,
    contact_info VARCHAR(120) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Backend APIs (Flask)

- `GET /drivers`
  - Returns all driver applications.
- `PUT /drivers/{id}/approve`
  - Changes status from `Pending` to `Approved`.
- `PUT /drivers/{id}/reject`
  - Changes status from `Pending` to `Rejected`.

Status update logic is enforced in backend:

- Driver must exist; otherwise returns `404`.
- Only `Pending` drivers can be updated (via mobile or web admin).

## Frontend Admin UI (PC)

- `admin_app/driver-approval.html`
- `admin_app/driver-approval.css`
- `admin_app/driver-approval.js`

UI behavior:

- Loads drivers using `GET /drivers`
- Filters by status and search text
- Shows Approve/Reject actions for `Pending` only
- Updates are handled via the Supabase-backed API on Port 9999.
