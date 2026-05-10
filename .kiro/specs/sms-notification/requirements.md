# Requirements Document

## Introduction

The AutorideSystem SMS Notification feature expands and formalizes the existing SMS delivery infrastructure built on the Semaphore API. The system currently sends SMS notifications for a subset of booking and driver lifecycle events via the `send_notification()` function in `notifications.py`. This feature closes the coverage gaps, improves message content to include vehicle details, dates, amounts, and reference numbers, adds SMS opt-out preferences for promotional messages, introduces admin SMS alerts for operational events, adds automatic retry on failure, and logs all SMS delivery attempts to the database for auditability.

The backend is a Flask application backed by Supabase PostgreSQL. SMS is delivered via the Semaphore API. Email delivery continues to run alongside SMS and is out of scope for this feature.

---

## Glossary

- **SMS_Service**: The backend component responsible for composing and dispatching SMS messages via the Semaphore API.
- **Notification_Log**: A database table (`sms_logs`) that records every SMS delivery attempt, its outcome, and metadata.
- **Transactional_SMS**: An SMS triggered by a user action or system event that directly affects the recipient's account or booking (e.g., booking confirmed, payment received). These are always sent regardless of opt-out preference.
- **Promotional_SMS**: An SMS that is marketing or informational in nature and not tied to a specific user action (reserved for future use; opt-out applies).
- **SMS_Preference**: A per-user flag (`sms_opt_out`) stored in the `users` table. When `true`, the user will not receive Promotional_SMS but will still receive Transactional_SMS.
- **Customer**: A registered end-user of the AutorideSystem who rents vehicles.
- **Driver**: A registered professional driver in the `drivers` table.
- **Admin**: An administrator of the AutorideSystem who manages bookings, vehicles, and driver applications. Admin phone numbers are stored in the `admins` table.
- **Booking**: A reservation record in the `bookings` table.
- **Split_Payment**: A cost-sharing arrangement tracked in the `split_payments` table where a partner Customer shares the cost of a Booking.
- **Semaphore_API**: The third-party SMS gateway at `https://api.semaphore.co/api/v4/messages` used to deliver SMS messages.
- **OTP**: A 6-digit one-time password sent via SMS for phone-based login authentication.

---

## Requirements

### Requirement 1: Transactional SMS for Booking Lifecycle Events

**User Story:** As a customer, I want to receive an SMS at every significant stage of my booking, so that I am always informed about my rental status without needing to open the app.

#### Acceptance Criteria

1. WHEN a booking is created, THE SMS_Service SHALL send the Customer an SMS containing the booking ID, vehicle brand and model, rental start date, rental end date, and total price.
2. WHEN a booking status changes to `Approved`, THE SMS_Service SHALL send the Customer an SMS containing the booking ID, vehicle brand and model, rental start date, and a prompt to proceed with pickup.
3. WHEN a booking status changes to `Rejected`, THE SMS_Service SHALL send the Customer an SMS containing the booking ID and a message directing them to contact support.
4. WHEN a booking is cancelled by the Customer, THE SMS_Service SHALL send the Customer an SMS containing the booking ID and the cancellation reason.
5. WHEN a booking is cancelled by an Admin, THE SMS_Service SHALL send the Customer an SMS containing the booking ID, the cancellation reason, and a note that a refund will be initiated if applicable.
6. WHEN a booking status changes to `Picked Up`, THE SMS_Service SHALL send the Customer an SMS containing the booking ID, vehicle brand and model, and the rental end date.
7. WHEN a booking status changes to `Completed`, THE SMS_Service SHALL send the Customer an SMS containing the booking ID and a thank-you message.
8. WHEN a booking's dates are modified, THE SMS_Service SHALL send the Customer an SMS containing the booking ID, the new start date, the new end date, and the recalculated total price.

---

### Requirement 2: Transactional SMS for Payment Events

**User Story:** As a customer, I want to receive an SMS confirmation whenever a payment is processed on my booking, so that I have a record of every transaction.

#### Acceptance Criteria

1. WHEN a full payment is successfully processed for a booking, THE SMS_Service SHALL send the Customer an SMS containing the booking ID, the amount paid, the payment method, and the reference number.
2. WHEN a downpayment is successfully processed for a booking, THE SMS_Service SHALL send the Customer an SMS containing the booking ID, the downpayment amount paid, the remaining balance amount, and the reference number.
3. WHEN a balance payment is successfully processed for a booking, THE SMS_Service SHALL send the Customer an SMS containing the booking ID, the balance amount paid, and the reference number confirming the booking is now fully paid.
4. WHEN an admin manually marks a booking as fully paid (over-the-counter cash), THE SMS_Service SHALL send the Customer an SMS containing the booking ID and the total amount marked as paid.

---

### Requirement 3: Transactional SMS for Split Payment Events

**User Story:** As a customer involved in a split payment, I want to receive SMS notifications about the split request and its payment status, so that both parties are kept informed.

#### Acceptance Criteria

1. WHEN a split bill request is created, THE SMS_Service SHALL send the partner Customer an SMS containing the booking ID, the initiating Customer's name, and the amount they owe.
2. WHEN a partner Customer pays their split bill, THE SMS_Service SHALL send the booking initiator an SMS containing the booking ID and the amount paid by the partner.

---

### Requirement 4: Transactional SMS for License Verification Events

**User Story:** As a customer, I want to receive an SMS when my driver's license verification status changes, so that I know when I can start booking vehicles.

#### Acceptance Criteria

1. WHEN an admin approves a Customer's driver's license, THE SMS_Service SHALL send the Customer an SMS stating that their license has been verified and they can now book vehicles.
2. WHEN an admin rejects a Customer's driver's license, THE SMS_Service SHALL send the Customer an SMS stating that their license was not approved and prompting them to re-upload a valid document.

---

### Requirement 5: Transactional SMS for Driver Application Events

**User Story:** As a driver applicant, I want to receive an SMS when my application is reviewed, so that I know the outcome without checking the portal.

#### Acceptance Criteria

1. WHEN an admin approves a driver application, THE SMS_Service SHALL send the Driver an SMS containing their name and a message confirming their application has been approved.
2. WHEN an admin rejects a driver application, THE SMS_Service SHALL send the Driver an SMS containing the rejection reason and a message that they may re-apply once the issues are resolved.

---

### Requirement 6: Admin SMS Alerts for Operational Events

**User Story:** As an admin, I want to receive an SMS when key operational events occur, so that I can respond promptly without being logged into the admin panel.

#### Acceptance Criteria

1. WHEN a new booking is created, THE SMS_Service SHALL send an SMS to all active admins containing the booking ID, the Customer's name, the vehicle brand and model, and the rental dates.
2. WHEN a new driver application is submitted, THE SMS_Service SHALL send an SMS to all active admins containing the applicant's name and a prompt to review the application.
3. WHEN a legacy payment proof is uploaded by a Customer, THE SMS_Service SHALL send an SMS to all active admins containing the booking ID, the Customer's name, and the payment amount.
4. THE SMS_Service SHALL retrieve admin phone numbers from the `admins` table and SHALL only send to admins whose accounts are active.

---

### Requirement 7: SMS OTP for Phone-Based Login

**User Story:** As a customer, I want to receive a one-time password via SMS when I request phone-based login, so that I can authenticate securely.

#### Acceptance Criteria

1. WHEN a Customer requests an OTP for phone-based login, THE SMS_Service SHALL send an SMS to the Customer's registered phone number containing the 6-digit OTP and an expiry notice.
2. THE SMS_Service SHALL send the OTP SMS through the same Semaphore API used for all other SMS notifications.
3. IF the OTP SMS delivery fails, THEN THE SMS_Service SHALL log the failure to the Notification_Log and return an error response to the caller.

---

### Requirement 8: SMS Opt-Out Preference for Promotional Messages

**User Story:** As a customer, I want to opt out of promotional SMS messages, so that I only receive messages that are directly relevant to my bookings and account.

#### Acceptance Criteria

1. THE Backend SHALL store an `sms_opt_out` boolean flag on the `users` table, defaulting to `false`.
2. WHEN a Customer sets `sms_opt_out` to `true`, THE SMS_Service SHALL not send Promotional_SMS to that Customer.
3. WHILE a Customer's `sms_opt_out` is `true`, THE SMS_Service SHALL still send all Transactional_SMS to that Customer.
4. THE Backend SHALL expose a `POST /user/sms-preference` endpoint accepting `user_id` and `sms_opt_out` (boolean) that updates the Customer's preference and returns a `200` response on success.
5. WHEN a Customer updates their SMS preference, THE Backend SHALL return the updated `sms_opt_out` value in the response body.

---

### Requirement 9: SMS Delivery Retry on Failure

**User Story:** As a system operator, I want the SMS service to automatically retry a failed send once, so that transient Semaphore API errors do not silently drop notifications.

#### Acceptance Criteria

1. WHEN a Semaphore API call returns a non-2xx HTTP status code or raises a network exception, THE SMS_Service SHALL wait 2 seconds and retry the request exactly once.
2. IF the retry also fails, THEN THE SMS_Service SHALL log the failure to the Notification_Log with `status = 'failed'` and SHALL NOT retry again.
3. IF the initial attempt succeeds, THE SMS_Service SHALL NOT perform a retry.
4. THE SMS_Service SHALL log the retry attempt to the Notification_Log with `status = 'retried'` before executing the retry.

---

### Requirement 10: SMS Delivery Logging

**User Story:** As an admin, I want every SMS delivery attempt recorded in the database, so that I can audit notification history and diagnose delivery failures.

#### Acceptance Criteria

1. THE Backend SHALL maintain an `sms_logs` table with columns: `id` (primary key), `recipient_phone` (text), `recipient_type` (text: `customer`, `driver`, or `admin`), `recipient_id` (integer, nullable), `message_body` (text), `status` (text: `sent`, `failed`, or `retried`), `semaphore_response_code` (integer, nullable), `error_message` (text, nullable), and `created_at` (timestamp with time zone, default now()).
2. WHEN the SMS_Service sends an SMS, THE SMS_Service SHALL insert a record into `sms_logs` with the outcome of the delivery attempt.
3. WHEN an SMS send succeeds, THE SMS_Service SHALL record `status = 'sent'` and the HTTP response code from the Semaphore API.
4. WHEN an SMS send fails after all retry attempts, THE SMS_Service SHALL record `status = 'failed'`, the HTTP response code (if available), and the error message.
5. THE Backend SHALL expose a `GET /admin/sms-logs` endpoint that returns paginated records from `sms_logs`, ordered by `created_at` descending, accepting optional query parameters `page` (default 1) and `per_page` (default 50).
6. IF a `recipient_type` query parameter is provided to `GET /admin/sms-logs`, THEN THE Backend SHALL filter results to only records matching that recipient type.

---

### Requirement 11: SMS Message Content Standards

**User Story:** As a customer or driver, I want SMS messages to include all relevant details (vehicle, dates, amounts, reference numbers), so that I have the information I need without opening the app.

#### Acceptance Criteria

1. THE SMS_Service SHALL prefix all outgoing SMS messages with `AUTORIDE:` to identify the sender.
2. WHEN composing a booking-related SMS, THE SMS_Service SHALL include the booking ID, vehicle brand and model, and rental dates where applicable.
3. WHEN composing a payment-related SMS, THE SMS_Service SHALL include the booking ID, the amount, and the reference number where applicable.
4. THE SMS_Service SHALL truncate any single SMS message that exceeds 320 characters (2 SMS segments) to 317 characters and append `...` to prevent excessive per-message costs.
5. THE SMS_Service SHALL use the `SEMAPHORE_SENDER_NAME` value from the application configuration as the sender name for all outgoing messages.

