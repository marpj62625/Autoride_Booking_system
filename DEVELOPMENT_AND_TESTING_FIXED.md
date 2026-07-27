# Development and Testing Framework
## Autoride Car Rental Booking System

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Development Framework](#development-framework)
3. [Testing Framework](#testing-framework)
4. [Quality Assurance Process](#quality-assurance-process)
5. [Tools and Technologies](#tools-and-technologies)
6. [Best Practices](#best-practices)

---

## System Overview

### What is the Autoride System?
The Autoride Car Rental Booking System is a comprehensive **mobile-first** application that enables customers to rent vehicles and administrators to manage the rental business operations.

### Architecture
```
???????????????????????????????????????????????????????????
?                    AUTORIDE SYSTEM                       ?
???????????????????????????????????????????????????????????
?                                                          ?
?  ????????????????    ????????????????                  ?
?  ?   Customer   ?    ?    Admin     ?                  ?
?  ?  Mobile App  ?    ?  Mobile App  ?                  ?
?  ?  (Capacitor) ?    ?  (Capacitor) ?                  ?
?  ????????????????    ????????????????                  ?
?         ?                    ?                          ?
?         ??????????????????????                          ?
?                  ?                                      ?
?         ???????????????????                            ?
?         ?   Backend API   ?                            ?
?         ?  (Flask/Python) ?                            ?
?         ???????????????????                            ?
?                  ?                                      ?
?         ???????????????????                            ?
?         ?    Database     ?                            ?
?         ?  (PostgreSQL)   ?                            ?
?         ???????????????????                            ?
?                                                          ?
?  External Services:                                     ?
?  • Google Sign-In (Authentication)                      ?
?  • Firebase (Push Notifications)                        ?
?  • Supabase (Storage & Database)                        ?
?  • PayMongo (Payment Gateway)                           ?
?  • Twilio (SMS Notifications)                           ?
?                                                          ?
???????????????????????????????????????????????????????????
```

---

## Development Framework

### 1. **Planning Phase**
The foundation of our development process:

#### Requirements Gathering
- **Business Requirements**: What features does the car rental business need?
  - Vehicle inventory management
  - Booking system with conflict detection
  - Payment processing (full/downpayment)
  - GPS tracking for rented vehicles
  - License verification system
  - Extension requests with conflict resolution
  
- **User Requirements**: What do customers and admins need?
  - **Customers**: Easy booking, real-time notifications, secure payments
  - **Admins**: Dashboard for managing bookings, vehicles, and users

#### Technical Design
- **Database Schema**: Designed relational database with tables for:
  - `users`, `admins`, `vehicles`, `bookings`, `payments`
  - `booking_extensions`, `booking_conflicts`, `notifications`
  - `license_details`, `vehicle_inspections`

- **API Design**: RESTful API endpoints:
  ```
  /api/auth/google           - Google OAuth authentication
  /api/bookings              - CRUD operations for bookings
  /api/vehicles              - Vehicle management
  /api/notifications         - In-app notifications
  /api/extensions            - Booking extension requests
  /api/conflicts             - Conflict resolution
  ```

- **Mobile App Architecture**: Hybrid app using Capacitor
  - HTML/CSS/JavaScript frontend
  - Native Android build with Capacitor
  - Cordova plugins for GPS, camera, notifications

### 2. **Development Phase**

#### Backend Development (Flask + Python)
```python
# Example: Booking Creation Flow
@app.route('/api/bookings', methods=['POST'])
def create_booking():
    # 1. Validate input data
    # 2. Check vehicle availability
    # 3. Detect booking conflicts
    # 4. Calculate pricing (base + addons + insurance - discount)
    # 5. Create booking record
    # 6. Send notifications (email, SMS, push)
    # 7. Return booking confirmation
```

**Key Development Practices:**
- **Modular Code**: Separate files for routes, services, utilities
  ```
  backend/
    ??? app.py              # Main application
    ??? config.py           # Configuration
    ??? database.py         # Database connection pool
    ??? routers/            # API route blueprints
    ?   ??? booking_routes.py
    ?   ??? payment_routes.py
    ?   ??? conflict_routes.py
    ??? services/           # Business logic
    ?   ??? extension_service.py
    ?   ??? notification_service.py
    ??? utils/              # Helper functions
        ??? pdf_generator.py
        ??? validators.py
  ```

- **Database Migrations**: Incremental schema updates
  ```python
  def migrate_extensions_v1():
      # Adds new tables without breaking existing data
      cur.execute("""
          CREATE TABLE IF NOT EXISTS booking_extensions (...)
      """)
      cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS has_active_extension")
  ```

- **Error Handling**: Graceful error responses
  ```python
  try:
      # Business logic
  except Exception as e:
      return jsonify({'error': str(e)}), 500
  ```

#### Frontend Development (Mobile Apps)

**Customer Mobile App:**
```javascript
// Example: Booking Flow
function createBooking() {
    // 1. Collect form data
    const bookingData = {
        vehicleId: selectedVehicle,
        startDate: pickupDate,
        endDate: returnDate,
        addons: selectedAddons,
        insurance: insuranceType
    };
    
    // 2. Call backend API
    fetch(`${API_URL}/api/bookings`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(bookingData)
    })
    .then(response => response.json())
    .then(data => {
        // 3. Show confirmation
        // 4. Navigate to payment
    });
}
```

**Key Features Implemented:**
- Google Sign-In integration
- Real-time GPS tracking with Geolocation API
- Push notifications via Firebase
- Camera integration for license uploads
- Responsive UI with Bootstrap

#### Integration Development
- **Google OAuth**: Secure authentication without passwords
- **Firebase Cloud Messaging**: Cross-platform push notifications
- **PayMongo API**: Credit card and e-wallet payments
- **Twilio SMS**: Text message notifications
- **Supabase Storage**: Cloud storage for images (licenses, payment proofs)

### 3. **Deployment Phase**

#### Backend Deployment (Vercel)
```json
// vercel.json
{
    "version": 2,
    "builds": [
        {
            "src": "backend/app.py",
            "use": "@vercel/python"
        }
    ],
    "routes": [
        {
            "src": "/(.*)",
            "dest": "backend/app.py"
        }
    ]
}
```

**Deployment URL**: `https://autoride-booking-system.vercel.app`

#### Mobile App Deployment
1. **Development Build** (Debug APK):
   ```bash
   cd customer_mobile/android
   gradlew assembleDebug
   ```
   
2. **Production Build** (Release Bundle):
   ```bash
   gradlew bundleRelease
   ```
   
3. **Google Play Console Upload**:
   - Upload AAB bundle
   - Configure app details
   - Submit for review

---

## Testing Framework

### 1. **Unit Testing**
Testing individual components in isolation.

#### Backend Unit Tests
```python
# Example: Test booking validation
def test_booking_date_validation():
    # Test case: Start date must be before end date
    start_date = datetime(2026, 6, 25)
    end_date = datetime(2026, 6, 20)  # Invalid!
    
    result = validate_booking_dates(start_date, end_date)
    assert result['valid'] == False
    assert 'must be before' in result['error']

def test_pricing_calculation():
    # Test case: 3-day rental with insurance
    days = 3
    daily_rate = 1000
    insurance = 200
    
    total = calculate_booking_price(days, daily_rate, insurance, addons=[])
    assert total == 3600  # (1000 * 3) + 200 + 200 + 200
```

**What We Test:**
- ? Input validation (dates, prices, IDs)
- ? Business logic (pricing, availability, conflicts)
- ? Data formatting (JSON responses, date formats)
- ? Error handling (invalid inputs, missing data)

#### Frontend Unit Tests
```javascript
// Example: Test booking form validation
test('validateBookingForm returns errors for invalid dates', () => {
    const formData = {
        startDate: '2026-06-25',
        endDate: '2026-06-20'  // Invalid!
    };
    
    const errors = validateBookingForm(formData);
    expect(errors.endDate).toBe('End date must be after start date');
});
```

### 2. **Integration Testing**
Testing how different components work together.

#### API Integration Tests
```python
# Test: Complete booking flow
def test_create_booking_api():
    # 1. Authenticate user
    token = login_user('test@gmail.com', 'password123')
    
    # 2. Select vehicle
    vehicles = get_available_vehicles('2026-06-25', '2026-06-28')
    vehicle_id = vehicles[0]['id']
    
    # 3. Create booking
    booking_data = {
        'vehicle_id': vehicle_id,
        'start_date': '2026-06-25',
        'end_date': '2026-06-28'
    }
    response = create_booking(booking_data, token)
    
    # 4. Verify response
    assert response.status_code == 200
    assert response.json()['status'] == 'Pending'
```

**What We Test:**
- ? API endpoints (request/response formats)
- ? Database operations (CRUD operations)
- ? External service integrations (Google, Firebase, PayMongo)
- ? Authentication flow (login, token validation)
- ? Notification delivery (email, SMS, push)

### 3. **System Testing**
Testing the entire system as a whole.

#### End-to-End Test Scenarios

**Scenario 1: Customer Booking Journey**
```
1. User opens Customer Mobile App
2. User signs in with Google
3. User browses available vehicles
4. User selects a vehicle and dates
5. User adds insurance and addons
6. User uploads driver's license
7. User proceeds to payment
8. User uploads payment proof
9. Admin approves booking
10. User receives confirmation notification
11. User tracks vehicle GPS during rental
12. User returns vehicle
```

**Scenario 2: Admin Management Journey**
```
1. Admin opens Admin Mobile App
2. Admin signs in with credentials
3. Admin views pending bookings
4. Admin approves booking
5. Admin marks vehicle as "Rented"
6. Admin monitors GPS tracking
7. Admin processes extension request
8. Admin resolves booking conflicts
9. Admin marks vehicle as "Available"
10. Admin generates revenue reports
```

**Scenario 3: Extension with Conflict**
```
1. Customer A has Booking #1 (June 1-5, Vehicle X)
2. Customer B has Booking #2 (June 6-10, Vehicle X)
3. Customer A requests extension to June 8 (conflicts!)
4. System detects conflict
5. System creates conflict record
6. System notifies Customer B about conflict
7. Customer B chooses alternative vehicle
8. Admin approves extension
9. Admin updates both bookings
10. System sends confirmations to both customers
```

### 4. **User Acceptance Testing (UAT)**
Real users test the system in real-world scenarios.

#### UAT Test Cases

| Test Case | User Type | Expected Result | Status |
|-----------|-----------|----------------|---------|
| Sign in with Google | Customer | Successful login, profile created | ? Pass |
| Book a vehicle | Customer | Booking created, notification sent | ? Pass |
| Upload license | Customer | Image uploaded, admin can view | ? Pass |
| Approve booking | Admin | Status changes to "Approved" | ? Pass |
| Track vehicle GPS | Customer | Real-time location updates | ? Pass |
| Request extension | Customer | Extension request submitted | ? Pass |
| Resolve conflict | Admin | Alternative vehicle assigned | ? Pass |

### 5. **Performance Testing**
Testing system performance under load.

#### Load Testing Scenarios
```python
# Simulate 100 concurrent users
def test_concurrent_bookings():
    users = [create_test_user() for _ in range(100)]
    
    # All users book at the same time
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(create_booking, user) for user in users]
        results = [f.result() for f in futures]
    
    # Verify no double-bookings occurred
    assert no_duplicate_bookings(results)
```

**What We Test:**
- ? Response time under load (< 2 seconds)
- ? Database connection pool handling (100+ concurrent connections)
- ? API rate limiting
- ? Memory usage and leaks
- ? File upload performance (images)

### 6. **Security Testing**
Testing for vulnerabilities and security flaws.

#### Security Test Cases
```python
# Test: SQL Injection Prevention
def test_sql_injection():
    malicious_input = "1' OR '1'='1"
    response = login_user(malicious_input, 'password')
    assert response.status_code == 401  # Should fail, not succeed!

# Test: Authentication Required
def test_protected_endpoint_without_token():
    response = get_bookings(token=None)
    assert response.status_code == 401  # Unauthorized

# Test: Authorization (User can only see their own bookings)
def test_user_cannot_access_other_bookings():
    user1_token = login_user('user1@gmail.com')
    user2_booking_id = 999
    
    response = get_booking_details(user2_booking_id, user1_token)
    assert response.status_code == 403  # Forbidden
```

**Security Measures Tested:**
- ? SQL Injection prevention (parameterized queries)
- ? XSS prevention (input sanitization)
- ? CSRF protection (token validation)
- ? Authentication enforcement (JWT tokens)
- ? Authorization checks (role-based access)
- ? Secure password hashing (bcrypt)
- ? HTTPS enforcement (SSL certificates)
- ? File upload validation (image type checking)

### 7. **Regression Testing**
Testing that new changes don't break existing features.

#### Regression Test Suite
After every code change, we run:
1. ? All unit tests (backend + frontend)
2. ? Critical path integration tests
3. ? Smoke tests (basic functionality)

Example:
```python
# After adding "booking extensions" feature, verify:
def test_regression_basic_booking_still_works():
    # Ensure basic booking flow is not broken
    booking = create_booking(...)
    assert booking['status'] == 'Pending'
    
def test_regression_existing_bookings_unaffected():
    # Ensure old bookings still display correctly
    old_bookings = get_user_bookings(user_id=1)
    assert len(old_bookings) > 0
```

---

## Quality Assurance Process

### QA Checklist Before Release

#### Backend QA
- [ ] All API endpoints return correct status codes
- [ ] Database migrations run successfully
- [ ] Error messages are user-friendly
- [ ] Logs are properly configured
- [ ] Environment variables are set
- [ ] CORS is configured correctly
- [ ] Rate limiting is enabled
- [ ] Backup system is in place

#### Frontend QA
- [ ] All screens render correctly
- [ ] Forms validate input properly
- [ ] Loading indicators display during API calls
- [ ] Error messages display for failed requests
- [ ] Navigation flows logically
- [ ] Images load correctly
- [ ] GPS tracking works
- [ ] Push notifications work
- [ ] App doesn't crash on invalid input

#### Mobile App QA
- [ ] APK builds successfully
- [ ] App installs on Android device
- [ ] Google Sign-In works
- [ ] Camera permission works
- [ ] Location permission works
- [ ] Notification permission works
- [ ] App works on different screen sizes
- [ ] App works on different Android versions (8.0+)

#### Deployment QA
- [ ] Backend is accessible at production URL
- [ ] Database connection works
- [ ] External APIs are reachable (Google, Firebase, PayMongo)
- [ ] SSL certificate is valid
- [ ] Privacy policy page is accessible
- [ ] Mobile apps connect to production backend

---

## Tools and Technologies

### Development Tools
| Tool | Purpose |
|------|---------|
| **VS Code** | Code editor |
| **Git** | Version control |
| **GitHub** | Code repository |
| **Postman** | API testing |
| **Chrome DevTools** | Frontend debugging |
| **Android Studio** | Mobile app building |
| **Python** | Backend language |
| **Flask** | Web framework |

### Testing Tools
| Tool | Purpose |
|------|---------|
| **pytest** | Python unit testing |
| **Jest** | JavaScript unit testing |
| **Postman** | API integration testing |
| **Chrome DevTools** | Frontend testing |
| **Android Emulator** | Mobile app testing |
| **Real Android Device** | Real-world testing |

### Deployment Tools
| Tool | Purpose |
|------|---------|
| **Vercel** | Backend hosting |
| **Supabase** | Database & storage |
| **Google Play Console** | App distribution |
| **GitHub Actions** | CI/CD automation |

### Monitoring Tools
| Tool | Purpose |
|------|---------|
| **Vercel Logs** | Backend error monitoring |
| **Supabase Logs** | Database query monitoring |
| **Firebase Console** | Push notification analytics |
| **Google Play Console** | App crash reports |

---

## Best Practices

### Development Best Practices

#### 1. **Code Organization**
```
? DO: Organize code into logical modules
? DON'T: Put all code in one giant file

? DO: Use meaningful variable names (customer_email)
? DON'T: Use cryptic names (ce, x, temp)
```

#### 2. **Error Handling**
```python
? DO: Handle errors gracefully
try:
    result = process_payment(...)
except PaymentError as e:
    return jsonify({'error': 'Payment failed: ' + str(e)}), 400

? DON'T: Let errors crash the app
result = process_payment(...)  # What if it fails?
```

#### 3. **Database Safety**
```python
? DO: Use parameterized queries
cur.execute("SELECT * FROM users WHERE email = %s", (email,))

? DON'T: Use string concatenation (SQL injection risk!)
cur.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

#### 4. **Input Validation**
```python
? DO: Validate all user input
if not email or '@' not in email:
    return jsonify({'error': 'Invalid email'}), 400

? DON'T: Trust user input blindly
user = create_user(email=request.json['email'])  # What if it's missing?
```

### Testing Best Practices

#### 1. **Test Coverage**
```
? DO: Test happy path AND error cases
test_valid_booking()
test_invalid_dates()
test_missing_vehicle_id()

? DON'T: Only test happy path
test_valid_booking()  # What about errors?
```

#### 2. **Test Independence**
```python
? DO: Each test should be independent
def test_create_booking():
    user = create_test_user()  # Fresh user for this test
    booking = create_booking(user)
    assert booking['status'] == 'Pending'

? DON'T: Tests that depend on each other
def test_create_booking():
    booking = create_booking(global_user)  # Depends on other test!
```

#### 3. **Realistic Test Data**
```python
? DO: Use realistic test data
test_user = {
    'email': 'john.doe@gmail.com',
    'name': 'John Doe',
    'phone': '+639171234567'
}

? DON'T: Use dummy data that doesn't represent reality
test_user = {
    'email': 'test',
    'name': 'x',
    'phone': '123'
}
```

#### 4. **Test Documentation**
```python
? DO: Document what you're testing
def test_booking_conflict_detection():
    """
    Test that the system detects when two bookings overlap
    for the same vehicle and prevents double-booking.
    """
    ...

? DON'T: Leave tests unexplained
def test_booking():  # Test what about booking?
    ...
```

---

## Summary

### Development Process
1. **Plan** ? Define requirements and design
2. **Build** ? Write code for backend, frontend, and mobile apps
3. **Integrate** ? Connect all components and external services
4. **Deploy** ? Release to production (Vercel, Google Play)

### Testing Process
1. **Unit Test** ? Test individual functions
2. **Integration Test** ? Test component interactions
3. **System Test** ? Test entire system end-to-end
4. **UAT** ? Real users test in real scenarios
5. **Performance Test** ? Test under load
6. **Security Test** ? Test for vulnerabilities
7. **Regression Test** ? Ensure no features break

### Key Takeaways
- ? **Development and testing go hand-in-hand** - test as you build
- ? **Catch bugs early** - unit tests catch issues before integration
- ? **Think like a user** - UAT reveals real-world problems
- ? **Security first** - always validate input and protect data
- ? **Monitor in production** - use logs to catch issues after release

---

**Document Version**: 1.0  
**Last Updated**: June 22, 2026  
**System**: Autoride Car Rental Booking System
