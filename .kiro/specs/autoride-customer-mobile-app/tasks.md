# Implementation Plan: AutorideSystem Customer Mobile App

## Overview

Build the Autoride Customer Mobile App from scratch as a Capacitor project at `AutorideSystem/customer_mobile/`, mirroring the structure of the existing `admin_mobile` app. The entire UI lives in a single `www/index.html` file (inline CSS + JS). Two new Flask endpoints are added to the backend. Pure utility functions are extracted to a testable module and covered by property-based tests using fast-check.

## Tasks

- [x] 1. Add new backend endpoints to the Flask API
  - [x] 1.1 Add `GET /vehicles/categories` endpoint to `AutorideSystem/backend/app.py`
    - Query the `vehicles` table grouped by `brand` + `model`, returning `brand`, `model`, `vehicle_type`, `transmission`, `fuel_type`, `seats`, `daily_rate`, `location`, `vehicle_image`, `total_units`, `available_units`, and `representative_id` (the `id` of one available unit in the group)
    - Only include groups where `available_units >= 1`
    - _Requirements: 6.1, 6.4_

  - [x] 1.2 Add `GET /vehicles/<int:vehicle_id>/location` endpoint to `AutorideSystem/backend/app.py`
    - Accept `user_id` as a query parameter; verify the requesting user has an active booking (`status` in `['Confirmed','Approved','Picked Up']`) for the given vehicle before returning data
    - Return `latitude`, `longitude`, and `last_gps_update` from the `vehicles` table; return `403` if the user has no qualifying booking
    - _Requirements: 11.1, 11.2, 11.3_

- [x] 2. Scaffold the Capacitor project structure
  - [x] 2.1 Create `AutorideSystem/customer_mobile/capacitor.config.json`
    - Set `appId` to `com.autoride.customer`, `appName` to `Autoride`, `webDir` to `www`, and `server.cleartext` to `true` with `allowNavigation` matching the admin app
    - _Requirements: 20.1_

  - [x] 2.2 Create `AutorideSystem/customer_mobile/package.json`
    - Mirror `admin_mobile/package.json`; add `@capacitor/preferences`, `@capacitor/camera`, and `@capacitor/push-notifications` as dependencies alongside the core Capacitor packages
    - Add a `test` script: `"vitest --run"`
    - _Requirements: 20.1_

  - [x] 2.3 Create the Android project scaffold files
    - Create `AutorideSystem/customer_mobile/android/app/src/main/AndroidManifest.xml` with `INTERNET`, `CAMERA`, `READ_EXTERNAL_STORAGE`, `WRITE_EXTERNAL_STORAGE`, and `RECEIVE_BOOT_COMPLETED` permissions, mirroring `admin_mobile/android/app/src/main/AndroidManifest.xml`
    - Create `AutorideSystem/customer_mobile/android/app/src/main/java/com/autoride/customer/MainActivity.java` with the Capacitor `BridgeActivity` subclass
    - Create `AutorideSystem/customer_mobile/android/app/build.gradle` and `AutorideSystem/customer_mobile/android/build.gradle` mirroring the admin app's Gradle files with the package name changed to `com.autoride.customer`
    - Create `AutorideSystem/customer_mobile/android/app/src/main/assets/capacitor.config.json` (copy of root config) and `AutorideSystem/customer_mobile/android/app/src/main/assets/capacitor.plugins.json`
    - _Requirements: 20.1, 20.2_

- [x] 3. Create the utility functions module and Vitest configuration
  - [x] 3.1 Create `AutorideSystem/customer_mobile/www/js/utils.js` with all eight pure utility functions
    - `isGmailAddress(email)` — returns `true` iff `email.toLowerCase().endsWith('@gmail.com')`
    - `isBlank(str)` — returns `true` for `null`, `undefined`, or strings whose `.trim()` is `''`
    - `normalizePhone(phone)` — strips non-digits, replaces leading `+63` with `0`, prepends `0` if not already starting with `0`, returns the result
    - `isValidLastFour(s)` — returns `true` iff `s` matches `/^\d{4}$/`
    - `formatPHP(value)` — returns `"PHP X,XXX.XX"` using `toLocaleString('en-PH', {minimumFractionDigits:2, maximumFractionDigits:2})` prefixed with `"PHP "`
    - `validateUploadFile(file)` — returns `null` on success or an error string if `file.type` is not `image/jpeg`/`image/png` or `file.size > 5 * 1024 * 1024`
    - `validateDateRange(startDate, endDate)` — returns `{valid: true}` or `{valid: false, error: '...'}` per design rules (start >= today, end > start)
    - `calculateBookingPrice(dailyRate, startDate, endDate, addons, insurancePrice, longTermDiscountDays, longTermDiscountPercent, couponPercent, pointsRedeemed)` — implements the formula from the design document exactly; returns `{days, basePrice, addonPrice, longTermDiscount, couponDiscount, pointsDiscount, total, pointsEarned}`
    - Export all functions via `export { ... }` for use in both the test suite and `index.html` (via `<script type="module">`)
    - _Requirements: 1.3, 1.8, 1.9, 3.6, 7.3, 7.4, 7.5, 14.4, 18.2, 18.3, 18.6, 20.7_

  - [x] 3.2 Create `AutorideSystem/customer_mobile/vitest.config.js`
    - Configure Vitest with `environment: 'node'` and `include: ['tests/**/*.test.js']`

  - [x] 3.3 Create `AutorideSystem/customer_mobile/tests/utils.test.js` — property-based tests for all 10 correctness properties
    - Import `fc` from `fast-check` and all utility functions from `../www/js/utils.js`
    - **Property 1: Gmail-only registration enforcement** — `fc.emailAddress()` generator; assert `isGmailAddress(email) === email.toLowerCase().endsWith('@gmail.com')` — _Validates: Requirements 1.3_
    - **Property 2: Booking price calculation correctness** — generate `dailyRate`, `days`, `addonPrices[]`, `insurancePrice`, `couponPercent`, `pointsRedeemed`, `longTermDiscountDays`, `longTermDiscountPercent`; assert total equals formula clamped to 0 and `pointsEarned === Math.floor(total / 100)` — _Validates: Requirements 7.5, 18.2, 18.3, 18.6_
    - **Property 3: Date range validation** — generate pairs of date strings; assert `validateDateRange` returns `valid: true` iff `start >= today && end > start` — _Validates: Requirements 7.3, 7.4_
    - **Property 4: Whitespace-only input rejection** — `fc.stringOf(fc.constantFrom(' ', '\t', '\n'))` generator; assert `isBlank(s) === true` for all such strings, and `isBlank(s) === false` for any string with at least one non-whitespace character — _Validates: Requirements 1.8, 1.9, 15.3_
    - **Property 5: Phone number format normalization** — generate phone strings with `+63`, `0`, or neither prefix; assert output is always 11 digits starting with `0` — _Validates: Requirements 3.6_
    - **Property 6: Loyalty points earned round-trip** — generate `P >= 0`; assert `Math.floor(P / 100) / 10 === Math.floor(P / 100) / 10` and `pointsEarned(P) === Math.floor(P / 100)` — _Validates: Requirements 18.6_
    - **Property 7: File validation — format and size** — generate mock file objects with varying `type` and `size`; assert `validateUploadFile` returns error for non-JPEG/PNG types and for `size > 5MB`, and returns `null` for valid files — _Validates: Requirements 5.4, 5.5, 8.7_
    - **Property 8: Downpayment amount calculation** — generate total price `T > 0`; assert `amountDueNow === T * 0.20`, `balance === T * 0.80`, and `amountDueNow + balance === T` (using `calculateBookingPrice` output with `payment_type = 'Downpayment'`) — _Validates: Requirements 8.8_
    - **Property 9: Last-four digits validation** — `fc.string()` generator; assert `isValidLastFour(s) === /^\d{4}$/.test(s)` — _Validates: Requirements 14.4_
    - **Property 10: Monetary display formatting** — `fc.float({min: 0, max: 1_000_000})` generator; assert `formatPHP(v)` starts with `"PHP "`, contains exactly one `.`, and the decimal part has exactly 2 digits — _Validates: Requirements 20.7_
    - Each test tagged with `// Feature: autoride-customer-mobile-app, Property N: {property_text}`
    - _Requirements: All above_

- [x] 4. Checkpoint — Run property-based tests
  - Run `npx vitest --run` in `AutorideSystem/customer_mobile/` and ensure all 10 property tests pass. Ask the user if any test fails before continuing.

- [x] 5. Build the `www/index.html` shell — global styles, constants, and infrastructure
  - [x] 5.1 Create `AutorideSystem/customer_mobile/www/index.html` with the document skeleton
    - `<meta viewport>` with `user-scalable=no`; load Inter from Google Fonts CDN; load Font Awesome 6 CDN; load Leaflet.js CDN
    - Declare `const API_BASE = 'http://192.168.1.x:9999'` at the top of the inline `<script>`
    - Define the full CSS custom property palette from the design document (`--primary: #e63946`, all background, text, status, border, radius, and shadow tokens)
    - Write global reset styles, body layout, `.hidden` utility class, and bottom-nav safe-area padding
    - _Requirements: 20.4, 20.5, 20.7_

  - [x] 5.2 Add the loading overlay and toast notification HTML + JS
    - `<div id="loadingOverlay">` with a spinner; implement `showLoading(show)` function
    - Implement `showToast(message, type)` — creates a floating `.toast` element, appends to `<body>`, auto-removes after 3 s; types: `success`, `error`, `info`
    - _Requirements: 19.5_

  - [x] 5.3 Implement the `Session` object and `apiCall` helper
    - `Session.save(user)`, `Session.load()`, `Session.clear()` using `@capacitor/preferences`
    - `apiCall(endpoint, options)` — prepends `API_BASE`, sets `Content-Type: application/json`, handles 401/403 session-clear-and-redirect logic, wraps network errors as `{status: 0, message: '...'}`, never exposes stack traces
    - `uploadFile(endpoint, formData)` — multipart POST without Content-Type header
    - _Requirements: 2.9, 19.1, 19.2, 19.4, 19.5_

  - [x] 5.4 Implement the page-switching system and bottom navigation bar
    - `showPage(id)` — hides all `.page` divs, shows the target, toggles bottom-nav active state, hides bottom nav on auth screens
    - Bottom nav HTML: 5 tabs (Home, Browse, Bookings, Profile, More) with Font Awesome icons; 75 px height; `padding-bottom: env(safe-area-inset-bottom)`
    - Wire tab clicks to `showPage('home')`, `showPage('vehicles')`, etc.
    - _Requirements: 20.3, 20.4_

  - [x] 5.5 Add the splash screen HTML and startup logic
    - `<div id="page-splash">` with Autoride logo, brand name, and spinner
    - On `deviceready` / `DOMContentLoaded`: call `Session.load()`; if session exists navigate to `home`, else navigate to `login`
    - _Requirements: 2.9_

- [x] 6. Implement authentication screens
  - [x] 6.1 Build the login screen (`page-login`)
    - Email + password fields, "Sign in with Google" button, "Login with Phone" link, "Register" link
    - On submit: validate non-empty fields, call `POST /login`; on `200` call `Session.save()` and `showPage('home')`; handle `401`, `403 Account Frozen`, `403 verification_required` per design error mapping
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.8_

  - [x] 6.2 Build the register screen (`page-register`)
    - Full name, Gmail, password fields; "Register" button; link back to login
    - Client-side: `isBlank` check on name and password, `isGmailAddress` check on email before calling `POST /register`
    - On `201`: navigate to `page-otp-verify` with email pre-filled; handle `409` with "Email already registered."
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.8, 1.9_

  - [x] 6.3 Build the OTP verification screen (`page-otp-verify`)
    - 6-digit OTP input, "Verify" button, "Resend Code" link
    - On submit: call `POST /auth/verify-email`; on `200` navigate to `page-login`; on `400` display "Invalid or expired verification code."
    - _Requirements: 1.6, 1.7_

  - [x] 6.4 Build the phone login screen (`page-phone-login`)
    - Phone number input + "Send OTP" button; OTP input + "Verify" button
    - Normalize phone with `normalizePhone()` before calling `POST /auth/request-otp`; handle `404` with "No account found with this phone number."
    - On OTP submit: call `POST /auth/verify-otp`; on `200` save session and navigate to `home`; on `401` display "Invalid or expired OTP."
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 7. Implement the Home screen (`page-home`)
  - Welcome banner with `currentUser.fullName`, notification bell with badge, quick-action cards (Browse, My Bookings, Support, Chat)
  - On load: call `GET /user-bookings?user_id={id}` and render a "Recent Bookings" strip (last 3 entries); call `GET /user/points?user_id={id}` and display points balance
  - Wire quick-action cards to `showPage` calls
  - _Requirements: 17.6_

- [x] 8. Implement the Vehicle Browse screen and Vehicle Detail overlay
  - [x] 8.1 Build the vehicles browse screen (`page-vehicles`)
    - On load: call `GET /vehicles/categories`; render a card grid with brand, model, type, transmission, fuel, seats, daily rate, location, image, available units
    - Filter chips for vehicle type, transmission, fuel type, seat count, location; filter client-side without reload; hide categories with `available_units < 1`
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 8.2 Build the vehicle detail overlay (`page-vehicle-detail`)
    - On open: call `GET /vehicle/{id}?user_id={id}`; render gallery carousel, full specs, daily rate, Long_Term_Discount notice, average rating, reviews list, pickup instructions
    - "Add to Favorites" / "Remove from Favorites" button calling `POST /toggle-favorite`; "Book Now" button (disabled with message if `is_verified < 2`)
    - _Requirements: 5.8, 6.5, 6.6, 6.7, 12.5, 12.6_

- [x] 9. Implement the Booking Form overlay (`page-booking-form`)
  - Date pickers for start/end date; validate with `validateDateRange()` and show inline errors per requirements 7.3 and 7.4
  - Granular location fields (province, municipality, barangay) for pickup and return; rental type selector; add-ons checkboxes; insurance type selector; payment type selector (Full / Downpayment)
  - Real-time price breakdown using `calculateBookingPrice()`; display base price, addon price, long-term discount, coupon discount, points discount, total, and points to be earned; use `formatPHP()` for all monetary values
  - Coupon code input calling `POST /coupons/verify`; loyalty points redemption input with current balance display
  - Odometer limit notice and Rental Terms display (fetched from `GET /settings` or embedded)
  - On submit: call `POST /book`; on `201` navigate to `page-payment` with `booking_id`; handle `403` and `400` errors inline
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.11, 7.12, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_

- [x] 10. Implement the Payment screen and receipt overlay
  - [x] 10.1 Build the payment screen (`page-payment`)
    - Booking summary, total amount, amount due now (full or 20% downpayment), balance amount; display using `formatPHP()`
    - Payment method selector; reference number input; "Pay Now" button calling `POST /payment`
    - "Upload Proof" option: file picker (JPEG/PNG, ?5 MB validated with `validateUploadFile()`), calls `POST /legacy-payment` via `uploadFile()`
    - "Split Payment" link opening `page-split-payment`
    - On success: navigate to `page-booking-receipt`
    - _Requirements: 8.1, 8.2, 8.3, 8.5, 8.7, 8.8_

  - [x] 10.2 Build the booking receipt overlay (`page-booking-receipt`)
    - Display booking ID, vehicle brand/model, rental period, total paid, reference number, payment method, date/time
    - "Download PDF Receipt" button calling `GET /bookings/{id}/receipt`
    - _Requirements: 8.4, 9.8_

- [x] 11. Implement the Bookings History screen and Booking Detail overlay
  - [x] 11.1 Build the bookings history screen (`page-bookings`)
    - On load: call `GET /user-bookings?user_id={id}`; render list with vehicle brand/model/plate, rental period, Booking_Status pill, Payment_Status pill
    - Tap a row to open `page-booking-detail`
    - _Requirements: 9.1_

  - [x] 11.2 Build the booking detail overlay (`page-booking-detail`)
    - Display all booking fields including granular pickup/return location, addons, insurance, payment type, amount paid, balance, cancellation reason
    - Conditional action buttons:
      - "Cancel Booking" when status is `Pending` or `Confirmed` — prompt for reason, call `POST /cancel-booking`
      - "Pay Remaining Balance" when `payment_status` is `Partially Paid` — call `POST /bookings/{id}/pay-balance`
      - "Modify Dates" when status is `Pending` or `Confirmed` — call `POST /modify-booking`, display `new_total`
      - "Pre-Rental Inspection" when status is `Confirmed` or `Approved`
      - "Post-Rental Inspection" when status is `Picked Up`
      - "Track Vehicle" when status is `Picked Up`
      - "Leave a Review" when status is `Completed`
    - Split payment status display
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 13.7_

- [x] 12. Implement the Inspection Form overlay (`page-inspection-form`)
  - Mileage input (required — validate with `isBlank`), fuel level text input, condition notes textarea
  - Photo capture section: "Take Photo" button using `@capacitor/camera`; display thumbnails of captured photos; convert base64/URI to `Blob` for `FormData`
  - On submit: build `FormData` with `booking_id`, `inspection_type`, `mileage`, `fuel_level`, `notes`, `inspector_id`, and photo files; call `POST /inspections/submit`; on `201` show success toast
  - "View Past Inspections" section: call `GET /inspections/{booking_id}` and render records with type, mileage, fuel, notes, photos, timestamp
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

- [x] 13. Implement the GPS Map overlay (`page-gps-map`)
  - Initialize Leaflet map in a `<div id="map">` container; set tile layer to OpenStreetMap
  - On open: call `GET /vehicles/{id}/location?user_id={id}`; if `latitude`/`longitude` are non-null, place a marker and center the map; if null, display "Live tracking is currently unavailable for this vehicle."
  - Display `last_gps_update` timestamp below the map
  - "Center on Vehicle" button re-centers the map to the marker's coordinates
  - Start GPS polling with `startGpsPolling(vehicleId)` (30 s interval); stop with `stopGpsPolling()` when the overlay is closed
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [x] 14. Implement the Review Form overlay (`page-review-form`)
  - 1–5 star rating selector (interactive star icons); optional comment textarea
  - Validate that a rating is selected before submit; display "Please select a rating before submitting." if not
  - On submit: call `POST /review` with `user_id`, `vehicle_id`, `rating`, `comment`; on `201` show success toast and close overlay
  - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [x] 15. Implement the Profile screen and related overlays
  - [x] 15.1 Build the profile screen (`page-profile`)
    - On load: call `GET /profile?user_id={id}` and `GET /user/points?user_id={id}` and `GET /user/verify-status?user_id={id}`
    - Display full name, email, phone, profile picture, License_Verification_Status label ("Not Verified" / "Pending Review" / "Verified"), loyalty points balance
    - "Edit Profile" form: full name and phone fields; phone validated with digit-only + 10–11 char check; profile picture upload via `@capacitor/camera`; submit to `POST /update-profile` as multipart
    - Links to "Upload License", "Saved Payments", "Favorites"
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [x] 15.2 Build the license upload overlay (`page-license-upload`)
    - File picker (JPEG/PNG, ?5 MB validated with `validateUploadFile()`); preview thumbnail; submit to `POST /user/upload-license`
    - On `200`: show "Your license has been submitted for review." and update profile status display
    - If `is_verified === 0` after a prior attempt: show "Please re-upload a valid document."
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.7, 5.8, 5.9_

  - [x] 15.3 Build the saved payments overlay (`page-saved-payments`)
    - On load: call `GET /saved-payments?user_id={id}`; render list with card type, last four, provider
    - "Add Payment Method" form: card type, last four (validated with `isValidLastFour()`), provider; submit to `POST /saved-payment`
    - _Requirements: 14.1, 14.2, 14.3, 14.4_

  - [x] 15.4 Build the favorites overlay (`page-favorites`)
    - On load: call `GET /favorites?user_id={id}`; render vehicle cards; tap to open `page-vehicle-detail`
    - _Requirements: 6.8_

- [x] 16. Implement the More screen and utility overlays
  - [x] 16.1 Build the more screen (`page-more`)
    - Menu items: Support, Newsletter, Chatbot, Notifications, Log Out
    - "Log Out" calls `Session.clear()` and `showPage('login')`
    - _Requirements: 2.10_

  - [x] 16.2 Build the support form overlay (`page-support`)
    - Name, email, subject, message fields; validate all required fields with `isBlank()` before submit
    - On submit: call `POST /support`; on `201` show "Support ticket submitted successfully."
    - Newsletter subscription input below the form; validate email format; call `POST /newsletter`; on `201` show "Subscribed successfully."
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

  - [x] 16.3 Build the chatbot overlay (`page-chatbot`)
    - Scrollable conversation view; user messages right-aligned, bot responses left-aligned with distinct background colors
    - Message input + send button; validate non-empty with `isBlank()`; call `POST /chat` with `message` and `user_id`; append `response` to conversation
    - _Requirements: 16.1, 16.2, 16.3, 16.4_

  - [x] 16.4 Build the notifications center overlay (`page-notifications`)
    - On open: load notification list from `@capacitor/preferences` (key: `notifications`); render each entry with message and timestamp
    - Unread badge count on the bell icon in the home header; mark all as read when overlay is opened
    - _Requirements: 17.5, 17.6_

- [x] 17. Implement the Split Payment overlay (`page-split-payment`)
  - Partner email input and amount input; "Request Split" button calling `POST /split-bill/request`; handle `404` with "Partner email not found in our system."
  - On success: display "Awaiting partner confirmation."
  - Incoming split bills section: call `GET /split-bills?email={email}`; render each with booking details, initiator name, amount; "Pay" button calling `POST /split-bill/pay`
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

- [x] 18. Checkpoint — Integration wiring and final validation
  - Ensure all `showPage()` calls are wired correctly (no dead navigation paths)
  - Ensure `stopGpsPolling()` is called whenever `page-gps-map` is closed
  - Ensure all monetary values throughout the app use `formatPHP()`
  - Ensure all file inputs use `validateUploadFile()` before any upload call
  - Ensure `Session.clear()` + redirect to login is triggered on unexpected `401`/`403` responses in `apiCall`
  - Ensure all text inputs are sanitized (strip `<`, `>`, `"`, `'` characters) before submission per requirement 19.6
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 20.7_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- The design uses vanilla JavaScript — no build step or bundler is required
- `www/js/utils.js` is the only file imported as an ES module; `index.html` uses `<script type="module">` to import it
- Property tests (Task 3.3) must be run with `npx vitest --run` inside `customer_mobile/`; install `fast-check` and `vitest` as dev dependencies in `package.json`
- The Android scaffold in Task 2.3 provides the minimum files needed; run `npx cap sync` after completing Task 5 to copy `www/` into the Android assets folder
- GPS polling (Task 13) uses the new `GET /vehicles/<id>/location` endpoint added in Task 1.2
- All monetary display uses `formatPHP()` from `utils.js` (Property 10)
