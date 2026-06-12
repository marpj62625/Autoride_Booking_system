# -*- coding: utf-8 -*-
"""Fix orphaned ')' lines and broken SMS comment blocks in app.py"""
import re

path = r'c:\Users\patri\OneDrive\Desktop\AutorideSystem2sides\AutorideSystem\backend\app.py'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

orig_len = len(src)

# ?????????????????????????????????????????????????????????????????????????????
# Pattern: these broken blocks all look like:
#
#   # Send SMS notification
#   [optional: <some dead code lines that produce no output>]
#
#   )
#
# followed by a kept notification_service.notify_user() call.
#
# Strategy: remove the "# Send SMS notification" comment + any orphaned dead
# lines up to and including the lone ')' that precedes notification_service.
# ?????????????????????????????????????????????????????????????????????????????

# Fix 1: cancel_booking (customer) - has orphaned `reason = ...` line too
src = src.replace(
    '            # Send SMS notification\n'
    '            reason = (data or {}).get(\'reason\', \'No reason provided\')\n'
    '\n'
    '\n'
    '            )\n'
    '\n'
    '            notification_service.notify_user(\n'
    '\n'
    '                bk[\'user_id\'],\n'
    '\n'
    '                "Booking Cancelled",\n'
    '\n'
    '                f"Your booking #{booking_id} has been cancelled. Reason: {reason}.",\n'
    '\n'
    '                \'booking_cancelled\'\n'
    '\n'
    '            )',

    '            reason = (data or {}).get(\'reason\', \'No reason provided\')\n'
    '            # Send in-app notification\n'
    '            notification_service.notify_user(\n'
    '                bk[\'user_id\'],\n'
    '                "Booking Cancelled",\n'
    '                f"Your booking #{booking_id} has been cancelled. Reason: {reason}.",\n'
    '                \'booking_cancelled\'\n'
    '            )'
)

# Fix 2: modify_booking - orphaned ) before notification_service
src = src.replace(
    '        # Send SMS notification to customer\n'
    '        try:\n'
    '            cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))\n'
    '            bk_row = cur.fetchone()\n'
    '            if bk_row:\n'
    '                )\n'
    '                notification_service.notify_user(\n'
    '                    bk_row[\'user_id\'],\n'
    '                    "Booking Updated",\n'
    '                    f"Your booking #{booking_id} dates have been updated: {new_start} to {new_end}. New total: PHP {round(new_total, 2)}.",\n'
    '                    \'booking_modified\'\n'
    '                )\n'
    '        except Exception as sms_err:\n'
    '            print(f"ERROR SENDING MODIFY BOOKING SMS: {sms_err}")',

    '        # Send in-app notification to customer\n'
    '        try:\n'
    '            cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))\n'
    '            bk_row = cur.fetchone()\n'
    '            if bk_row:\n'
    '                notification_service.notify_user(\n'
    '                    bk_row[\'user_id\'],\n'
    '                    "Booking Updated",\n'
    '                    f"Your booking #{booking_id} dates have been updated: {new_start} to {new_end}. New total: PHP {round(new_total, 2)}.",\n'
    '                    \'booking_modified\'\n'
    '                )\n'
    '        except Exception as notif_err:\n'
    '            print(f"ERROR SENDING MODIFY BOOKING NOTIFICATION: {notif_err}")'
)

# Fix 3: split request - orphaned ) inside if partner_row block
src = src.replace(
    '            if partner_row:\n'
    '                )\n'
    '                notification_service.notify_user(\n'
    '                    partner_row[\'id\'],\n'
    '                    "Split Payment Request",\n'
    '                    f"{initiator_name} has requested a split payment for booking #{booking_id}. Your share: PHP {float(amount)}.",\n'
    '                    \'split_request\'\n'
    '                )\n'
    '        except Exception as sms_err:\n'
    '            print(f"ERROR SENDING SPLIT REQUEST SMS: {sms_err}")',

    '            if partner_row:\n'
    '                notification_service.notify_user(\n'
    '                    partner_row[\'id\'],\n'
    '                    "Split Payment Request",\n'
    '                    f"{initiator_name} has requested a split payment for booking #{booking_id}. Your share: PHP {float(amount)}.",\n'
    '                    \'split_request\'\n'
    '                )\n'
    '        except Exception as notif_err:\n'
    '            print(f"ERROR SENDING SPLIT REQUEST NOTIFICATION: {notif_err}")'
)

# Fix 4: split paid - orphaned ) inside if sp_row and bk_row block
src = src.replace(
    '                if sp_row and bk_row:\n'
    '                    )\n'
    '                    notification_service.notify_user(\n'
    '                        bk_row[\'user_id\'],\n'
    '                        "Split Payment Received",\n'
    '                        f"Your split payment partner has paid PHP {float(sp_row[\'amount\'])} for booking #{b_id[\'booking_id\']}.",\n'
    '                        \'split_paid\'\n'
    '                    )\n'
    '        except Exception as sms_err:\n'
    '            print(f"ERROR SENDING SPLIT PAID SMS: {sms_err}")',

    '                if sp_row and bk_row:\n'
    '                    notification_service.notify_user(\n'
    '                        bk_row[\'user_id\'],\n'
    '                        "Split Payment Received",\n'
    '                        f"Your split payment partner has paid PHP {float(sp_row[\'amount\'])} for booking #{b_id[\'booking_id\']}.",\n'
    '                        \'split_paid\'\n'
    '                    )\n'
    '        except Exception as notif_err:\n'
    '            print(f"ERROR SENDING SPLIT PAID NOTIFICATION: {notif_err}")'
)

# Fix 5: approve_booking - orphaned ) before notification_service inside if b_data
src = src.replace(
    '        if b_data:\n'
    '            )\n'
    '            notification_service.notify_user(\n'
    '                b_data[\'user_id\'],\n'
    '                "Booking Approved",\n'
    '                f"Good news! Booking #{booking_id} for {b_data[\'brand\']} {b_data[\'model\']} starting {b_data[\'start_date\']} has been approved.",\n'
    '                \'booking_approved\'\n'
    '            )',

    '        if b_data:\n'
    '            notification_service.notify_user(\n'
    '                b_data[\'user_id\'],\n'
    '                "Booking Approved",\n'
    '                f"Good news! Booking #{booking_id} for {b_data[\'brand\']} {b_data[\'model\']} starting {b_data[\'start_date\']} has been approved.",\n'
    '                \'booking_approved\'\n'
    '            )'
)

# Fix 6: reject_booking - orphaned ) + bad comment
src = src.replace(
    '        # Send SMS notification\n'
    '\n'
    '\n'
    '        )\n'
    '\n'
    '        notification_service.notify_user(\n'
    '\n'
    '            row[\'user_id\'],\n'
    '\n'
    '            "Booking Rejected",\n'
    '\n'
    '            f"Booking #{booking_id} has been rejected. Please contact our support team for assistance.",\n'
    '\n'
    '            \'booking_rejected\'\n'
    '\n'
    '        )',

    '        # Send in-app notification\n'
    '        notification_service.notify_user(\n'
    '            row[\'user_id\'],\n'
    '            "Booking Rejected",\n'
    '            f"Booking #{booking_id} has been rejected. Please contact our support team for assistance.",\n'
    '            \'booking_rejected\'\n'
    '        )'
)

# Fix 7: admin_cancel_booking - orphaned ) after reason line, before raw psycopg insert
src = src.replace(
    '        # Send SMS notification\n'
    '\n'
    '        reason = (request.json or {}).get(\'reason\', \'No reason provided\')\n'
    '\n'
    '\n'
    '        )\n'
    '\n'
    '        # Insert notification using a fresh connection',

    '        reason = (request.json or {}).get(\'reason\', \'No reason provided\')\n'
    '\n'
    '        # Insert notification using a fresh connection'
)

# Fix 8: pickup_booking - orphaned ) inside if b_data
src = src.replace(
    '        if b_data:\n'
    '\n'
    '\n'
    '            )\n'
    '\n'
    '            notification_service.notify_user(\n'
    '\n'
    '                b_data[\'user_id\'],\n'
    '\n'
    '                "Vehicle Picked Up",\n'
    '\n'
    '                f"Drive safely! Booking #{booking_id} for {b_data[\'brand\']} {b_data[\'model\']} is now active. Return by {b_data[\'end_date\']}.",\n'
    '\n'
    '                \'booking_picked_up\'',

    '        if b_data:\n'
    '            notification_service.notify_user(\n'
    '                b_data[\'user_id\'],\n'
    '                "Vehicle Picked Up",\n'
    '                f"Drive safely! Booking #{booking_id} for {b_data[\'brand\']} {b_data[\'model\']} is now active. Return by {b_data[\'end_date\']}.",\n'
    '                \'booking_picked_up\''
)

# Fix 9: complete_booking - orphaned ) inside if b_data
src = src.replace(
    '        # Send SMS notification\n'
    '\n'
    '        cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))\n'
    '\n'
    '        b_data = cur.fetchone()\n'
    '\n'
    '        if b_data:\n'
    '\n'
    '\n'
    '            )\n'
    '\n'
    '            notification_service.notify_user(\n'
    '\n'
    '                b_data[\'user_id\'],\n'
    '\n'
    '                "Booking Completed",\n'
    '\n'
    '                f"Thank you for choosing Autoride! Booking #{booking_id} is now completed. We hope to see you again.",\n'
    '\n'
    '                \'booking_completed\'',

    '        cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))\n'
    '        b_data = cur.fetchone()\n'
    '        if b_data:\n'
    '            notification_service.notify_user(\n'
    '                b_data[\'user_id\'],\n'
    '                "Booking Completed",\n'
    '                f"Thank you for choosing Autoride! Booking #{booking_id} is now completed. We hope to see you again.",\n'
    '                \'booking_completed\''
)

# Fix 10: approve_driver - orphaned ) inside if d_data
src = src.replace(
    '        if d_data:\n'
    '\n'
    '\n'
    '            )\n'
    '\n'
    '            notification_service.notify_user(\n'
    '\n'
    '                d_data[\'user_id\'],\n'
    '\n'
    '                "Driver Application Approved",\n'
    '\n'
    '                f"Congratulations, {d_data[\'full_name\']}! Your driver application has been approved. You can now start accepting bookings.",\n'
    '\n'
    '                \'driver_approved\'',

    '        if d_data:\n'
    '            notification_service.notify_user(\n'
    '                d_data[\'user_id\'],\n'
    '                "Driver Application Approved",\n'
    '                f"Congratulations, {d_data[\'full_name\']}! Your driver application has been approved. You can now start accepting bookings.",\n'
    '                \'driver_approved\''
)

# Fix 11: reject_driver - orphaned ) inside if d_data
src = src.replace(
    '        if d_data:\n'
    '\n'
    '\n'
    '            )\n'
    '\n'
    '            notification_service.notify_user(\n'
    '\n'
    '                d_data[\'user_id\'],\n'
    '\n'
    '                "Driver Application Rejected",\n'
    '\n'
    '                f"Your driver application was not approved. Reason: {reason}. You may re-apply once the issues are resolved.",\n'
    '\n'
    '                \'driver_rejected\'',

    '        if d_data:\n'
    '            notification_service.notify_user(\n'
    '                d_data[\'user_id\'],\n'
    '                "Driver Application Rejected",\n'
    '                f"Your driver application was not approved. Reason: {reason}. You may re-apply once the issues are resolved.",\n'
    '                \'driver_rejected\''
)

# Fix 12: user_cancel_booking - empty try: block
src = src.replace(
    '        # Notifications\n'
    '        try:\n'
    '        except Exception:\n'
    '            pass\n'
    '        try:\n',

    '        # Notifications\n'
    '        try:\n'
)

# Fix 13: pickup_booking - also has "# Send SMS notification" comment to clean
src = src.replace(
    '        # Send SMS notification\n'
    '\n'
    '        cur.execute(\n'
    '\n'
    '            """SELECT b.user_id, v.brand, v.model, b.end_date\n'
    '\n'
    '               FROM bookings b\n'
    '\n'
    '               JOIN vehicles v ON b.vehicle_id = v.id\n'
    '\n'
    '               WHERE b.id = %s""",\n'
    '\n'
    '            (booking_id,)\n'
    '\n'
    '        )',

    '        cur.execute(\n'
    '            """SELECT b.user_id, v.brand, v.model, b.end_date\n'
    '               FROM bookings b\n'
    '               JOIN vehicles v ON b.vehicle_id = v.id\n'
    '               WHERE b.id = %s""",\n'
    '            (booking_id,)\n'
    '        )'
)

# Fix 14: also remove leftover "# Send SMS notification" comment lines that
#         have no associated code below (just dangling comments)
src = re.sub(r'\n        # Send SMS notification\s*\n\s*\n\s*(?=\n)', '\n', src)
src = re.sub(r'\n        # Send SMS notification to customer\s*\n\s*\n\s*(?=\n)', '\n', src)

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)

print(f"Fixed app.py: {orig_len} -> {len(src)} chars")

# ?????????????????????????????????????????????????????????????????????????????
# Fix frontend/login.html - missing </script> before <script src="chat.js">
# ?????????????????????????????????????????????????????????????????????????????

login_path = r'c:\Users\patri\OneDrive\Desktop\AutorideSystem2sides\AutorideSystem\frontend\login.html'
with open(login_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Check if </script> is missing before <script src="chat.js">
if '    </script>\n    <script src="chat.js">' not in html and \
   '        });' in html and \
   '    <script src="chat.js"></script>' in html:
    # Find the last }); before <script src="chat.js"> and add closing </script>
    html = html.replace(
        '    <script src="chat.js"></script>\n</body>\n</html>',
        '    </script>\n    <script src="chat.js"></script>\n</body>\n</html>'
    )
    with open(login_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Fixed login.html: added missing </script>")
else:
    print("login.html: no fix needed for </script>")

print("Done.")
