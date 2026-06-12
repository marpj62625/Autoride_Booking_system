import re

with open('backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the start and end of the breakdown and html generation
start_str = "    # Build breakdown rows"
end_str = "    print('RECEIPT EMAIL - TO: ' + email + ' BOOKING: #' + booking_id)"

start_idx = content.find(start_str)
end_idx = content.find(end_str)

if start_idx != -1 and end_idx != -1:
    new_html_logic = '''    # Build breakdown rows for POS style receipt
    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = (
        "<body style='margin:0;padding:20px;background:#f0f0f0;font-family:Arial,sans-serif;'>"
        "<div style='max-width:380px;margin:0 auto;background:#fff;padding:20px;color:#000;box-shadow:0 2px 10px rgba(0,0,0,0.1);'>"
        "<div style='text-align:center;margin-bottom:15px;'>"
        "<h2 style='margin:0;font-size:22px;letter-spacing:1px;text-transform:uppercase;'>AUTORIDE</h2>"
        "<p style='margin:2px 0 0;font-size:12px;'>Your ride, your way</p>"
        "</div>"
        
        "<div style='text-align:center;font-weight:bold;font-size:16px;margin:15px 0;border-top:1px dashed #000;border-bottom:1px dashed #000;padding:8px 0;letter-spacing:2px;'>"
        "INVOICE"
        "</div>"
        
        "<table width='100%' style='font-size:13px;margin-bottom:15px;line-height:1.4;'>"
        "<tr><td width='35%'>Booking No</td><td width='65%' style='text-align:right;'>" + booking_id + "</td></tr>"
        "<tr><td>Date</td><td style='text-align:right;'>" + now_str + "</td></tr>"
        "<tr><td>Customer</td><td style='text-align:right;'>" + full_name + "</td></tr>"
        "<tr><td>Rental Period</td><td style='text-align:right;'>" + start_date + " to " + end_date + "</td></tr>"
        "<tr><td>Vehicle</td><td style='text-align:right;'>" + brand + " " + model_name + "</td></tr>"
        "</table>"
        
        "<div style='border-top:1px dashed #000;margin:10px 0;'></div>"
        
        "<table width='100%' style='font-size:13px;margin-bottom:10px;'>"
        "<tr>"
        "<th style='text-align:left;padding-bottom:5px;width:65%;'>Item</th>"
        "<th style='text-align:center;padding-bottom:5px;width:10%;'>Qty</th>"
        "<th style='text-align:right;padding-bottom:5px;width:25%;'>Amount</th>"
        "</tr>"
        
        "<tr>"
        "<td style='padding:3px 0;'>Base Rental</td>"
        "<td style='text-align:center;padding:3px 0;'>1</td>"
        "<td style='text-align:right;padding:3px 0;'>" + '{:,.2f}'.format(base_price) + "</td>"
        "</tr>"
    )
    
    if addon_price > 0 and addons_raw and addons_raw != 'None':
        addon_list = [a.strip() for a in addons_raw.split(',') if a.strip()]
        for addon in addon_list:
            html += (
                "<tr>"
                "<td style='padding:3px 0;'>- " + addon + "</td>"
                "<td style='text-align:center;padding:3px 0;'>1</td>"
                "<td style='text-align:right;padding:3px 0;'>" + '{:,.2f}'.format(addon_price / max(1, len(addon_list))) + "</td>"
                "</tr>"
            )
            
    if insurance_price > 0:
        html += (
            "<tr>"
            "<td style='padding:3px 0;'>Insurance (" + insurance_text + ")</td>"
            "<td style='text-align:center;padding:3px 0;'>1</td>"
            "<td style='text-align:right;padding:3px 0;'>" + '{:,.2f}'.format(insurance_price) + "</td>"
            "</tr>"
        )
        
    if discount_amount > 0:
        html += (
            "<tr>"
            "<td style='padding:3px 0;'>Discount</td>"
            "<td style='text-align:center;padding:3px 0;'></td>"
            "<td style='text-align:right;padding:3px 0;'>-" + '{:,.2f}'.format(discount_amount) + "</td>"
            "</tr>"
        )
        
    html += (
        "</table>"
        "<div style='border-top:1px dashed #000;margin:10px 0;'></div>"
        
        "<table width='100%' style='font-size:14px;margin-bottom:15px;'>"
        "<tr>"
        "<td><strong>TOTAL (PHP)</strong></td>"
        "<td style='text-align:right;'><strong>" + '{:,.2f}'.format(total_price) + "</strong></td>"
        "</tr>"
    )
    
    if payment_type == 'Downpayment' and balance_amount > 0:
        html += (
            "<tr>"
            "<td style='padding-top:5px;font-size:13px;'>Paid Now (20%)</td>"
            "<td style='text-align:right;padding-top:5px;font-size:13px;'>" + '{:,.2f}'.format(amount_paid) + "</td>"
            "</tr>"
            "<tr>"
            "<td style='padding-top:3px;font-size:13px;'>Balance</td>"
            "<td style='text-align:right;padding-top:3px;font-size:13px;'>" + '{:,.2f}'.format(balance_amount) + "</td>"
            "</tr>"
        )
    else:
        html += (
            "<tr>"
            "<td style='padding-top:5px;font-size:13px;'>Amount Paid</td>"
            "<td style='text-align:right;padding-top:5px;font-size:13px;'>" + '{:,.2f}'.format(amount_paid) + "</td>"
            "</tr>"
        )
        
    html += (
        "</table>"
        "<div style='border-top:1px dashed #000;margin:10px 0;'></div>"
        
        "<table width='100%' style='font-size:13px;margin-bottom:20px;'>"
        "<tr><td>Payment Method</td><td style='text-align:right;'>" + method + "</td></tr>"
        "<tr><td>Reference No</td><td style='text-align:right;'>" + ref_num + "</td></tr>"
        "</table>"
        
        "<div style='text-align:center;margin:25px 0 15px;'>"
        "<p style='margin:0 0 5px;font-size:13px;'>Please Come Again</p>"
        "<p style='margin:0;font-size:11px;color:#555;'>autoride-booking-system.vercel.app</p>"
        "</div>"
        
        "<div style='text-align:center;margin-top:20px;'>"
        "<a href='" + receipt_url + "' style='display:inline-block;border:1px solid #000;color:#000;text-decoration:none;padding:8px 15px;font-size:12px;text-transform:uppercase;'>Download PDF</a>"
        "</div>"
        
        "</div>"
        "</body>"
    )

'''
    
    content = content[:start_idx] + new_html_logic + content[end_idx:]
    
    with open('backend/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated email receipt layout')
else:
    print('Could not find logic block')
