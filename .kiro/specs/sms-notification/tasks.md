# Tasks Document: SMS Notification

## Task List

- [x] 1. Database migrations
  - [x] 1.1 Add `sms_opt_out` boolean column (default `false`) to `users` table
  - [x] 1.2 Add `phone` (VARCHAR 20) and `is_active` (BOOLEAN default TRUE) columns to `admins` table
  - [x] 1.3 Create `sms_logs` table with all columns defined in the design (id, recipient_phone, recipient_type, recipient_id, message_body, status, semaphore_response_code, error_message, created_at)
  - [x] 1.4 Add indexes on `sms_logs.created_at DESC` and `sms_logs.recipient_type`
  - [x] 1.5 Wire migrations into the existing `run_migrations()` function in `app.py` using `ADD COLUMN IF NOT EXISTS` / `CREATE TABLE IF NOT EXISTS` guards

- [x] 2. Message composition functions (`notifications.py`)
  - [x] 2.1 Implement `truncate_message(message, max_len=320)` — truncates to 317 chars + `...` if over limit, returns unchanged if within limit
  - [x] 2.2 Implement booking lifecycle compose functions: `compose_booking_created_sms`, `compose_booking_approved_sms`, `compose_booking_rejected_sms`, `compose_customer_cancel_sms`, `compose_admin_cancel_sms`, `compose_pickup_sms`, `compose_completed_sms`, `compose_modify_booking_sms`
  - [x] 2.3 Implement payment compose functions: `compose_full_payment_sms`, `compose_downpayment_sms`, `compose_balance_payment_sms`, `compose_cash_paid_sms`
  - [x] 2.4 Implement split payment compose functions: `compose_split_request_sms`, `compose_split_paid_sms`
  - [x] 2.5 Implement license verification compose functions: `compose_license_approved_sms`, `compose_license_rejected_sms`
  - [x] 2.6 Implement driver application compose functions: `compose_driver_approved_sms`, `compose_driver_rejected_sms`
  - [x] 2.7 Implement admin alert compose functions: `compose_admin_new_booking_sms`, `compose_admin_driver_application_sms`, `compose_admin_payment_proof_sms`
  - [x] 2.8 Implement OTP compose function: `compose_otp_sms`

- [x] 3. `SMS_Service` core delivery (`notifications.py`)
  - [x] 3.1 Implement `send_sms(phone, message, recipient_type, recipient_id)` — prefixes with `AUTORIDE:`, applies `truncate_message()`, posts to Semaphore API using `SEMAPHORE_API_KEY` and `SEMAPHORE_SENDER_NAME` from config
  - [x] 3.2 Add retry logic to `send_sms()` — on non-2xx response or network exception, log `status='retried'` to `sms_logs`, wait 2 seconds, retry exactly once
  - [x] 3.3 Add `sms_logs` insertion to `send_sms()` — log `status='sent'` with response code on success; log `status='failed'` with response code and error message after all retries exhausted
  - [x] 3.4 Implement `notify_customer(user_id, message, is_transactional=True)` — queries `users` for `phone_number` and `sms_opt_out`; skips send if `sms_opt_out=True` and `is_transactional=False`; calls `send_sms()` with `recipient_type='customer'`
  - [x] 3.5 Implement `notify_admins(message)` — queries `admins` for all rows where `is_active=True` and `phone IS NOT NULL`; calls `send_sms()` for each with `recipient_type='admin'`
  - [x] 3.6 Implement `notify_phone(phone, message, recipient_type, recipient_id)` — delegates directly to `send_sms()` without DB lookup (used for OTP)

- [x] 4. Update existing notification call sites
  - [x] 4.1 Update `POST /book` (`booking_routes.py`) — replace `send_notification()` with `notify_customer()` using `compose_booking_created_sms()` (requires JOIN to `vehicles` for brand/model); add `notify_admins()` call with `compose_admin_new_booking_sms()`
  - [x] 4.2 Update `POST /bookings/<id>/cancel` (`booking_routes.py`) — replace with `notify_customer()` using `compose_customer_cancel_sms()` including cancellation reason
  - [x] 4.3 Update `PUT /bookings/<id>/approve` (`app.py`) — replace with `notify_customer()` using `compose_booking_approved_sms()` (requires JOIN to `vehicles`)
  - [x] 4.4 Update `PUT /bookings/<id>/reject` (`app.py`) — replace with `notify_customer()` using `compose_booking_rejected_sms()`
  - [x] 4.5 Update `PUT /bookings/<id>/cancel` admin route (`app.py`) — replace with `notify_customer()` using `compose_admin_cancel_sms()` including cancellation reason from request body
  - [x] 4.6 Update `PUT /bookings/<id>/pickup` (`app.py`) — replace with `notify_customer()` using `compose_pickup_sms()` (requires JOIN to `vehicles` for brand/model and `end_date`)
  - [x] 4.7 Update `PUT /bookings/<id>/complete` (`app.py`) — replace with `notify_customer()` using `compose_completed_sms()`
  - [x] 4.8 Update `PUT /drivers/<id>/approve` (`app.py`) — replace with `notify_customer()` using `compose_driver_approved_sms()` (requires driver name lookup)
  - [x] 4.9 Update `PUT /drivers/<id>/reject` (`app.py`) — replace with `notify_customer()` using `compose_driver_rejected_sms()` including rejection reason
  - [x] 4.10 Update `POST /admin/verify-action` (`app.py`) — add `notify_customer()` call: use `compose_license_approved_sms()` when `status=2`, `compose_license_rejected_sms()` when `status=0`
  - [x] 4.11 Update `POST /cancel-booking` legacy route (`app.py`) — replace with `notify_customer()` using `compose_customer_cancel_sms()` including reason

- [x] 5. Add new SMS calls to routes that currently have none
  - [x] 5.1 Add to `POST /payment` (`payment_routes.py`) — after commit, call `notify_customer()` with `compose_full_payment_sms()` if `payment_type='Full'` or `compose_downpayment_sms()` if `payment_type='Downpayment'`; requires fetching `user_id`, `payment_type`, `amount`, `method`, `reference_number`, `balance_amount` from DB
  - [x] 5.2 Add to `POST /bookings/<id>/pay-balance` (`payment_routes.py`) — after commit, call `notify_customer()` with `compose_balance_payment_sms()`; requires fetching `user_id`, `amount`, `reference_number`
  - [x] 5.3 Add to `POST /admin/bookings/<id>/mark-paid` (`booking_routes.py`) — after commit, call `notify_customer()` with `compose_cash_paid_sms()`; requires fetching `user_id` and `total_price`
  - [x] 5.4 Add to `POST /legacy-payment` (`app.py`) — after commit, call `notify_customer()` with appropriate payment template; also call `notify_admins()` with `compose_admin_payment_proof_sms()` including booking ID, customer name, and amount
  - [x] 5.5 Add to `POST /modify-booking` (`app.py`) — after commit, call `notify_customer()` with `compose_modify_booking_sms()`; requires fetching `user_id`, new dates, and new total price
  - [x] 5.6 Add to `POST /split-bill/request` (`app.py`) — after commit, look up partner user by `partner_email`, call `notify_customer()` with `compose_split_request_sms()` including initiator name and amount
  - [x] 5.7 Add to `POST /split-bill/pay` (`app.py`) — after commit, look up booking initiator `user_id` via `split_payments ? bookings`, call `notify_customer()` with `compose_split_paid_sms()` including amount
  - [x] 5.8 Add admin new-driver-application alert — identify the driver application submission route in `app.py` and add `notify_admins()` call with `compose_admin_driver_application_sms()` after successful insert

- [x] 6. New API endpoints
  - [x] 6.1 Implement `POST /user/sms-preference` in `app.py` — accepts `user_id` and `sms_opt_out` (boolean), updates `users.sms_opt_out`, returns `200` with `{ "user_id": ..., "sms_opt_out": ... }`; returns `400` on missing params, `404` on user not found
  - [x] 6.2 Implement `GET /admin/sms-logs` in `app.py` — queries `sms_logs` ordered by `created_at DESC`; supports `page` (default 1), `per_page` (default 50), and optional `recipient_type` filter; returns `{ "logs": [...], "page": ..., "per_page": ..., "total": ... }`

- [x] 7. OTP integration
  - [x] 7.1 Locate the existing OTP send logic in `app.py` and replace the direct Semaphore call with `notify_phone()` using `compose_otp_sms()`
  - [x] 7.2 Ensure the OTP route returns an error response to the caller if `notify_phone()` returns `False`

- [x] 8. Property-based tests
  - [x] 8.1 Set up Hypothesis as a test dependency; create `AutorideSystem/backend/tests/test_sms_properties.py`
  - [x] 8.2 Write property test for Property 1: `truncate_message()` length invariant — generate strings of random length, verify output ? 320 chars, verify `...` suffix when truncated, verify unchanged when within limit
    - `# Feature: sms-notification, Property 1: truncate_message preserves length invariant`
  - [x] 8.3 Write property test for Property 2: booking lifecycle compose functions — generate random booking data (id, brand, model, dates, price), verify all required fields appear in output for each compose function
    - `# Feature: sms-notification, Property 2: booking lifecycle messages contain required fields`
  - [x] 8.4 Write property test for Property 3: cancellation compose functions — generate random booking IDs and reason strings, verify both appear in output
    - `# Feature: sms-notification, Property 3: cancellation messages preserve the cancellation reason`
  - [x] 8.5 Write property test for Property 4: payment compose functions — generate random amounts, methods, and reference numbers, verify all fields appear in output
    - `# Feature: sms-notification, Property 4: payment messages contain required financial fields`
  - [x] 8.6 Write property test for Property 5: split payment compose functions — generate random names and amounts, verify fields appear in output
    - `# Feature: sms-notification, Property 5: split payment messages contain required fields`
  - [x] 8.7 Write property test for Property 6: driver application compose functions — generate random names and rejection reasons, verify they appear in output
    - `# Feature: sms-notification, Property 6: driver application messages preserve variable fields`
  - [x] 8.8 Write property test for Property 7: admin alert compose functions — generate random booking/customer data, verify all required fields appear
    - `# Feature: sms-notification, Property 7: admin alert messages contain required fields`
  - [x] 8.9 Write property test for Property 8: OTP compose function — generate random 6-digit codes, verify code and expiry notice appear in output
    - `# Feature: sms-notification, Property 8: OTP messages contain the OTP code`
  - [x] 8.10 Write property test for Property 9: opt-out logic — mock `send_sms()`, generate users with `sms_opt_out=True`, verify zero calls for promotional and exactly one call for transactional
    - `# Feature: sms-notification, Property 9: opt-out blocks promotional SMS but not transactional SMS`
  - [x] 8.11 Write property test for Property 10: SMS preference round-trip — generate random boolean values, POST to `/user/sms-preference`, verify response body matches input and DB reflects the value
    - `# Feature: sms-notification, Property 10: SMS preference endpoint round-trip`
  - [x] 8.12 Write property test for Property 11: every SMS send produces exactly one log entry — mock Semaphore API, call `send_sms()` N times, verify `sms_logs` count increases by exactly N
    - `# Feature: sms-notification, Property 11: every SMS send produces exactly one log entry`
  - [x] 8.13 Write property test for Property 12: pagination ordering — insert N log entries with known timestamps, call `GET /admin/sms-logs` with varying page/per_page, verify ordering and correct slice
    - `# Feature: sms-notification, Property 12: SMS log pagination returns correct ordered slices`
  - [x] 8.14 Write property test for Property 13: log filtering — insert logs with mixed recipient types, call `GET /admin/sms-logs?recipient_type=X`, verify all returned records match type X
    - `# Feature: sms-notification, Property 13: SMS log filtering returns only matching recipient types`
  - [x] 8.15 Write property test for Property 14: notify_admins fan-out — generate lists of admins with random active/inactive status and phone presence, mock `send_sms()`, verify it is called only for active admins with phones
    - `# Feature: sms-notification, Property 14: notify_admins only sends to active admins`

- [x] 9. Unit tests (example-based)
  - [x] 9.1 Test `compose_booking_rejected_sms()` contains booking ID and support contact text
  - [x] 9.2 Test `compose_completed_sms()` contains booking ID and thank-you text
  - [x] 9.3 Test `compose_license_approved_sms()` contains "verified" and "book vehicles"
  - [x] 9.4 Test `compose_license_rejected_sms()` contains "not approved" and "re-upload"
  - [x] 9.5 Test `send_sms()` with mocked Semaphore returning 200 — logs `status='sent'`, returns `True`, API called once
  - [x] 9.6 Test `send_sms()` with mocked Semaphore always returning 500 — logs `status='failed'`, API called exactly twice
  - [x] 9.7 Test `send_sms()` with mocked Semaphore failing then succeeding — logs `status='retried'` then `status='sent'`, API called exactly twice
  - [x] 9.8 Test `POST /user/sms-preference` with valid data — 200 response, DB updated
  - [x] 9.9 Test `POST /user/sms-preference` with missing fields — 400 response
  - [x] 9.10 Test `GET /admin/sms-logs` with no filters — returns records ordered by `created_at DESC`
