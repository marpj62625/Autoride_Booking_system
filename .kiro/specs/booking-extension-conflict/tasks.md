# Tasks Document: Booking Extension with Conflict Resolution

## Overview

Implementation of booking extension feature with automatic conflict detection, 3-tier alternative vehicle matching, and customer notification system. Includes backward compatibility safeguards to ensure zero breaking changes to existing functionality.

**Estimated Effort:** 185 hours (~4-5 weeks with 2-3 developers)

# Implementation Plan:

### Phase 1: Database & Backend Foundation (Week 1)
- Database schema and core APIs
- Conflict detection and alternative matching algorithms
- Extension request and approval workflows

### Phase 2: Notification & Conflict Resolution (Week 2)
- Multi-channel notification system (push + email)
- Conflict resolution APIs
- Refund processing integration
- Background jobs (deadline monitoring, reminders)

### Phase 3: Customer Mobile App (Week 2-3)
- Extension request UI
- Conflict notification and resolution screens
- Alternative vehicle selection interface

### Phase 4: Admin Panel (Week 3)
- Extension review and approval interface
- Conflict monitoring dashboard

### Phase 5: Testing & QA (Week 3-4)
- Integration testing
- Backward compatibility verification
- Performance testing
- User acceptance testing

### Phase 6: Deployment & Monitoring (Week 4)
- Feature flag setup
- Production deployment
- Monitoring and alerting configuration

### Phase 7: Documentation & Training (Week 4)
- Technical documentation
- User guides
- Admin training

## Task Dependency Graph

```json
{
  "waves": [
    {
      "waveName": "Wave 1: Database Foundation",
      "tasks": [1]
    },
    {
      "waveName": "Wave 2: Core Backend APIs",
      "tasks": [2, 3, 4]
    },
    {
      "waveName": "Wave 3: Admin & Advanced Backend",
      "tasks": [5, 6, 7, 8]
    },
    {
      "waveName": "Wave 4: Background Jobs",
      "tasks": [9, 10]
    },
    {
      "waveName": "Wave 5: Mobile & Admin UI",
      "tasks": [11, 12, 13, 14, 15, 16, 17, 18]
    },
    {
      "waveName": "Wave 6: Testing",
      "tasks": [19, 20, 21, 22]
    },
    {
      "waveName": "Wave 7: Deployment Preparation",
      "tasks": [23, 24, 25, 26, 27]
    },
    {
      "waveName": "Wave 8: Rollout & Documentation",
      "tasks": [28, 29, 30, 31, 32]
    }
  ]
}
```

## Tasks

- [ ] 1. Database Schema Implementation (4 hours)
  - [ ] 1.1 Create migration script file `backend/migrations/XXX_add_extension_tables.sql`
  - [ ] 1.2 Create `booking_extensions` table with all columns (extension_id, booking_id, requested_by_user_id, original_end_date, requested_end_date, additional_days, additional_cost, status, admin_notes, approved_by_admin_id, approved_at, has_conflicts, created_at, updated_at)
  - [ ] 1.3 Create `booking_conflicts` table with all columns (conflict_id, extension_id, affected_booking_id, affected_user_id, conflict_start_date, conflict_end_date, resolution_status, resolution_deadline, selected_alternative_vehicle_id, refund_amount, refund_status, refund_transaction_id, customer_notified_at, customer_responded_at, created_at, updated_at)
  - [ ] 1.4 Create `extension_payments` table with all columns (payment_id, extension_id, booking_id, user_id, amount, payment_method, payment_status, payment_proof_url, transaction_reference, paid_at, created_at)
  - [ ] 1.5 Add new columns to `bookings` table using ALTER TABLE with DEFAULT values (has_active_extension BOOLEAN DEFAULT FALSE, extension_count INT DEFAULT 0, is_conflict_affected BOOLEAN DEFAULT FALSE, conflict_id INT DEFAULT NULL)
  - [ ] 1.6 Add foreign key constraints for all relationships
  - [ ] 1.7 Create indexes on frequently queried columns (booking_id, status, resolution_deadline, created_at)
  - [ ] 1.8 Test migration on development database
  - [ ] 1.9 Create rollback script file `backend/migrations/XXX_rollback_extension_tables.sql`
  - [ ] 1.10 Verify rollback script works correctly

- [ ] 2. Extension Request API - Customer (8 hours)
  - [ ] 2.1 Create route file `backend/routes/booking_extensions.py`
  - [ ] 2.2 Create model file `backend/models/booking_extension.py`
  - [ ] 2.3 Create validator file `backend/validators/extension_validator.py`
  - [ ] 2.4 Implement `POST /api/bookings/<id>/extension/request` endpoint
  - [ ] 2.5 Add validation: booking must have status='Active'
  - [ ] 2.6 Add validation: vehicle must be picked up (vehicle_picked_up=True)
  - [ ] 2.7 Add validation: extension_count must be < 1 (max 1 extension per booking)
  - [ ] 2.8 Add validation: requested_end_date must be > current end_date
  - [ ] 2.9 Add validation: additional days must be <= 30
  - [ ] 2.10 Add validation: no outstanding payments exist
  - [ ] 2.11 Calculate additional_days and additional_cost
  - [ ] 2.12 Create extension record with status='Pending'
  - [ ] 2.13 Implement `GET /api/bookings/<id>/extension/status` endpoint
  - [ ] 2.14 Write unit tests in `backend/tests/test_extension_request.py`
  - [ ] 2.15 Test all validation rules with invalid data
  - [ ] 2.16 Test successful extension request creation
  - [ ] 2.17 Update API documentation

- [ ] 3. Conflict Detection Algorithm (6 hours)
  - [ ] 3.1 Create service file `backend/services/conflict_detector.py`
  - [ ] 3.2 Implement conflict detection SQL query with date overlap logic
  - [ ] 3.3 Query checks: new_end_date >= future_booking_start_date
  - [ ] 3.4 Query filters: same vehicle_id, status IN ('Approved', 'Pending')
  - [ ] 3.5 Query excludes current booking_id
  - [ ] 3.6 Return list of affected bookings with full details
  - [ ] 3.7 Add performance optimization with proper indexes
  - [ ] 3.8 Create test file `backend/tests/test_conflict_detection.py`
  - [ ] 3.9 Test scenario: extension overlaps one future booking
  - [ ] 3.10 Test scenario: extension overlaps multiple future bookings
  - [ ] 3.11 Test scenario: extension does not overlap any bookings
  - [ ] 3.12 Test scenario: same-day overlap
  - [ ] 3.13 Test scenario: multi-day overlap
  - [ ] 3.14 Verify query executes in < 2 seconds

- [ ] 4. Alternative Vehicle Matching - 3-Tier Algorithm (8 hours)
  - [ ] 4.1 Create service file `backend/services/alternative_matcher.py`
  - [ ] 4.2 Implement Tier 1 query: same brand AND price within ±2%
  - [ ] 4.3 Implement Tier 2 query: same brand OR price within ±5%
  - [ ] 4.4 Implement Tier 3 query: same category, price within ±10%
  - [ ] 4.5 Add availability check for requested date range
  - [ ] 4.6 Add location/branch matching filter
  - [ ] 4.7 Add vehicle status filter (exclude 'Under Maintenance')
  - [ ] 4.8 Implement sorting: Tier 1 first, then Tier 2, then Tier 3
  - [ ] 4.9 Within tiers, sort by: brand match priority, then price proximity
  - [ ] 4.10 Limit results to top 5 matches
  - [ ] 4.11 Return tier label with each result ('Perfect Match', 'Close Match', 'Alternative')
  - [ ] 4.12 Create test file `backend/tests/test_alternative_matching.py`
  - [ ] 4.13 Test with inventory containing Tier 1 matches
  - [ ] 4.14 Test with inventory containing only Tier 2 matches
  - [ ] 4.15 Test with inventory containing only Tier 3 matches
  - [ ] 4.16 Test with empty inventory (no alternatives)
  - [ ] 4.17 Verify query executes in < 3 seconds

- [ ] 5. Admin Extension Approval API (10 hours)
  - [ ] 5.1 Create route file `backend/routes/admin_extensions.py`
  - [ ] 5.2 Create service file `backend/services/extension_approval_service.py`
  - [ ] 5.3 Implement `GET /api/admin/extensions/pending` endpoint
  - [ ] 5.4 Implement `GET /api/admin/extensions/<id>/check-conflicts` endpoint using conflict detector
  - [ ] 5.5 Implement `POST /api/admin/extensions/<id>/approve` endpoint
  - [ ] 5.6 Wrap approval in database transaction
  - [ ] 5.7 Step 1 in transaction: Update extension status to 'Approved'
  - [ ] 5.8 Step 2 in transaction: Update booking end_date with new date
  - [ ] 5.9 Step 3 in transaction: Increment booking extension_count
  - [ ] 5.10 Step 4 in transaction: Run conflict detection
  - [ ] 5.11 Step 5 in transaction: Create conflict records for affected bookings
  - [ ] 5.12 Step 6 in transaction: Update affected bookings is_conflict_affected=True
  - [ ] 5.13 Step 7 in transaction: Trigger notification system
  - [ ] 5.14 Add rollback on any failure
  - [ ] 5.15 Log admin action with admin_id and timestamp
  - [ ] 5.16 Create test file `backend/tests/test_extension_approval.py`
  - [ ] 5.17 Test approval without conflicts
  - [ ] 5.18 Test approval with conflicts
  - [ ] 5.19 Test transaction rollback on failure
  - [ ] 5.20 Update API documentation

- [ ] 6. Conflict Notification System (8 hours)
  - [ ] 6.1 Create service file `backend/services/conflict_notifier.py`
  - [ ] 6.2 Create email template file `backend/templates/email_conflict_notification.html`
  - [ ] 6.3 Implement push notification integration (use existing push system)
  - [ ] 6.4 Implement email notification using template
  - [ ] 6.5 Create notification sending function with multi-channel delivery
  - [ ] 6.6 Add retry logic: retry up to 3 times on failure
  - [ ] 6.7 Add 2-second delay between retries
  - [ ] 6.8 Track notification delivery status in database
  - [ ] 6.9 Log failed notifications for manual follow-up
  - [ ] 6.10 Set resolution_deadline = NOW() + 72 hours
  - [ ] 6.11 Create test file `backend/tests/test_conflict_notifications.py`
  - [ ] 6.12 Test push notification delivery
  - [ ] 6.13 Test email notification delivery
  - [ ] 6.14 Test retry logic on failure
  - [ ] 6.15 Test notification tracking

- [ ] 7. Conflict Resolution APIs (10 hours)
  - [ ] 7.1 Create route file `backend/routes/conflict_resolution.py`
  - [ ] 7.2 Create service file `backend/services/conflict_resolver.py`
  - [ ] 7.3 Implement `GET /api/conflicts/my-affected-bookings` endpoint
  - [ ] 7.4 Implement `GET /api/conflicts/<id>/alternatives` endpoint using alternative matcher
  - [ ] 7.5 Implement `POST /api/conflicts/<id>/select-alternative` endpoint
  - [ ] 7.6 Validate: conflict must have status='Pending'
  - [ ] 7.7 Validate: not past resolution deadline
  - [ ] 7.8 Validate: selected vehicle must be available
  - [ ] 7.9 Validate: selected vehicle must be in alternatives list
  - [ ] 7.10 Update booking with new vehicle_id
  - [ ] 7.11 Update conflict resolution_status='Alternative_Selected'
  - [ ] 7.12 Record customer_responded_at timestamp
  - [ ] 7.13 Send confirmation notification to customer
  - [ ] 7.14 Implement `POST /api/conflicts/<id>/request-refund` endpoint
  - [ ] 7.15 Update conflict resolution_status='Refund_Processed'
  - [ ] 7.16 Initiate refund processing
  - [ ] 7.17 Update booking status='Cancelled - Extension Conflict'
  - [ ] 7.18 Send refund confirmation to customer
  - [ ] 7.19 Create test file `backend/tests/test_conflict_resolution.py`
  - [ ] 7.20 Test alternative vehicle selection
  - [ ] 7.21 Test refund request
  - [ ] 7.22 Test validation rules
  - [ ] 7.23 Update API documentation

- [ ] 8. Refund Processing Integration (6 hours)
  - [ ] 8.1 Create service file `backend/services/refund_processor.py`
  - [ ] 8.2 Create integration file `backend/integrations/paymongo_refund.py`
  - [ ] 8.3 Implement PayMongo refund API integration
  - [ ] 8.4 Implement GCash refund (if API available, otherwise flag for manual)
  - [ ] 8.5 Implement Maya refund (if API available, otherwise flag for manual)
  - [ ] 8.6 Calculate refund amount = 100% of payment received
  - [ ] 8.7 Determine original payment method from booking
  - [ ] 8.8 Create refund transaction record
  - [ ] 8.9 Update refund_status through processing stages
  - [ ] 8.10 Handle refund API failures gracefully
  - [ ] 8.11 Log failed refunds for manual admin processing
  - [ ] 8.12 Send refund confirmation email to customer
  - [ ] 8.13 Create test file `backend/tests/test_refund_processing.py`
  - [ ] 8.14 Test PayMongo refund flow with sandbox
  - [ ] 8.15 Test refund failure handling
  - [ ] 8.16 Test manual refund flagging

- [ ] 9. Background Job - Deadline Monitor (6 hours)
  - [ ] 9.1 Create job file `backend/jobs/conflict_deadline_monitor.py`
  - [ ] 9.2 Query conflicts where resolution_deadline < NOW() AND resolution_status='Pending'
  - [ ] 9.3 For each expired conflict, update resolution_status='Auto_Cancelled'
  - [ ] 9.4 Initiate automatic refund processing
  - [ ] 9.5 Update booking status='Cancelled - Extension Conflict'
  - [ ] 9.6 Send final notification to customer
  - [ ] 9.7 Notify admin of auto-cancellation
  - [ ] 9.8 Log auto-cancellation event
  - [ ] 9.9 Create cron schedule file `backend/cron/schedule_jobs.sh`
  - [ ] 9.10 Set cron to run every 1 hour
  - [ ] 9.11 Create test file `backend/tests/test_deadline_monitor.py`
  - [ ] 9.12 Test expired conflict detection
  - [ ] 9.13 Test auto-cancellation process
  - [ ] 9.14 Test notification delivery

- [ ] 10. Background Job - Reminder Notifications (4 hours)
  - [ ] 10.1 Create job file `backend/jobs/conflict_reminder.py`
  - [ ] 10.2 Query conflicts where resolution_deadline BETWEEN NOW() AND NOW()+24h AND resolution_status='Pending'
  - [ ] 10.3 Exclude conflicts where reminder already sent (check customer_notified_at)
  - [ ] 10.4 Send reminder push notification
  - [ ] 10.5 Send reminder email
  - [ ] 10.6 Update reminder sent tracking
  - [ ] 10.7 Set cron to run every 12 hours
  - [ ] 10.8 Create test file `backend/tests/test_conflict_reminder.py`
  - [ ] 10.9 Test reminder detection logic
  - [ ] 10.10 Test duplicate prevention

- [ ] 11. Customer Mobile - Extension Request UI (8 hours)
  - [ ] 11.1 Add "Extend Booking" button to `customer_mobile/www/pages/booking-detail.html`
  - [ ] 11.2 Show button only when booking status='Active'
  - [ ] 11.3 Create extension request form page `customer_mobile/www/pages/extension-request.html`
  - [ ] 11.4 Add date picker component for new return date
  - [ ] 11.5 Display current return date for reference
  - [ ] 11.6 Calculate and display additional days dynamically
  - [ ] 11.7 Calculate and display additional cost (additional_days × daily_rate)
  - [ ] 11.8 Add optional reason text area
  - [ ] 11.9 Create controller file `customer_mobile/www/js/extension-controller.js`
  - [ ] 11.10 Implement form validation (date must be future, max 30 days)
  - [ ] 11.11 Call POST /api/bookings/<id>/extension/request API
  - [ ] 11.12 Show success message on submission
  - [ ] 11.13 Show error messages for validation failures
  - [ ] 11.14 Update booking detail to show "Extension Pending" status
  - [ ] 11.15 Create CSS file `customer_mobile/www/css/extension.css`
  - [ ] 11.16 Test on Android device
  - [ ] 11.17 Test on iOS device (if available)

- [ ] 12. Customer Mobile - Conflict Notification Banner (6 hours)
  - [ ] 12.1 Create banner component file `customer_mobile/www/components/conflict-banner.html`
  - [ ] 12.2 Create controller file `customer_mobile/www/js/conflict-banner-controller.js`
  - [ ] 12.3 Display banner on home screen when conflict exists
  - [ ] 12.4 Fetch conflicts using GET /api/conflicts/my-affected-bookings
  - [ ] 12.5 Show warning icon and red/orange styling
  - [ ] 12.6 Display affected booking details (vehicle, dates)
  - [ ] 12.7 Add "View Options" button
  - [ ] 12.8 Implement push notification handler (open app to conflict screen)
  - [ ] 12.9 Navigate to conflict resolution screen on tap
  - [ ] 12.10 Create CSS file `customer_mobile/www/css/conflict-banner.css`
  - [ ] 12.11 Test banner display
  - [ ] 12.12 Test push notification tap behavior

- [ ] 13. Customer Mobile - Alternative Vehicles Screen (10 hours)
  - [ ] 13.1 Create alternative vehicles page `customer_mobile/www/pages/alternative-vehicles.html`
  - [ ] 13.2 Create controller file `customer_mobile/www/js/alternative-vehicles-controller.js`
  - [ ] 13.3 Fetch alternatives using GET /api/conflicts/<id>/alternatives
  - [ ] 13.4 Display tier badge for each vehicle (Perfect Match / Close Match / Alternative)
  - [ ] 13.5 Create vehicle card component `customer_mobile/www/components/vehicle-card.html`
  - [ ] 13.6 Display vehicle photo, brand, model, year
  - [ ] 13.7 Display price comparison with original vehicle
  - [ ] 13.8 Show "No extra cost to you" label when applicable
  - [ ] 13.9 Add "Select This Vehicle" button for each option
  - [ ] 13.10 Implement vehicle detail modal view
  - [ ] 13.11 Show loading spinner while fetching
  - [ ] 13.12 Handle empty results (no alternatives available)
  - [ ] 13.13 Show "Request Full Refund" button at bottom
  - [ ] 13.14 Call POST /api/conflicts/<id>/select-alternative on selection
  - [ ] 13.15 Show confirmation dialog before finalizing
  - [ ] 13.16 Navigate to success screen after selection
  - [ ] 13.17 Create CSS file `customer_mobile/www/css/alternatives.css`
  - [ ] 13.18 Test tier badge display
  - [ ] 13.19 Test vehicle selection flow
  - [ ] 13.20 Test "no alternatives" scenario

- [ ] 14. Customer Mobile - Refund Request Screen (4 hours)
  - [ ] 14.1 Create refund request page `customer_mobile/www/pages/refund-request.html`
  - [ ] 14.2 Create controller file `customer_mobile/www/js/refund-controller.js`
  - [ ] 14.3 Display refund amount prominently
  - [ ] 14.4 Display original payment method
  - [ ] 14.5 Display refund timeline (3-5 business days)
  - [ ] 14.6 Show booking details being cancelled
  - [ ] 14.7 Add confirmation checkbox ("I understand this will cancel my booking")
  - [ ] 14.8 Add "Confirm Full Refund" button
  - [ ] 14.9 Call POST /api/conflicts/<id>/request-refund
  - [ ] 14.10 Show success message with refund reference
  - [ ] 14.11 Update booking status to "Cancelled"
  - [ ] 14.12 Test refund flow
  - [ ] 14.13 Test confirmation requirement

- [ ] 15. Customer Mobile - Conflict Resolution Main Screen (6 hours)
  - [ ] 15.1 Create conflict resolution page `customer_mobile/www/pages/conflict-resolution.html`
  - [ ] 15.2 Create controller file `customer_mobile/www/js/conflict-resolution-controller.js`
  - [ ] 15.3 Display affected booking details (vehicle name, dates)
  - [ ] 15.4 Display conflict reason ("Current renter extended booking")
  - [ ] 15.5 Show resolution deadline with countdown timer
  - [ ] 15.6 Display two large option buttons: "Choose Alternative Vehicle" and "Get Full Refund"
  - [ ] 15.7 Show number of alternatives available on button
  - [ ] 15.8 Add warning styling (orange/red theme)
  - [ ] 15.9 Implement countdown timer that updates every minute
  - [ ] 15.10 Navigate to alternatives screen on "Choose Alternative" tap
  - [ ] 15.11 Navigate to refund screen on "Get Full Refund" tap
  - [ ] 15.12 Create CSS file `customer_mobile/www/css/conflict-resolution.css`
  - [ ] 15.13 Test timer functionality
  - [ ] 15.14 Test navigation
  - [ ] 15.15 Test UI on small screens

- [ ] 16. Admin Panel - Extension Request Review (8 hours)
  - [ ] 16.1 Add "Extensions" menu item to admin sidebar `admin_mobile/www/index.html`
  - [ ] 16.2 Create extensions list page `admin_mobile/www/pages/extensions-list.html`
  - [ ] 16.3 Create extension detail page `admin_mobile/www/pages/extension-detail.html`
  - [ ] 16.4 Create controller file `admin_mobile/www/js/extensions-controller.js`
  - [ ] 16.5 Fetch pending extensions using GET /api/admin/extensions/pending
  - [ ] 16.6 Display list with customer name, vehicle, dates, additional cost
  - [ ] 16.7 Add conflict indicator badge if has_potential_conflicts=true
  - [ ] 16.8 In detail view, display all customer information
  - [ ] 16.9 Display current booking period and requested extension
  - [ ] 16.10 Show calculated additional cost
  - [ ] 16.11 Fetch and display conflicts using GET /api/admin/extensions/<id>/check-conflicts
  - [ ] 16.12 Show affected booking details in conflict section
  - [ ] 16.13 Add admin notes text area
  - [ ] 16.14 Add confirmation checkbox ("I acknowledge affected customers will be notified")
  - [ ] 16.15 Add "Reject" and "Approve" buttons
  - [ ] 16.16 Call POST /api/admin/extensions/<id>/approve on approval
  - [ ] 16.17 Show success message on approval
  - [ ] 16.18 Refresh list after approval
  - [ ] 16.19 Create CSS file `admin_mobile/www/css/extensions.css`
  - [ ] 16.20 Test extension review workflow

- [ ] 17. Admin Panel - Conflict Management Dashboard (6 hours)
  - [ ] 17.1 Create conflicts dashboard page `admin_mobile/www/pages/conflicts-dashboard.html`
  - [ ] 17.2 Create controller file `admin_mobile/www/js/conflicts-controller.js`
  - [ ] 17.3 Fetch active conflicts using GET /api/admin/conflicts/active
  - [ ] 17.4 Display summary statistics (total active, pending response, resolved, expired)
  - [ ] 17.5 Display conflict cards with customer name, vehicle, dates, deadline
  - [ ] 17.6 Show resolution status badge for each conflict
  - [ ] 17.7 Show countdown timer for deadline
  - [ ] 17.8 Highlight conflicts approaching deadline (< 24 hours) in orange
  - [ ] 17.9 Add filter dropdown (All / Pending / Resolved / Expired)
  - [ ] 17.10 Add search by customer name or booking ID
  - [ ] 17.11 Add refresh button
  - [ ] 17.12 Show customer response status (viewed notification, responded, etc.)
  - [ ] 17.13 Create CSS file `admin_mobile/www/css/conflicts.css`
  - [ ] 17.14 Test dashboard display
  - [ ] 17.15 Test filters and search

- [ ] 18. Admin Panel - Admin Notifications (4 hours)
  - [ ] 18.1 Create notification component `admin_mobile/www/components/admin-notifications.html`
  - [ ] 18.2 Create controller file `admin_mobile/www/js/admin-notifications-controller.js`
  - [ ] 18.3 Add notification badge to header showing count of pending extensions
  - [ ] 18.4 Add notification badge showing count of unresolved conflicts
  - [ ] 18.5 Implement toast notification for new extension requests
  - [ ] 18.6 Implement toast notification for customer conflict resolutions
  - [ ] 18.7 Add notification center panel (slide-in from right)
  - [ ] 18.8 List all admin alerts with timestamps
  - [ ] 18.9 Make notifications clickable (navigate to relevant screen)
  - [ ] 18.10 Test notification display
  - [ ] 18.11 Test navigation from notifications

- [ ] 19. Integration Testing (12 hours)
  - [ ] 19.1 Test complete extension request flow (customer ? admin approval, no conflicts)
  - [ ] 19.2 Test extension approval creating conflicts
  - [ ] 19.3 Test conflict notification delivery (push + email)
  - [ ] 19.4 Test customer selects Tier 1 alternative vehicle
  - [ ] 19.5 Test customer selects Tier 2 alternative vehicle
  - [ ] 19.6 Test customer selects Tier 3 alternative vehicle
  - [ ] 19.7 Test customer requests full refund
  - [ ] 19.8 Test refund processing through payment gateway
  - [ ] 19.9 Test no alternatives available scenario
  - [ ] 19.10 Test auto-cancellation after deadline expiry
  - [ ] 19.11 Test reminder notification sent before deadline
  - [ ] 19.12 Test multiple simultaneous conflicts from one extension
  - [ ] 19.13 Test extension on last day of rental (edge case)
  - [ ] 19.14 Test maximum extension days (30 days)
  - [ ] 19.15 Test extension request with outstanding payments (should fail)
  - [ ] 19.16 Test transaction rollback on approval failure
  - [ ] 19.17 Document all test results

- [ ] 20. Backward Compatibility Testing (6 hours)
  - [ ] 20.1 Test existing GET /api/bookings (should return same format)
  - [ ] 20.2 Test existing POST /api/bookings (should create bookings unchanged)
  - [ ] 20.3 Test existing booking approval flow (should work as before)
  - [ ] 20.4 Test existing booking cancellation (should work as before)
  - [ ] 20.5 Test existing payment processing (should work as before)
  - [ ] 20.6 Test vehicle availability check (should respect extended bookings automatically)
  - [ ] 20.7 Test old mobile app version compatibility (extension features hidden)
  - [ ] 20.8 Test admin panel existing functions (all should work unchanged)
  - [ ] 20.9 Run existing test suite (all should pass)
  - [ ] 20.10 Measure database query performance on bookings table (should be unchanged)
  - [ ] 20.11 Test with feature flag disabled (extension features should be inaccessible)
  - [ ] 20.12 Document compatibility test results

- [ ] 21. Performance Testing (4 hours)
  - [ ] 21.1 Load test POST /api/bookings/<id>/extension/request with 100 concurrent requests
  - [ ] 21.2 Load test conflict detection with various data sizes
  - [ ] 21.3 Load test alternative matching with 100+ vehicles in inventory
  - [ ] 21.4 Measure conflict detection execution time (must be < 2 seconds)
  - [ ] 21.5 Measure alternative matching execution time (must be < 3 seconds)
  - [ ] 21.6 Monitor server CPU and memory usage during load test
  - [ ] 21.7 Test database connection pool under load
  - [ ] 21.8 Verify notification delivery within 30 seconds
  - [ ] 21.9 Test background job execution time (deadline monitor)
  - [ ] 21.10 Document performance metrics

- [ ] 22. User Acceptance Testing - UAT (8 hours)
  - [ ] 22.1 Recruit 5 test users (3 customers, 2 admins)
  - [ ] 22.2 Prepare test scenarios and test data
  - [ ] 22.3 Customer UAT: Request extension on active booking
  - [ ] 22.4 Customer UAT: Receive conflict notification
  - [ ] 22.5 Customer UAT: Select alternative vehicle from options
  - [ ] 22.6 Customer UAT: Request full refund
  - [ ] 22.7 Admin UAT: Review extension request
  - [ ] 22.8 Admin UAT: Approve extension with conflicts
  - [ ] 22.9 Admin UAT: Monitor conflict resolutions
  - [ ] 22.10 Collect usability feedback from all participants
  - [ ] 22.11 Document usability issues found
  - [ ] 22.12 Prioritize fixes (Critical / High / Medium / Low)
  - [ ] 22.13 Create UAT report with recommendations

- [ ] 23. Feature Flag Configuration (2 hours)
  - [ ] 23.1 Add EXTENSION_FEATURE_ENABLED to `backend/config.py`
  - [ ] 23.2 Set default value to 'false'
  - [ ] 23.3 Add feature flag check to all extension endpoints
  - [ ] 23.4 Return 503 Service Unavailable when flag is disabled
  - [ ] 23.5 Add flag check to mobile app (hide extension buttons when disabled)
  - [ ] 23.6 Test enabling and disabling feature via config
  - [ ] 23.7 Document feature flag usage in `docs/FEATURE_FLAGS.md`

- [ ] 24. Database Migration to Production (2 hours)
  - [ ] 24.1 Schedule maintenance window with stakeholders
  - [ ] 24.2 Create full backup of production database
  - [ ] 24.3 Verify backup integrity
  - [ ] 24.4 Run migration script on production
  - [ ] 24.5 Verify all tables created successfully
  - [ ] 24.6 Verify all indexes created successfully
  - [ ] 24.7 Run test queries to confirm schema
  - [ ] 24.8 Test rollback script on staging (do not run on prod unless needed)
  - [ ] 24.9 Document migration completion

- [ ] 25. Backend Deployment (3 hours)
  - [ ] 25.1 Deploy backend code to staging environment
  - [ ] 25.2 Run smoke tests on staging
  - [ ] 25.3 Verify all extension APIs responding on staging
  - [ ] 25.4 Deploy backend code to production
  - [ ] 25.5 Verify all APIs responding on production
  - [ ] 25.6 Check application logs for errors
  - [ ] 25.7 Test health check endpoints
  - [ ] 25.8 Verify database connections working
  - [ ] 25.9 Document deployment completion

- [ ] 26. Mobile App Deployment (4 hours)
  - [ ] 26.1 Build customer mobile app (APK + iOS bundle)
  - [ ] 26.2 Test customer app on staging backend
  - [ ] 26.3 Submit customer app to Google Play Store
  - [ ] 26.4 Submit customer app to Apple App Store (if applicable)
  - [ ] 26.5 Build admin mobile app
  - [ ] 26.6 Test admin app on staging backend
  - [ ] 26.7 Deploy admin app to internal distribution
  - [ ] 26.8 Monitor app crash reports
  - [ ] 26.9 Document app versions deployed

- [ ] 27. Monitoring & Alerting Setup (4 hours)
  - [ ] 27.1 Set up monitoring for extension request API response time
  - [ ] 27.2 Set up monitoring for conflict detection execution time
  - [ ] 27.3 Set up monitoring for alternative matching execution time
  - [ ] 27.4 Set up monitoring for notification delivery success rate
  - [ ] 27.5 Set up monitoring for refund processing success rate
  - [ ] 27.6 Set up monitoring for background job execution time
  - [ ] 27.7 Set up monitoring for database query performance on bookings table
  - [ ] 27.8 Configure alert: Extension approval time > 5 seconds
  - [ ] 27.9 Configure alert: Notification delivery failure rate > 10%
  - [ ] 27.10 Configure alert: Refund processing failure
  - [ ] 27.11 Configure alert: Background job execution failure
  - [ ] 27.12 Test all alerts by triggering test conditions
  - [ ] 27.13 Document monitoring setup in `docs/MONITORING.md`

- [ ] 28. Gradual Feature Rollout (2 hours)
  - [ ] 28.1 Enable feature flag for 10% of users (use user_id % 10 == 0)
  - [ ] 28.2 Monitor for 48 hours (check error rates, performance, user feedback)
  - [ ] 28.3 Review monitoring dashboards and alerts
  - [ ] 28.4 If no critical issues, increase to 50% of users (user_id % 2 == 0)
  - [ ] 28.5 Monitor for 24 hours
  - [ ] 28.6 Review monitoring dashboards and alerts
  - [ ] 28.7 If no critical issues, enable for 100% of users
  - [ ] 28.8 Monitor for 24 hours
  - [ ] 28.9 Document rollout completion

- [ ] 29. Technical Documentation (6 hours)
  - [ ] 29.1 Create `docs/EXTENSION_SCHEMA.md` documenting all new tables and columns
  - [ ] 29.2 Create `docs/EXTENSION_API.md` with Swagger/OpenAPI documentation for all endpoints
  - [ ] 29.3 Document conflict detection algorithm logic in `docs/EXTENSION_ALGORITHMS.md`
  - [ ] 29.4 Document 3-tier alternative matching algorithm in `docs/EXTENSION_ALGORITHMS.md`
  - [ ] 29.5 Create `docs/EXTENSION_JOBS.md` documenting background jobs (deadline monitor, reminder)
  - [ ] 29.6 Create `docs/EXTENSION_CONFIG.md` documenting configuration options and feature flags
  - [ ] 29.7 Create architecture diagram showing all components
  - [ ] 29.8 Create flowchart for extension request workflow
  - [ ] 29.9 Create flowchart for conflict resolution workflow
  - [ ] 29.10 Review all documentation for accuracy

- [ ] 30. Customer User Guide (4 hours)
  - [ ] 30.1 Write "How to Request a Booking Extension" guide
  - [ ] 30.2 Add screenshots of extension request flow
  - [ ] 30.3 Write "Understanding Booking Conflicts" guide
  - [ ] 30.4 Add screenshots of conflict notification
  - [ ] 30.5 Write "Choosing an Alternative Vehicle" guide
  - [ ] 30.6 Add screenshots of alternative vehicle selection
  - [ ] 30.7 Write "Requesting a Full Refund" guide
  - [ ] 30.8 Add screenshots of refund request flow
  - [ ] 30.9 Write FAQ section covering common questions
  - [ ] 30.10 Review guides for clarity and completeness
  - [ ] 30.11 Save as `docs/user_guides/CUSTOMER_EXTENSION_GUIDE.md`

- [ ] 31. Admin User Guide (4 hours)
  - [ ] 31.1 Write "Reviewing Extension Requests" guide
  - [ ] 31.2 Add screenshots of extension review interface
  - [ ] 31.3 Write "Understanding and Approving Extensions with Conflicts" guide
  - [ ] 31.4 Add screenshots of conflict detection warnings
  - [ ] 31.5 Write "Monitoring Conflict Resolutions" guide
  - [ ] 31.6 Add screenshots of conflict dashboard
  - [ ] 31.7 Write "Troubleshooting Guide" covering common issues
  - [ ] 31.8 Document manual refund processing procedure
  - [ ] 31.9 Review guides for accuracy
  - [ ] 31.10 Save as `docs/user_guides/ADMIN_EXTENSION_GUIDE.md`

- [ ] 32. Admin Training Session (2 hours)
  - [ ] 32.1 Prepare training presentation slides
  - [ ] 32.2 Schedule training session with admin team
  - [ ] 32.3 Conduct live demo of extension approval workflow
  - [ ] 32.4 Demonstrate conflict monitoring dashboard
  - [ ] 32.5 Walk through manual intervention scenarios
  - [ ] 32.6 Answer admin questions
  - [ ] 32.7 Provide user guide documents to admins
  - [ ] 32.8 Collect feedback on training
  - [ ] 32.9 Document any additional questions for FAQ

## Notes

### Feature Flag
- `EXTENSION_FEATURE_ENABLED` in `backend/config.py` controls entire feature
- Default: `false` (disabled)
- Must be explicitly enabled after deployment
- Can be disabled instantly if issues arise

### Backward Compatibility Guarantee
- All database changes use `DEFAULT` values
- No existing tables deleted or modified destructively
- All existing APIs unchanged
- Old mobile app versions continue working
- Feature can be completely disabled via flag

### Critical Success Metrics
- Extension approval response time < 5 seconds
- Conflict detection accuracy: 100%
- Notification delivery rate > 90%
- Zero impact on existing booking performance
- Customer satisfaction ? 4.5/5 for conflict resolution

### Rollback Plan
If critical issues occur:
1. Disable feature via `EXTENSION_FEATURE_ENABLED=false`
2. Monitor that existing booking flows work normally
3. If needed, run database rollback script
4. Investigate issues in staging environment
5. Deploy fixes and re-enable gradually
