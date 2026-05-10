# Tasks Document: In-App Notifications

## Task List

- [x] 1. Database migration
  - [x] 1.1 Implement `migrate_notifications()` in `app.py` — creates `notifications` table with `id`, `user_id`, `admin_id`, `title`, `message`, `type`, `is_read`, `created_at` columns and the `chk_one_recipient` CHECK constraint
  - [x] 1.2 Add indexes `idx_notifications_user_id` on `(user_id, created_at DESC)` and `idx_notifications_admin_id` on `(admin_id, created_at DESC)` inside `migrate_notifications()`
  - [x] 1.3 Call `migrate_notifications()` from the existing `run_migrations()` function in `app.py`

- [x] 2. `Notification_Service` class (`notifications.py`)
  - [x] 2.1 Implement `Notification_Service` class with `notify_user(user_id, title, message, notif_type)` — inserts one row into `notifications` with `user_id` set and `admin_id` NULL; wraps in try/except, logs errors to stderr, returns `True`/`False`
  - [x] 2.2 Implement `notify_admins_inapp(title, message, notif_type)` — queries `admins` for all rows where `is_active = TRUE`, inserts one notification row per admin with `admin_id` set and `user_id` NULL; returns list of booleans
  - [x] 2.3 Export module-level singleton `notification_service = Notification_Service()` at the bottom of `notifications.py`

- [x] 3. Customer notification API endpoints (`app.py`)
  - [x] 3.1 Implement `GET /notifications` — accepts `user_id` query param (integer), returns all notifications for that user ordered by `created_at DESC` as JSON array with fields `id`, `title`, `message`, `type`, `is_read`, `created_at` (ISO string); returns `400` if `user_id` missing or non-integer
  - [x] 3.2 Implement `POST /notifications/read-all` — accepts `{ "user_id": int }` in request body, sets `is_read = true` for all notifications where `user_id` matches, returns `200` with `{ "updated": <count> }`; returns `400` on missing/invalid `user_id`
  - [x] 3.3 Implement `POST /notifications/<int:notif_id>/read` — accepts `{ "user_id": int }` in request body, verifies notification's `user_id` matches, sets `is_read = true`, returns `200` with updated notification; returns `403` on mismatch, `404` if not found

- [x] 4. Admin notification API endpoints (`app.py`)
  - [x] 4.1 Implement `GET /admin/notifications` — accepts `admin_id` query param (integer), returns all notifications for that admin ordered by `created_at DESC`; returns `400` if `admin_id` missing or non-integer
  - [x] 4.2 Implement `POST /admin/notifications/read-all` — accepts `{ "admin_id": int }` in request body, sets `is_read = true` for all notifications where `admin_id` matches, returns `200` with `{ "updated": <count> }`
  - [x] 4.3 Implement `POST /admin/notifications/<int:notif_id>/read` — accepts `{ "admin_id": int }` in request body, verifies notification's `admin_id` matches, sets `is_read = true`, returns `200` with updated notification; returns `403` on mismatch, `404` if not found

- [x] 5. Wire `notification_service` into booking lifecycle routes
  - [x] 5.1 Update `POST /book` (`booking_routes.py`) — add `notification_service.notify_user()` with `type='booking_created'` and `notification_service.notify_admins_inapp()` with `type='admin_new_booking'` alongside existing SMS calls
  - [x] 5.2 Update `POST /bookings/<id>/cancel` (`booking_routes.py`) — add `notification_service.notify_user()` with `type='booking_cancelled'`
  - [x] 5.3 Update `PUT /bookings/<id>/approve` (`app.py`) — add `notification_service.notify_user()` with `type='booking_approved'`
  - [x] 5.4 Update `PUT /bookings/<id>/reject` (`app.py`) — add `notification_service.notify_user()` with `type='booking_rejected'`
  - [x] 5.5 Update `PUT /bookings/<id>/cancel` admin route (`app.py`) — add `notification_service.notify_user()` with `type='booking_cancelled_by_admin'`
  - [x] 5.6 Update `PUT /bookings/<id>/pickup` (`app.py`) — add `notification_service.notify_user()` with `type='booking_picked_up'`
  - [x] 5.7 Update `PUT /bookings/<id>/complete` (`app.py`) — add `notification_service.notify_user()` with `type='booking_completed'`
  - [x] 5.8 Update `POST /modify-booking` (`app.py`) — add `notification_service.notify_user()` with `type='booking_modified'`
  - [x] 5.9 Update `POST /cancel-booking` legacy route (`app.py`) — add `notification_service.notify_user()` with `type='booking_cancelled'`

- [x] 6. Wire `notification_service` into payment and verification routes
  - [x] 6.1 Update `POST /payment` (`payment_routes.py`) — add `notification_service.notify_user()` with `type='payment_confirmed'` or `type='payment_downpayment'` based on `payment_type`
  - [x] 6.2 Update `POST /bookings/<id>/pay-balance` (`payment_routes.py`) — add `notification_service.notify_user()` with `type='payment_balance'`
  - [x] 6.3 Update `POST /admin/bookings/<id>/mark-paid` (`booking_routes.py`) — add `notification_service.notify_user()` with `type='payment_cash'`
  - [x] 6.4 Update `POST /legacy-payment` (`app.py`) — add `notification_service.notify_user()` with appropriate payment type and `notification_service.notify_admins_inapp()` with `type='admin_payment_proof'`
  - [x] 6.5 Update `POST /split-bill/request` (`app.py`) — add `notification_service.notify_user()` for the partner with `type='split_request'`
  - [x] 6.6 Update `POST /split-bill/pay` (`app.py`) — add `notification_service.notify_user()` for the initiator with `type='split_paid'`
  - [x] 6.7 Update `POST /admin/verify-action` (`app.py`) — add `notification_service.notify_user()` with `type='license_approved'` when `status=2`, `type='license_rejected'` when `status=0`
  - [x] 6.8 Update `PUT /drivers/<id>/approve` (`app.py`) — add `notification_service.notify_user()` with `type='driver_approved'`
  - [x] 6.9 Update `PUT /drivers/<id>/reject` (`app.py`) — add `notification_service.notify_user()` with `type='driver_rejected'`
  - [x] 6.10 Update driver application submission route (`app.py`) — add `notification_service.notify_admins_inapp()` with `type='admin_driver_application'`

- [x] 7. Customer mobile app — Supabase client and Realtime subscription (`www/js/app.js` + `www/index.html`)
  - [x] 7.1 Add Supabase JS CDN script tag to `index.html` before `app.js`: `<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>`
  - [x] 7.2 Add `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `supabaseClient`, `notifChannel`, and `notifList` variables to `app.js`
  - [x] 7.3 Implement `loadNotifications(userId)` — calls `GET /notifications?user_id=<id>`, stores result in `notifList`, calls `updateNotifBadge()`
  - [x] 7.4 Update `updateNotifBadge()` — compute unread count from `notifList` instead of `NotifStore`; show/hide `notifBadge` element with count
  - [x] 7.5 Implement `subscribeToNotifications(userId)` — subscribes to Supabase Realtime `INSERT` events on `notifications` table filtered by `user_id=eq.<userId>`; on new event, prepends to `notifList` and calls `updateNotifBadge()`
  - [x] 7.6 Implement `unsubscribeFromNotifications()` — removes the Realtime channel; call this on logout
  - [x] 7.7 Call `loadNotifications()` and `subscribeToNotifications()` after successful login (in the post-login init flow)
  - [x] 7.8 Call `unsubscribeFromNotifications()` in the logout handler

- [ ] 8. Customer mobile app — notifications page (`www/js/app.js`)
  - [x] 8.1 Implement `openNotificationsPage()` — shows `page-notifications`, renders loading state, calls `GET /notifications`, renders notification cards with title/message/timestamp; shows empty state if no notifications
  - [x] 8.2 Call `POST /notifications/read-all` when the notifications page opens; update `notifList` to mark all as read and call `updateNotifBadge()`
  - [x] 8.3 Render unread notifications with a highlighted left border (red) and read notifications with a neutral style using the existing `.notif-item` and `.notif-item.unread` CSS classes

- [x] 9. Admin web app — notification bell and panel
  - [x] 9.1 Add notification bell button and `adminNotifBadge` span to the admin app header in `booking-management.html` (and other admin HTML pages that have a header)
  - [x] 9.2 Add `adminNotifPanel` dropdown div to the admin header HTML
  - [x] 9.3 Implement `loadAdminNotifications(adminId)` in `booking-management.js` — calls `GET /admin/notifications?admin_id=<id>`, stores in `adminNotifList`, calls `updateAdminNotifBadge()`
  - [x] 9.4 Implement `updateAdminNotifBadge()` — shows/hides `adminNotifBadge` with unread count
  - [x] 9.5 Implement `subscribeAdminNotifications(adminId)` — subscribes to Supabase Realtime `INSERT` events on `notifications` table filtered by `admin_id=eq.<adminId>`; on new event, prepends to `adminNotifList` and calls `updateAdminNotifBadge()`
  - [x] 9.6 Implement `toggleAdminNotifPanel()` — shows/hides `adminNotifPanel`, renders notification list, calls `POST /admin/notifications/read-all` and resets badge when opened
  - [x] 9.7 Call `loadAdminNotifications()` and `subscribeAdminNotifications()` after admin login

- [x] 10. Property-based tests (`backend/tests/test_notification_properties.py`)
  - [x] 10.1 Set up test file with module-level config/database mocks (same pattern as `test_sms_properties.py`)
  - [x] 10.2 Write property test for Property 1: `notify_user()` always inserts exactly one row — mock `get_cursor`, generate random `user_id`/`title`/`message`/`type`, verify `execute` called once with correct `user_id` and `admin_id=None`
    - `# Feature: in-app-notifications, Property 1: notify_user inserts exactly one row`
  - [x] 10.3 Write property test for Property 2: `notify_admins_inapp()` inserts one row per active admin — generate lists of admins with mixed `is_active`, mock cursor, verify insert count equals active admin count
    - `# Feature: in-app-notifications, Property 2: notify_admins_inapp inserts one row per active admin`
  - [x] 10.4 Write property test for Property 3: `GET /notifications` returns only the requesting user's data — use Flask test client, mock cursor returning mixed-user rows, verify all returned rows have matching `user_id`
    - `# Feature: in-app-notifications, Property 3: GET /notifications returns only requesting user's notifications`
  - [x] 10.5 Write property test for Property 4: `POST /notifications/read-all` sets all to read — generate N notifications, call endpoint, verify `updated` equals N
    - `# Feature: in-app-notifications, Property 4: read-all sets is_read=true for all user notifications`
  - [x] 10.6 Write property test for Property 5: notification ordering — insert N rows with known timestamps, call `GET /notifications`, verify `created_at` values are in descending order
    - `# Feature: in-app-notifications, Property 5: GET /notifications returns notifications ordered by created_at DESC`
  - [x] 10.7 Write property test for Property 6: `notify_user()` failure does not raise — mock `get_cursor` to raise an exception, call `notify_user()`, verify it returns `False` without raising
    - `# Feature: in-app-notifications, Property 6: notify_user failure does not raise`
