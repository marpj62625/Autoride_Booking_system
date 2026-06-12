# Requirements Document

## Introduction

The AutorideSystem Customer Mobile App is a cross-platform mobile application (iOS and Android) built with Capacitor, targeting customers of the Autoride car rental service. The app allows customers to register, verify their identity, browse and book vehicles, manage payments, track rented vehicles via GPS, complete vehicle inspection checklists, and review their rental history. It integrates with the existing Flask/Supabase PostgreSQL backend API and complements the existing admin web app, admin mobile app, and driver portal.

The backend is already fully implemented. This document describes the mobile UI requirements that consume those existing APIs.

---

## Glossary

- **App**: The AutorideSystem Customer Mobile Application (iOS and Android).
- **Customer**: A registered end-user of the App who rents vehicles. Must use a `@gmail.com` email address.
- **Backend**: The existing Flask REST API backed by a Supabase PostgreSQL database.
- **Supabase_Storage**: The cloud file storage service (Supabase) used by the Backend for license images, profile pictures, inspection photos, and payment proofs.
- **Booking**: A reservation record in the `bookings` table linking a Customer to a Vehicle for a defined rental period.
- **Vehicle**: A car or other motorized unit in the `vehicles` table available for rental.
- **Vehicle_Category**: A logical grouping of vehicles sharing the same `brand` and `model`. The Backend auto-assigns an available physical unit from the category when a booking is created.
- **Driver**: An optional professional driver registered in the `drivers` table that can be assigned to a Booking by an admin.
- **Coupon**: A discount code in the `coupons` table with a percentage reduction, expiry date, and usage limit.
- **Loyalty_Points**: Reward points stored in `users.loyalty_points`. Customers earn 1 point per PHP 100 spent and can redeem points for discounts on future bookings.
- **Inspection_Record**: A pre-rental ("pickup") or post-rental ("return") condition record in the `vehicle_inspections` table, including photos (JSONB array), mileage, fuel level, and notes.
- **OTP**: A 6-digit one-time password used for identity verification, delivered via email (SMTP) or SMS (Semaphore API).
- **Email_Verification**: The process of confirming a Customer's email address via OTP. Stored as `users.is_email_verified`. Required before login.
- **License_Verification_Status**: An integer flag on `users.is_verified`: `0` = Not Verified (no license uploaded), `1` = Pending Review (license uploaded, awaiting admin approval), `2` = Fully Verified (admin approved). Booking requires status `2`.
- **Payment_Type**: The payment mode chosen at booking time — `Full` (100%) or `Downpayment` (20% upfront, balance due later).
- **Payment_Status**: The payment state on a booking — `Unpaid`, `Partially Paid`, `Paid`, `Refund Pending`, `Refunded`, or `Cancelled`.
- **Booking_Status**: The lifecycle state of a booking — `Pending`, `Confirmed`, `Approved`, `Picked Up`, `Completed`, `Cancelled`, or `Rejected`.
- **Downpayment**: A partial upfront payment equal to 20% of the total Booking price. The remaining 80% is the balance.
- **Odometer_Limit**: The maximum daily mileage allowance, configurable in the `settings` table (default: 250 km/day, key: `mileage_limit`).
- **Long_Term_Discount**: A percentage discount applied automatically to Bookings meeting a minimum day threshold, configurable in `settings` (default: 10% for 7+ days, keys: `long_term_discount_percent` and `long_term_discount_days`).
- **Add-on**: An optional service (e.g., child seat, GPS device, extra insurance) stored as a comma-separated string in `bookings.addons`.
- **Split_Payment**: A feature allowing a second registered Customer (partner) to share the cost of a Booking, tracked in the `split_payments` table.
- **Saved_Payment**: A stored payment method (card type, last four digits, provider) in the `saved_payments` table for faster checkout.
- **Granular_Location**: A pickup or return address broken into three fields: province, municipality, and barangay (e.g., `pickup_province`, `pickup_municipality`, `pickup_barangay`).
- **Rental_Terms**: A text block stored in `settings` (key: `rental_terms`) displayed to Customers before booking confirmation.

---

## Requirements

### Requirement 1: Customer Registration and Email Verification

**User Story:** As a new customer, I want to register an account with my Gmail address and verify my email via OTP, so that I can access the App securely.

#### Acceptance Criteria

1. THE App SHALL provide a registration form collecting full name, Gmail address, and password.
2. WHEN a Customer submits the registration form, THE App SHALL send the data to `POST /register` and display a success message upon a `201` response.
3. IF the submitted email does not end with `@gmail.com`, THEN THE App SHALL display the error "Only @gmail.com emails are allowed for registration." and prevent submission.
4. IF the Backend returns a `409` response, THEN THE App SHALL display the error "Email already registered." and prevent account creation.
5. WHEN registration succeeds, THE App SHALL navigate the Customer to a 6-digit OTP entry screen and display the message "A verification code has been sent to your email."
6. WHEN the Customer submits a 6-digit OTP, THE App SHALL call `POST /auth/verify-email` with the email and OTP; upon a `200` response, THE App SHALL navigate to the login screen.
7. IF `POST /auth/verify-email` returns a `400` response, THEN THE App SHALL display the error "Invalid or expired verification code." and allow re-entry.
8. THE App SHALL validate that the password field is not empty before submission.
9. THE App SHALL validate that the full name field is not empty before submission.

---

### Requirement 2: Customer Login and Authentication

**User Story:** As a registered customer, I want to log in with my Gmail and password or via Google Sign-In, so that I can access my account.

#### Acceptance Criteria

1. THE App SHALL provide a login screen with email and password fields and a "Sign in with Google" button.
2. WHEN a Customer submits valid credentials, THE App SHALL call `POST /login`; upon a `200` response, THE App SHALL store the `user_id`, `full_name`, and `is_verified` value in secure local storage.
3. IF `POST /login` returns a `401` response, THEN THE App SHALL display the error "Invalid credentials."
4. IF `POST /login` returns a `403` response with `"Account Frozen"`, THEN THE App SHALL display the `reason` field returned by the Backend and prevent login.
5. IF `POST /login` returns a `403` response with `"verification_required": true`, THEN THE App SHALL redirect the Customer to the OTP verification screen with the email pre-filled.
6. WHEN a Customer taps "Sign in with Google", THE App SHALL initiate the Google OAuth flow and call `POST /auth/google` with the resulting credential token.
7. IF `POST /auth/google` returns `"verification_required": true`, THEN THE App SHALL navigate to the OTP entry screen for the returned email.
8. WHEN a Customer successfully logs in (email/password or Google), THE App SHALL navigate to the Home screen.
9. THE App SHALL persist the session so that the Customer remains logged in across App restarts until they explicitly log out.
10. WHEN a Customer taps "Log Out", THE App SHALL clear all locally stored session data and navigate to the login screen.

---

### Requirement 3: SMS OTP Login

**User Story:** As a registered customer, I want to log in using my phone number and an SMS OTP, so that I have an alternative login method.

#### Acceptance Criteria

1. THE App SHALL provide a "Login with Phone" option on the login screen.
2. WHEN a Customer enters their phone number and taps "Send OTP", THE App SHALL call `POST /auth/request-otp` with the phone number.
3. IF `POST /auth/request-otp` returns a `404` response, THEN THE App SHALL display the error "No account found with this phone number. Please register normally first."
4. WHEN the Customer submits the 6-digit SMS OTP, THE App SHALL call `POST /auth/verify-otp` with the phone and OTP; upon a `200` response, THE App SHALL store the `user_id` and `full_name` and navigate to the Home screen.
5. IF `POST /auth/verify-otp` returns a `401` response, THEN THE App SHALL display the error "Invalid or expired OTP."
6. THE App SHALL format the phone number to the 11-digit local format (e.g., `09XXXXXXXXX`) before sending to the Backend.

---

### Requirement 4: Customer Profile Management

**User Story:** As a customer, I want to view and edit my profile information, so that my account details are always accurate.

#### Acceptance Criteria

1. THE App SHALL display a Profile screen by calling `GET /profile?user_id={id}`, showing the Customer's full name, email, phone number, and profile picture.
2. WHEN a Customer edits and saves profile fields (full name, phone), THE App SHALL submit a multipart form to `POST /update-profile` and display a success confirmation upon a `200` response.
3. THE App SHALL allow the Customer to upload or replace their profile picture from the device camera or photo library; the image SHALL be included in the `POST /update-profile` multipart form as the `profile_picture` field and stored in Supabase Storage.
4. IF `POST /update-profile` returns an error, THEN THE App SHALL display the error message returned by the Backend and retain the previous values.
5. THE App SHALL display the Customer's current License_Verification_Status with a human-readable label: "Not Verified" (0), "Pending Review" (1), or "Verified" (2).
6. THE App SHALL display the Customer's current Loyalty_Points balance by calling `GET /user/points?user_id={id}`.
7. THE App SHALL validate that the phone number field, when provided, contains only digits and is between 10 and 11 characters before submission.

---

### Requirement 5: Document Upload and Identity Verification

**User Story:** As a customer, I want to upload my driver's license, so that I can be verified and allowed to book vehicles.

#### Acceptance Criteria

1. THE App SHALL provide a document upload screen where the Customer can upload a driver's license image.
2. WHEN a Customer selects and submits a license image, THE App SHALL submit a multipart form to `POST /user/upload-license` with the `user_id` and `license` file; upon a `200` response, THE App SHALL display the message "Your license has been submitted for review."
3. THE Backend stores the license image in Supabase Storage and sets `users.is_verified` to `1` (Pending Review); THE App SHALL reflect this status change on the Profile screen.
4. THE App SHALL accept image files in JPEG and PNG formats only; IF a file of another format is selected, THEN THE App SHALL display the error "Only JPEG and PNG images are accepted."
5. THE App SHALL enforce a maximum file size of 5 MB per uploaded document; IF the file exceeds this limit, THEN THE App SHALL display the error "File size must not exceed 5 MB."
6. WHEN the Customer's License_Verification_Status changes to `2` (Fully Verified), THE App SHALL display a notification with the message "Your license has been approved. You can now book vehicles."
7. WHEN the Customer's License_Verification_Status is `0` after a prior upload attempt (rejected), THE App SHALL display a message prompting the Customer to re-upload a valid document.
8. WHILE the Customer's License_Verification_Status is `0` or `1`, THE App SHALL disable the booking flow and display the message "License verification required before booking."
9. THE App SHALL call `GET /user/verify-status?user_id={id}` to retrieve the current `is_verified` value and `license_image_url` for display.

---

### Requirement 6: Vehicle Browsing and Search

**User Story:** As a customer, I want to browse and search available vehicle categories, so that I can find a car that fits my needs.

#### Acceptance Criteria

1. THE App SHALL display a vehicle catalog by calling `GET /vehicles/categories`, showing each category's brand, model, vehicle type, transmission, fuel type, seat count, daily rate, location, primary image, total units, and available units.
2. THE App SHALL provide filter controls for vehicle type, transmission, fuel type, seat count, and location.
3. WHEN a Customer applies filters, THE App SHALL update the vehicle list to show only matching categories without a full page reload.
4. THE App SHALL display only categories with at least one available unit in the browsing list.
5. WHEN a Customer taps a vehicle category, THE App SHALL navigate to a Vehicle Detail screen by calling `GET /vehicle/{id}?user_id={id}`, showing all gallery images, full specifications, daily rate, average rating, reviews, and pickup instructions.
6. THE App SHALL display the Long_Term_Discount notice on the Vehicle Detail screen using the configured threshold and percentage from the Backend settings.
7. THE App SHALL allow the Customer to add or remove a vehicle from their Favorites list by calling `POST /toggle-favorite`; favorites SHALL persist across sessions.
8. THE App SHALL display a Favorites screen listing all vehicles the Customer has saved by calling `GET /favorites?user_id={id}`.

---

### Requirement 7: Booking and Scheduling

**User Story:** As a verified customer, I want to create a booking for a vehicle category, so that the system assigns me an available unit for my desired rental period.

#### Acceptance Criteria

1. WHILE the Customer's License_Verification_Status is `2`, THE App SHALL allow the Customer to initiate a booking from the Vehicle Detail screen.
2. THE App SHALL provide a booking form collecting: start date, end date, pickup Granular_Location (province, municipality, barangay), return Granular_Location (province, municipality, barangay), rental type (`Self-Drive` or `With Driver`), optional Add-ons, insurance type, and Payment_Type (`Full` or `Downpayment`).
3. THE App SHALL prevent the Customer from selecting a start date in the past; IF an invalid date is entered, THEN THE App SHALL display the error "Start date must be today or a future date."
4. THE App SHALL prevent the Customer from selecting an end date before the start date; IF an invalid range is entered, THEN THE App SHALL display the error "End date must be after the start date."
5. WHEN the Customer selects dates, THE App SHALL calculate and display the base price, Add-on price, applicable Long_Term_Discount, and total price in real time.
6. THE App SHALL display the Odometer_Limit notice "Daily mileage limit: {limit} km" on the booking form, using the value from the Backend `settings` table (key: `mileage_limit`, default 250).
7. THE App SHALL display the system Rental_Terms fetched from the Backend `settings` table (key: `rental_terms`) on the booking confirmation screen.
8. THE App SHALL allow the Customer to apply a Coupon code; WHEN a valid code is entered, THE App SHALL call `POST /coupons/verify` with the code and display the resulting `discount_percent`; IF the coupon is invalid or expired, THE App SHALL display the error returned by the Backend.
9. THE App SHALL allow the Customer to redeem Loyalty_Points as a discount; THE App SHALL display the current points balance and the equivalent discount value.
10. WHEN the Customer submits the booking form, THE App SHALL call `POST /book` with all required fields including granular location fields, addons, insurance type, payment type, base price, addon price, total price, applied coupon ID, discount amount, and points redeemed; upon a `201` response, THE App SHALL navigate to the Payment screen with the returned `booking_id`.
11. IF `POST /book` returns a `403` response, THEN THE App SHALL display the error message from the Backend (e.g., license not verified) and keep the Customer on the booking form.
12. IF `POST /book` returns a `400` response indicating no available units, THEN THE App SHALL display the error "No units available for this model on the selected dates."

---

### Requirement 8: Payment Processing

**User Story:** As a customer, I want to pay for my booking using an online method or upload a payment proof, so that my reservation is confirmed.

#### Acceptance Criteria

1. THE App SHALL display a Payment screen showing the booking summary, total amount due, amount to pay now (full or 20% downpayment), and payment method options.
2. WHEN the Customer submits an online payment, THE App SHALL call `POST /payment` with `booking_id`, `amount`, `method`, and `reference_number`; upon a `200` response, THE App SHALL navigate to a confirmation screen.
3. WHEN the Customer submits a legacy payment with proof upload, THE App SHALL submit a multipart form to `POST /legacy-payment` with `booking_id`, `amount`, `method`, `reference_number`, and optional `payment_proof` image; upon a `201` response, THE App SHALL display the receipt details returned by the Backend.
4. WHEN payment is successful, THE App SHALL display a receipt screen showing booking ID, vehicle brand and model, rental period, total paid, reference number, payment method, and date/time.
5. IF a payment request fails, THEN THE App SHALL display the error message returned by the Backend and allow the Customer to retry.
6. WHEN the Customer has a booking with `payment_status` of `Partially Paid`, THE App SHALL display a "Pay Remaining Balance" button on the Booking Detail screen; WHEN tapped, THE App SHALL call `POST /bookings/{id}/pay-balance` with the amount, method, and reference number.
7. THE App SHALL allow the Customer to upload a payment proof image (JPEG or PNG, up to 5 MB) for the legacy payment flow.
8. WHEN `payment_type` is `Downpayment`, THE App SHALL display the 20% amount due now and the 80% balance amount on the Payment screen.

---

### Requirement 9: Booking Management and History

**User Story:** As a customer, I want to view and manage my bookings, so that I can track my rental history and cancel if needed.

#### Acceptance Criteria

1. THE App SHALL display a Booking History screen by calling `GET /user-bookings?user_id={id}`, listing all bookings with vehicle brand, model, plate number, rental period, Booking_Status, and Payment_Status.
2. WHEN a Customer taps a booking, THE App SHALL navigate to a Booking Detail screen showing all booking fields including pickup and return Granular_Location, addons, insurance type, payment type, amount paid, balance amount, and cancellation reason if applicable.
3. WHILE a booking's `status` is `Pending` or `Confirmed`, THE App SHALL display a "Cancel Booking" button on the Booking Detail screen.
4. WHEN the Customer taps "Cancel Booking", THE App SHALL prompt for a cancellation reason and call `POST /cancel-booking` with `booking_id` and `user_id` upon confirmation; upon a `200` response, THE App SHALL update the booking status in the list.
5. IF the cancellation request fails, THEN THE App SHALL display the error message returned by the Backend.
6. THE App SHALL allow the Customer to modify booking dates for `Pending` or `Confirmed` bookings by calling `POST /modify-booking` with `booking_id`, `start_date`, and `end_date`; THE App SHALL display the recalculated `new_total` returned by the Backend.
7. THE App SHALL display the Payment_Status on each booking entry using the values: `Unpaid`, `Partially Paid`, `Paid`, `Refund Pending`, `Refunded`, or `Cancelled`.
8. THE App SHALL allow the Customer to download a PDF receipt for a booking by calling `GET /bookings/{id}/receipt`.

---

### Requirement 10: Vehicle Inspection Checklist

**User Story:** As a customer, I want to complete a vehicle inspection checklist before and after my rental, so that vehicle condition is documented and disputes are avoided.

#### Acceptance Criteria

1. WHEN a booking's `status` is `Confirmed` or `Approved`, THE App SHALL display a "Pre-Rental Inspection" option on the Booking Detail screen.
2. THE App SHALL provide an inspection form collecting mileage reading, fuel level (text), and condition notes.
3. THE App SHALL allow the Customer to capture and attach multiple photos of the vehicle during the inspection; photos SHALL be uploaded to Supabase Storage via the Backend.
4. WHEN the Customer submits the pre-rental inspection, THE App SHALL submit a multipart form to `POST /inspections/submit` with `booking_id`, `inspection_type` set to `pickup`, `mileage`, `fuel_level`, `notes`, `inspector_id`, and `photos` files; upon a `201` response, THE App SHALL display a success confirmation.
5. WHEN a booking's `status` is `Picked Up`, THE App SHALL display a "Post-Rental Inspection" option on the Booking Detail screen.
6. THE App SHALL provide the same inspection form for the post-rental inspection with `inspection_type` set to `return`.
7. IF the Customer attempts to submit an inspection without entering a mileage value, THEN THE App SHALL display the error "Mileage reading is required."
8. THE App SHALL display previously submitted inspection records for a booking by calling `GET /inspections/{booking_id}`, showing inspection type, mileage, fuel level, notes, photos, and timestamp.

---

### Requirement 11: GPS Vehicle Tracking

**User Story:** As a customer with an active rental, I want to see the real-time location of my rented vehicle on a map, so that I can monitor it during the rental period.

#### Acceptance Criteria

1. WHILE a booking's `status` is `Picked Up`, THE App SHALL display a "Track Vehicle" button on the Booking Detail screen.
2. WHEN the Customer taps "Track Vehicle", THE App SHALL open a map view showing the vehicle's current GPS coordinates (`latitude`, `longitude`) from the vehicle record.
3. THE App SHALL refresh the vehicle location on the map at intervals of no more than 30 seconds.
4. IF the vehicle's `latitude` and `longitude` fields are null, THEN THE App SHALL display the message "Live tracking is currently unavailable for this vehicle."
5. THE App SHALL display the vehicle's `last_gps_update` timestamp on the map view.
6. THE App SHALL allow the Customer to center the map on the vehicle's current location with a single tap.

---

### Requirement 12: Reviews and Ratings

**User Story:** As a customer who has completed a rental, I want to leave a rating and comment for the vehicle, so that other customers can make informed decisions.

#### Acceptance Criteria

1. WHEN a booking's `status` is `Completed`, THE App SHALL display a "Leave a Review" option on the Booking Detail screen.
2. THE App SHALL provide a review form with a 1–5 star rating selector and an optional comment text field.
3. WHEN the Customer submits a review, THE App SHALL call `POST /review` with `user_id`, `vehicle_id`, `rating`, and `comment`; upon a `201` response, THE App SHALL display a success confirmation.
4. IF the Customer submits a review without selecting a star rating, THEN THE App SHALL display the error "Please select a rating before submitting."
5. THE App SHALL display the average rating and individual reviews for each vehicle on the Vehicle Detail screen, using data returned by `GET /vehicle/{id}` (which includes `avg_rating` and `reviews` array with `full_name`, `profile_picture`, `rating`, `comment`, and `created_at`).
6. THE App SHALL display individual customer reviews on the Vehicle Detail screen, showing the reviewer's name, profile picture, rating, comment, and submission date.

---

### Requirement 13: Split Payment

**User Story:** As a customer, I want to split the cost of a booking with another registered customer, so that we can share the rental expense.

#### Acceptance Criteria

1. THE App SHALL provide a "Split Payment" option on the Payment screen.
2. WHEN the Customer enables Split Payment, THE App SHALL display an input field for the partner customer's email address and the amount to split.
3. WHEN the Customer submits a split request, THE App SHALL call `POST /split-bill/request` with `booking_id`, `partner_email`, and `amount`; IF the Backend returns a `404` response, THE App SHALL display the error "Partner email not found in our system."
4. WHEN a split request is successfully created, THE App SHALL display the status "Awaiting partner confirmation."
5. THE App SHALL display incoming split bill requests by calling `GET /split-bills?email={email}`, showing the booking details, initiator name, and amount owed.
6. WHEN the partner Customer taps "Pay" on a split bill, THE App SHALL call `POST /split-bill/pay` with the `split_id`; upon a `200` response, THE App SHALL update the split status to "Paid."
7. THE App SHALL display the split payment status on the Booking Detail screen.

---

### Requirement 14: Saved Payment Methods

**User Story:** As a customer, I want to save my payment method details, so that I can check out faster on future bookings.

#### Acceptance Criteria

1. THE App SHALL display a "Saved Payment Methods" section on the Profile or Payment screen.
2. THE App SHALL list saved payment methods by calling `GET /saved-payments?user_id={id}`, showing card type, last four digits, and provider.
3. WHEN the Customer adds a new payment method, THE App SHALL call `POST /saved-payment` with `user_id`, `card_type`, `last_four`, and `provider`; upon a `201` response, THE App SHALL add the method to the list.
4. THE App SHALL validate that the `last_four` field contains exactly 4 digits before submission.

---

### Requirement 15: Support and Newsletter

**User Story:** As a customer, I want to submit a support ticket and subscribe to the newsletter, so that I can get help and stay informed about promotions.

#### Acceptance Criteria

1. THE App SHALL provide a Support screen with a form collecting name, email, subject, and message.
2. WHEN the Customer submits the support form, THE App SHALL call `POST /support` with `name`, `email`, `subject`, and `message`; upon a `201` response, THE App SHALL display the message "Support ticket submitted successfully."
3. IF any of the required fields (name, subject, message) are empty, THEN THE App SHALL display the error "Please fill in all required fields." and prevent submission.
4. THE App SHALL provide a newsletter subscription option; WHEN the Customer submits their email, THE App SHALL call `POST /newsletter` with the email; upon a `201` response, THE App SHALL display the message "Subscribed successfully."
5. THE App SHALL validate that the email field on the newsletter form is a valid email format before submission.

---

### Requirement 16: In-App Chatbot

**User Story:** As a customer, I want to ask common questions to an in-app chatbot, so that I can get quick answers without contacting support.

#### Acceptance Criteria

1. THE App SHALL provide a chat interface accessible from the Home screen or Support screen.
2. WHEN the Customer sends a message, THE App SHALL call `POST /chat` with `message` and `user_id`; THE App SHALL display the `response` field returned by the Backend.
3. IF the message field is empty, THEN THE App SHALL prevent submission and display the error "Message is required."
4. THE App SHALL display the chat history in a scrollable conversation view with user messages and bot responses visually distinguished.

---

### Requirement 17: Notifications

**User Story:** As a customer, I want to receive in-app notifications about my bookings and account, so that I stay informed without checking the App manually.

#### Acceptance Criteria

1. WHEN a booking is created, THE App SHALL display a notification with the message "We have received your booking. Our team will review it shortly."
2. WHEN a booking status changes to `Approved` or `Confirmed`, THE App SHALL display a notification reflecting the new status.
3. WHEN a booking is cancelled by the admin, THE App SHALL display a notification with the cancellation reason.
4. WHEN the Customer's License_Verification_Status changes, THE App SHALL display a notification reflecting the new status.
5. THE App SHALL display an in-app notification center listing past notifications with their timestamps.
6. WHEN the Customer has unread notifications, THE App SHALL display a badge count on the notification icon.

---

### Requirement 18: Pricing, Discounts, and Rates

**User Story:** As a customer, I want to see transparent pricing with all applicable discounts, so that I know exactly what I will pay before confirming a booking.

#### Acceptance Criteria

1. THE App SHALL display the daily rate for each vehicle category on the Vehicle Detail screen.
2. WHEN the Customer selects a rental period meeting or exceeding the `long_term_discount_days` threshold (default 7 days), THE App SHALL automatically apply the `long_term_discount_percent` (default 10%) and display the discounted total.
3. THE App SHALL display a price breakdown on the booking confirmation screen showing: base price, Add-on price, insurance price, Long_Term_Discount (if applicable), coupon discount (if applied), loyalty points discount (if redeemed), and total price.
4. WHEN a Coupon is applied, THE App SHALL display the coupon code, discount percentage, and the resulting savings amount.
5. THE App SHALL display the Odometer_Limit on the booking form so the Customer is informed before confirming.
6. THE App SHALL calculate Loyalty_Points to be earned for the booking as `floor(total_price / 100)` and display this on the booking confirmation screen.

---

### Requirement 19: Security and Data Validation

**User Story:** As a customer, I want my personal data and transactions to be protected, so that my account and payment information remain secure.

#### Acceptance Criteria

1. THE App SHALL transmit all data to the Backend over HTTPS.
2. THE App SHALL store the `user_id` and session data in the device's secure storage and not in plain-text local storage.
3. THE App SHALL validate all form inputs on the client side before sending requests to the Backend, including required fields, format checks, and length limits.
4. IF a Backend request returns a `401` or `403` status (other than expected verification flows), THEN THE App SHALL clear the local session and redirect the Customer to the login screen.
5. THE App SHALL not display raw Backend error stack traces to the Customer; IF an unexpected error occurs, THEN THE App SHALL display the message "Something went wrong. Please try again."
6. THE App SHALL sanitize all text inputs to prevent injection of script or markup characters before submission to the Backend.
7. THE App SHALL request only the device permissions required for its features (camera, location, notifications) and SHALL display a rationale to the Customer before requesting each permission.

---

### Requirement 20: Cross-Platform Compatibility (iOS and Android)

**User Story:** As a customer using either an iPhone or an Android device, I want the App to work correctly on my device, so that I have a consistent experience regardless of platform.

#### Acceptance Criteria

1. THE App SHALL be built using Capacitor and SHALL produce deployable builds for both Android (APK/AAB) and iOS (IPA).
2. THE App SHALL support Android API level 26 (Android 8.0) and above.
3. THE App SHALL support iOS 14 and above.
4. THE App SHALL adapt its layout to both portrait and landscape orientations without content overflow or truncation.
5. THE App SHALL use the AutorideSystem color palette consistently across all screens on both platforms.
6. THE App SHALL use native device camera and file picker APIs via Capacitor plugins for document and photo uploads.
7. THE App SHALL display all monetary values in Philippine Peso (PHP) format with two decimal places.
8. WHEN the App is launched on iOS, THE App SHALL request camera and photo library permissions using iOS-standard permission dialogs before accessing those resources.
