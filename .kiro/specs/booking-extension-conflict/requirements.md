# Booking Extension with Conflict Resolution

## Overview
Allow customers who currently possess a rented vehicle to request booking extensions. When an extension conflicts with future bookings, the system prioritizes the current renter and automatically handles the conflict by notifying affected customers and offering alternative solutions.

## Business Problem
Currently, when a customer wants to extend their rental period, there's no automated way to handle conflicts with existing future bookings. This creates manual work for admins and poor customer experience for those whose bookings get displaced.

## Core Business Rule: "Possession Priority"
**The customer who currently has physical possession of the vehicle has priority for extension requests over customers with future bookings.**

Rationale: A customer who already has the vehicle should not be forced to return it if they need more time, as they are the active user. Future bookings should be flexible to accommodate the current renter's needs.

---

## User Stories

### US1: Customer Requests Booking Extension
**As a** customer currently renting a vehicle  
**I want to** request an extension of my rental period  
**So that** I can keep the vehicle longer without returning and re-booking

**Acceptance Criteria:**
- Customer can request extension only if they have an active (picked-up) booking
- Customer selects new return date (must be after current return date)
- System calculates additional cost for extended period
- Extension request is sent to admin for approval
- Customer receives confirmation that request was submitted

### US2: Admin Reviews Extension Request Without Conflict
**As an** admin  
**I want to** review and approve extension requests that don't conflict with other bookings  
**So that** I can quickly process straightforward extensions

**Acceptance Criteria:**
- Admin sees extension request with customer details, vehicle info, current dates, and requested new date
- System shows if extension is conflict-free (no other bookings overlap)
- Admin can approve or deny the request
- If approved, booking is updated and customer is notified
- Additional payment is calculated and added to the booking

### US3: Admin Reviews Extension Request With Conflict
**As an** admin  
**I want to** see which future bookings will be affected when approving an extension  
**So that** I can make an informed decision about displacement

**Acceptance Criteria:**
- System automatically detects if extension overlaps with future approved bookings
- Admin sees list of affected bookings (customer names, dates, payment status)
- Admin can still approve extension despite conflicts (possession priority rule)
- System warns admin that affected customers will be notified
- Admin confirms approval understanding the impact

### US4: Affected Customer Receives Conflict Notification
**As a** customer whose future booking is displaced by an extension  
**I want to** be immediately notified and given clear options  
**So that** I can quickly resolve the situation

**Acceptance Criteria:**
- Customer receives notification (push + email) immediately after extension approval
- Notification clearly states:
  - Their booking is no longer available due to extension by current renter
  - Vehicle details and affected dates
  - Two available options
- Customer must take action (cannot ignore)
- Notification includes deadline to respond (e.g., 48 hours)

### US5: Affected Customer Chooses Alternative Vehicle
**As an** affected customer  
**I want to** be offered the closest match to my original vehicle  
**So that** I get a similar or better vehicle without extra cost

**Acceptance Criteria:**
- System searches for alternatives using priority matching algorithm (see FR4)
- Best matches are shown first (same brand + same price)
- If no exact matches, show near matches (similar brand or similar price)
- Customer can view vehicle details and select replacement
- Original booking is updated with new vehicle
- Customer receives confirmation of new booking details
- No refund needed, just vehicle swap

### US6: Affected Customer Cancels for Full Refund
**As an** affected customer  
**I want to** cancel my booking with a full refund  
**So that** I'm not financially impacted by the unavailability

**Acceptance Criteria:**
- Customer selects "Cancel with Full Refund" option
- System immediately marks booking as "Cancelled - Vehicle Unavailable"
- Full refund is processed automatically (100% of paid amount)
- Customer receives refund confirmation with timeline (e.g., 3-5 business days)
- Cancellation reason is logged as "Extension Conflict"
- No cancellation penalties apply

---

## Functional Requirements

### FR1: Extension Request Eligibility
- Only customers with booking status = "Active" (vehicle picked up) can request extensions
- Extension request must be for date AFTER current return date
- Customer cannot extend beyond vehicle's maximum rental period (if such limit exists)
- Customer must have no outstanding payment issues

### FR2: Conflict Detection Algorithm
System must automatically detect conflicts when:
- Admin approves an extension request
- New end date overlaps with any "Approved" or "Pending" future bookings for the same vehicle

Detection logic:
```
IF extension_new_end_date >= future_booking_start_date
AND current_booking_vehicle_id == future_booking_vehicle_id
AND future_booking_status IN ('Approved', 'Pending')
THEN flag as conflict
```

### FR3: Conflict Resolution Workflow
When extension approval creates conflict:
1. System approves the extension request
2. System identifies all affected bookings
3. For each affected booking:
   - Update status to "Conflict - Action Required"
   - Send multi-channel notification (push + email)
   - Create conflict resolution record
4. System waits for customer response
5. If no response within 48 hours, send reminder notification
6. If still no response after 72 hours, auto-cancel with full refund

### FR4: Alternative Vehicle Selection Logic - Priority Matching Algorithm

**Priority Tier 1: Exact Match** (Highest Priority)
- Same brand AND same price (±2% tolerance)
- Same category as original
- Available for exact same dates

**Priority Tier 2: Near Match** (If Tier 1 has no results)
- Same brand OR same price (±5% tolerance)
- Same category as original
- Available for exact same dates
- Sort by: Brand match first, then price proximity

**Priority Tier 3: Category Match** (If Tier 2 has no results)
- Same category as original
- Available for exact same dates
- Any brand, any price (±10% tolerance)
- Sort by: Price proximity

**No Alternatives Available:**
- If no vehicles found in any tier, hide "Choose Alternative Vehicle" option
- Show only "Full Refund" option with clear message:
  > "Unfortunately, no alternative vehicles are available for your dates. We will process a full refund immediately."

**Search Constraints:**
- Vehicle must be "Available" status
- Vehicle must not have overlapping bookings for the required dates
- Vehicle must be in same location/branch as original booking
- Vehicle must meet minimum quality standards (not "Under Maintenance")

**Display to Customer:**
```
If Tier 1 found: "? Perfect Match - Same brand and price"
If Tier 2 found: "~ Close Match - Similar to your original booking"
If Tier 3 found: "Alternative Available - Same category, different brand/price"
If None found: "No alternatives available - Full refund only"
```

**Customer Selection:**
- Customer can view up to 5 best matches
- Each option shows: Vehicle photo, brand, model, price comparison, feature highlights
- Customer confirms selection
- Original booking_id is updated with new vehicle_id
- Confirmation sent to customer

### FR5: Refund Processing
When customer chooses full refund:
- Calculate refund amount = 100% of payment received
- Initiate refund through original payment method (GCash/Maya/PayMongo)
- Update booking status to "Cancelled - Extension Conflict"
- Log refund transaction
- Send refund receipt to customer

### FR6: Extension Payment Calculation
When extension is approved:
- Calculate additional days = new_end_date - original_end_date
- Calculate additional cost = additional_days × daily_rate
- Add late return buffer if extension is requested after original return date
- Send payment request to customer
- Block vehicle return until extension payment is received

---

## Non-Functional Requirements

### NFR1: Performance
- Conflict detection must complete within 2 seconds
- Notification delivery must occur within 30 seconds of extension approval
- Alternative vehicle search must return results within 3 seconds

### NFR2: Reliability
- System must handle simultaneous extension requests for the same vehicle
- All database updates must be atomic (extension approval + conflict notifications)
- Failed notifications must retry up to 3 times

### NFR3: Usability
- Conflict notification must be clear and non-technical
- Alternative vehicle selection must show side-by-side comparison
- Entire conflict resolution flow should take customer < 5 minutes

### NFR4: Auditability
- All extension requests, approvals, and conflicts must be logged
- Customer choices (alternative vehicle or refund) must be timestamped
- Admin actions must be tracked with admin_id and timestamp

---

## Business Rules

### BR1: Possession Priority
Current renter always has priority over future bookings when requesting extensions.

### BR2: Full Refund Guarantee
Customers displaced by extensions receive 100% refund with no penalties or fees.

### BR3: Smart Alternative Matching
When offering alternative vehicles, system uses 3-tier priority matching:
1. **Tier 1:** Same brand + same price (exact match)
2. **Tier 2:** Same brand OR same price (near match)
3. **Tier 3:** Same category only (fallback)
4. **No match:** Only full refund option displayed

### BR4: Price Protection
Customers choosing alternative vehicles never pay more than their original booking rate.

### BR5: Response Deadline
Affected customers must respond within 72 hours or automatic cancellation with refund occurs.

### BR6: Extension Limits
- Customer can only request one extension per active booking
- Extension cannot exceed 30 additional days
- Extension must be requested at least 24 hours before original return date

---

## Edge Cases & Constraints

### EC1: Multiple Conflicting Bookings
**Scenario:** Extension affects 3 future bookings  
**Solution:** All affected customers receive notifications simultaneously and each resolves independently

### EC2: No Alternative Vehicles Available
**Scenario:** No vehicles match any tier in priority algorithm  
**Solution:** System automatically hides "Choose Alternative Vehicle" option and shows only "Full Refund" with explanation message. Customer receives immediate refund processing.

### EC2.1: Only Lower-Tier Alternatives Available
**Scenario:** Original vehicle is Toyota Vios ?2,500/day. Only Tier 3 match available (Honda City ?2,800/day - different brand, higher price)  
**Solution:** Show the alternative with clear labeling "Alternative Available (Different brand)" and note that company absorbs the ?300/day difference. Customer pays original ?2,500/day rate.

### EC3: Extension Request on Last Day
**Scenario:** Customer requests extension on the day of return  
**Solution:** Charge late return fee + extension fee; mark as "Late Extension"

### EC4: Customer Already Displaced Once
**Scenario:** Customer's replacement booking also gets displaced by another extension  
**Solution:** Offer priority upgrade to higher category vehicle at no extra cost + apology credit

### EC5: Payment Failure for Extension
**Scenario:** Current renter's extension payment fails  
**Solution:** Extension is revoked, affected bookings are restored, current renter must return vehicle by original date

### EC6: Simultaneous Extension Requests
**Scenario:** Two customers with sequential bookings both request extensions  
**Solution:** Process in chronological order (current renter first, then next renter)

---

## Success Metrics

### Customer Satisfaction
- 90%+ of affected customers choose alternative vehicle over refund
- Average resolution time < 10 minutes
- Customer satisfaction score ? 4.5/5 for conflict handling

### Operational Efficiency
- 100% automated conflict detection (no manual checking needed)
- 80%+ of conflicts resolved without admin intervention
- Average admin time per extension approval < 2 minutes

### Financial Impact
- Extension revenue tracked separately
- Refund rate < 20% of conflict cases
- Extension approval rate > 85%

---

## Out of Scope (Future Enhancements)

- Dynamic pricing for extensions (surge pricing during high demand)
- Customer-initiated vehicle swaps without admin approval
- Automatic extension approval based on vehicle availability
- Extension insurance/protection plans
- Multi-vehicle extensions (customer renting multiple vehicles)

---

## Dependencies

### Internal Dependencies
- Notification system (push, email, SMS) must be operational
- Payment gateway must support partial charges for extensions
- Refund processing system must be integrated

### External Dependencies
- PayMongo/GCash/Maya APIs for payment and refund
- SMS gateway for notifications
- Email service provider

---

## Questions for Stakeholders

1. Should there be a limit on how many times a customer can be displaced before receiving compensation/upgrade?
2. What happens if a customer disputes the displacement and demands their original vehicle?
3. Should we offer incentives (discount codes) to customers who choose alternative vehicles?
4. What if the current renter damages the vehicle during extension period - does insurance coverage extend automatically?
5. Should admins have the ability to override the possession priority rule in special cases?

---

**Status:** Requirements Defined  
**Next Step:** Design Phase  
**Estimated Complexity:** High  
**Priority:** Medium  
**Target Release:** Q2 2026
