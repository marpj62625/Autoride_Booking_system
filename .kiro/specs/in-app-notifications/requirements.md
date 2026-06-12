# Requirements Document

## Introduction

The AutorideSystem In-App Notification feature adds a persistent, database-backed notification system for both customers (Capacitor mobile app) and admins (admin web app). Notifications are stored in a `notifications` table in Supabase PostgreSQL and delivered in real-time via Supabase Realtime subscriptions. This feature runs alongside the existing Semaphore SMS system — it does not replace it.

The customer mobile app already has a `NotifStore` (local Capacitor Preferences/localStorage), a notification bell icon with badge in the home screen, and a `page-notifications` overlay. This feature replaces the local-only store with server-backed notifications while preserving the existing UI shell.

The admin web app already uses the Supabase JS client (`supabaseClient`) and subscribes to realtime changes on several tables. This feature extends that subscription to include admin notifications.

---

## Glossary

- **Notification**: A record in the `notifications` table representing a message delivered to a Customer or Admin about a system event.
- **Notification_Service**: The backend component (Python, in `notifications.py`) responsible for inserting notification rows into the `notifications` table alongside existing SMS delivery.
- **Customer**: A registered end-user of the AutorideSystem mobile app (`users` table).
- **Admin**: An administrator of the AutorideSystem (`admins` table) who uses the admin web app.
- **Supabase_Realtime**: The Supabase WebSocket-based change-data-capture service used to push `INSERT` events on the `notifications` table to connected clients.
- **NotifStore**: The existing local notification store in the customer mobile app (`app.js`) backed by Capacitor Preferences or localStorage. It will be superseded by server-backed notifications but its `updateNotifBadge()` integration point is preserved.
- **Unread_Count**: The number of notifications for a recipient where `is_read = false`.
- **Notification_Badge**: The red circular counter displayed on the bell icon in the customer mobile app home screen and the admin web app header, showing the Unread_Count.
- **Notification_Type**: A string label categorising the event that triggered the notification (e.g., `booking_created`, `payment_confirmed`, `license_approved`).
- **Backend**: The Flask REST API (`app.py`) backed by Supabase PostgreSQL, hosted on Vercel.
- **API_BASE**: `https://autoride-booking-system.vercel.app/api` — the base URL used by the customer mobile app for all backend calls.

---

## Requirements

### Requirement 1: Notifications Database Table

**User Story:** As a system operator, I want all notifications stored in the database, so that they persist across sessions and can be retrieved by any client.

#### Acceptance Criteria

1. THE Backend SHALL maintain a `notifications` table with columns: `id` (bigint, primary key, auto-increment), `user_id` (integer, nullable, foreign key ? `users.id`), `admin_id` (integer, nullable, foreign key ? `admins.id`), `title` (text, not null), `message` (text, not null), `type` (text, not null), `is_read` (boolean, not null, default `false`), `created_at` (timestamp with time zone, not null, default `now()`).
2. THE `notifications` table SHALL enforce that exactly one of `user_id` or `admin_id` is non-null per row (a notification targets either a Customer or an Admin, not both).
3. THE Backend SHALL enable Supabase Realtime replication on the `notifications` table so that `INSERT` events are broadcast to subscribed clients.

---

### Requirement 2: Backend Notification Insertion on Customer Events

**User Story:** As a customer, I want an in-app notification created for every significant event on my account, so that I have a persistent record of all activity.

#### Acceptance Criteria

1. WHEN a booking is created, THE Notification_Service SHALL insert a notification for the Customer with `type = 'booking_created'`, a title of `"Booking Received"`, and a message containing the booking ID, vehicle brand and model, rental start date, rental end date, and total price.
2. WHEN a booking status changes to `Approved`, THE Notification_Service SHALL insert a notification for the Customer with `type = 'booking_approved'`, a title of `"Booking Approved"`, and a message containing the booking ID, vehicle brand and model, and rental start date.
3. WHEN a booking status changes to `Rejected`, THE Notification_Service SHALL insert a notification for the Customer with `type = 'booking_rejected'`, a title of `"Booking Rejected"`, and a message containing the booking ID and a prompt to contact support.
4. WHEN a booking is cancelled by the Customer, THE Notification_Service SHALL insert a notification for the Customer with `type = 'booking_cancelled'` and a message containing the booking ID and the cancellation reason.
5. WHEN a booking is cancelled by an Admin, THE Notification_Service SHALL insert a notification for the Customer with `type = 'booking_cancelled_by_admin'` and a message containing the booking ID, the cancellation reason, and a note that a refund will be initiated if applicable.
6. WHEN a booking status changes to `Picked Up`, THE Notification_Service SHALL insert a notification for the Customer with `type = 'booking_picked_up'` and a message containing the booking ID, vehicle brand and model, and rental end date.
7. WHEN a booking status changes to `Completed`, THE Notification_Service SHALL insert a notification for the Customer with `type = 'booking_completed'` and a message containing the booking ID and a thank-you message.
8. WHEN a booking's dates are modified, THE Notification_Service SHALL insert a notification for the Customer with `type = 'booking_modified'` and a message containing the booking ID, the new start date, the new end date, and the recalculated total price.

---

### Requirement 3: Backend Notification Insertion on Payment Events

**User Story:** As a customer, I want an in-app notification for every payment event on my booking, so that I have a persistent record of all transactions.

#### Acceptance Criteria

1. WHEN a full payment is confirmed, THE Notification_Service SHALL insert a notification for the Customer with `type = 'payment_confirmed'` and a message containing the booking ID, the amount paid, the payment method, and the reference number.
2. WHEN a downpayment is confirmed, THE Notification_Service SHALL insert a notification for the Customer with `type = 'payment_downpayment'` and a message containing the booking ID, the downpayment amount, the remaining balance, and the reference number.
3. WHEN a balance payment is confirmed, THE Notification_Service SHALL insert a notification for the Customer with `type = 'payment_balance'` and a message containing the booking ID, the balance amount paid, and the reference number.
4. WHEN an admin marks a booking as cash-paid, THE Notification_Service SHALL insert a notification for the Customer with `type = 'payment_cash'` and a message containing the booking ID and the total amount marked as paid.
5. WHEN a split payment request is created, THE Notification_Service SHALL insert a notification for the partner Customer with `type = 'split_request'` and a message containing the booking ID, the initiating Customer's name, and the amount owed.
6. WHEN a split payment partner pays their share, THE Notification_Service SHALL insert a notification for the booking initiator with `type = 'split_paid'` and a message containing the booking ID and the amount paid by the partner.

---

### Requirement 4: Backend Notification Insertion on License and Driver Events

**User Story:** As a customer or driver applicant, I want an in-app notification when my license or driver application is reviewed, so that I know the outcome immediately.

#### Acceptance Criteria

1. WHEN an admin approves a Customer's driver's license, THE Notification_Service SHALL insert a notification for the Customer with `type = 'license_approved'`, a title of `"License Approved"`, and a message stating that their license has been verified and they can now book vehicles.
2. WHEN an admin rejects a Customer's driver's license, THE Notification_Service SHALL insert a notification for the Customer with `type = 'license_rejected'`, a title of `"License Rejected"`, and a message stating that their license was not approved and prompting them to re-upload a valid document.
3. WHEN an admin approves a driver application, THE Notification_Service SHALL insert a notification for the Driver's associated user account with `type = 'driver_approved'` and a message containing the driver's name and a confirmation that their application has been approved.
4. WHEN an admin rejects a driver application, THE Notification_Service SHALL insert a notification for the Driver's associated user account with `type = 'driver_rejected'` and a message containing the rejection reason.

---

### Requirement 5: Backend Notification Insertion on Admin Events

**User Story:** As an admin, I want an in-app notification for key operational events, so that I can respond promptly from the admin web app without relying solely on SMS.

#### Acceptance Criteria

1. WHEN a new booking is created, THE Notification_Service SHALL insert a notification row for each active Admin with `type = 'admin_new_booking'`, a title of `"New Booking"`, and a message containing the booking ID, the Customer's name, the vehicle brand and model, and the rental dates.
2. WHEN a new driver application is submitted, THE Notification_Service SHALL insert a notification row for each active Admin with `type = 'admin_driver_application'`, a title of `"New Driver Application"`, and a message containing the applicant's name.
3. WHEN a Customer uploads a payment proof, THE Notification_Service SHALL insert a notification row for each active Admin with `type = 'admin_payment_proof'`, a title of `"Payment Proof Uploaded"`, and a message containing the booking ID, the Customer's name, and the payment amount.
4. THE Notification_Service SHALL retrieve active admin IDs from the `admins` table and SHALL only insert notifications for admins whose accounts are active (`is_active = true`).

---

### Requirement 6: Customer Notification API Endpoints

**User Story:** As a customer, I want API endpoints to fetch my notifications and mark them as read, so that the mobile app can display an accurate notification history and badge count.

#### Acceptance Criteria

1. THE Backend SHALL expose a `GET /notifications` endpoint that accepts a `user_id` query parameter and returns all notifications for that Customer ordered by `created_at` descending, as a JSON array with fields: `id`, `title`, `message`, `type`, `is_read`, `created_at`.
2. THE Backend SHALL expose a `POST /notifications/<id>/read` endpoint that sets `is_read = true` for the notification with the given `id` and returns a `200` response with the updated notification.
3. THE Backend SHALL expose a `POST /notifications/read-all` endpoint that accepts a `user_id` in the request body and sets `is_read = true` for all notifications belonging to that Customer, returning a `200` response.
4. IF a `GET /notifications` request is made without a `user_id` parameter, THEN THE Backend SHALL return a `400` response with an error message.
5. IF `POST /notifications/<id>/read` is called with a non-existent notification `id`, THEN THE Backend SHALL return a `404` response.

---

### Requirement 7: Admin Notification API Endpoints

**User Story:** As an admin, I want API endpoints to fetch my notifications and mark them as read, so that the admin web app can display an accurate notification panel and badge count.

#### Acceptance Criteria

1. THE Backend SHALL expose a `GET /admin/notifications` endpoint that accepts an `admin_id` query parameter and returns all notifications for that Admin ordered by `created_at` descending, as a JSON array with fields: `id`, `title`, `message`, `type`, `is_read`, `created_at`.
2. THE Backend SHALL expose a `POST /admin/notifications/<id>/read` endpoint that sets `is_read = true` for the notification with the given `id` and returns a `200` response with the updated notification.
3. THE Backend SHALL expose a `POST /admin/notifications/read-all` endpoint that accepts an `admin_id` in the request body and sets `is_read = true` for all notifications belonging to that Admin, returning a `200` response.
4. IF a `GET /admin/notifications` request is made without an `admin_id` parameter, THEN THE Backend SHALL return a `400` response with an error message.
5. IF `POST /admin/notifications/<id>/read` is called with a non-existent notification `id`, THEN THE Backend SHALL return a `404` response.

---

### Requirement 8: Customer Mobile App — Realtime Subscription

**User Story:** As a customer, I want new notifications to appear instantly in the app without refreshing, so that I am informed of events as they happen.

#### Acceptance Criteria

1. WHEN a Customer logs in, THE App SHALL subscribe to Supabase_Realtime on the `notifications` table filtered by `user_id = <current user id>` for `INSERT` events.
2. WHEN a new notification `INSERT` event is received via Supabase_Realtime, THE App SHALL prepend the notification to the in-memory notification list and call `updateNotifBadge()` to refresh the badge count.
3. WHEN a Customer logs out, THE App SHALL unsubscribe from the Supabase_Realtime channel to prevent memory leaks and stale subscriptions.
4. IF the Supabase_Realtime connection is unavailable, THE App SHALL fall back to displaying notifications fetched from `GET /notifications` on page load without blocking the user interface.

---

### Requirement 9: Customer Mobile App — Notifications Page

**User Story:** As a customer, I want to view my full notification history with read/unread state, so that I can review past alerts at any time.

#### Acceptance Criteria

1. WHEN the Customer opens the notifications page (`page-notifications`), THE App SHALL call `GET /notifications?user_id={id}` and render the returned notifications in the `notificationsContent` element, ordered newest first.
2. WHEN the notifications page is opened, THE App SHALL call `POST /notifications/read-all` with the current `user_id` to mark all notifications as read, then call `updateNotifBadge()` to reset the badge.
3. THE App SHALL render each notification as a card showing the `title`, `message`, and a human-readable `created_at` timestamp.
4. THE App SHALL visually distinguish unread notifications (e.g., with a highlighted left border or background tint) from read notifications.
5. IF the notification list is empty, THE App SHALL display the message "No notifications yet" with a bell-slash icon.
6. THE App SHALL display a loading state while the `GET /notifications` request is in flight.

---

### Requirement 10: Customer Mobile App — Notification Badge

**User Story:** As a customer, I want the notification bell badge to always reflect my current unread count, so that I know at a glance whether I have new alerts.

#### Acceptance Criteria

1. WHEN the App initialises after login, THE App SHALL call `GET /notifications?user_id={id}` and compute the Unread_Count from the returned list, then display it on the `notifBadge` element.
2. WHEN the Unread_Count is zero, THE App SHALL hide the `notifBadge` element.
3. WHEN the Unread_Count is greater than zero, THE App SHALL show the `notifBadge` element with the count value.
4. WHEN a new notification arrives via Supabase_Realtime, THE App SHALL increment the displayed Unread_Count by one without re-fetching the full list.
5. WHEN the Customer opens the notifications page and `POST /notifications/read-all` succeeds, THE App SHALL set the Unread_Count to zero and hide the `notifBadge`.

---

### Requirement 11: Admin Web App — Realtime Notification Panel

**User Story:** As an admin, I want to see new notifications appear in real-time in the admin web app, so that I can act on operational events immediately.

#### Acceptance Criteria

1. WHEN an Admin is logged in, THE Admin_App SHALL extend the existing `supabaseClient` `admin-realtime` channel subscription to also listen for `INSERT` events on the `notifications` table filtered by `admin_id = <current admin id>`.
2. WHEN a new admin notification `INSERT` event is received via Supabase_Realtime, THE Admin_App SHALL prepend the notification to the admin notification list and increment the admin Notification_Badge count.
3. THE Admin_App SHALL display a Notification_Badge on the admin header showing the current Unread_Count for the logged-in Admin.
4. WHEN an Admin clicks the Notification_Badge or notification bell, THE Admin_App SHALL open a notification panel listing all admin notifications ordered newest first, showing `title`, `message`, and `created_at`.
5. WHEN the Admin opens the notification panel, THE Admin_App SHALL call `POST /admin/notifications/read-all` with the current `admin_id` and reset the Notification_Badge to zero.
6. IF no notifications exist for the Admin, THE Admin_App SHALL display the message "No notifications yet" in the notification panel.

---

### Requirement 12: Coexistence with SMS Notifications

**User Story:** As a system operator, I want in-app notifications to be inserted alongside existing SMS sends, so that both channels deliver independently without one blocking the other.

#### Acceptance Criteria

1. WHEN the Notification_Service inserts a notification row, THE Backend SHALL continue to call the existing `SMS_Service` methods for the same event without modification.
2. IF inserting a notification row fails, THEN THE Backend SHALL log the error and SHALL NOT prevent the SMS send from proceeding.
3. IF the SMS send fails, THE Backend SHALL NOT prevent the notification row from being inserted.
4. THE Notification_Service SHALL insert notification rows within the same request handler that triggers the SMS, so that both channels are invoked synchronously before the HTTP response is returned.

---

### Requirement 13: Notification Data Integrity and Security

**User Story:** As a system operator, I want notification data to be accurate and access-controlled, so that customers cannot read each other's notifications and admins cannot read customer notifications.

#### Acceptance Criteria

1. THE `GET /notifications` endpoint SHALL only return notifications where `user_id` matches the `user_id` query parameter; it SHALL NOT return notifications belonging to other users or to admins.
2. THE `GET /admin/notifications` endpoint SHALL only return notifications where `admin_id` matches the `admin_id` query parameter; it SHALL NOT return notifications belonging to customers or other admins.
3. THE `POST /notifications/<id>/read` endpoint SHALL verify that the notification's `user_id` matches the `user_id` provided in the request body before updating; IF there is a mismatch, THE Backend SHALL return a `403` response.
4. THE `POST /admin/notifications/<id>/read` endpoint SHALL verify that the notification's `admin_id` matches the `admin_id` provided in the request body before updating; IF there is a mismatch, THE Backend SHALL return a `403` response.
5. THE Backend SHALL validate that `user_id` and `admin_id` values in all notification API requests are integers; IF a non-integer value is provided, THE Backend SHALL return a `400` response.
