# COMPLETE SYSTEM INPUT FIELDS & LIMITS INVENTORY

## PART 1: CUSTOMER APP (Mobile & Web)

| Category | Field ID / Name | Type | Current Limit (`maxlength` / `min`-`max`) | Recommended / Target Limit | Status |
|---|---|---|---|---|---|
| Customer HTML | `loginEmail` | email | 60 | yourname@gmail.com | Protected |
| Customer HTML | `loginPassword` | password | 64 | Enter your password | Protected |
| Customer HTML | `forgotPwEmail` | email | 60 | yourname@gmail.com | Protected |
| Customer HTML | `regFirstName` | text | 30 | Juan | Protected |
| Customer HTML | `regMiddleName` | text | 30 | M. (Optional) | Protected |
| Customer HTML | `regLastName` | text | 30 | Dela Cruz | Protected |
| Customer HTML | `regEmail` | email | 60 | yourname@gmail.com | Protected |
| Customer HTML | `regPassword` | password | 64 | At least 8 characters | Protected |
| Customer HTML | `otp0` | number | 1 |  | Protected |
| Customer HTML | `otp1` | number | 1 |  | Protected |
| Customer HTML | `otp2` | number | 1 |  | Protected |
| Customer HTML | `otp3` | number | 1 |  | Protected |
| Customer HTML | `otp4` | number | 1 |  | Protected |
| Customer HTML | `otp5` | number | 1 |  | Protected |
| Customer HTML | `vehicleSearch` | text | 50 | Search for cars, location | Protected |
| Customer HTML | `editFirstName` | text | 30 | Juan | Protected |
| Customer HTML | `editMiddleName` | text | 30 | M. (Optional) | Protected |
| Customer HTML | `editLastName` | text | 30 | Dela Cruz | Protected |
| Customer HTML | `editPhone` | tel | 11 | 09XXXXXXXXX | Protected |
| Customer HTML | `editEmail` | email | 60 | yourname@gmail.com | Protected |
| Customer HTML | `profilePicFileInput` | file | None |  | NEEDS LIMIT |
| Customer HTML | `editLicenseNumber` | text | 13 | e.g. N01-23-456789 | Protected |
| Customer HTML | `editLicenseExpiry` | date | 2026-01-01 to 2037-12-31 |  | Protected |
| Customer HTML | `editLicenseClass` | text | 15 | e.g. A, B, B1 | Protected |
| Customer HTML | `editLicenseAddress` | text | 100 | House/Unit No., Street, B | Protected |
| Customer HTML | `editLicenseName` | text | 50 | First Name, Middle Name,  | Protected |
| Customer HTML | `editLicenseDob` | date | 1950-01-01 to 2008-12-31 |  | Protected |
| Customer HTML | `editLicenseEmName` | text | 50 | Maria Dela Cruz | Protected |
| Customer HTML | `editLicenseEmPhone` | tel | 11 | 09XXXXXXXXX | Protected |
| Customer HTML | `editLicenseEmRel` | select | None |  | NEEDS LIMIT |
| Customer HTML | `licenseFileInputFront` | file | None |  | NEEDS LIMIT |
| Customer HTML | `licenseCameraInputFront` | file | None |  | NEEDS LIMIT |
| Customer HTML | `licenseFileInputBack` | file | None |  | NEEDS LIMIT |
| Customer HTML | `licenseCameraInputBack` | file | None |  | NEEDS LIMIT |
| Customer HTML | `changePasswordCurrent` | password | 64 | Enter current password | Protected |
| Customer HTML | `changePasswordNew` | password | 64 | At least 8 characters | Protected |
| Customer HTML | `changePasswordConfirm` | password | 64 | Re-enter new password | Protected |
| Customer HTML | `mandatoryReviewComment` | textarea | 300 | Tell us how we did or how | Protected |
| Customer Dynamic JS | `vd-trans` | select | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `vd-color` | select | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `bfStartDate` | date | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `bfPickupTime` | select | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `bfEndDate` | date | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `bfReturnTime` | select | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `bfDestination` | text | 60 | e.g., Baguio City, Tagayt | Protected |
| Customer Dynamic JS | `bfRentalPurpose` | select | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `bfPickupLocation` | select | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `bfReturnLocation` | select | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `bfDeliveryZone` | select | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `bfDeliveryAddress` | text | 100 | Enter specific delivery a | Protected |
| Customer Dynamic JS | `bfDeliveryBarangay` | text | 40 | Barangay | Protected |
| Customer Dynamic JS | `bfDeliveryMunicipality` | text | 40 | Municipality or City | Protected |
| Customer Dynamic JS | `bfDeliveryProvince` | text | 40 | Province | Protected |
| Customer Dynamic JS | `bfPoints` | number | 0 to None |  | Protected |
| Customer Dynamic JS | `extNewEnd` | date | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `extMethod` | select | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `extRef` | text | 30 | e.g. 1234567890 | Protected |
| Customer Dynamic JS | `refundAcctName` | text | 50 | Full name on account | Protected |
| Customer Dynamic JS | `refundAcctNum` | tel | 11 | e.g. 09XX-XXX-XXXX | Protected |
| Customer Dynamic JS | `refundNotes` | textarea | 200 | e.g. Bank name, branch, e | Protected |
| Customer Dynamic JS | `modStart` | date | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `modEnd` | date | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `inspMileage` | number | None | e.g. 12500 | NEEDS LIMIT |
| Customer Dynamic JS | `inspFuel` | select | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `inspNotes` | textarea | 300 | Describe vehicle conditio | Protected |
| Customer Dynamic JS | `reviewComment` | textarea | 300 | Share your experience... | Protected |
| Customer Dynamic JS | `newCardType` | select | None |  | NEEDS LIMIT |
| Customer Dynamic JS | `newLastFour` | text | 4 | 1234 | Protected |
| Customer Dynamic JS | `newProvider` | text | 40 | e.g. BDO, BPI, GCash | Protected |
| Customer Dynamic JS | `chatInput` | text | 250 | Type a message... | Protected |
| Customer Dynamic JS | `nlEmail` | email | 60 | Enter your email address | Protected |
| Customer Dynamic JS | `lcInput` | text | 250 | Type a message... | Protected |


## PART 2: ADMIN APP (Desktop & Mobile)

| Module / Area | Field ID / Name | Type | Current Limit | Recommended Limit | Severity / Risk |
|---|---|---|---|---|---|
| Date Range Pickers | `popupDateFrom` | date | None | Valid date range bounds | Medium |
| Date Range Pickers | `popupDateTo` | date | None | Valid date range bounds | Medium |
| Dropdown Select Filter | `popupStatusFilter` | select | None | Restricted to enum values | Low (Enum select) |
| Vehicle Add/Edit Form | `popupVehicleFilter` | select | None | maxlength=50 | HIGH (Vehicle specs, plates, rates) |
| Dropdown Select Filter | `popupMetricFilter` | select | None | Restricted to enum values | Low (Enum select) |
| Dropdown Select Filter | `popupLimitFilter` | select | None | Restricted to enum values | Low (Enum select) |
| Date Range Pickers | `dashDateFrom` | date | None | Valid date range bounds | Medium |
| Date Range Pickers | `dashDateTo` | date | None | Valid date range bounds | Medium |
| Vehicle Add/Edit Form | `vehicleSearch` | text | None | maxlength=50 | HIGH (Vehicle specs, plates, rates) |
| Vehicle Add/Edit Form | `vehicleCategoryFilter` | select | None | maxlength=50 | HIGH (Vehicle specs, plates, rates) |
| Search & Filter Bars | `activitySearch` | text | None | maxlength=50 (strip dangerous chars) | Low |
| Search & Filter Bars | `pastBookingsSearch` | text | None | maxlength=50 (strip dangerous chars) | Low |
| Dropdown Select Filter | `pastBookingsSort` | select | None | Restricted to enum values | Low (Enum select) |
| Dropdown Select Filter | `pastBookingsPageSize` | select | None | Restricted to enum values | Low (Enum select) |
| Search & Filter Bars | `archivedBookingsSearch` | text | None | maxlength=50 (strip dangerous chars) | Low |
| Dropdown Select Filter | `archivedBookingsReasonFilter` | select | None | Restricted to enum values | Low (Enum select) |
| Dropdown Select Filter | `newBookingsSort` | select | None | Restricted to enum values | Low (Enum select) |
| Dropdown Select Filter | `allBookingsSort` | select | None | Restricted to enum values | Low (Enum select) |
| Search & Filter Bars | `verificationsSearch` | text | None | maxlength=50 (strip dangerous chars) | Low |
| Dropdown Select Filter | `verificationsSort` | select | None | Restricted to enum values | Low (Enum select) |
| Blackout Dates | `blackoutStartDate` | date | None | valid date range | Medium |
| Blackout Dates | `blackoutEndDate` | date | None | valid date range | Medium |
| Blackout Dates | `blackoutReason` | text | None | maxlength=100 | Medium |
| Promos & Newsletters | `nlFormTitle` | text | None | maxlength=80 | HIGH (Promo codes, titles, percentage) |
| Promos & Newsletters | `nlFormCategory` | select | None | maxlength=100 | HIGH (Promo codes, titles, percentage) |
| Promos & Newsletters | `nlFormDiscount` | number | 1 to 99 | min=1 max=99 (%) | HIGH (Promo codes, titles, percentage) |
| Promos & Newsletters | `nlFormCode` | text | None | maxlength=15 (alphanumeric) | HIGH (Promo codes, titles, percentage) |
| Promos & Newsletters | `nlFormContent` | textarea | None | maxlength=1000 | HIGH (Promo codes, titles, percentage) |
| Promos & Newsletters | `nlSubSearchInput` | text | None | maxlength=100 | HIGH (Promo codes, titles, percentage) |
| Maintenance & Logs | `maintBatchBookingDays` | select | None | maxlength=100 or select bounds | Medium |
| Maintenance & Logs | `maintLogsDays` | select | None | maxlength=100 or select bounds | Medium |
| Maintenance & Logs | `maintNotificationsDays` | select | None | maxlength=100 or select bounds | Medium |
| Maintenance & Logs | `maintChatsDays` | select | None | maxlength=100 or select bounds | Medium |
| Admin General | `quickCustomColorPicker` | color | None | Set limit | Medium |
| Admin General | `quickTotalPrice` | number | 0 to None | Set limit | Medium |
| Admin General | `quickAmountPaid` | number | 0 to None | Set limit | Medium |
| Admin General | `quickBalanceAmount` | text | None | Set limit | Medium |
| Admin General | `quickPaymentStatus` | select | None | Set limit | Medium |
| Admin General | `quickPaymentMethod` | select | None | Set limit | Medium |
| Walk-in Booking Modal | `walkinCustName` | text | None | maxlength=50 (letters & spaces) | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinCustPhone` | tel | None | maxlength=11 (numeric only) | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinCustAddress` | text | None | maxlength=100 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinEmergName` | text | None | maxlength=50 (letters & spaces) | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinEmergPhone` | tel | None | maxlength=11 (numeric only) | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinEmergRel` | text | None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinCustomerSearch` | text | None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinVehicleSelect` | select | None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinStartDate` | date | None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinStartTime` | time | None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinEndDate` | date | None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinEndTime` | time | None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinRentalType` | select | None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinPickupLocation` | text | None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinBasePrice` | number | 0 to None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinExtraFee` | number | 0 to None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinDiscount` | number | 0 to None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinPaymentMethod` | select | None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinPaymentStatus` | select | None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinAmountPaid` | number | 0 to None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Walk-in Booking Modal | `walkinBookingStatus` | select | None | maxlength=50 | HIGH (Customer info input directly by staff) |
| Live Chat & FAQ Management | `chatCtrlAiGreeting` | textarea | None | maxlength=250 | Medium |
| Live Chat & FAQ Management | `chatCtrlAiFallback` | textarea | None | maxlength=250 | Medium |
| Live Chat & FAQ Management | `faqFormChipLabel` | text | None | maxlength=250 | Medium |
| Live Chat & FAQ Management | `faqFormCategory` | text | None | maxlength=250 | Medium |
| Live Chat & FAQ Management | `faqFormQuestion` | text | None | maxlength=250 | Medium |
| Live Chat & FAQ Management | `faqFormKeywords` | text | None | maxlength=250 | Medium |
| Live Chat & FAQ Management | `faqFormAnswer` | textarea | None | maxlength=250 | Medium |
| Live Chat & FAQ Management | `faqFormDisplayOrder` | number | 1 to 999 | maxlength=250 | Medium |
| Search & Filter Bars | `settingsSearchInput` | text | None | maxlength=50 (strip dangerous chars) | Low |
| Date Range Pickers | `fleetExportStartDate` | date | None | Valid date range bounds | Medium |
| Date Range Pickers | `fleetExportEndDate` | date | None | Valid date range bounds | Medium |
| Vehicle Add/Edit Form | `fleetExportVehicle` | select | None | maxlength=50 | HIGH (Vehicle specs, plates, rates) |
| Admin General | `fleetExportStatus` | select | None | Set limit | Medium |
| Admin General | `fcImportFileInput` | file | None | Set limit | Medium |
| Vehicle Add/Edit Form | `expVehicleId` | select | None | maxlength=50 | HIGH (Vehicle specs, plates, rates) |
| Admin General | `expType` | select | None | Set limit | Medium |
| Admin General | `expAmount` | number | 0 to None | Set limit | Medium |
| Date Range Pickers | `expDate` | date | None | Valid date range bounds | Medium |
| Admin General | `expDesc` | textarea | None | Set limit | Medium |
| Admin General | `expProofFile` | file | None | Set limit | Medium |
| Admin General | `addonNameInput` | text | None | Set limit | Medium |
| Admin General | `addonPriceInput` | number | None | Set limit | Medium |
| Admin General | `addonDescInput` | textarea | None | Set limit | Medium |
| Admin General | `insuranceNameInput` | text | None | Set limit | Medium |
| Admin General | `insurancePriceInput` | number | None | Set limit | Medium |
| Admin General | `insuranceDescInput` | textarea | None | Set limit | Medium |
| Admin General | `locationNameInput` | text | None | Set limit | Medium |
| Admin General | `locationProvinceInput` | text | None | Set limit | Medium |
| Admin General | `locationMuniInput` | text | None | Set limit | Medium |
| Admin General | `locationBrgyInput` | text | None | Set limit | Medium |
| Admin General | `locationFeeInput` | number | None | Set limit | Medium |
| Admin General | `assignDriverSelect` | select | None | Set limit | Medium |
| Date Range Pickers | `rptDateFrom` | date | None | Valid date range bounds | Medium |
| Date Range Pickers | `rptDateTo` | date | None | Valid date range bounds | Medium |
| Admin General | `driverWageInput` | text | None | Set limit | Medium |
| Search & Filter Bars | `driverSearchInput` | text | None | maxlength=50 (strip dangerous chars) | Low |
| Dropdown Select Filter | `driverStatusFilter` | select | None | Restricted to enum values | Low (Enum select) |
| Vehicle Add/Edit Form | `gpsVehicleSelect` | select | None | maxlength=50 | HIGH (Vehicle specs, plates, rates) |
| Admin General | `newInstructionInput` | text | None | Set limit | Medium |
| Admin General | `staffName` | text | None | Set limit | Medium |
| System Settings | `staffEmail` | email | None | maxlength=60 or 100 | HIGH (Configuration & credentials) |
| Admin General | `staffPass` | password | None | Set limit | Medium |
| Admin General | `staffRole` | select | None | Set limit | Medium |
| Admin General | `vGalleryPicker` | file | None | Set limit | Medium |
| Vehicle Add/Edit Form | `vBrand` | select | None | maxlength=50 | HIGH (Vehicle specs, plates, rates) |
| Vehicle Add/Edit Form | `vModel` | select | None | maxlength=50 | HIGH (Vehicle specs, plates, rates) |
| Vehicle Add/Edit Form | `vPlate` | text | None | maxlength=8 (e.g. ABC 1234) | HIGH (Vehicle specs, plates, rates) |
| Vehicle Add/Edit Form | `vColor` | text | None | maxlength=50 | HIGH (Vehicle specs, plates, rates) |
| Vehicle Add/Edit Form | `vTrans` | select | None | maxlength=50 | HIGH (Vehicle specs, plates, rates) |
| Admin General | `vType` | select | None | Set limit | Medium |
| Vehicle Add/Edit Form | `vFuel` | select | None | maxlength=50 | HIGH (Vehicle specs, plates, rates) |
| Vehicle Add/Edit Form | `vSeats` | select | None | min=2 max=30 | HIGH (Vehicle specs, plates, rates) |
| Vehicle Add/Edit Form | `vYear` | text | 4 | min=2000 max=2027 | HIGH (Vehicle specs, plates, rates) |
| Vehicle Add/Edit Form | `vRate` | number | None | min=500 max=50000 | HIGH (Vehicle specs, plates, rates) |
| Vehicle Add/Edit Form | `vMileageType` | select | None | min=0 max=999999 | HIGH (Vehicle specs, plates, rates) |
| Vehicle Add/Edit Form | `vMileageKm` | number | None | min=0 max=999999 | HIGH (Vehicle specs, plates, rates) |
| Admin General | `vLocation` | select | None | Set limit | Medium |
| Admin General | `vStatus` | select | None | Set limit | Medium |
| Admin General | `vOdometer` | number | None | Set limit | Medium |
| Vehicle Add/Edit Form | `vFuelLevel` | select | None | maxlength=50 | HIGH (Vehicle specs, plates, rates) |
| Date Range Pickers | `vNextService` | date | None | Valid date range bounds | Medium |
| Date Range Pickers | `vLtoExpiry` | date | None | Valid date range bounds | Medium |
| Admin General | `vGpsDeviceName` | text | None | Set limit | Medium |
| Admin General | `vGpsDeviceToken` | text | None | Set limit | Medium |
| System Settings | `superAdminEditEmail` | email | None | maxlength=60 or 100 | HIGH (Configuration & credentials) |
| Admin General | `superAdminCurrentPassword` | password | None | Set limit | Medium |
| Admin General | `superAdminNewPassword` | password | None | Set limit | Medium |
| Admin General | `superAdminConfirmPassword` | password | None | Set limit | Medium |
| Admin General | `newMobilePassword` | password | None | Set limit | Medium |
| Admin General | `confirmMobilePassword` | password | None | Set limit | Medium |
| Admin General | `inspectMileage` | number | None | Set limit | Medium |
| Admin General | `inspectFuel` | select | None | Set limit | Medium |
| Admin General | `inspectFuelChargeAmount` | number | 0 to None | Set limit | Medium |
| Admin General | `inspectFuelChargeNotes` | text | None | Set limit | Medium |
| Admin General | `inspectDriverOTHours` | number | 0 to None | Set limit | Medium |
| Admin General | `inspectDriverOTAmount` | text | None | Set limit | Medium |
| Admin General | `inspectDriverOTNotes` | text | None | Set limit | Medium |
| Admin General | `inspectPhotos` | file | None | Set limit | Medium |
| Admin General | `inspectNotes` | textarea | None | Set limit | Medium |
| Search & Filter Bars | `umSearch` | text | None | maxlength=50 (strip dangerous chars) | Low |
| Dropdown Select Filter | `umSort` | select | None | Restricted to enum values | Low (Enum select) |
| Admin General | `pushNotifTitle` | text | None | Set limit | Medium |
| Admin General | `pushNotifBody` | textarea | None | Set limit | Medium |
| Search & Filter Bars | `fleetCalendarSearch` | text | None | maxlength=50 (strip dangerous chars) | Low |
| System Settings | `loginEmail` | email | None | maxlength=60 or 100 | HIGH (Configuration & credentials) |
| Admin General | `loginPass` | password | None | Set limit | Medium |
| Vehicle Add/Edit Form | `fleetVehicleRateInput` | number | 0 to None | min=500 max=50000 | HIGH (Vehicle specs, plates, rates) |
| Admin General | `penaltyType_${b.id}` | select | None | Set limit | Medium |
| Admin General | `penaltyAmount_${b.id}` | number | None | Set limit | Medium |
| Admin General | `penaltyNotes_${b.id}` | textarea | None | Set limit | Medium |
| Admin General | `refundProofFile_${b.id}` | file | None | Set limit | Medium |
| Admin General | `refundRefInput_${b.id}` | text | None | Set limit | Medium |
| Admin General | `extRfAmt_${extensionId}` | number | None | Set limit | Medium |
| Admin General | `extRfMethod_${extensionId}` | select | None | Set limit | Medium |
| Admin General | `extRfRef_${extensionId}` | text | None | Set limit | Medium |
| Admin General | `extRfProof_${extensionId}` | file | None | Set limit | Medium |
| Admin General | `${inputId}` | password | None | Set limit | Medium |
| Admin General | `umEditName` | text | None | Set limit | Medium |
| Admin General | `umEditPhone` | text | None | Set limit | Medium |
| Admin General | `umLoyaltyInput` | number | None | Set limit | Medium |
| Admin General | `umNewPass` | password | None | Set limit | Medium |
| Admin General | `editStrikes_${u.id}` | select | None | Set limit | Medium |
| Admin General | `editSuspPreset_${u.id}` | select | None | Set limit | Medium |
| Admin General | `editSuspCustom_${u.id}` | datetime-local | None | Set limit | Medium |
| Admin General | `editNote_${u.id}` | text | None | Set limit | Medium |
| Admin General | `umFreezeReason` | text | None | Set limit | Medium |
| Live Chat & FAQ Management | `chatSearchInput` | text | None | maxlength=250 | Medium |
| Search & Filter Bars | `acUserSearchInput` | text | None | maxlength=50 (strip dangerous chars) | Low |
| Admin General | `acInput` | text | None | Set limit | Medium |
| System Settings | `manualSmtpEmail` | email | None | maxlength=60 or 100 | HIGH (Configuration & credentials) |
| System Settings | `manualSmtpPass` | password | None | maxlength=60 or 100 | HIGH (Configuration & credentials) |
| System Settings | `testEmailRecipient` | email | None | maxlength=60 or 100 | HIGH (Configuration & credentials) |
| Admin General | `permStaffSelect` | select | None | Set limit | Medium |
| Admin General | `staffReqPermReason` | textarea | None | Set limit | Medium |
| Vehicle Add/Edit Form | `gpsConfigVehicleSelect` | select | None | maxlength=50 | HIGH (Vehicle specs, plates, rates) |
| Admin General | `gpsConfigDeviceName` | text | None | Set limit | Medium |
| Admin General | `gpsConfigToken` | password | None | Set limit | Medium |
| Admin General | `gpsConfigServer` | text | None | Set limit | Medium |


## PART 3: BACKEND API PAYLOAD LIMITS (`backend/app.py`)

| Endpoint | Method | Key Incoming Fields | Missing / Needed Backend Guard |
|---|---|---|---|
| `/api/auth/register` | POST | `first_name`, `last_name`, `email`, `password` | Enforce max len: name <= 30, email <= 60, pass <= 64 |
| `/api/auth/login` | POST | `email`, `password` | Enforce max len: email <= 60, pass <= 64 |
| `/api/user/profile` | PUT | `first_name`, `last_name`, `phone`, `email` | Enforce max len: name <= 30, phone == 11, email <= 60 |
| `/api/user/driver-license` | POST/PUT | `license_number`, `name_on_license`, `address`, `license_class`, `emergency_contact_name`, `emergency_contact_phone` | Enforce: class <= 15, address <= 100, name <= 50, em_name <= 50, em_phone == 11 |
| `/api/bookings` | POST | `destination`, `delivery_address`, `start_date`, `end_date`, `service_type` | Enforce: dest <= 60, delivery_addr <= 100. (Note: rental duration limit is deferred per user) |
| `/api/admin/walkin` | POST | `customer_name`, `contact_number`, `address`, `emergency_name`, `emergency_phone`, `license_number` | Enforce: name <= 50, phone == 11, addr <= 100, license == 13 |
| `/api/vehicles` (Admin) | POST/PUT | `brand`, `model`, `plate_number`, `daily_rate`, `year`, `seats` | Enforce: brand <= 30, model <= 30, plate <= 8, rate (500-50000), year (2000-2027), seats (2-30) |
| `/api/admin/newsletter` | POST | `title`, `promo_code`, `discount_percent`, `content` | Enforce: title <= 80, promo_code <= 15, discount (1-99), content <= 1000 |
| `/api/reviews` | POST | `rating`, `comment` | Enforce: rating in 1-5, comment <= 300 |
| `/api/chat/send` | POST | `message` | Enforce: message <= 250 |
| `/api/bookings/refund-request` | POST | `account_name`, `account_number`, `notes` | Enforce: acct_name <= 50, acct_num <= 16, notes <= 200 |


## PART 4: SYSTEM BUSINESS LIMITS & CONSTRAINTS

| Area / Feature | Current Value | Recommended Limit / Guard | Notes |
|---|---|---|---|
| **Image & File Uploads** (License, Proof of Payment, Inspection) | Unlimited base64 / Multipart | **Max 5 MB per file**, JPG/PNG/WEBP only | Prevents memory exhaustion / payload crash |
| **Driver Age Limit** | Validated in utils/backend | **18 to 75 years old** | Already enforced in validation |
| **License Expiry Range** | Validated in utils/backend | **Current date up to +10 years** | Already enforced in validation |
| **Rental Duration Limit** | `max_booking_duration_days` | **[DEFERRED - WAG GALAWIN]** | Explicitly kept as-is per user instruction |
| **Mileage / Odometer Reading** | Number input without max | **Min: last recorded odometer, Max: 999,999 km** | Rejects negative or impossible numbers |
| **Fuel Tank Level** | Enum select | **Full, 3/4, 1/2, 1/4, Empty** | Strict enum selection |
| **Security Deposit & Refund Amounts** | Number input | **Min: 0, Max: Booking total price** | Prevents negative or over-refund amounts |
