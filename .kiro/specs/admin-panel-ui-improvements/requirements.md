# Requirements Document

## Introduction

This document specifies the requirements for UI/UX improvements to the Autoride Admin Panel. The improvements focus on enhancing readability, accessibility, and usability across multiple sections including booking management, dashboard analytics, live chat, print views, and customer mobile interface. These enhancements aim to provide administrators with better visibility into booking details, customer information, and system analytics while improving the overall user experience.

## Glossary

- **Admin_Panel**: The web-based administrative interface used by Autoride staff to manage bookings, vehicles, users, and system operations
- **Booking_Details_Modal**: A popup dialog that displays comprehensive information about a specific booking
- **Customer_Preview_Popup**: A modal window that shows customer profile information including license details
- **Dashboard**: The main analytics view displaying charts and key performance indicators
- **Chart_Popup**: An enlarged modal view of a dashboard chart with interactive controls
- **Live_Chat**: The real-time messaging interface between administrators and customers
- **Print_View**: A printer-friendly page layout for generating physical or PDF documents
- **Booking_Record**: A single entry in the bookings database containing rental transaction details
- **Active_Booking**: A booking currently in progress with status "Active" or "In Progress"
- **Past_Booking**: A completed booking with status "Completed" or "Finished"
- **Cancelled_Booking**: A booking that was terminated before completion with status "Cancelled"
- **Customer_Mobile_App**: The mobile application interface used by customers to view and manage their bookings
- **Recent_Booking_Section**: A UI component in the customer mobile app displaying the user's most recent booking

## Requirements

### Requirement 1: Enhanced Booking Details Readability

**User Story:** As an administrator, I want larger font sizes in the booking details modal, so that I can read booking information more easily without straining my eyes.

#### Acceptance Criteria

1. WHEN THE Admin_Panel displays THE Booking_Details_Modal, THE Admin_Panel SHALL render all text content with font sizes increased by at least 15% compared to the current implementation
2. THE Booking_Details_Modal SHALL maintain proper text hierarchy with headings at least 1.2rem, body text at least 0.95rem, and labels at least 0.85rem
3. THE Booking_Details_Modal SHALL ensure all text remains fully visible without overflow or truncation after font size increases
4. THE Booking_Details_Modal SHALL maintain responsive layout that adapts to increased text sizes on mobile and desktop viewports

### Requirement 2: Customer Profile Preview in Booking Details

**User Story:** As an administrator, I want to see customer profile pictures and license details when viewing booking information, so that I can quickly verify customer identity and license validity.

#### Acceptance Criteria

1. WHEN an administrator views THE Booking_Details_Modal, THE Admin_Panel SHALL display a clickable customer profile section
2. WHEN an administrator clicks the customer profile section, THE Admin_Panel SHALL open THE Customer_Preview_Popup
3. THE Customer_Preview_Popup SHALL display the customer's profile picture if available, or a default avatar if not
4. THE Customer_Preview_Popup SHALL display the customer's license photo if uploaded
5. THE Customer_Preview_Popup SHALL display the license number, license type, and expiry date
6. IF the license expiry date is within 30 days or expired, THEN THE Customer_Preview_Popup SHALL highlight the expiry date with a warning indicator
7. THE Customer_Preview_Popup SHALL provide a close button to dismiss the popup

### Requirement 3: Expandable Dashboard Charts

**User Story:** As an administrator, I want to click on dashboard charts to view them in a larger size, so that I can analyze trends and data points more clearly.

#### Acceptance Criteria

1. WHEN THE Dashboard displays a chart, THE Admin_Panel SHALL make the chart clickable
2. WHEN an administrator clicks a chart, THE Admin_Panel SHALL open THE Chart_Popup displaying the enlarged chart
3. THE Chart_Popup SHALL render the chart at minimum 150% of its original size
4. THE Chart_Popup SHALL maintain the chart's data, labels, and visual styling from the original view
5. THE Chart_Popup SHALL provide a close button or overlay click to dismiss the popup
6. THE Chart_Popup SHALL be responsive and scale appropriately on mobile devices

### Requirement 4: Chart Filter Controls in Popup

**User Story:** As an administrator, I want filter and slicer controls in the enlarged chart popup, so that I can interactively explore different data segments and time ranges.

#### Acceptance Criteria

1. WHEN THE Chart_Popup is displayed, THE Admin_Panel SHALL render filter controls above or beside the enlarged chart
2. THE Chart_Popup SHALL provide a date range filter with start date and end date inputs
3. THE Chart_Popup SHALL provide category filters relevant to the chart type (e.g., vehicle type, booking status, location)
4. WHEN an administrator changes a filter value, THE Admin_Panel SHALL update the chart data within 500 milliseconds
5. THE Chart_Popup SHALL display a "Reset Filters" button to restore default filter values
6. THE Chart_Popup SHALL persist filter selections while the popup remains open

### Requirement 5: Live Chat Search Functionality

**User Story:** As an administrator, I want to search through chat conversations, so that I can quickly find specific customer conversations without scrolling through the entire list.

#### Acceptance Criteria

1. THE Live_Chat interface SHALL display a search input field at the top of the conversation list
2. WHEN an administrator types in the search field, THE Admin_Panel SHALL filter conversations in real-time
3. THE Admin_Panel SHALL match search queries against customer names, email addresses, and message content
4. THE Admin_Panel SHALL display matching conversations with search terms highlighted
5. WHEN the search field is empty, THE Admin_Panel SHALL display all conversations
6. THE Live_Chat SHALL display a "No results found" message when no conversations match the search query

### Requirement 6: Print View Navigation

**User Story:** As an administrator, I want a back button in the print view, so that I can easily return to the previous screen without using browser navigation.

#### Acceptance Criteria

1. THE Print_View SHALL display a back button in the top-left corner of the page
2. WHEN an administrator clicks the back button, THE Admin_Panel SHALL navigate to the previous page in the application
3. THE Print_View back button SHALL be visible on screen but hidden when printing to paper or PDF
4. THE Print_View back button SHALL include an icon and label for clarity

### Requirement 7: Location Field in Active Bookings

**User Story:** As an administrator, I want to see the pickup/dropoff location in the Active Now tab, so that I can quickly identify where active rentals are taking place.

#### Acceptance Criteria

1. WHEN THE Admin_Panel displays THE Active_Booking list in the "Active Now" tab, THE Admin_Panel SHALL include a location field for each Booking_Record
2. THE Active_Booking list SHALL display the pickup location as the primary location field
3. IF the dropoff location differs from the pickup location, THEN THE Admin_Panel SHALL display both pickup and dropoff locations
4. THE location field SHALL be clearly labeled and positioned prominently in the booking card or row
5. THE location field SHALL truncate long location names with ellipsis and show full text on hover

### Requirement 8: Past Bookings List View

**User Story:** As an administrator, I want a dedicated list view for past/finished bookings, so that I can review completed transactions and rental history.

#### Acceptance Criteria

1. THE Admin_Panel SHALL provide a "Past Bookings" or "Finished" tab in the bookings section
2. WHEN an administrator navigates to the Past Bookings tab, THE Admin_Panel SHALL display all Past_Booking records
3. THE Past_Booking list SHALL display booking ID, customer name, vehicle, rental dates, total price, and completion date
4. THE Past_Booking list SHALL support sorting by completion date, customer name, and total price
5. THE Past_Booking list SHALL support pagination with configurable page size (10, 25, 50, 100 records per page)
6. WHEN an administrator clicks a Past_Booking record, THE Admin_Panel SHALL open THE Booking_Details_Modal

### Requirement 9: Cancelled Bookings List View

**User Story:** As an administrator, I want a dedicated list view for cancelled bookings, so that I can track cancellation patterns and review refund history.

#### Acceptance Criteria

1. THE Admin_Panel SHALL provide a "Cancelled Bookings" tab in the bookings section
2. WHEN an administrator navigates to the Cancelled Bookings tab, THE Admin_Panel SHALL display all Cancelled_Booking records
3. THE Cancelled_Booking list SHALL display booking ID, customer name, vehicle, original rental dates, cancellation date, cancellation reason, and cancelled_by field
4. THE Cancelled_Booking list SHALL support sorting by cancellation date, customer name, and original booking date
5. THE Cancelled_Booking list SHALL support pagination with configurable page size (10, 25, 50, 100 records per page)
6. WHEN an administrator clicks a Cancelled_Booking record, THE Admin_Panel SHALL open THE Booking_Details_Modal showing cancellation details

### Requirement 10: Remove Recent Booking Section from Customer Mobile

**User Story:** As a product manager, I want to remove the recent booking section from the customer mobile app, so that we can simplify the interface and reduce visual clutter.

#### Acceptance Criteria

1. THE Customer_Mobile_App SHALL NOT display THE Recent_Booking_Section on any screen
2. THE Customer_Mobile_App SHALL remove all UI components, styles, and logic related to THE Recent_Booking_Section
3. THE Customer_Mobile_App SHALL maintain access to booking history through the existing bookings list or history screen
4. THE Customer_Mobile_App layout SHALL adjust to fill the space previously occupied by THE Recent_Booking_Section
