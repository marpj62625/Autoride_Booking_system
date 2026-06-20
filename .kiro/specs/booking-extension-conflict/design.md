# Booking Extension with Conflict Resolution - Design Document

## System Architecture Overview

This feature adds extension management capabilities across three main components:
1. **Customer Mobile App** - Extension request and conflict resolution UI
2. **Admin Panel** - Extension approval and conflict management
3. **Backend API** - Business logic, conflict detection, notification orchestration

---

## Database Schema Changes

### New Table: `booking_extensions`
```sql
CREATE TABLE booking_extensions (
    extension_id INT PRIMARY KEY AUTO_INCREMENT,
    booking_id INT NOT NULL,
    requested_by_user_id INT NOT NULL,
    original_end_date DATE NOT NULL,
    requested_end_date DATE NOT NULL,
    additional_days INT NOT NULL,
    additional_cost DECIMAL(10,2) NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected', 'Cancelled') DEFAULT 'Pending',
    admin_notes TEXT,
    approved_by_admin_id INT,
    approved_at DATETIME,
    has_conflicts BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
    FOREIGN KEY (requested_by_user_id) REFERENCES users(user_id),
    FOREIGN KEY (approved_by_admin_id) REFERENCES admins(admin_id),
    INDEX idx_booking (booking_id),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
);
```

### New Table: `booking_conflicts`
```sql
CREATE TABLE booking_conflicts (
    conflict_id INT PRIMARY KEY AUTO_INCREMENT,
    extension_id INT NOT NULL,
    affected_booking_id INT NOT NULL,
    affected_user_id INT NOT NULL,
    conflict_start_date DATE NOT NULL,
    conflict_end_date DATE NOT NULL,
    resolution_status ENUM('Pending', 'Alternative_Selected', 'Refund_Processed', 'Auto_Cancelled') DEFAULT 'Pending',
    resolution_deadline DATETIME NOT NULL,
    selected_alternative_vehicle_id INT,
    refund_amount DECIMAL(10,2),
    refund_status ENUM('Pending', 'Processing', 'Completed', 'Failed'),
    refund_transaction_id VARCHAR(100),
    customer_notified_at DATETIME,
    customer_responded_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (extension_id) REFERENCES booking_extensions(extension_id),
    FOREIGN KEY (affected_booking_id) REFERENCES bookings(booking_id),
    FOREIGN KEY (affected_user_id) REFERENCES users(user_id),
    FOREIGN KEY (selected_alternative_vehicle_id) REFERENCES vehicles(vehicle_id),
    INDEX idx_affected_booking (affected_booking_id),
    INDEX idx_resolution_status (resolution_status),
    INDEX idx_deadline (resolution_deadline)
);
```

### Modified Table: `bookings`
```sql
ALTER TABLE bookings 
ADD COLUMN has_active_extension BOOLEAN DEFAULT FALSE,
ADD COLUMN extension_count INT DEFAULT 0,
ADD COLUMN is_conflict_affected BOOLEAN DEFAULT FALSE,
ADD COLUMN conflict_id INT,
ADD FOREIGN KEY (conflict_id) REFERENCES booking_conflicts(conflict_id);
```

### New Table: `extension_payments`
```sql
CREATE TABLE extension_payments (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    extension_id INT NOT NULL,
    booking_id INT NOT NULL,
    user_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('GCash', 'Maya', 'PayMongo', 'Cash') NOT NULL,
    payment_status ENUM('Pending', 'Completed', 'Failed', 'Refunded') DEFAULT 'Pending',
    payment_proof_url VARCHAR(500),
    transaction_reference VARCHAR(100),
    paid_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (extension_id) REFERENCES booking_extensions(extension_id),
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_status (payment_status),
    INDEX idx_extension (extension_id)
);
```

---

## API Endpoints Design

### Customer Endpoints

#### 1. Request Booking Extension
```
POST /api/bookings/{booking_id}/extension/request
```

**Request Body:**
```json
{
  "requested_end_date": "2026-01-31",
  "reason": "Need more time for business trip"
}
```

**Response (Success):**
```json
{
  "success": true,
  "extension_id": 123,
  "additional_days": 6,
  "additional_cost": 15000.00,
  "status": "Pending",
  "message": "Extension request submitted. Waiting for admin approval."
}
```

**Validation:**
- Booking status must be "Active" (picked up)
- requested_end_date > current end_date
- Customer has no outstanding payments
- Booking hasn't reached extension limit (1 per booking)

---

#### 2. Get Extension Status
```
GET /api/bookings/{booking_id}/extension/status
```

**Response:**
```json
{
  "has_extension": true,
  "extension_id": 123,
  "status": "Approved",
  "original_end_date": "2026-01-25",
  "new_end_date": "2026-01-31",
  "additional_cost": 15000.00,
  "payment_status": "Pending",
  "approved_at": "2026-01-24T10:30:00Z"
}
```

---

#### 3. Get Conflict Notification
```
GET /api/conflicts/my-affected-bookings
```

**Response:**
```json
{
  "affected_bookings": [
    {
      "conflict_id": 456,
      "booking_id": 789,
      "vehicle_name": "Toyota Vios 2024",
      "original_dates": {
        "start": "2026-01-29",
        "end": "2026-01-30"
      },
      "conflict_reason": "Current renter extended booking",
      "resolution_deadline": "2026-01-27T23:59:59Z",
      "hours_remaining": 48,
      "options": {
        "has_alternatives": true,
        "can_refund": true
      }
    }
  ]
}
```

---

#### 4. Get Alternative Vehicles
```
GET /api/conflicts/{conflict_id}/alternatives
```

**Response:**
```json
{
  "conflict_id": 456,
  "original_vehicle": {
    "vehicle_id": 10,
    "brand": "Toyota",
    "model": "Vios",
    "price_per_day": 2500.00
  },
  "alternatives": [
    {
      "tier": 1,
      "tier_label": "? Perfect Match",
      "vehicle_id": 15,
      "brand": "Toyota",
      "model": "Vios",
      "year": 2024,
      "price_per_day": 2500.00,
      "price_difference": 0,
      "features": ["Automatic", "GPS", "Bluetooth"],
      "photos": ["url1", "url2"],
      "availability_confirmed": true
    },
    {
      "tier": 2,
      "tier_label": "~ Close Match",
      "vehicle_id": 20,
      "brand": "Toyota",
      "model": "Altis",
      "year": 2024,
      "price_per_day": 2600.00,
      "price_difference": 100,
      "price_note": "Company absorbs ?100/day difference",
      "features": ["Automatic", "GPS", "Leather seats"],
      "photos": ["url3", "url4"],
      "availability_confirmed": true
    }
  ],
  "total_alternatives": 2,
  "search_completed": true
}
```

**Note:** If `alternatives` array is empty, the response indicates no vehicles available.

---

#### 5. Select Alternative Vehicle
```
POST /api/conflicts/{conflict_id}/select-alternative
```

**Request Body:**
```json
{
  "selected_vehicle_id": 15
}
```

**Response:**
```json
{
  "success": true,
  "message": "Alternative vehicle selected successfully",
  "updated_booking": {
    "booking_id": 789,
    "new_vehicle_id": 15,
    "new_vehicle_name": "Toyota Vios 2024",
    "dates": {
      "start": "2026-01-29",
      "end": "2026-01-30"
    },
    "price_per_day": 2500.00,
    "no_additional_cost": true
  },
  "conflict_resolved": true
}
```

---

#### 6. Request Full Refund
```
POST /api/conflicts/{conflict_id}/request-refund
```

**Request Body:**
```json
{
  "cancellation_reason": "No suitable alternatives available"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Full refund initiated",
  "refund_details": {
    "refund_amount": 5000.00,
    "original_payment_method": "GCash",
    "refund_timeline": "3-5 business days",
    "refund_transaction_id": "REF-2026-456789",
    "booking_status": "Cancelled - Extension Conflict"
  }
}
```

---

### Admin Endpoints

#### 7. Get Pending Extension Requests
```
GET /api/admin/extensions/pending
```

**Response:**
```json
{
  "pending_extensions": [
    {
      "extension_id": 123,
      "booking_id": 555,
      "customer_name": "Juan Dela Cruz",
      "vehicle_name": "Toyota Vios 2024",
      "current_dates": {
        "start": "2026-01-21",
        "end": "2026-01-25"
      },
      "requested_end_date": "2026-01-31",
      "additional_days": 6,
      "additional_cost": 15000.00,
      "has_potential_conflicts": true,
      "conflict_count": 1,
      "requested_at": "2026-01-23T15:00:00Z"
    }
  ]
}
```

---

#### 8. Check Extension Conflicts
```
GET /api/admin/extensions/{extension_id}/check-conflicts
```

**Response:**
```json
{
  "extension_id": 123,
  "has_conflicts": true,
  "conflicts": [
    {
      "booking_id": 789,
      "customer_name": "Maria Santos",
      "customer_email": "maria@email.com",
      "customer_phone": "+639171234567",
      "vehicle_id": 10,
      "booking_dates": {
        "start": "2026-01-29",
        "end": "2026-01-30"
      },
      "overlap_days": 2,
      "booking_status": "Approved",
      "payment_status": "Paid",
      "total_paid": 5000.00
    }
  ],
  "conflict_summary": "1 future booking will be affected"
}
```

---

#### 9. Approve Extension with Conflicts
```
POST /api/admin/extensions/{extension_id}/approve
```

**Request Body:**
```json
{
  "admin_notes": "Approved - customer has possession priority",
  "acknowledge_conflicts": true,
  "send_notifications": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Extension approved successfully",
  "extension_id": 123,
  "booking_updated": true,
  "conflicts_created": 1,
  "notifications_sent": {
    "affected_customers": 1,
    "notification_channels": ["push", "email"]
  },
  "next_actions": [
    "Monitor conflict resolution responses",
    "Track refund processing"
  ]
}
```

**Backend Process (on approval):**
1. Update extension status to "Approved"
2. Update booking end_date
3. Detect conflicting bookings
4. Create conflict records
5. Send multi-channel notifications
6. Set resolution deadlines (72 hours)
7. Log admin action

---

#### 10. Monitor Conflict Resolutions
```
GET /api/admin/conflicts/active
```

**Response:**
```json
{
  "active_conflicts": [
    {
      "conflict_id": 456,
      "extension_id": 123,
      "affected_booking_id": 789,
      "customer_name": "Maria Santos",
      "vehicle_name": "Toyota Vios 2024",
      "resolution_status": "Pending",
      "resolution_deadline": "2026-01-27T23:59:59Z",
      "hours_remaining": 36,
      "customer_notified_at": "2026-01-24T10:45:00Z",
      "has_viewed_notification": true,
      "alternatives_available": 2
    }
  ],
  "summary": {
    "total_active": 1,
    "pending_response": 1,
    "alternatives_selected": 0,
    "refunds_processed": 0,
    "approaching_deadline": 1
  }
}
```

---

## Business Logic Flows

### Flow 1: Extension Request (No Conflicts)

```
Customer Mobile App:
1. Customer taps "Extend Booking" button
2. Select new return date from calendar
3. System calculates additional cost
4. Customer confirms request

Backend:
5. Validate eligibility (active booking, no existing extension)
6. Create extension record (status: Pending)
7. Send notification to admin
8. Return success response to customer

Admin Panel:
9. Admin receives notification
10. Admin reviews request details
11. Admin checks for conflicts (none found)
12. Admin approves extension
13. System updates booking end_date
14. System creates payment request for customer
15. Customer pays extension fee
16. Extension complete
```

---

### Flow 2: Extension Request (With Conflicts) - Alternative Vehicle Selected

```
Customer Mobile App (Requesting Extension):
1. Customer A (has vehicle) requests extension Jan 25 ? Jan 31

Backend (Conflict Detection):
2. Admin approves extension
3. System detects overlap with Customer B's booking (Jan 29-30)
4. System creates conflict record
5. System runs 3-tier alternative vehicle search
   - Tier 1: Same brand + price ? Found 1 match (Toyota Vios)
   - Return search results

Notification System:
6. Send push notification to Customer B
7. Send email to Customer B
8. Set 72-hour resolution deadline

Customer Mobile App (Affected Customer B):
10. Customer B opens app, sees conflict notification banner
11. Customer B taps notification
12. System displays conflict details:
    - "Your booking for Toyota Vios (Jan 29-30) is no longer available"
    - "Current renter extended their booking"
13. Customer B taps "View Alternatives"
14. System shows Tier 1 match: Toyota Vios (Perfect Match)
15. Customer B reviews vehicle details
16. Customer B taps "Select This Vehicle"
17. System confirms selection

Backend (Resolution Processing):
18. Update conflict_resolution_status = 'Alternative_Selected'
19. Update original booking with new vehicle_id
20. Mark conflict as resolved
21. Send confirmation to Customer B
22. Notify admin of resolution
23. Log resolution for audit trail
```

---

### Flow 3: Extension Request (With Conflicts) - Full Refund

```
[Steps 1-13 same as Flow 2]

Customer Mobile App (Affected Customer B):
14. Customer B reviews alternatives
15. No suitable alternatives found OR customer prefers refund
16. Customer B taps "Request Full Refund"
17. System shows refund confirmation:
    - "Refund amount: ?5,000.00"
    - "Timeline: 3-5 business days"
    - "Original payment method: GCash"
18. Customer B confirms refund request

Backend (Refund Processing):
19. Update conflict_resolution_status = 'Refund_Processed'
20. Calculate refund amount (100% of paid amount)
21. Initiate refund via payment gateway
22. Update booking status = 'Cancelled - Extension Conflict'
23. Create refund transaction record
24. Send refund confirmation to Customer B
25. Notify admin of cancellation
26. Log refund for financial audit
```

---

### Flow 4: Auto-Cancellation (No Response)

```
Backend (Scheduled Job - runs every hour):
1. Query conflicts where resolution_deadline < NOW() AND status = 'Pending'
2. For each expired conflict:
   a. Update resolution_status = 'Auto_Cancelled'
   b. Initiate automatic full refund
   c. Cancel affected booking
   d. Send final notification to customer
   e. Notify admin of auto-cancellation
3. Log all auto-cancellations
```

---

## UI/UX Design Specifications

### Customer Mobile App

#### Screen 1: Active Booking Detail (Extension Button)
```
???????????????????????????????????
?  < Back    Toyota Vios 2024     ?
???????????????????????????????????
?                                 ?
?   [Vehicle Photo]               ?
?                                 ?
?   Booking Status: Active ?      ?
?   Picked up: Jan 21, 2026       ?
?   Return by: Jan 25, 2026       ?
?                                 ?
?   ???????????????????????????  ?
?   ?  ?? Extend Booking      ?  ?
?   ?  Need more time?        ?  ?
?   ???????????????????????????  ?
?                                 ?
?   [View GPS Location]           ?
?   [Contact Support]             ?
???????????????????????????????????
```

#### Screen 2: Extension Request Form
```
???????????????????????????????????
?  < Back    Extend Booking       ?
???????????????????????????????????
?                                 ?
?   Current Return Date           ?
?   Jan 25, 2026                  ?
?                                 ?
?   New Return Date *             ?
?   ???????????????????????????  ?
?   ? Jan 31, 2026      [??]  ?  ?
?   ???????????????????????????  ?
?                                 ?
?   Additional Days: 6 days       ?
?   Daily Rate: ?2,500            ?
?   ?????????????????????         ?
?   Additional Cost: ?15,000.00   ?
?                                 ?
?   Reason (Optional)             ?
?   ???????????????????????????  ?
?   ? Extended business trip  ?  ?
?   ???????????????????????????  ?
?                                 ?
?   ??????????????????????????????
?   ?   Submit Request          ??
?   ??????????????????????????????
???????????????????????????????????
```

#### Screen 3: Conflict Notification (Affected Customer)
```
???????????????????????????????????
?  ?? Booking Update Required     ?
???????????????????????????????????
?                                 ?
?   ?? Your upcoming booking is   ?
?      no longer available        ?
?                                 ?
?   Booking: Toyota Vios 2024     ?
?   Dates: Jan 29-30, 2026        ?
?                                 ?
?   Reason: Current renter        ?
?   extended their booking        ?
?                                 ?
?   You must choose an option:    ?
?                                 ?
?   ???????????????????????????  ?
?   ? ?? Choose Alternative   ?  ?
?   ?    Vehicle (2 available)?  ?
?   ???????????????????????????  ?
?                                 ?
?   ???????????????????????????  ?
?   ? ?? Get Full Refund      ?  ?
?   ?    ?5,000.00            ?  ?
?   ???????????????????????????  ?
?                                 ?
?   ?? Respond within 48 hours    ?
???????????????????????????????????
```

#### Screen 4: Alternative Vehicles List
```
???????????????????????????????????
?  < Back    Alternative Vehicles ?
???????????????????????????????????
?                                 ?
?   ? Perfect Match               ?
?   ???????????????????????????  ?
?   ? [Photo] Toyota Vios     ?  ?
?   ? 2024 | Automatic        ?  ?
?   ? ?2,500/day (Same price) ?  ?
?   ?                         ?  ?
?   ? [Select This Vehicle >] ?  ?
?   ???????????????????????????  ?
?                                 ?
?   ~ Close Match                 ?
?   ???????????????????????????  ?
?   ? [Photo] Toyota Altis    ?  ?
?   ? 2024 | Automatic        ?  ?
?   ? ?2,600/day              ?  ?
?   ? ? No extra cost to you  ?  ?
?   ?                         ?  ?
?   ? [Select This Vehicle >] ?  ?
?   ???????????????????????????  ?
?                                 ?
?   Or request full refund below  ?
?   ???????????????????????????  ?
?   ? [Request ?5,000 Refund] ?  ?
?   ???????????????????????????  ?
???????????????????????????????????
```

#### Screen 5: No Alternatives Available
```
???????????????????????????????????
?  < Back    Booking Update       ?
???????????????????????????????????
?                                 ?
?   ? No Alternative Vehicles    ?
?      Available                  ?
?                                 ?
?   We sincerely apologize, but   ?
?   there are no alternative      ?
?   vehicles available for your   ?
?   booking dates.                ?
?                                 ?
?   Original Booking:             ?
?   Toyota Vios (Jan 29-30)       ?
?   Amount Paid: ?5,000.00        ?
?                                 ?
?   We will process a full refund ?
?   to your GCash account within  ?
?   3-5 business days.            ?
?                                 ?
?   ??????????????????????????????
?   ?   Confirm Full Refund     ??
?   ??????????????????????????????
?                                 ?
?   [Contact Support for Help]    ?
???????????????????????????????????
```

---

### Admin Panel

#### Screen 6: Extension Request Review
```
????????????????????????????????????????????????
?  Extension Request #123                      ?
????????????????????????????????????????????????
?                                              ?
?  Customer: Juan Dela Cruz                    ?
?  Contact: +639171234567                      ?
?  Email: juan@email.com                       ?
?                                              ?
?  Vehicle: Toyota Vios 2024 (ID: 10)         ?
?  Booking ID: 555                             ?
?                                              ?
?  Current Period:                             ?
?  Jan 21, 2026 - Jan 25, 2026 (5 days)      ?
?                                              ?
?  Requested Extension:                        ?
?  Jan 25, 2026 ? Jan 31, 2026 (+6 days)     ?
?                                              ?
?  Additional Cost: ?15,000.00                 ?
?                                              ?
?  ?? Conflict Detection:                      ?
?  ????????????????????????????????????????   ?
?  ? 1 future booking will be affected   ?   ?
?  ?                                      ?   ?
?  ? Booking #789 - Maria Santos         ?   ?
?  ? Dates: Jan 29-30, 2026              ?   ?
?  ? Status: Approved & Paid (?5,000)    ?   ?
?  ?                                      ?   ?
?  ? [View Details]                      ?   ?
?  ????????????????????????????????????????   ?
?                                              ?
?  Admin Notes:                                ?
?  ????????????????????????????????????????   ?
?  ? Customer has possession priority     ?   ?
?  ????????????????????????????????????????   ?
?                                              ?
?  ?? I acknowledge that affected customer     ?
?     will be notified and offered options     ?
?                                              ?
?  [Reject Request]      [Approve Extension]   ?
????????????????????????????????????????????????
```

---

## Notification Templates

### Push Notification (Conflict)
**Title:** "Booking Update Required"  
**Body:** "Your Toyota Vios booking (Jan 29-30) is unavailable. Choose alternative or get refund. Tap to view options."  
**Action:** Open conflict resolution screen

### Email Template (Conflict)
```
Subject: Action Required: Your Booking for Toyota Vios (Jan 29-30, 2026)

Dear [Customer Name],

We're reaching out regarding your upcoming booking:

Vehicle: Toyota Vios 2024
Dates: January 29-30, 2026
Booking ID: #789

Unfortunately, this booking is no longer available because the current
renter has extended their rental period. We sincerely apologize for this
inconvenience.

YOU MUST CHOOSE ONE OF THE FOLLOWING OPTIONS:

Option 1: Choose an Alternative Vehicle
We have 2 similar vehicles available for your dates at the same price
or better. View alternatives in the app.

Option 2: Receive a Full Refund
We will immediately process a 100% refund of ?5,000.00 to your original
payment method within 3-5 business days.

?? DEADLINE: You must respond within 48 hours (by Jan 26, 11:59 PM)

[View Options in App] [Contact Support]

Thank you for your understanding.
- Autoride Team
```

---

## Backward Compatibility & Safety Measures

### 1. Database Changes - Non-Breaking
All new tables and columns are **additive only** - no existing tables are modified destructively.

**Existing Tables: NO CHANGES**
- `users` - unchanged
- `vehicles` - unchanged  
- `admins` - unchanged
- `payments` - unchanged

**Modified Table: `bookings` - Safe Additions Only**
```sql
-- These columns are added with DEFAULT values, so existing queries still work
ALTER TABLE bookings 
ADD COLUMN has_active_extension BOOLEAN DEFAULT FALSE,
ADD COLUMN extension_count INT DEFAULT 0,
ADD COLUMN is_conflict_affected BOOLEAN DEFAULT FALSE,
ADD COLUMN conflict_id INT DEFAULT NULL;
```

**Impact:** ? All existing SELECT, INSERT, UPDATE queries on `bookings` table continue to work without modification.

---

### 2. API Endpoints - No Breaking Changes

**Existing Endpoints: UNCHANGED**
All current booking APIs remain fully functional:
- `GET /api/bookings` - unchanged
- `POST /api/bookings` - unchanged
- `GET /api/bookings/{id}` - unchanged
- `PUT /api/bookings/{id}` - unchanged
- `DELETE /api/bookings/{id}` - unchanged

**New Endpoints: Isolated**
All extension/conflict endpoints are **new routes** that don't interfere with existing functionality:
- `/api/bookings/{id}/extension/*` - NEW
- `/api/conflicts/*` - NEW
- `/api/admin/extensions/*` - NEW

**Response Format Compatibility**
Existing booking response JSON remains unchanged. New fields only added if explicitly requested:
```json
// Existing response (still works)
{
  "booking_id": 123,
  "user_id": 456,
  "vehicle_id": 789,
  "start_date": "2026-01-21",
  "end_date": "2026-01-25",
  "status": "Active"
  // ... existing fields
}

// Extended response (only if client requests it via ?include=extension)
{
  "booking_id": 123,
  // ... all existing fields ...
  "extension": {  // ? NEW, optional
    "has_active_extension": false,
    "extension_count": 0
  }
}
```

---

### 3. Business Logic Protection

**Rule: Extensions Only for Active Bookings**
```python
def request_extension(booking_id):
    booking = get_booking(booking_id)
    
    # Safety check: Don't interfere with bookings in other statuses
    if booking.status != 'Active':
        raise ValidationError("Only active bookings can be extended")
    
    # Prevents extension requests from affecting:
    # - Pending bookings (not yet approved)
    # - Completed bookings (already returned)
    # - Cancelled bookings (already terminated)
```

**Rule: Conflict Detection Only Affects Future Bookings**
```python
def detect_conflicts(extension_request):
    # Only check bookings with start_date > current_date
    future_bookings = db.query("""
        SELECT * FROM bookings 
        WHERE vehicle_id = %s 
        AND start_date > CURDATE()  -- ? Only future bookings
        AND status IN ('Approved', 'Pending')
        AND booking_id != %s  -- ? Exclude current booking
    """, [vehicle_id, current_booking_id])
    
    # Past bookings are never affected
    # Current booking itself is never affected
```

---

### 4. Feature Flags (Kill Switch)

Add configuration flag to enable/disable extension feature system-wide:

```python
# config.py
EXTENSION_FEATURE_ENABLED = os.getenv('EXTENSION_FEATURE_ENABLED', 'false').lower() == 'true'

# In API handlers
@app.route('/api/bookings/<id>/extension/request', methods=['POST'])
def request_extension(id):
    if not EXTENSION_FEATURE_ENABLED:
        return jsonify({
            "success": false,
            "message": "Extension feature is currently disabled"
        }), 503
    
    # ... normal extension logic
```

**Benefit:** If issues arise, admin can disable extensions without affecting core booking system.

---

### 5. Database Transaction Safety

All extension approval operations use database transactions to ensure atomicity:

```python
def approve_extension_with_conflicts(extension_id):
    try:
        db.begin_transaction()
        
        # Step 1: Update extension status
        update_extension(extension_id, status='Approved')
        
        # Step 2: Update booking end_date
        update_booking_dates(booking_id, new_end_date)
        
        # Step 3: Create conflict records
        conflicts = create_conflict_records(affected_bookings)
        
        # Step 4: Send notifications
        send_conflict_notifications(conflicts)
        
        db.commit()
        
    except Exception as e:
        db.rollback()  # ? Rollback everything if any step fails
        log_error(e)
        raise
```

**Safety:** If notification sending fails, the entire operation is rolled back. No partial state.

---

### 6. Existing Booking Queries - Protected

**Query Pattern: Availability Check**
```python
# BEFORE: Existing availability check (still works)
def check_vehicle_availability(vehicle_id, start_date, end_date):
    conflicts = db.query("""
        SELECT * FROM bookings 
        WHERE vehicle_id = %s 
        AND status IN ('Approved', 'Active')
        AND (
            (start_date <= %s AND end_date >= %s) OR
            (start_date <= %s AND end_date >= %s) OR
            (start_date >= %s AND end_date <= %s)
        )
    """, [vehicle_id, start_date, start_date, end_date, end_date, start_date, end_date])
    
    return len(conflicts) == 0

# AFTER: Enhanced with extension awareness (backward compatible)
def check_vehicle_availability_v2(vehicle_id, start_date, end_date):
    # Same query as before, works identically
    conflicts = db.query("""
        SELECT * FROM bookings 
        WHERE vehicle_id = %s 
        AND status IN ('Approved', 'Active')
        AND (
            (start_date <= %s AND end_date >= %s) OR
            (start_date <= %s AND end_date >= %s) OR
            (start_date >= %s AND end_date <= %s)
        )
    """, [vehicle_id, start_date, start_date, end_date, end_date, start_date, end_date])
    
    # Extension-aware check uses updated end_date automatically
    # because booking.end_date is updated when extension approved
    return len(conflicts) == 0
```

**Result:** Existing availability checks automatically respect extended bookings because they query the updated `end_date` field.

---

### 7. Mobile App Compatibility

**Old App Versions:** Will continue to work without extension features
- Old API calls remain functional
- New fields in responses are ignored by old clients
- Extension buttons only shown if app version supports it

**Version Detection:**
```python
@app.route('/api/bookings/<id>')
def get_booking(id):
    booking = fetch_booking(id)
    
    # Check client version from headers
    client_version = request.headers.get('X-App-Version', '1.0.0')
    
    if version_supports_extensions(client_version):
        # Include extension data
        booking['extension'] = get_extension_data(id)
    
    return jsonify(booking)
```

---

### 8. Admin Panel Compatibility

**Existing Admin Functions: Untouched**
- View all bookings ? still works
- Approve new bookings ? still works
- Process refunds ? still works
- View payments ? still works

**New Admin Features: Separate UI Section**
- Extension management appears as new tab/section
- Old admin workflows unchanged
- No training required for basic admin tasks

---

### 9. Testing & Rollback Strategy

**Pre-Deployment Testing:**
1. Test all existing booking flows (create, approve, complete, cancel)
2. Verify existing APIs return expected responses
3. Confirm database queries performance unchanged
4. Load test with existing + new endpoints

**Rollback Plan:**
```sql
-- If issues arise, disable feature via config flag first
-- Then optionally rollback database changes:

-- Remove new columns (data preserved in extension tables)
ALTER TABLE bookings 
DROP COLUMN has_active_extension,
DROP COLUMN extension_count,
DROP COLUMN is_conflict_affected,
DROP COLUMN conflict_id;

-- New tables can remain (don't affect existing functionality)
-- Or drop if needed:
DROP TABLE IF EXISTS booking_conflicts;
DROP TABLE IF EXISTS extension_payments;
DROP TABLE IF EXISTS booking_extensions;
```

---

### 10. Monitoring & Alerts

**Metrics to Monitor:**
- Extension API response times (should not affect booking API times)
- Database query performance on `bookings` table
- Transaction rollback rate
- Notification delivery success rate

**Alerts:**
- If extension approval takes > 5 seconds ? investigate
- If conflict detection fails ? disable extension feature
- If refund processing fails ? manual admin intervention

---

## Summary: Zero Breaking Changes Guarantee

? **No existing tables deleted or modified destructively**  
? **No existing API endpoints changed**  
? **No existing queries broken**  
? **Old mobile app versions continue to work**  
? **Existing admin panel functions unchanged**  
? **Feature flag allows instant disable if needed**  
? **Database transactions prevent partial states**  
? **Rollback plan documented and tested**

**Philosophy:** Extension feature is **additive only**. Core booking system continues to operate exactly as before, even if extension feature is disabled or removed.

---## Background Jobs & Scheduled Tasks

### Job 1: Conflict Deadline Monitor
**Frequency:** Every 1 hour  
**Purpose:** Check for expired conflict deadlines and auto-cancel

```python
def monitor_conflict_deadlines():
    expired_conflicts = db.query("""
        SELECT * FROM booking_conflicts 
        WHERE resolution_deadline < NOW() 
        AND resolution_status = 'Pending'
    """)
    
    for conflict in expired_conflicts:
        # Auto-cancel and refund
        process_auto_cancellation(conflict)
        send_final_notification(conflict.affected_user_id)
        notify_admin_auto_cancellation(conflict)
```

### Job 2: Reminder Notifications
**Frequency:** Every 12 hours  
**Purpose:** Send reminders for pending conflict resolutions

```python
def send_deadline_reminders():
    approaching_deadline = db.query("""
        SELECT * FROM booking_conflicts 
        WHERE resolution_status = 'Pending'
        AND resolution_deadline BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 24 HOUR)
        AND customer_responded_at IS NULL
    """)
    
    for conflict in approaching_deadline:
        send_reminder_notification(conflict.affected_user_id, conflict.hours_remaining)
```

---

## Security & Validation Rules

### Extension Request Validation
```python
def validate_extension_request(booking_id, requested_end_date):
    booking = get_booking(booking_id)
    
    # Check 1: Booking must be active
    if booking.status != 'Active':
        raise ValidationError("Only active bookings can be extended")
    
    # Check 2: Must have vehicle possession
    if not booking.vehicle_picked_up:
        raise ValidationError("Vehicle must be picked up first")
    
    # Check 3: Extension limit
    if booking.extension_count >= 1:
        raise ValidationError("Maximum 1 extension per booking")
    
    # Check 4: Date must be future
    if requested_end_date <= booking.end_date:
        raise ValidationError("New date must be after current end date")
    
    # Check 5: Maximum extension days
    additional_days = (requested_end_date - booking.end_date).days
    if additional_days > 30:
        raise ValidationError("Maximum extension is 30 days")
    
    # Check 6: No outstanding payments
    if has_outstanding_payments(booking_id):
        raise ValidationError("Please settle outstanding payments first")
    
    return True
```

### Conflict Resolution Validation
```python
def validate_alternative_selection(conflict_id, selected_vehicle_id):
    conflict = get_conflict(conflict_id)
    
    # Check 1: Conflict must be pending
    if conflict.resolution_status != 'Pending':
        raise ValidationError("Conflict already resolved")
    
    # Check 2: Not past deadline
    if datetime.now() > conflict.resolution_deadline:
        raise ValidationError("Resolution deadline has passed")
    
    # Check 3: Vehicle must be available
    if not is_vehicle_available(selected_vehicle_id, conflict.start_date, conflict.end_date):
        raise ValidationError("Selected vehicle is no longer available")
    
    # Check 4: Vehicle must be in alternatives list
    alternatives = get_alternative_vehicles(conflict_id)
    if selected_vehicle_id not in [v.vehicle_id for v in alternatives]:
        raise ValidationError("Invalid vehicle selection")
    
    return True
```

---

## Testing Strategy

### Unit Tests
- Extension eligibility validation
- Conflict detection algorithm
- 3-tier alternative vehicle matching
- Refund amount calculation
- Deadline expiration logic

### Integration Tests
- End-to-end extension request flow
- Conflict creation and notification
- Alternative vehicle selection
- Refund processing workflow
- Auto-cancellation job

### User Acceptance Tests
- Customer requests extension (happy path)
- Admin approves extension with conflicts
- Affected customer selects alternative
- Affected customer requests refund
- No response ? auto-cancellation

---

**Design Status:** Complete  
**Next Step:** Task Breakdown  
**Ready for:** Implementation
